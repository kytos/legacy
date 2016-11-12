"""Test UserSpeed."""
import json
import logging
from pathlib import Path
import unittest

from unittest import mock
from main import UserSpeed

logging.basicConfig(level=logging.CRITICAL)


class TestUserSpeed(unittest.TestCase):
    """Test UserSpeed."""

    def test_no_file(self):
        """Speed should be s None without user file."""
        with mock.patch.object(Path, 'exists', return_value=False):
            user = UserSpeed()
            self.assertIsNone(user.get_speed('dpid'))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'dpid': 42})
    def test_user_defined(self, mock1, mock2):
        """Speed should be the one assigned in user file."""
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid'))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'dpid': 42})
    def test_user_not_defined(self, mock1, mock2):
        """Speed should be None if not in the user file."""
        self.assertIsNone(UserSpeed().get_speed('dpid2'))

    @mock.patch.object(Path, 'exists', return_value=True)
    @mock.patch.object(json, 'load', return_value={'default': 42})
    def test_user_default(self, mock1, mock2):
        """Default speed in user file should be used."""
        self.assertEqual(42 * 10**9, UserSpeed().get_speed('dpid2'))
