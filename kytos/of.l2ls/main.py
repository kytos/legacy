"""This App is the responsible for the main OpenFlow basic operations."""

import logging

# TODO: This timeout should be setup on a config file from this napp
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.foundation.network_types import Ethernet
from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.controller2switch.packet_out import PacketOut

log = logging.getLogger('KycoNApp')


class Main(KycoCoreNApp):
    """Main class of KycoCoreNApp, responsible for the main OpenFlow basic
    operations.

    """

    def setup(self):
        """'Replaces' the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly."""
        # TODO: App information goes to app_name.json
        self.name = 'kytos.l2_learning_switch'
        self.controller.log_websocket.register_log(log)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        pass

    @listen_to('kytos/of.core.messages.in.ofpt_packet_in')
    def handle_packet_in(self, event):
        """Handle PacketIn Event by installing flows allowing communication
        between switch ports.

        Args:
            event (KycoPacketIn): Received Event
        """
        log.debug("PacketIn Received")

        packet_in = event.content['message']

        ethernet = Ethernet()
        ethernet.unpack(packet_in.data.value)
        in_port = packet_in.in_port.value
        switch = event.source.switch

        switch.update_mac_table(ethernet.source, in_port)

        lldp_macs = ['01:80:c2:00:00:0e', '01:80:c2:00:00:03',
                     '01:80:c2:00:00:00']

        # IGNORE LLDP packets
        if ethernet.destination not in lldp_macs:
            ports = switch.where_is_mac(ethernet.destination)

            if ports:
                flow_mod = FlowMod()
                flow_mod.command = FlowModCommand.OFPFC_ADD
                flow_mod.match = Match()
                flow_mod.match.dl_src = ethernet.source.value
                flow_mod.match.dl_dst = ethernet.destination.value
                flow_mod.match.dl_type = ethernet.type
                flow_mod.buffer_id = packet_in.buffer_id
                flow_mod.actions.append(ActionOutput(port=ports[0]))
                event_out = KycoEvent(name=('kytos/of.l2ls.messages.out.'
                                            'ofpt_flow_mod'),
                                      content={'destination': event.source,
                                               'message': flow_mod})
            else:
                # Flood the packet if we haven't done it yet
                packet_out = PacketOut()
                packet_out.buffer_id = packet_in.buffer_id
                packet_out.in_port = packet_in.in_port

                packet_out.actions.append(ActionOutput(port=Port.OFPP_FLOOD))
                event_out = KycoEvent(name=('kytos/of.l2ls.messages.out.'
                                            'ofpt_packet_out'),
                                      content={'destination': event.source,
                                               'message': packet_out})

            self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        pass
