"""NApp responsible to update links detail and create a network topology."""

import json

from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to
from pyof.foundation.basic_types import HWAddress
from pyof.foundation.network_types import Ethernet

from napps.kytos.of_topology import constants


class Main(KytosNApp):
    """Main class of a KytosNApp, responsible build a network topology.

    This app intends to update the links between machines and switches. It
    considers that if an interface is connected to another interface then this
    is a link. If not, it must be a connection to a server.
    """

    def setup(self):
        """Nothing to setup."""
        pass

    def execute(self):
        """Do nothing, only wait for packet-in messages."""
        pass

    @staticmethod
    @listen_to('kytos/of_core.v0x01.messages.in.ofpt_packet_in')
    def update_links(event):
        """Receive a kytos event and update links interface.

        Get the event kytos/of_core.messages.in.ofpt_packet_in and update
        the interface endpoints, ignoring the LLDP packages.

        Parameters:
            event (KytosEvent): event with Ethernet packet.
        """
        ethernet = Ethernet()
        ethernet.unpack(event.message.data.value)
        if ethernet.ether_type != constants.LLDP_ETHERTYPE:
            port_no = event.message.in_port
            hw_address = ethernet.source
            switch = event.source.switch
            interface = switch.get_interface_by_port_no(port_no.value)

            if interface is not None and \
               not interface.is_link_between_switches():
                interface.update_endpoint(hw_address)

    @staticmethod
    @listen_to('kytos/of_core.v0x01.messages.in.ofpt_port_status')
    def update_port_stats(event):
        """Receive a Kytos event and update port.

        Get the event kytos/of_core.messages.in.ofpt_port_status and update the
        port status.

        Parameters:
            event (KytosEvent): event with port_status content.
        """
        port_status = event.message
        reasons = ['CREATED', 'DELETED', 'MODIFIED']
        dpid = event.source.switch.dpid
        port_no = port_status.desc.port_no
        port_name = port_status.desc.name
        reason = reasons[port_status.reason.value]
        msg = 'The port %s (%s) from switch %s was %s.'
        log.debug(msg, port_no, port_name, dpid, reason)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')

    @rest('topology')
    def get_json_topology(self):
        """Return a json with topology details.

        Method responsible to return a json in /kytos/topology route.
        Returns:
            topology (string): json with topology details.
        """
        nodes, links = [], []
        switches = self.controller.switches

        switches_mac_address = []
        for switch in switches.values():
            for interface in switch.interfaces.values():
                switches_mac_address.append(interface.address)

        for _, switch in switches.items():
            nodes.append(switch.as_dict())
            for _, interface in switch.interfaces.items():
                link = {'source': switch.id,
                        'target': interface.id,
                        'type': 'interface'}
                nodes.append(interface.as_dict())
                links.append(link)

                for endpoint, _ in interface.endpoints:
                    if isinstance(endpoint, HWAddress):
                        if endpoint in switches_mac_address:
                            continue

                        link = {'source': interface.id,
                                'target': endpoint.value,
                                'type': 'link'}
                        host = {"type": 'host',
                                "id": endpoint.value,
                                "name": endpoint.value,
                                "mac": endpoint.value}
                        if host not in nodes:
                            nodes.append(host)
                        if not interface.is_link_between_switches():
                            links.append(link)
                    else:
                        link = {'source': interface.id,
                                'target': endpoint.id,
                                'type': 'link'}
                        links.append(link)

        output = {'nodes': nodes, 'links': links}
        return json.dumps(output)
