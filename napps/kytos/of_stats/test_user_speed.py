"""Test UserSpeed."""
import logging
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch  # noqa (isort conflict)

from napps.kytos.of_stats.user_speed import UserSpeed

logging.basicConfig(level=logging.CRITICAL)


class TestUserSpeed(unittest.TestCase):
    """Test UserSpeed."""

    def setUp(self):
        """Path().exists() mock."""
        patcher = patch.object(Path, 'exists', return_value=True)
        self.file_exists = patcher.start()
        self.addCleanup(patcher.stop)

    def set_file_content(self, content):
        """Mock for the user configuration file."""
        open_method = mock_open(read_data=content)
        patcher = patch.object(Path, 'open', open_method)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_no_file(self):
        """Speed should be s None without user file."""
        self.file_exists.return_value = False
        user = UserSpeed()
        self.assertIsNone(user.get_speed('dpid'))

    def test_default(self):
        """Test the default for all switches."""
        self.set_file_content('{"default": 42}')
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid'))
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid', 4))

    def test_no_dpid_no_default(self):
        """Return None when no default and no dpid is found."""
        self.set_file_content('{"dpid": 42}')
        self.assertIsNone(UserSpeed().get_speed('dpid2'))
        self.assertIsNone(UserSpeed().get_speed('dpid2', 4))

    def test_dpid_default(self):
        """Return default speed for dpid."""
        self.set_file_content('{"dpid": {"default": 42}}')
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid'))
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid', 1))

    def test_port_speed(self):
        """Return the speed defined for that port, ignoring defaults."""
        self.set_file_content('{"default": 1, "dpid": {"default": 2, "4": 3}}')
        self.assertEqual(3 * 10**9, UserSpeed().get_speed('dpid', 4))
