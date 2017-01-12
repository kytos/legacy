"""Statistics application."""
from kyco.core.napps import KycoNApp
from kyco.utils import listen_to
from pyof.v0x01.controller2switch.stats_request import StatsTypes

from napps.kytos.of_stats import settings
from napps.kytos.of_stats.stats import Description, FlowStats, PortStats
from napps.kytos.of_stats.stats_api import FlowStatsAPI, PortStatsAPI, StatsAPI

log = settings.log


class Main(KycoNApp):
    """Main class for statistics application."""

    def setup(self):
        """Initialize all statistics and set their loop interval."""
        msg_out = self.controller.buffers.msg_out
        self._stats = {StatsTypes.OFPST_DESC.value: Description(msg_out),
                       StatsTypes.OFPST_PORT.value: PortStats(msg_out),
                       StatsTypes.OFPST_FLOW.value: FlowStats(msg_out)}
        self.execute_as_loop(settings.STATS_INTERVAL)
        Description.controller = self.controller

        StatsAPI.controller = self.controller
        FlowStatsAPI.register_endpoints(self.controller)
        PortStatsAPI.register_endpoints(self.controller)
        self.controller.log_websocket.register_log(log)

    def execute(self):
        """Query all switches sequentially and then sleep before repeating."""
        for switch in self.controller.switches.values():
            self._update_stats(switch)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')

    def _update_stats(self, switch):
        for stats in self._stats.values():
            if switch.connection is not None:
                stats.request(switch.connection)

    @listen_to('kytos/of.core.messages.in.ofpt_stats_reply')
    def listener(self, event):
        """Store switch descriptions."""
        msg = event.content['message']
        if msg.body_type.value in self._stats:
            stats = self._stats[msg.body_type.value]
            stats.listen(event.source.switch.dpid, msg.body)
        else:
            log.debug('No listener for %s in %s.', msg.body_type.value,
                      list(self._stats.keys()))
