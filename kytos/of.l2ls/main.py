"""This App is the responsible for the main OpenFlow basic operations."""

import logging

from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.phy_port import Port

from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.common.flow_match import FlowWildCards

from pyof.foundation.basic_types import Ethernet

from pyof.v0x01.controller2switch.flow_mod import FlowMod
from pyof.v0x01.controller2switch.flow_mod import FlowModCommand
from pyof.v0x01.controller2switch.flow_mod import FlowModFlags

from pyof.v0x01.controller2switch.packet_out import PacketOut

# TODO: This timeout should be setup on a config file from this napp
from kyco.constants import FLOOD_TIMEOUT
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to


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
        # Updating mac_src and in_port
        if ethernet.source.value in switch.mac2port:
            switch.mac2port[ethernet.source.value].add(in_port)
        else:
            switch.mac2port[ethernet.source.value] = set([in_port])

#        msg = '----------------------------------------------------------\n'
#        msg += '    dpid({}) | '.format(switch.dpid)
#        msg += 'port({}) | '.format(switch.connection_id[1])
#        msg += 'src({}) | '.format(mac_src.value)
#        msg += 'dst({})\n'.format(mac_dst.value)
#        msg += '    switch_mac2port: {}\n'.format(switch.mac2port)
#        msg += '    switch_flood_table: {}\n'.format(switch.flood_table)
#        msg += '=======================================================\n\n'

        if ethernet.destination.value in switch.mac2port:
            # If we know the destination, just forward it.
            # Install a Flow with destination on the dst of this packet.
            flow_mod = FlowMod(xid=packet_in.header.xid)
            flow_mod.command = FlowModCommand.OFPFC_ADD
            flow_mod.match = Match()
            # As the default value for wildcards is OFPFW_ALL,
            # we will decrement the bit of OFPFW_DL_DST.
            flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_SRC
            flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_DST
            flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_TYPE
            flow_mod.match.dl_src = ethernet.source.value
            flow_mod.match.dl_dst = ethernet.destination.value
            flow_mod.match.dl_type = ethernet.type
            flow_mod.cookie = 0
            flow_mod.idle_timeout = 100
            flow_mod.hard_timeout = 200
            flow_mod.priority = 100  # a high number
            flow_mod.buffer_id = packet_in.buffer_id
            flow_mod.out_port = Port.OFPP_NONE
            flow_mod.flags = FlowModFlags.OFPFF_CHECK_OVERLAP  # 0 pox

            output_action = ActionOutput()
            output_action.port = list(switch.mac2port[ethernet.destination.value])[0]
            output_action.max_length = 0
            flow_mod.actions.append(output_action)

#            msg2 = '\n\n====================================================\n'
#            msg2 += ' ************* FORWARDING ************* '
#            msg2 += '    Dest: {} | out_port: {}\n'.format(mac_dst.value,
#                                                           output_action.port)
#            msg2 += msg
#            log.debug(msg2)

            event_out = KycoEvent(name='kytos/of.l2ls.messages.out.ofpt_flow_mod',
                                  content={'destination': event.source,
                                           'message': flow_mod})
            self.controller.buffers.msg_out.put(event_out)
        else:
            # Flood the packet if we haven't done it yet
            packet_out = PacketOut(xid=packet_in.header.xid)
            packet_out.buffer_id = packet_in.buffer_id
            packet_out.in_port = packet_in.in_port
            # TODO: update actions_len on packet_out dynamically during pack()
            packet_out.actions_len = 8  # Only 1 ActionOutput (bytes)

            output_action = ActionOutput()
            output_action.port = Port.OFPP_FLOOD
            output_action.max_length = 0

#            msg2 = '\n\n====================================================\n'
#            msg2 += ' $$$$$$$$$$$$$ FLOODING $$$$$$$$$$$$$ '
#            msg2 += '    Dest: {} | out_port: {}\n'.format(mac_dst.value,
#                                                           output_action.port)
#            msg2 += msg
#            log.debug(msg2)

            packet_out.actions.append(output_action)
            content = {'message': packet_out}
            event_out = KycoEvent(name='kytos/of.l2ls.messages.out.ofpt_packet_out',
                                  content={'destination': event.source,
                                           'message': packet_out})
            self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        pass
