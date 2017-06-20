"""Test of.stats app."""
import os
import unittest
from tempfile import mkstemp
from unittest.mock import patch  # noqa (isort conflict)

from napps.kytos.of_stats.settings import STATS_INTERVAL
from napps.kytos.of_stats.stats import RRD


class TestRRD(unittest.TestCase):
    """Test RRD interpolation."""

    @patch.object(RRD, 'get_rrd')
    def test_2_points_out_of_3(self, get_rrd_method):
        """Without the middle point, interpolate first and last points.

        Suppose STATS_INTERVAL is 10:
        - At 1234567800 (first),  rx = tx = 10;
        - At 1234567810 (second), rx = tx = unknown;
        - At 1234567820 (third),  rx = tx = 30.

        Test if the average is 1 at 1234567810 (second).
        """
        # Mock will return a temporary file for rrd file.
        f, rrd_file = mkstemp('.rrd')
        os.close(f)
        get_rrd_method.return_value = rrd_file

        start = 1234567800 - STATS_INTERVAL  # can't update using start time
        rrd = RRD('test', ('rx', 'tx'))
        rrd.create_rrd(rrd_file, tstamp=start)

        def update_rrd(multiplier):
            """Update rrd."""
            rx = tx = multiplier * STATS_INTERVAL
            tstamp = start + rx
            # any value for index is OK
            rrd.update([None], tstamp, rx=rx, tx=tx)

        update_rrd(1)
        update_rrd(3)

        second = start + 2 * STATS_INTERVAL
        # Interval between x and y excludes y
        tstamps, _, rows = rrd.fetch([None], start=second, end=second)

        os.unlink(rrd_file)

        self.assertEqual(second, list(tstamps)[0])
        self.assertEqual((1.0, 1.0), rows[0])

    @patch('napps.kytos.of_stats.stats.Path')
    def test_non_existent_rrd(self, path_mock):
        """Test fetch_latest with non existent rrd."""
        obj = path_mock.return_value.exists.return_value = False
        rrd = RRD('app_folder', ['data_source'])
        row = rrd.fetch_latest('index')
        self.assertEqual(row, {})
