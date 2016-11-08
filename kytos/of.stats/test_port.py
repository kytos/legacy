"""Test PortStats."""
import logging
import unittest

from kyco.core.switch import Interface, Switch
from main import PortStatsAPI
from pyof.v0x01.common.phy_port import PortFeatures

logging.basicConfig(level=logging.CRITICAL)


class TestPortStats(unittest.TestCase):
    """Test PortStats."""

    def setUp(self):
        """Create switches."""
        self.dpid = ':01'
        self.port = 43

        switch = Switch(self.dpid)
        # speed = PortFeatures.
        features = PortFeatures.OFPPF_100MB_HD
        iface = Interface('name', self.port, switch, features=features)
        switch.update_interface(iface)
        PortStatsAPI.switches = {self.dpid: switch}

    def test_speed_without_switch(self):
        """No switch in the controller."""
        speed = PortStatsAPI.get_speed(':02', self.port)
        self.assertIsNone(speed)

    def test_speed_without_interface(self):
        """No interface in the switch."""
        speed = PortStatsAPI.get_speed(self.dpid, self.port + 1)
        self.assertIsNone(speed)
