"""Statistics application."""
import sys
from logging import getLogger
from os.path import dirname
from threading import Event

from kyco.constants import POOLING_TIME
from kyco.core.napps import KycoNApp
from kyco.utils import listen_to
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.common import PortStatsRequest
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes

sys.path.insert(0, dirname(__file__))
from stats import Stats
sys.path.pop(0)

log = getLogger('Stats')


class Main(KycoNApp):
    """Main class for statistics application."""

    def setup(self):
        """`__init__` method of KycoNApp."""
        msg_out = self.controller.buffers.msg_out
        self._stats = {StatsTypes.OFPST_DESC.value: Description(msg_out),
                       StatsTypes.OFPST_PORT.value: PortStats(msg_out)}
        # To stop the main loop
        self._stopper = Event()

    def execute(self):
        """Query all switches sequentially and then sleep before repeating."""
        while not self._stopper.is_set():
            for switch in self.controller.switches.values():
                self._update_stats(switch)
            self._stopper.wait(POOLING_TIME)
        log.debug('Thread finished.')

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')
        self._stopper.set()

    def _update_stats(self, switch):
        for stats in self._stats.values():
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


class PortStats(Stats):
    """Deal with PortStats messages."""

    def request(self, conn):
        """Ask for port stats."""
        body = PortStatsRequest(Port.OFPP_NONE)  # All ports
        req = StatsRequest(body_type=StatsTypes.OFPST_PORT, body=body)
        self._send_event(req, conn)
        log.debug('Port Stats request for switch %s sent.', conn.switch.dpid)

    def listen(self, dpid, ports_stats):
        """Receive port stats."""
        for port_stats in ports_stats:
            log.debug('Received port %d stats of switch %s: %s',
                      port_stats.port_no.value, dpid, port_stats.__dict__)


class Description(Stats):
    """Deal with Description messages."""

    def __init__(self, msg_out_buffer):
        """Initialize database."""
        super().__init__(msg_out_buffer)
        # Key is dpid, value is StatsReply object
        self._desc = {}

    def request(self, conn):
        """Ask for switch description. It is done only once per switch."""
        dpid = conn.switch.dpid
        if dpid not in self._desc:
            req = StatsRequest(body_type=StatsTypes.OFPST_DESC)
            self._send_event(req, conn)
            log.debug('Desc request for switch %s sent.', dpid)

    def listen(self, dpid, desc):
        """Store switch description."""
        self._desc[dpid] = desc
        log.debug('Adding switch %s: mfr_desc = %s, hw_desc = %s,'
                  ' sw_desc = %s, serial_num = %s', dpid,
                  desc.mfr_desc, desc.hw_desc, desc.sw_desc,
                  desc.serial_num)
