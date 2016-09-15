"""This App is the responsible for the main OpenFlow basic operations."""

import logging

from pyof.v0x01.common import header as of_header
from pyof.v0x01.common import constants

from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.phy_port import Port

from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.common.flow_match import FlowWildCards

from pyof.v0x01.controller2switch.common import ListOfActions
from pyof.v0x01.controller2switch.flow_mod import FlowMod
from pyof.v0x01.controller2switch.flow_mod import FlowModCommand
from pyof.v0x01.controller2switch.flow_mod import FlowModFlags



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


    @listen_to('KycoMessageInPacketIn')
    def handle_message_in_packet_event(self, event):
        """Handle PacketIn Event by installing flows allowing communication
        between switch ports.

        Args:
            event (KycoMessageInPacketIn): Received Event
        """
        log.debug("PacketIn Received")

        log.warning(event.dpid)
        log.warning(event.connection_id)
        packet_in = event.content['message']

        ethernet_frame = packet_in.data

        mac_dst = HWAddress()
        mac_src = HWAddress()
        
        mac_dst.unpack(ethernet_frame[0:6])
        mac_src.unpack(ethernet_frame[6:12])

        in_port = packet_in.in_port.value
        
        self.mac2port[mac_src.value] = (event.dpid, in_port)
        
        if mac_dst.is_broadcast():
            packet_out = PacketOut(xid = packet_in.header.xid)
            packet_out.buffer_id = packet_in.buffer_id
            packet_out.in_port = packet_in.in_port
            packet_out.actions_len = 8 #Only one ActionOutput (amount of bytes)

            actions = ListOfActions()
            output_action = ActionOutput()
            output_action.port = Port.OFPP_FLOOD
            output_action.max_length = 0

            actions.append(output_action)
            content = {'message': packet_out}
            event_out = events.KycoMessageOutEchoReply(event.dpid, content)
            self.controller.buffers.msg_out.put(event_out)

        #Install Flow with the information from the packet_in just received
        flow_mod = FlowMod(xid=packet_in.xid)
        flow_mod.command = FlowModCommand.OFPFC_ADD
        flow_mod.match = Match()
        flow_mod.match.wildcards = FlowWildCards.OFPFW_DL_DST
        flow_mod.cookie = 0
        flow_mod.idle_timeout = 100
        flow_mod.hard_timeout = 300
        flow_mod.priority = 100 # a high number
        flow_mod.buffer_id = constants.NO_BUFFER
        flow_mod.out_port = Port.OFPP_NONE
        flow_mod.flags = FlowModFlags.OFPFF_CHECK_OVERLAP # 0 pox
        flow_mod.match.in_port = 2
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

        actions = ListOfActions()
        output_action = ActionOutput()
        output_action.port = packet_in.in_port
        output_action.max_length = 0
        actions.append(output_action)
        flow_mod.actions = actions
            



    def shutdown(self):
        pass

def install_flow(controller, buffer_id):
    
    head = of_header.Header()

    message = flow_mod.FlowMod()
    message.header.xid = 1
    message.command = flow_mod.FlowModCommand.OFPFC_ADD
    message.match = flow_match.Match()
    message.match.wildcards = flow_match.FlowWildCards.OFPFW_IN_PORT
    message.cookie = 0
    message.idle_timeout = 100
    message.hard_timeout = 300
    message.priority = 32768
    message.buffer_id = 2**32-1
    message.out_port = phy_port.Port.OFPP_NONE
    message.flags = 0
    #message.flags = flow_mod.FlowModFlags.OFPFF_CHECK_OVERLAP
    message.match.in_port = 2
    message.match.dl_src = '00:00:00:00:00:02'
    message.match.dl_dst = '00:00:00:00:00:01'
    message.match.dl_vlan = 0xffff
    message.match.dl_vlan_pcp = 0
    message.match.dl_type = 0
    message.match.nw_tos = 0
    message.match.nw_proto = 0
    message.match.nw_src = 0
    message.match.nw_dst = 0
    message.match.tp_src = 0
    message.match.tp_dst = 0

    actions = ListOfActions()

    output_action = ActionOutput()


    output_action.port = 1

    output_action.max_length = 18

    actions.append(output_action)

    message.actions = actions

    destination = list(controller.connections)[0]

    controller.send_to(destination,message.pack())




