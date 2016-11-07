"""Statistics application."""
import json
import time
from abc import ABCMeta, abstractmethod
from glob import glob
from logging import getLogger
from pathlib import Path
from threading import Lock

from flask import Flask, Response, request

import rrdtool
from kyco.core.events import KycoEvent
from kyco.core.flow import Flow
from kyco.core.napps import KycoNApp
from kyco.utils import listen_to
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.common import (AggregateStatsRequest,
                                                 FlowStatsRequest,
                                                 PortStatsRequest)
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes

#: Seconds to wait before asking for more statistics.
#: Delete RRDs everytime this interval is changed
STATS_INTERVAL = 30
# STATS_INTERVAL = 1  # 1 second for testing - check RRD._get_archives()
log = getLogger(__name__)
#: Avoid segmentation fault
rrd_lock = Lock()


class Main(KycoNApp):
    """Main class for statistics application."""

    def setup(self):
        """Initialize all statistics and set their loop interval."""
        msg_out = self.controller.buffers.msg_out
        self._stats = {StatsTypes.OFPST_DESC.value: Description(msg_out),
                       StatsTypes.OFPST_PORT.value: PortStats(msg_out),
                       StatsTypes.OFPST_FLOW.value: FlowStats(msg_out)}
        self.execute_as_loop(STATS_INTERVAL)
        PortStatsAPI.switches = self.controller.switches
        FlowStatsAPI.register_endpoints(self.controller)
        PortStatsAPI.register_endpoints(self.controller)

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
        event = KycoEvent(
            name='kytos/of.stats.messages.out.ofpt_stats_request',
            content={'message': req, 'destination': conn})
        self._buffer.put(event)


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
    _XFF = '0.5'
    #: How long to keep the data. Accepts s (seconds), m (minutes), h (hours),
    #: d (days), w (weeks), M (months), and y (years).
    #: Must be a multiple of consolidation steps.
    _PERIOD = '30d'

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
        with rrd_lock:
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
        path = self._DIR / self._app
        folders, basename = index[:-1], index[-1]
        for folder in folders:
            path = path / folder
        path = path / '{}.rrd'.format(basename)
        return str(path)

    def get_rrds(self, index):
        """List files inside the folder specified by *index*.

        Args:
            index (iterable): Subfolders. Like *index* of :meth:`get_rrd`
                without the last item, for example.

        Returns:
            str iterable: Generator of rrd basenames, without *.rrd* suffix.
                For example, return the string `1` for `folder/1.rdd`
        """
        path = self._DIR / self._app
        for folder in index:
            path = path / folder
        preffix = str(path) + '/'
        pattern = preffix + '*.rrd'
        return (rrd[len(preffix):-4] for rrd in glob(pattern))

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
                parent.mkdir(parents=True)
            self.create_rrd(rrd, tstamp)
        return rrd

    def create_rrd(self, rrd, tstamp=None):
        """Create an RRD file.

        Args:
            rrd (str): Path of RRD file to be created.
            tstamp (str, int): Unix timestamp in seconds for RRD creation.
                Defaults to now.
        """
        if tstamp is None:
            tstamp = 'N'
        options = [rrd, '--start', str(tstamp), '--step', str(STATS_INTERVAL)]
        options.extend([self._get_counter(ds) for ds in self._ds])
        options.extend(self._get_archives())
        with rrd_lock:
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
        if end == 'now':
            end = int(time.time())
        if start == 'first':
            with rrd_lock:
                start = rrdtool.first(rrd)

        # Find the best matching resolution for returning n_points.
        res_args = []
        if n_points is not None and isinstance(start, int) \
                and isinstance(end, int):
            resolution = (end - start) // n_points
            if resolution > 0:
                res_args.extend(['-a', '-r', '{}s'.format(resolution)])

        # For RRDtool to include start and end timestamps.
        if isinstance(start, int):
            start -= 1
        if isinstance(end, int):
            end -= 1

        args = [rrd, 'AVERAGE', '--start', str(start), '--end', str(end)]
        args.extend(res_args)
        with rrd_lock:
            tstamps, cols, rows = rrdtool.fetch(*args)
        start, stop, step = tstamps
        # rrdtool range is different from Python's.
        return range(start + step, stop + 1, step), cols, rows

    def fetch_latest(self, index):
        """Fetch only the value for now.

        Return empty dict if there are no values recorded.
        """
        start = 'end-{}s'.format(STATS_INTERVAL * 3)  # two rows
        tstamps, cols, rows = self.fetch(index, start, end='now')
        # Last rows may have future timestamp and be empty
        latest = None
        min_tstamp = int(time.time()) - STATS_INTERVAL * 2
        for tstamp, row in zip(tstamps[::-1], rows[::-1]):
            if row[0] is not None and tstamp > min_tstamp:
                latest = row
        return {k: v for k, v in zip(cols, latest)} if latest else {}

    def _get_counter(self, ds):
        return 'DS:{}:COUNTER:{}:{}:{}'.format(ds, self._TIMEOUT, self._MIN,
                                               self._MAX)

    @classmethod
    def _get_archives(cls):
        """Averaged for all Data Sources."""
        averages = []
        # One month stats for the following periods:
        for steps in ('30s', '1m', '2m', '4m', '8m', '15m', '30m', '1h', '2h',
                      '4h', '8h', '12h', '1d', '2d', '3d', '6d', '10d', '15d'):
            averages.append('RRA:AVERAGE:{}:{}:{}'.format(cls._XFF, steps,
                                                          cls._PERIOD))
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
        debug_msg = 'Received flow stats:\n' \
                    '  Flow id %s\n' \
                    '  table %s, switch %s, counters: packet = %s, byte = %s'

        for fs in flows_stats:
            flow = Flow.from_flow_stats(fs)
            cls.rrd.update((dpid, flow.id),
                           packet_count=fs.packet_count.value,
                           byte_count=fs.byte_count.value)

            log.debug(debug_msg, flow.id, fs.table_id.value, dpid,
                      fs.packet_count.value, fs.byte_count.value)


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


