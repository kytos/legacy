"""Common code for different statistics."""
from abc import ABCMeta, abstractmethod

from kyco.core.events import KycoEvent


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
