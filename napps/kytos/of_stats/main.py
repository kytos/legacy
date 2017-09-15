"""Statistics application."""

from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to
from pyof.v0x01.controller2switch.stats_request import StatsTypes

from napps.kytos.of_stats import settings
from napps.kytos.of_stats.stats import Description, FlowStats, PortStats
from napps.kytos.of_stats.stats_api import FlowStatsAPI, PortStatsAPI, StatsAPI


class Main(KytosNApp):
    """Main class for statistics application."""

    def setup(self):
        """Initialize all statistics and set their loop interval."""
        self.execute_as_loop(settings.STATS_INTERVAL)

        # Initialize statistics
        msg_out = self.controller.buffers.msg_out
        self._stats = {StatsTypes.OFPST_DESC.value: Description(msg_out),
                       StatsTypes.OFPST_PORT.value: PortStats(msg_out),
                       StatsTypes.OFPST_FLOW.value: FlowStats(msg_out)}

        # Give Description and StatsAPI the controller
        Description.controller = self.controller
        StatsAPI.controller = self.controller

    def execute(self):
        """Query all switches sequentially and then sleep before repeating."""
        switches = list(self.controller.switches.values())
        for switch in switches:
            if not (switch.is_connected() and
                    switch.connection.protocol.version == 0x01):
                continue
            self._update_stats(switch)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')

    def _update_stats(self, switch):
        for stats in self._stats.values():
            if switch.connection is not None:
                stats.request(switch.connection)

    @listen_to('kytos/of_core.v0x01.messages.in.ofpt_stats_reply')
    def listener(self, event):
        """Store switch descriptions."""
        msg = event.content['message']
        if msg.body_type.value in self._stats:
            stats = self._stats[msg.body_type.value]
            stats.listen(event.source.switch.dpid, msg.body)
        else:
            log.debug('No listener for %s in %s.', msg.body_type.value,
                      list(self._stats.keys()))

    # REST API

    @rest('<dpid>/ports/<int:port>')
    @staticmethod
    def get_port_stats(dpid, port):
        """Return statistics for ``dpid`` and ``port``."""
        return PortStatsAPI.get_port_stats(dpid, port)

    @rest('<dpid>/ports')
    @staticmethod
    def get_ports_list(dpid):
        """Return ports of ``dpid``."""
        return PortStatsAPI.get_ports_list(dpid)

    @rest('<dpid>/flows/<flow_hash>')
    @staticmethod
    def get_flow_stats(dpid, flow_hash):
        """Return statistics of a flow in ``dpid``."""
        return FlowStatsAPI.get_flow_stats(dpid, flow_hash)

    @rest('<dpid>/flows')
    @staticmethod
    def get_flow_list(dpid):
        """Return all flows of ``dpid``."""
        return FlowStatsAPI.get_flow_list(dpid)
