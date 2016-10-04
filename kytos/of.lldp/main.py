import logging
import time

from pyof.foundation.basic_types import HWAddress, UBInt8, UBInt16, UBInt64
from pyof.foundation.constants import UBINT64_MAX_VALUE
from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.constants import NO_BUFFER
from pyof.v0x01.common.flow_match import FlowWildCards, Match
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.controller2switch.packet_out import PacketOut

from kyco.constants import POOLING_TIME
from kyco.core import events
from kyco.core.events import KycoEvent
from kyco.utils import KycoCoreNApp, listen_to

log = logging.getLogger('KycoNApp')


class Main(KycoCoreNApp):
    """
    """

    def setup(self):
        """Creates an empty dict to store the switches references and data"""
        self.name = 'kytos/of.lldp'
        self.stop_signal = False
        # TODO: This switches object may change according to changes from #62

    def execute(self):
        """Implement a loop to check switches liveness"""
        while not self.stop_signal:
            for switch in self.controller.switches.values():
                # Gerar lldp para cada uma das portas do switch
                # Gerar o hash de cada um dos pacotes e armazenar

                for port in switch.features.ports:
                    output_action = ActionOutput()
                    output_action.port = port.port_no

                    packet_out = PacketOut()
                    packet_out.data = lldp_generator(port.hw_addr,
                                                     switch.dpid,
                                                     port.port_no)
                    packet_out.actions.append(output_action)
                    event_out = KycoEvent()
                    event_out.name = 'kytos/of.lldp.messages.out.packet_out'
                    event_out.content = {'destination': switch.connection,
                                         'message': packet_out}
                    self.controller.buffers.msg_out.put(event_out)

                    log.debug("Sending a LLDP PacketOut to the switch %s",
                              switch.dpid)

            # wait 1s until next check...
            time.sleep(POOLING_TIME)

    @listen_to('KycoMessageIn')
    def update_lldp(self, event):
        log.debug("PacketIn Received")
        packet_in = event.message
        # ethernet_frame = packet_in.data

    @listen_to('KycoSwitchUp')
    def install_lldp_flow(self, event):
        """Install initial flow to forward any lldp to controller.

        Args:
            event (KycoSwitchUp): Switch connected to the controller
        """
        log.debug("Installing LLDP Flow on Switch %s",
                  event.source.switch.dpid)

        flow_mod = FlowMod()
        flow_mod.command = FlowModCommand.OFPFC_ADD
        flow_mod.match = Match()
        flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_DST
        flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_TYPE
        flow_mod.match.dl_dst = "01:23:20:00:00:01"
        flow_mod.match.dl_type = 0x88cc
        flow_mod.priority = 65000  # a high number TODO: Review
        flow_mod.actions.append(ActionOutput(port=Port.OFPP_CONTROLLER,
                                             max_length=UBINT64_MAX_VALUE))
        event_out = KycoEvent(name='kytos/of.lldp.messages.out.ofpt_flow_mod',
                              content={'destination': event.source,
                                       'message': flow_mod})

        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        self.stop_signal = True


def lldp_generator(src_mac, dpid, port):
    """ Generate a lldp ethernet packet.
    This frame must be unique for each port of each switch. In order to create
    unique LLDP frames, it use SRC Mac Address, DPID and PORT. This routine
    is based on POX controller.

    Args:
        src_mac (string): A string representing the MAC ADDRESS of the
            port.
        dpid (string): Switch unique ID
    """

    # Ether Header
    # dst_mac_bin = b'\x01\x80\xc2\x00\x00\x0e'

    lldp_broadcast = HWAddress(hw_address='01:80:c2:00:00:0e')
    dst_mac_bin = lldp_broadcast.pack()
    ether_type = b'\x88\xcc'
    # src_mac = src_mac.split(':')
    # src_mac_bin = pack('!6B', *[int(x, 16) for x in src_mac])
    src_mac_bin = src_mac.pack()
    ether_header = dst_mac_bin + src_mac_bin + ether_type
    lldp_frame = ether_header

    # LLDP Payload

    # Chassis ID TLV
    # Type
    TLV1_type = b'\x02'
    # Len
    TLV1_len = b'\x07'
    # Subtype
    TLV1_subtype = b'\x04'
    # Value
    TLV1_value = src_mac_bin
    TLV1 = TLV1_type + TLV1_len + TLV1_subtype + TLV1_value

    # Port ID TLV
    TLV2_type = b'\x04'
    # TODO: Port must change to create unique LLDP frames
    TLV2_len = b'\x02'
    TLV2_subtype = b'\x02'
    TLV2_value = port.pack()
    TLV2_len = port.get_size()+1
    TLV2 = TLV2_type + TLV2_len.to_bytes(1,'big') + TLV2_subtype + TLV2_value

    # TTL TLV
    TLV3_type = b'\x06'
    TLV3_len = b'\x02'
    TLV3_value = b'\x00\x78'
    TLV3 = TLV3_type + TLV3_len + TLV3_value

    # System Description TLV
    TLV4_type = b'\x0c'
    # TODO: Sys desc must change to create unique LLDP frames
    TLV4_value = UBInt64(value=int(dpid))
    TLV4_len = UBInt8(value=TLV4_value.get_size())
    TLV4 = TLV4_type + TLV4_len.pack() + TLV4_value.pack()

    # sys_desc = str.encode(dpid) + port.pack() + src_mac_bin
    # TLV4 += len(sys_desc).to_bytes(2, byteorder='big')
    # TLV4 += sys_desc
    # lldp_frame += TLV4

    # End of LLDPDU
    TLV5_type = b'\x00'
    TLV5_len = b'\x00'
    TLV5 = TLV5_type + TLV5_len

    lldp_frame += TLV1 + TLV2 + TLV3 + TLV4 + TLV5

    return lldp_frame
