import logging
import json

from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.foundation.network_types import Ethernet
from pyof.foundation.basic_types import HWAddress


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
        self.controller.register_rest_endpoint('/topology',
                                               self.get_json_topology,
                                               methods=['GET'])

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
            hw_address = ethernet.source
            switch = event.source.switch
            interface = switch.get_interface_by_port_no(port_no.value)

            if interface != None and not interface.is_link_between_switches():
                interface.update_endpoint(hw_address)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')

    def get_json_topology(self):
        nodes,links = [], []
        for dpid, switch in self.controller.switches.items():
            nodes.append(switch.as_dict())
            for port_no, interface in switch.interfaces.items():
                link = {'source': switch.id,
                        'target': interface.id,
                        'type': 'interface'}
                nodes.append(interface.as_dict())
                links.append(link)

                for endpoint, ts in interface.endpoints:
                    if type(endpoint) is HWAddress:
                        link = {'source': interface.id,
                                'target': endpoint.value,
                                'type': 'link'}
                        host = {"type": 'host',
                                "id": endpoint.value,
                                "name": endpoint.value,
                                "mac": endpoint.value}
                        if not interface.is_link_between_switches():
                            links.append(link)
                            nodes.append(host)
                    else:
                        link = {'source': interface.id,
                                'target': endpoint.id,
                                'type': 'link'}
                        links.append(link)

        output = {'nodes': nodes, 'links': links}
        return json.dumps(output)
