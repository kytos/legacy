"""Module with Classes to handle statistics."""
import time
from abc import ABCMeta, abstractmethod
from pathlib import Path

import rrdtool
from kytos.core import KytosEvent, log
from napps.legacy.of_core.flow import Flow
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.common import (AggregateStatsRequest,
                                                 FlowStatsRequest,
                                                 PortStatsRequest)
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes


from . import settings


class Stats(metaclass=ABCMeta):
    """Abstract class for Statistics implementation."""

    rrd = None

    def __init__(self, msg_out_buffer):
        """Store a reference to the controller's msg_out buffer.

        Args:
            msg_out_buffer: Where to send events.
        """
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
        event = KytosEvent(
            name='kytos/of_stats.messages.out.ofpt_stats_request',
            content={'message': req, 'destination': conn})
        self._buffer.put(event)


class RRD:
    """"Round-robin database for keeping stats.

    It store statistics every :data:`STATS_INTERVAL`.
    """

    def __init__(self, app_folder, data_sources):
        """Specify a folder to store RRDs.

        Args:
            app_folder (str): Parent folder for dpids folders.
            data_sources (iterable): Data source names (e.g. tx_bytes,
                rx_bytes).
        """
        self._app = app_folder
        self._ds = data_sources

    def update(self, index, tstamp=None, **ds_values):
        """Add a row to rrd file of *dpid* and *_id*.

        Args:
            dpid (str): Switch dpid.
            index (list of str): Index for the RRD database. Examples:
                [dpid], [dpid, port_no], [dpid, table id, flow hash].
            tstamp (str, int): Unix timestamp in seconds. Defaults to now.

        Create rrd if necessary.
        """
        if tstamp is None:
            tstamp = 'N'
        rrd = self.get_or_create_rrd(index)
        data = ':'.join(str(ds_values[ds]) for ds in self._ds)
        with settings.rrd_lock:
            rrdtool.update(rrd, '{}:{}'.format(tstamp, data))

    def get_rrd(self, index):
        """Return path of the RRD file for *dpid* with *basename*.

        If rrd doesn't exist, it is *not* created.

        Args:
            index (iterable of str): Index for the RRD database. Examples:
                [dpid], [dpid, port_no], [dpid, table id, flow hash].

        Returns:
            str: Absolute RRD path.

        See Also:
            :meth:`get_or_create_rrd`
        """
        path = settings.DIR / self._app
        folders, basename = index[:-1], index[-1]
        for folder in folders:
            path = path / folder
        path = path / '{}.rrd'.format(basename)
        return str(path)

    def get_or_create_rrd(self, index, tstamp=None):
        """If rrd is not found, create it.

        Args:
            index (list of str): Index for the RRD database. Examples:
                [dpid], [dpid, port_no], [dpid, table id, flow hash].
            tstamp (str, int): Value for start argument of RRD creation.
        """
        if tstamp is None:
            tstamp = 'N'

        rrd = self.get_rrd(index)
        if not Path(rrd).exists():
            log.debug('Creating rrd for app %s, index %s.', self._app, index)
            parent = Path(rrd).parent
            if not parent.exists():
                # We may have concurrency problems creating a folder
                parent.mkdir(parents=True, exist_ok=True)
            self.create_rrd(rrd, tstamp)
        return rrd

    def create_rrd(self, rrd, tstamp=None):
        """Create an RRD file.

        Args:
            rrd (str): Path of RRD file to be created.
            tstamp (str, int): Unix timestamp in seconds for RRD creation.
                Defaults to now.
        """
        def get_counter(ds):
            """Return a DS for rrd creation."""
            return 'DS:{}:COUNTER:{}:{}:{}'.format(ds, settings.TIMEOUT,
                                                   settings.MIN, settings.MAX)

        if tstamp is None:
            tstamp = 'N'
        options = [rrd, '--start', str(tstamp), '--step',
                   str(settings.STATS_INTERVAL)]
        options.extend([get_counter(ds) for ds in self._ds])
        options.extend(self._get_archives())
        with settings.rrd_lock:
            rrdtool.create(*options)

    def fetch(self, index, start='first', end='now', n_points=None):
        """Fetch average values from rrd.

        Args:
            index (list of str): Index for the RRD database. Examples:
                [dpid], [dpid, port_no], [dpid, table id, flow hash].
            start (str, int): Unix timestamp in seconds for the first stats.
                Defaults to the first recorded sample.
            end (str, int): Unix timestamp in seconds for the last stats.
                Defaults to current time.
            n_points (int): Number of points to return. May return more if
                there is no matching resolution in the RRD file, or less if
                there is no records for all the time range.
                Defaults to as many points as possible.

        Returns:
            A tuple with:

            1. Iterator over timestamps
            2. Column (DS) names
            3. List of rows as tuples
        """
        rrd = self.get_rrd(index)
        if not Path(rrd).exists():
            msg = 'RRD for app {} and index {} not found'.format(self._app,
                                                                 index)
            raise FileNotFoundError(msg)

        # Use integers to calculate resolution
        start, end = self._calc_start_end(start, end, rrd)

        # Find the best matching resolution for returning n_points.
        res_args = []
        if n_points is not None and isinstance(start, int) \
                and isinstance(end, int):
            resolution = (end - start) // n_points
            if resolution > 0:
                res_args.extend(['-a', '-r', '{}s'.format(resolution)])

        args = [rrd, 'AVERAGE', '--start', str(start), '--end', str(end)]
        args.extend(res_args)
        with settings.rrd_lock:
            tstamps, cols, rows = rrdtool.fetch(*args)
        start, stop, step = tstamps
        # rrdtool range is different from Python's.
        return range(start + step, stop + 1, step), cols, rows

    @staticmethod
    def _calc_start_end(start, end, rrd):
        """Calculate start and end values for fetch command."""
        # Use integers to calculate resolution
        if end == 'now':
            end = int(time.time())
        if start == 'first':
            with settings.rrd_lock:
                start = rrdtool.first(rrd)

        # For RRDtool to include start and end timestamps.
        if isinstance(start, int):
            start -= 1
        if isinstance(end, int):
            end -= 1

        return start, end

    def fetch_latest(self, index):
        """Fetch only the value for now.

        Return zero values if there are no values recorded.
        """
        start = 'end-{}s'.format(settings.STATS_INTERVAL * 3)  # two rows
        try:
            tstamps, cols, rows = self.fetch(index, start, end='now')
        except FileNotFoundError:
            # No RRD for port, so it will return zero values
            return {}
        # Last rows may have future timestamp and be empty
        latest = None
        min_tstamp = int(time.time()) - settings.STATS_INTERVAL * 2
        # Search backwards for non-null values
        for tstamp, row in zip(tstamps[::-1], rows[::-1]):
            if row[0] is not None and tstamp > min_tstamp:
                latest = row
        # If no values are found, add zeros.
        if not latest:
            latest = [0] * len(cols)
        return {k: v for k, v in zip(cols, latest)}

    @classmethod
    def _get_archives(cls):
        """Averaged for all Data Sources."""
        averages = []
        # One month stats for the following periods:
        for steps in ('30s', '1m', '2m', '4m', '8m', '15m', '30m', '1h', '2h',
                      '4h', '8h', '12h', '1d', '2d', '3d', '6d', '10d', '15d'):
            averages.append('RRA:AVERAGE:{}:{}:{}'.format(settings.XFF, steps,
                                                          settings.PERIOD))
        # averages = ['RRA:AVERAGE:0:1:1d']  # More samples for testing
        return averages


