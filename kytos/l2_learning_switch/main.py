"""This App is the responsible for the main OpenFlow basic operations."""

import logging

from pyof.v0x01.common.header import Header 
from pyof.v0x01.common import constants

from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.phy_port import Port

from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.common.flow_match import FlowWildCards

from pyof.foundation.basic_types import HWAddress

from pyof.v0x01.controller2switch.common import ListOfActions
from pyof.v0x01.controller2switch.flow_mod import FlowMod
from pyof.v0x01.controller2switch.flow_mod import FlowModCommand
from pyof.v0x01.controller2switch.flow_mod import FlowModFlags

from pyof.v0x01.controller2switch.packet_out import PacketOut

from kyco.core import events
from kyco.utils import KycoCoreNApp
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
        self.mac2port = {} 

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        pass


    @listen_to('KycoPacketIn')
    def handle_message_in_packet_event(self, event):
        """Handle PacketIn Event by installing flows allowing communication
        between switch ports.

        Args:
            event (KycoPacketIn): Received Event
        """
        log.debug("PacketIn Received")

        log.warning(event.dpid)
        log.warning(event.connection_id)
        packet_in = event.content['message']


        ethernet_frame = packet_in.data


        mac_dst = HWAddress()
        mac_src = HWAddress()
        
        mac_dst.unpack(ethernet_frame.value[0:6])
        mac_src.unpack(ethernet_frame.value[6:12])


        in_port = packet_in.in_port.value
        
        self.mac2port[mac_src.value] = (event.dpid, in_port)
        
        if mac_dst.is_broadcast():
            packet_out = PacketOut(xid=packet_in.header.xid)
            packet_out.buffer_id = packet_in.buffer_id
            packet_out.in_port = packet_in.in_port
            #TODO: update actions_len on packet_out dynamically during pack()
            packet_out.actions_len = 8 #Only one ActionOutput (amount of bytes)

            output_action = ActionOutput()
            output_action.port = Port.OFPP_FLOOD
            output_action.max_length = 0

            packet_out.actions.append(output_action)
            content = {'message': packet_out}
            event_out = events.KycoPacketOut(event.dpid, content)
            self.controller.buffers.msg_out.put(event_out)

        #Install Flow with the information from the packet_in just received
        flow_mod = FlowMod(xid=packet_in.header.xid)
        flow_mod.command = FlowModCommand.OFPFC_ADD
        flow_mod.match = Match()
        #flow_mod.match.wildcards = FlowWildCards.OFPFW_DL_DST
        flow_mod.match.wildcards = 1 << 4 
        flow_mod.cookie = 0
        flow_mod.idle_timeout = 100
        flow_mod.hard_timeout = 300
        flow_mod.priority = 100 # a high number
        flow_mod.buffer_id = constants.NO_BUFFER
        flow_mod.out_port = Port.OFPP_NONE
        flow_mod.flags = FlowModFlags.OFPFF_CHECK_OVERLAP # 0 pox
        flow_mod.match.in_port = Port.OFPP_NONE
        flow_mod.match.dl_src = '00:00:00:00:00:00'
        flow_mod.match.dl_dst = mac_src.value
        flow_mod.match.dl_vlan = 0xffff
        flow_mod.match.dl_vlan_pcp = 0
        flow_mod.match.dl_type = 0
        flow_mod.match.nw_tos = 0
        flow_mod.match.nw_proto = 0
        flow_mod.match.nw_src = 0
        flow_mod.match.nw_dst = 0
        flow_mod.match.tp_src = 0
        flow_mod.match.tp_dst = 0

        output_action = ActionOutput()
        output_action.port = packet_in.in_port
        output_action.max_length = 0
        flow_mod.actions.append(output_action)
        
        log.debug("Action: %s", output_action.pack())

        content = {'message': flow_mod}
        event_out = events.KycoMessageOutFlowMod(event.dpid, content)
        self.controller.buffers.msg_out.put(event_out)


    def shutdown(self):
        pass