app = Flask(__name__)


class StatsAPI(metaclass=ABCMeta):
    """Class to answer REST API requests."""

    _rrd = None

    def __init__(self):
        """Initialize instance attributes."""
        self._stats = {}

    def get_points(self, index, n_points=30):
        """Return Flask response for port stats."""
        start_str = request.args.get('start', 'first')
        start = int(start_str) if start_str.isdigit() else start_str
        end_str = request.args.get('end', 'now')
        end = int(end_str) if end_str.isdigit() else end_str

        try:
            content = self._fetch(index, start, end, n_points)
        except FileNotFoundError as e:
            content = self._get_rrd_not_found_error(e)
        return StatsAPI._get_response(content)

    @classmethod
    def get_list(cls, dpid):
        """List all ports that have statistics and their latest stats.

        Args:
            dpid (str): Switch dpid.
            get_port (function): Return port number from RRD basename.
        """
        ix = (dpid,)
        data = {}
        for rrd in cls._rrd.get_rrds(ix):
            rrd_ix = (dpid, rrd)
            latest = cls._rrd.fetch_latest(rrd_ix)
            if latest:  # test if dictionary is empty
                data[rrd] = latest
        return data

    def _fetch(self, index, start, end, n_points):
        tstamps, cols, rows = self._rrd.fetch(index, start, end, n_points)
        self._stats = {col: [] for col in cols}
        self._stats['timestamps'] = list(tstamps)
        for row in rows:
            for col, value in zip(cols, row):
                self._stats[col].append(value)
        self._remove_null()
        return {'data': self._stats}

    def _remove_null(self):
        """Remove a row if all its values are null."""
        nullable_cols = list(self._stats.keys())
        nullable_cols.remove('timestamps')
        n_elements = len(self._stats['timestamps'])

        # Check elements backwards for safe removal
        for i in range(n_elements - 1, -1, -1):
            for col in nullable_cols:
                # Stop if a non-null element is found in the row.
                if self._stats[col][i] is not None:
                    break
            if self._stats[col][i] is not None:
                # Keep current row and check the next one.
                continue
            # Remove the current row from every list
            for lst in self._stats.values():
                lst.pop(i)

    @staticmethod
    def _get_response(dct):
        json_ = json.dumps(dct, sort_keys=True, indent=4)
        return Response(json_, mimetype='application/vnd.api+json')

    @staticmethod
    def _get_rrd_not_found_error(exception):
        return {'errors': {
            'status': '404',
            'title': 'Database not found.',
            'detail': str(exception)}}


