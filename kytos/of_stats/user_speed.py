"""Manage link speeds when OF spec is not enough."""
import json
from os.path import dirname
from pathlib import Path


class UserSpeed:
    """User-defined interface speeds.

    In case there is no matching speed in OF spec or the speed is not correctly
    detected.
    """

    _FILE = Path(dirname(__file__)) / 'user_speed.json'

    def __init__(self):
        """Load user-created file."""
        if self._FILE.exists():
            with self._FILE.open() as user_file:
                # print('UserSpeed', user_file.read())
                self._speed = json.load(user_file)
        else:
            self._speed = {}

    def get_speed(self, dpid, port=None):
        """Return speed in bits/sec or None if not defined by the user.

        Args:
            dpid (str): Switch dpid.
            port (int or str): Port number.
        """
        if not isinstance(port, str):
            port = str(port)
        speed = None
        switch = self._speed.get(dpid)
        if switch is None:
            speed = self._speed.get('default')
        else:
            if port is None or port not in switch:
                speed = switch.get('default')
            else:
                speed = switch.get(port)
        if speed is not None:
            speed *= 10**9
        return speed