class PortStats(Stats):
    """Deal with PortStats messages."""

    rrd = RRD('ports', [rt + 'x_' + stat for stat in
                        ('bytes', 'dropped', 'errors') for rt in 'rt'])

    def request(self, conn):
        """Ask for port stats."""
        body = PortStatsRequest(Port.OFPP_NONE)  # All ports
        req = StatsRequest(body_type=StatsTypes.OFPST_PORT, body=body)
        self._send_event(req, conn)
        log.debug('Port Stats request for switch %s sent.', conn.switch.dpid)

    @classmethod
    def listen(cls, dpid, ports_stats):
        """Receive port stats."""
        debug_msg = 'Received port %s stats of switch %s: rx_bytes %s,' \
                    ' tx_bytes %s, rx_dropped %s, tx_dropped %s,' \
                    ' rx_errors %s, tx_errors %s'

        for ps in ports_stats:
            cls.rrd.update((dpid, ps.port_no.value),
                           rx_bytes=ps.rx_bytes.value,
                           tx_bytes=ps.tx_bytes.value,
                           rx_dropped=ps.rx_dropped.value,
                           tx_dropped=ps.tx_dropped.value,
                           rx_errors=ps.rx_errors.value,
                           tx_errors=ps.tx_errors.value)

            log.debug(debug_msg, ps.port_no.value, dpid, ps.rx_bytes.value,
                      ps.tx_bytes.value, ps.rx_dropped.value,
                      ps.tx_dropped.value, ps.rx_errors.value,
                      ps.tx_errors.value)


class AggregateStats(Stats):
    """Deal with AggregateStats message."""

    _rrd = RRD('aggr', ('packet_count', 'byte_count', 'flow_count'))

    def __init__(self, msg_out_buffer):
        """Initialize database."""
        super().__init__(msg_out_buffer)

    def request(self, conn):
        """Ask for flow stats."""
        body = AggregateStatsRequest()  # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_AGGREGATE, body=body)
        self._send_event(req, conn)
        log.debug('Aggregate Stats request for switch %s sent.',
                  conn.switch.dpid)

    @classmethod
    def listen(cls, dpid, aggregate_stats):
        """Receive flow stats."""
        debug_msg = 'Received aggregate stats from switch {}:' \
                    ' packet_count {}, byte_count {}, flow_count {}'

        for ag in aggregate_stats:
            # need to choose the _id to aggregate_stats
            # this class isn't used yet.
            cls.rrd.update((dpid,),
                           packet_count=ag.packet_count.value,
                           byte_count=ag.byte_count.value,
                           flow_count=ag.flow_count.value)

            log.debug(debug_msg, dpid, ag.packet_count.value,
                      ag.byte_count.value, ag.flow_count.value)


class FlowStats(Stats):
    """Deal with FlowStats message."""

    rrd = RRD('flows', ('packet_count', 'byte_count'))

    def request(self, conn):
        """Ask for flow stats."""
        body = FlowStatsRequest()  # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_FLOW, body=body)
        self._send_event(req, conn)
        log.debug('Flow Stats request for switch %s sent.', conn.switch.dpid)

    @classmethod
    def listen(cls, dpid, flows_stats):
        """Receive flow stats."""
        for fs in flows_stats:
            flow = Flow.from_flow_stats(fs)
            cls.rrd.update((dpid, flow.id),
                           packet_count=fs.packet_count.value,
                           byte_count=fs.byte_count.value)


class Description(Stats):
    """Deal with Description messages."""

    controller = {}

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
        switch = self.controller.get_switch_by_dpid(dpid)
        switch.update_description(desc)
        log.debug('Adding switch %s: mfr_desc = %s, hw_desc = %s,'
                  ' sw_desc = %s, serial_num = %s', dpid,
                  desc.mfr_desc, desc.hw_desc, desc.sw_desc,
                  desc.serial_num)
