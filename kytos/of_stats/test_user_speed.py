"""Test UserSpeed."""
import json
import logging
import unittest
from pathlib import Path

from unittest import mock

from napps.kytos.of_stats.stats_api import UserSpeed

logging.basicConfig(level=logging.CRITICAL)


class TestUserSpeed(unittest.TestCase):
    """Test UserSpeed."""

    def test_no_file(self):
        """Speed should be s None without user file."""
        with mock.patch.object(Path, 'exists', return_value=False):
            user = UserSpeed()
            self.assertIsNone(user.get_speed('dpid'))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'default': 42})
    def test_default(self, mock1, mock2):
        """Test the default for all switches."""
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid'))
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid', 4))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'dpid': 42})
    def test_no_dpid_no_default(self, mock1, mock2):
        """Return None when no default and no dpid is found."""
        self.assertIsNone(UserSpeed().get_speed('dpid2'))
        self.assertIsNone(UserSpeed().get_speed('dpid2', 4))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'dpid': {'default': 42}})
    def test_dpid_default(self, mock1, mock2):
        """Return default speed for dpid."""
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid'))
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid', 1))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'default': 1,
                       'dpid': {'default': 2, 4: 3}})  # noqa
    def test_port_speed(self, mock1, mock2):
        """Return the speed defined for that port, ignoring defaults."""
        self.assertEqual(3 * 10**9, UserSpeed().get_speed('dpid', 4))
