"""Module that implements a L2 Learning Switch algorithm with loop support."""

from kytos.core.events import KytosEvent
from kytos.core.napps import KytosNApp
from kytos.core.helpers import listen_to
from pyof.foundation.network_types import Ethernet
from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.flow_match import FlowWildCards, Match
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.controller2switch.packet_out import PacketOut

from napps.kytos.of_l2lsloop import settings


class Main(KytosNApp):
    """The main class for of.l2lsloop application."""

    def setup(self):
        """Method used to setup the of.l2lsloop application."""
        pass

    def execute(self):
        """Do nothing."""
        pass

    @listen_to('kytos/of_core.messages.in.ofpt_packet_in')
    def handle_packet_in(self, event):
        """Method to handle flows to allow communication between switch ports.

        Args:
            event (:class:`~kytos.core.events.KytosEvent):
                event with packet_in message.
        """
        self.log.debug("PacketIn Received")
        packet_in = event.content['message']
        ethernet = Ethernet()
        ethernet.unpack(packet_in.data.value)
        in_port = packet_in.in_port.value
        switch = event.source.switch
        switch.update_mac_table(ethernet.source, in_port)
        ports = switch.where_is_mac(ethernet.destination)

        if ports:
            flow_mod = FlowMod()
            flow_mod.command = FlowModCommand.OFPFC_ADD
            flow_mod.match = Match()
            flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_SRC
            flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_DST
            flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_TYPE
            flow_mod.match.dl_src = ethernet.source.value
            flow_mod.match.dl_dst = ethernet.destination.value
            flow_mod.match.dl_type = ethernet.ether_type
            flow_mod.buffer_id = packet_in.buffer_id
            flow_mod.actions.append(ActionOutput(port=ports[0]))

            message_name = 'kytos/of_l2ls.messages.out.ofpt_flow_mod'
            content = {'destination': event.source,
                       'message': flow_mod}
            event_out = KytosEvent(name=message_name, content=content)

        elif switch.should_flood(ethernet):
            # Flood the packet if we haven't done it yet
            packet_out = PacketOut()
            packet_out.buffer_id = packet_in.buffer_id
            packet_out.in_port = packet_in.in_port

            packet_out.actions.append(ActionOutput(port=Port.OFPP_FLOOD))

            switch.update_flood_table(ethernet)

            message_name = 'kytos/of_l2ls.messages.out.ofpt_packet_out'
            content = {'destination': event.source,
                       'message': packet_out}
            event_out = KytosEvent(name=message_name,
                                   content=content)
        else:
            msg = "Not sending flood, since that was flooded already."
            self.log.debug(msg)
            return

        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        """End of the application."""
        self.log.debug('Shutting down...')
