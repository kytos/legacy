"""Statistics application."""
import json
from abc import ABCMeta, abstractmethod
from logging import getLogger
from pathlib import Path
from threading import Event, Lock

from flask import Flask, Response

import rrdtool
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoNApp
from kyco.utils import listen_to
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.common import PortStatsRequest
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes

#: Seconds to wait before asking for more statistics.
STATS_INTERVAL = 30
log = getLogger('Stats')
#: Avoid segmentation fault
rrd_lock = Lock()


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
            self._stopper.wait(STATS_INTERVAL)
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

    def update(self, dpid, port, rx_bytes, tx_bytes, tstamp='N'):
        """Add a row to rrd file of *dpid* and *port*.

        Create rrd if necessary.
        """
        rrd = self.get_or_create_rrd(dpid, port)
        with rrd_lock:
            rrdtool.update(rrd, '{}:{}:{}'.format(tstamp, rx_bytes, tx_bytes))

    def get_rrd(self, dpid, port):
        """Return path of the rrd for *dpid* and *port*.

        If rrd doesn't exist, it is *not* created.

        Args:
            dpid (str): Switch dpid.
            port (str, int): Switch port number.

        See Also:
            :meth:`get_or_create_rrd`
        """
        return str(self._DIR / dpid / '{}.rrd'.format(port))

    def get_or_create_rrd(self, dpid, port, tstamp=None):
        """If rrd is not found, create it."""
        rrd = self.get_rrd(dpid, port)
        if not Path(rrd).exists():
            log.debug('Creating rrd for dpid %s, port %d', dpid, port)
            parent = Path(rrd).parent
            if not parent.exists():
                parent.mkdir()
            self.create_rrd(rrd, tstamp)
        return rrd

    def create_rrd(self, rrd, tstamp=None):
        """Create an RRD file."""
        tstamp = 'now' if tstamp is None else str(tstamp)
        interval = '{}s'.format(STATS_INTERVAL)
        args = [self._get_counter('rx_bytes'), self._get_counter('tx_bytes'),
                *self._get_archives()]
        with rrd_lock:
            rrdtool.create(rrd, '--start', tstamp, '--step', interval, *args)

    def fetch(self, dpid, port, start, end, n_points=None):
        """Fetch average values from rrd.

        Args:
            dpid (str): Switch dpid.
            port (str, int): Switch port number.
            start (int): Unix timestamp in seconds for the first stats.
            end (int): Unix timestamp in seconds for the last stats.
            n_points (int): Return n_points. May return more if there is no
                matching resolution in the RRD file. Defaults to as many points
                as possible.

        Returns:
            A tuple with:

            1. Iterator over timestamps
            2. Column (DS) names
            3. List of rows as tuples
        """
        def get_res_args():
            """Return the best matching resolution for returning n_points."""
            if n_points is not None:
                resolution = (end - start) // n_points
                if resolution > 0:
                    return ['-a', '-r', '{}s'.format(resolution)]
            return []

        rrd = self.get_rrd(dpid, port)
        if not Path(rrd).exists():
            msg = 'RRD for dpid {} and port {} not found'.format(dpid, port)
            raise FileNotFoundError(msg)

        res_args = get_res_args()
        tstamps, cols, rows = rrdtool.fetch(rrd, 'AVERAGE', '--start',
                                            str(start - 1), '--end',
                                            str(end - 1), *res_args)
        start, stop, step = tstamps
        return range(start + step, stop + 1, step), cols, rows

    def _get_counter(self, name):
        return 'DS:{}:COUNTER:{}:{}:{}'.format(name, self._TIMEOUT, self._MIN,
                                               self._MAX)

    def _get_archives(self):
        """Average every row."""
        averages = []
        # One month stats for the following periods:
        for steps in ('30s', '1m', '2m', '4m', '8m', '15m', '30m', '1h', '2h',
                      '4h', '8h', '12h', '1d', '2d', '3d', '6d', '10d', '15d'):
            averages.append('RRA:AVERAGE:{}:{}:{}'.format(self._XFF, steps,
                                                          self._PERIOD))
        return averages


app = Flask(__name__)


class StatsAPI:
    """Class to answer REST API requests."""

    def __init__(self):
        """Initialize stats attribute."""
        self._stats = {}

    def fetch_port(self, dpid, port, start, end):
        """Return Flask response for port stats."""
        try:
            content = self._fetch(dpid, port, start, end)
        except FileNotFoundError as e:
            content = StatsAPI._get_rrd_not_found_error(e)
        return StatsAPI._get_response(content)

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

    def _fetch(self, dpid, port, start, end):
        tstamps, cols, rows = RRD().fetch(dpid, port, start, end, n_points=30)
        self._stats = {col: [] for col in cols}
        self._stats['timestamps'] = list(tstamps)
        for row in rows:
            for col, value in zip(cols, row):
                self._stats[col].append(value)
        self._remove_null()
        return {'data': self._stats}

    @staticmethod
    def _get_rrd_not_found_error(exception):
        return {'errors': {
            'status': '404',
            'title': 'Database not found.',
            'detail': str(exception)}}

    @staticmethod
    def _get_response(dct):
        json_ = json.dumps(dct, sort_keys=True, indent=4)
        return Response(json_, mimetype='application/vnd.api+json')


@app.route("/of.stats/<dpid>/<int:port>/<int:start>/<int:end>")
def get_stats(dpid, port, start, end):
    """Get 30 rx and tx bytes/sec between start and end, including both.

    Args:
        dpid (str): Switch dpid.
        port (str, int): Switch port number.
        start (int): Unix timestamp in seconds for the first stats.
        end (int): Unix timestamp in seconds for the last stats.
        n_points (int): Return n_points. May return more if there is no
            matching resolution in the RRD file. Defaults to as many points
            as possible.
    """
    api = StatsAPI()
    return api.fetch_port(dpid, port, start, end)


if __name__ == "__main__":
    app.run()
