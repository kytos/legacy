import logging

from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.foundation.network_types import Ethernet

log = logging.getLogger('KycoNApp')


class Main(KycoCoreNApp):
    """
    This app intends to update the links between machines and switches. It
    considers that if an interface is connected to another interface then this
    is a link. If not, it must be a connection to a server
    """

    def setup(self):
        """Creates an empty dict to store the switches references and the
        information about the hosts"""

        self.name = 'kytos/of.topology'
        self.stop_signal = False

    def execute(self):
        """ Do nothing, only wait for packet-in messages"""
        pass

    @listen_to('kytos/of.core.messages.in.ofpt_packet_in')
    def update_links(self, event):
        """
        Main operation of the app., the one responsible for update the
        interface endpoints.
        """
        ethernet = Ethernet()
        ethernet.unpack(event.message.data.value)
        if ethernet.type != 0x88cc:

            port_no = event.message.in_port
            hw_address = event.message.source
            switch = event.source.switch
            interface = switch.get_interface_by_port_no(port_no)
            if not interface.is_link_between_switches():
                interface.update_endpoint(hw_address)

    def shutdown(self):
        self.stop_signal = True
