"""Statistics application."""
from abc import ABCMeta, abstractmethod
from logging import getLogger
from pathlib import Path
from threading import Event

import rrdtool

from kyco.constants import POOLING_TIME
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoNApp
from kyco.utils import listen_to
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.common import PortStatsRequest
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes


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


class Stats(metaclass=ABCMeta):
    """Abstract class for Statistics implementation."""

    def __init__(self, msg_out_buffer):
        """Store a reference to the controller's msg_out buffer."""
        self._buffer = msg_out_buffer

    @abstractmethod
    def request(self, conn):
        """Request statistics."""
        pass

    @abstractmethod
    def listen(self, dpid, ports_stats):
        """Listener for statistics."""
        pass

    def _send_event(self, req, conn):
        event = KycoEvent(
            name='kytos/of.stats.messages.out.ofpt_stats_request',
            content={'message': req, 'destination': conn})
        self._buffer.put(event)


class PortStats(Stats):
    """Deal with PortStats messages."""

    def __init__(self, msg_out_buffer):
        """Initialize database."""
        super().__init__(msg_out_buffer)
        self._rrd = RRD()

    def request(self, conn):
        """Ask for port stats."""
        body = PortStatsRequest(Port.OFPP_NONE)  # All ports
        req = StatsRequest(body_type=StatsTypes.OFPST_PORT, body=body)
        self._send_event(req, conn)
        log.debug('Port Stats request for switch %s sent.', conn.switch.dpid)

    def listen(self, dpid, ports_stats):
        """Receive port stats."""
        for ps in ports_stats:
            self._rrd.update(dpid, ps.port_no.value, ps.rx_bytes, ps.tx_bytes)
            log.debug('Received port %d stats of switch %s: rx_bytes %d'
                      ', tx_bytes %d', ps.port_no.value, dpid,
                      ps.rx_bytes.value, ps.tx_bytes.value)


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


class RRD:
    """"Round-robin database for keeping stats.

    It store statistics every :data:`kyco.constants.POOLING_TIME`.
    """

    _DIR = Path(__file__).parent / 'rrd'
    #: If no new data is supplied for more than *_TIMEOUT* seconds,
    #: the temperature becomes *UNKNOWN*.
    _TIMEOUT = 2 * POOLING_TIME
    #: Minimum accepted value
    _MIN = 0
    #: Maximum accepted value is the maximum PortStats attribute value.
    _MAX = 2**64 - 1
    #: The xfiles factor defines what part of a consolidation interval may be
    #: made up from *UNKNOWN* data while the consolidated value is still
    #: regarded as known. It is given as the ratio of allowed *UNKNOWN* PDPs
    #: to the number of PDPs in the interval. Thus, it ranges from 0 to 1
    #: (exclusive).
    _XFF = 0
    #: How long to keep the data. Accepts s (seconds), m (minutes), h (hours),
    #: d (days), w (weeks), M (months), and y (years).
    _PERIOD = '1M'

    def update(self, dpid, port, rx_bytes, tx_bytes):
        """Add a row to rrd file of *dpid* and *port*.

        Create rrd if necessary.
        """
        rrd = self.get_or_create_rrd(dpid, port)
        rrdtool.update(rrd, 'N:{}:{}'.format(rx_bytes, tx_bytes))

    def get_rrd(self, dpid, port):
        """Return path of the rrd for *dpid* and *port*.

        If rrd doesn't exist, it is *not* created.

        See Also:
            :meth:`get_or_create_rdd`
        """
        return str(self._DIR / 'switch{}port{}.rrd'.format(dpid, port))

    def get_or_create_rrd(self, dpid, port):
        """If rrd is not found, create it."""
        rrd = self.get_rrd(dpid, port)
        if not Path(rrd).exists():
            log.debug('Creating rrd for dpid %d, port %d', dpid, port)
            rrdtool.create(rrd, '--start', 'now', '--step', str(POOLING_TIME),
                           self._get_counter('rx_bytes'),
                           self._get_counter('tx_bytes'), self._get_archive())
        return rrd

    def _get_counter(self, name):
        return 'DS:{}:COUNTER:{}:{}:{}'.format(name, self._TIMEOUT, self._MIN,
                                               self._MAX)

    def _get_archive(self):
        """Average every row."""
        return 'RRA:AVERAGE:{}:1:{}'.format(self._XFF, self._PERIOD)
