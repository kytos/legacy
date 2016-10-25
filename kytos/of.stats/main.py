"""Statistics application."""
from abc import ABCMeta, abstractmethod
from logging import getLogger
from pathlib import Path
from threading import Event

import rrdtool

from kyco.core.events import KycoEvent
from kyco.core.napps import KycoNApp
from kyco.utils import listen_to
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.common import (PortStatsRequest,
    FlowStatsRequest, AggregateStatsRequest)
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes

#: Seconds to wait before asking for more statistics.
STATS_INTERVAL = 30
log = getLogger('Stats')


class Main(KycoNApp):
    """Main class for statistics application."""

    def setup(self):
        """`__init__` method of KycoNApp."""
        msg_out = self.controller.buffers.msg_out
        self._stats = {StatsTypes.OFPST_DESC.value: Description(msg_out),
                       StatsTypes.OFPST_PORT.value: PortStats(msg_out),
                       StatsTypes.OFPST_FLOW.value: FlowStats(msg_out)}
        self.EXECUTE_INTERVAL = STATS_INTERVAL

    def execute(self):
        """Query all switches sequentially and then sleep before repeating."""
        switches = self.controller.switches.values()
        for switch in switches:
            self._update_stats(switch)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')

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
    def listen(self, dpid, stats):
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
        debug_msg = 'Received port {} stats of switch {}: rx_bytes {}'
        debug_msg += ', tx_bytes {}, rx_dropped {}, tx_dropped {},'
        debug_msg += 'rx_errors {}, tx_errors {}'

        for ps in ports_stats:
            self._rrd.update(dpid, 'port',
                             port=ps.port_no.value,
                             rx_bytes=ps.rx_bytes.value,
                             tx_bytes=ps.tx_bytes.value,
                             rx_dropped=ps.rx_dropped.value,
                             tx_dropped=ps.tx_dropped.value,
                             rx_errors=ps.rx_errors.value,
                             tx_errors=ps.tx_errors.value)

            log.debug(debug_msg.format(ps.port_no.value, dpid,
                      ps.rx_bytes.value, ps.tx_bytes.value,
                      ps.rx_dropped.value, ps.tx_dropped.value,
                      ps.rx_errors.value, ps.tx_errors.value))


class AggregateStats(Stats):
    """Deal with FlowStats message."""

    def __init__(self, msg_out_buffer):
        """Initialize database."""
        super().__init__(msg_out_buffer)
        self._rrd = RRD()

    def request(self, conn):
        """Ask for flow stats."""
        body = AggregateStatsRequest() # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_AGGREGATE, body=body)
        self._send_event(req, conn)
        log.debug('Aggregate Stats request for switch %s sent.', conn.switch.dpid)

    def listen(self, dpid, aggregate_stats):
        """Receive flow stats."""
        debug_msg = 'Received aggregate stats from switch {}:'
        debug_msg += ' packet_count {}, byte_count {}, flow_count {}'

        for ag in aggregate_stats:
            # need to choose the _id to aggregate_stats
            # this class isn't used yet.
            self._rrd.update(dpid, "",
                             packet_count=ag.packet_count.value,
                             byte_count=ag.byte_count.value,
                             flow_count=ag.flow_count.value)

            log.debug(debug_msg.format(dpid, ag.packet_count.value,
                      ag.byte_count.value, ag.flow_count.value))


class FlowStats(Stats):
    """Deal with FlowStats message."""

    def __init__(self, msg_out_buffer):
        """Initialize database."""
        super().__init__(msg_out_buffer)
        self._rrd = RRD()

    def request(self, conn):
        """Ask for flow stats."""
        body = FlowStatsRequest() # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_FLOW, body=body)
        self._send_event(req, conn)
        log.debug('Flow Stats request for switch %s sent.', conn.switch.dpid)

    def listen(self, dpid, flows_stats):
        """Receive flow stats."""
        debug_msg = 'Received flow stats from table {} of switch {}:'
        debug_msg += 'packet_count {}, byte_count {}'

        for fs in flows_stats:
            self._rrd.update(dpid,'table_id',
                             table_id=fs.table_id.value,
                             packet_count = fs.packet_count.value,
                             byte_count = fs.byte_count.value)

            log.debug(debug_msg.format(fs.table_id.value, dpid,
                      fs.packet_count.value, fs.byte_count.value))


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

    It store statistics every :data:`STATS_INTERVAL`.
    """

    _DIR = Path(__file__).parent / 'rrd'
    #: If no new data is supplied for more than *_TIMEOUT* seconds,
    #: the temperature becomes *UNKNOWN*.
    _TIMEOUT = 2 * STATS_INTERVAL
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

    def update(self,dpid,_id, **kwargs):
        """Add a row to rrd file of *dpid* and *_id*.

        Create rrd if necessary.
        """
        tstamp = kwargs.pop('tstamp','N')
        msg = "{}:".format(tstamp)
        msg += ":".join(str(value) for value in kwargs.values())
        rrd = self.get_or_create_rrd(dpid, _id, **kwargs)
        rrdtool.update(rrd, msg)

    def get_rrd(self, dpid, _id):
        """Return path of the rrd for *dpid* and *_id*.

        If rrd doesn't exist, it is *not* created.

        See Also:
            :meth:`get_or_create_rrd`
        """
        return str(self._DIR / str(dpid) / '{}.rrd'.format(_id))

    def get_or_create_rrd(self, dpid, _id, **kwargs):
        """If rrd is not found, create it."""
        tstamp = kwargs.get('tstamp',None)

        rrd = self.get_rrd(dpid, _id)
        if not Path(rrd).exists():
            log_msg = 'Creating rrd for dpid {}, {} {}'
            log.debug(log_msg.format(dpid, _id, kwargs.get(_id)))
            parent = Path(rrd).parent
            if not parent.exists():
                parent.mkdir()
            self.create_rrd(rrd, **kwargs)
        return rrd

    def create_rrd(self, rrd, **kwargs):
        """Create an RRD file."""
        tstamp = kwargs.get('tstamp','now')
        options = [rrd, '--start', str(tstamp), '--step', str(STATS_INTERVAL)]

        options.extend([self._get_counter(arg) for arg in kwargs.keys()])
        options.append(self._get_archive())
        rrdtool.create(*options)

    def fetch(self, dpid, _id, start, end):
        """Fetch average values from rrd.

        Returns:
            A tuple with:

            1. Iterator over timestamps
            2. Column (DS) names
            3. List of rows as tuples
        """
        rrd = self.get_or_create_rrd(dpid, _id)
        tstamps, cols, rows = rrdtool.fetch(rrd, 'AVERAGE', '--start',
                                            str(start), '--end', str(end))
        start, stop, step = tstamps
        return range(start + step, stop + 1, step), cols, rows

    def _get_counter(self, name):
        return 'DS:{}:COUNTER:{}:{}:{}'.format(name, self._TIMEOUT, self._MIN,
                                               self._MAX)

    def _get_archive(self):
        """Average every row."""
        return 'RRA:AVERAGE:{}:1:{}'.format(self._XFF, self._PERIOD)
