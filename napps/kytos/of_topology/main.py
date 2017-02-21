"""NApp responsible to update links detail and create a network topology."""

import json

from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.foundation.basic_types import HWAddress
from pyof.foundation.network_types import Ethernet

from napps.kytos.of_topology import constants, settings

log = settings.log


class Main(KycoCoreNApp):
    """Main class of a KycoCoreNApp, responsible build a network topology.

    This app intends to update the links between machines and switches. It
    considers that if an interface is connected to another interface then this
    is a link. If not, it must be a connection to a server.
    """

    def setup(self):
        """Setup the app of.topology.

        This setup will set the name of app, register the endpoint
        /kytos/topology and setup the logger.
        """
        self.name = 'kytos/of.topology'
        self.controller.register_rest_endpoint('/topology',
                                               self.get_json_topology,
                                               methods=['GET'])
        self.controller.log_websocket.register_log(log)

    def execute(self):
        """Do nothing, only wait for packet-in messages."""
        pass

    @staticmethod
    @listen_to('kytos/of.core.messages.in.ofpt_packet_in')
    def update_links(event):
        """Receive a kytos event and update links interface.

        Get the event kytos/of.core.messages.in.ofpt_packet_in and update
        the interface endpoints, ignoring the LLDP packages.

        Parameters:
            event (KycoEvent): event with Ethernet packet.
        """
        ethernet = Ethernet()
        ethernet.unpack(event.message.data.value)
        if ethernet.type != constants.LLDP_ETHERTYPE:
            port_no = event.message.in_port
            hw_address = ethernet.source
            switch = event.source.switch
            interface = switch.get_interface_by_port_no(port_no.value)

            if interface is not None and \
               not interface.is_link_between_switches():
                interface.update_endpoint(hw_address)

    @staticmethod
    @listen_to('kytos/of.core.messages.in.ofpt_port_status')
    def update_port_stats(event):
        """Receive a Kytos event and update port.

        Get the event kytos/of.core.messages.in.ofpt_port_status and update the
        port status.

        Parameters:
            event (KycoEvent): event with port_status content.
        """
        port_status = event.content['message']
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

    def get_json_topology(self):
        """Return a json with topology details.

        Method responsible to return a json in /kytos/topology route.
        Returns:
            topology (string): json with topology details.
        """
        nodes, links = [], []
        for _, switch in self.controller.switches.items():
            nodes.append(switch.as_dict())
            for _, interface in switch.interfaces.items():
                link = {'source': switch.id,
                        'target': interface.id,
                        'type': 'interface'}
                nodes.append(interface.as_dict())
                links.append(link)

                for endpoint, _ in interface.endpoints:
                    if isinstance(endpoint, HWAddress):
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