class PortStatsAPI(StatsAPI):
    """REST API for port statistics."""

    #: Controller's switches to inform link speed.
    switches = None
    #: key is RRD column, value is a new column name for utilization
    #: percentage.
    _util_cols = {'rx_bytes': 'rx_utilization',
                  'tx_bytes': 'tx_utilization'}
    _rrd = PortStats.rrd

    @classmethod
    def register_endpoints(cls, controller):
        """Register REST API endpoints in the controller."""
        controller.register_rest_endpoint('/stats/<dpid>/ports/<int:port>',
                                          cls.get_port_stats, methods=['GET'])
        controller.register_rest_endpoint('/stats/<dpid>/ports',
                                          cls.get_ports_list, methods=['GET'])

    @classmethod
    def get_port_stats(cls, dpid, port):
        """Get up to 60 points of all statistics of PortStats.

        Includes start and end that are both optional and and must be submitted
        in the form "?start=x&end=y".

        Args:
            dpid (str): Switch dpid.
            port (str, int): Switch port number.
            start (int): Unix timestamp in seconds for the first stats.
                Defaults to the start parameter of the RRD creation.
            end (int): Unix timestamp in seconds for the last stats. Defaults
                to now.
            n_points (int): Return n_points. May return more if there is no
                matching resolution in the RRD file. Defaults to as many points
                as possible.
        """
        index = (dpid, port)
        api = cls()
        return api.get_points(index)

    @classmethod
    def get_ports_list(cls, dpid):
        """List all ports that have statistics and their latest stats.

        Include link utilization.

        Args:
            dpid (str): Switch dpid.
        """
        rrd_data = super().get_list(dpid)
        data = cls._add_utilization(rrd_data, dpid)
        return cls._get_response({'data': data})

    @classmethod
    def _add_utilization(cls, rrd_data, dpid):
        for rrd, row in rrd_data.items():
            port = int(rrd)
            speed = cls.switches[dpid].interfaces[port].get_speed()
            for bytes_col, util_col in cls._util_cols.items():
                if speed:
                    row[util_col] = row[bytes_col] / speed / 8  # bytes/sec
                # We may have zero bytes for a port we can't get the speed
                elif row[bytes_col] == 0.0:
                    row[util_col] = 0
                else:
                    log.warning('Speed for port %d dpid %s not found', port,
                                dpid)
        return rrd_data


class FlowStatsAPI(StatsAPI):
    """REST API for flow statistics."""

    _rrd = FlowStats.rrd

    @classmethod
    def register_endpoints(cls, controller):
        """Register REST API endpoints in the controller."""
        controller.register_rest_endpoint('/stats/<dpid>/flows/<flow_hash>',
                                          cls.get_flow_stats, methods=['GET'])
        controller.register_rest_endpoint('/stats/<dpid>/flows',
                                          cls.get_flow_list, methods=['GET'])

    @classmethod
    def get_flow_list(cls, dpid):
        """List all flows that have statistics and their latest stats.

        Args:
            dpid (str): Switch dpid.
        """
        data = super().get_list(dpid)
        return cls._get_response({'data': data})

    @classmethod
    def get_flow_stats(cls, dpid, flow_hash):
        """Return flow statics by its hash.

        Includes start and end that are both optional and and must be submitted
        in the form "?start=x&end=y".

        Args:
            dpid (str): Switch dpid.
            flow_hash (str): Flow hash.
            start (int): Unix timestamp in seconds for the first stats.
                Defaults to the start parameter of the RRD creation.
            end (int): Unix timestamp in seconds for the last stats. Defaults
                to now.
        """
        index = (dpid, flow_hash)
        api = cls()
        return api.get_points(index)


if __name__ == "__main__":
    app.run()
