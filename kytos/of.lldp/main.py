import logging
import time

from kyco.constants import POOLING_TIME
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.foundation.basic_types import HWAddress, UBInt8, UBInt16, UBInt64, DPID
from pyof.foundation.constants import UBINT16_MAX_VALUE
from pyof.foundation.network_types import Ethernet, LLDP
from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.constants import NO_BUFFER
from pyof.v0x01.common.flow_match import FlowWildCards, Match
from pyof.v0x01.common.phy_port import Port
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.controller2switch.packet_out import PacketOut

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

                    if port.port_no.value == 65534:
                        continue

                    ethernet = Ethernet()
                    ethernet.type = 0x88cc # lldp
                    ethernet.source = port.hw_addr
                    ethernet.destination = '01:80:c2:00:00:0e' # lldp multicast

                    lldp = LLDP()
                    lldp.chassis_id.sub_value = DPID(switch.dpid)
                    lldp.port_id.sub_value = port.port_no

                    ethernet.data = lldp.pack()

                    packet_out = PacketOut()
                    packet_out.actions.append(output_action)
                    packet_out.data = ethernet.pack()

                    event_out = KycoEvent()
                    event_out.name = 'kytos/of.lldp.messages.out.ofpt_packet_out'
                    event_out.content = {'destination': switch.connection,
                                         'message': packet_out}
                    self.controller.buffers.msg_out.put(event_out)

                    log.debug("Sending a LLDP PacketOut to the switch %s",
                              switch.dpid)

            # wait 1s until next check...
            time.sleep(POOLING_TIME)

    @listen_to('kytos/of.core.messages.in.ofpt_packet_in')
    def update_links(self, event):
        ethernet = Ethernet()
        ethernet.unpack(event.message.data.value)
        if ethernet.type == 0x88cc:
            lldp = LLDP()
            lldp.unpack(ethernet.data.value)

            dpid = DPID()
            dpid.unpack(lldp.chassis_id.sub_value.value)

            port_no_b = UBInt16()

            switch_a = event.source.switch
            port_no_a = event.message.in_port
            interface_a = switch_a.get_interface_by_port_no(port_no_a.value)

            switch_b = self.controller.get_switch_by_dpid(dpid.value)
            port_no_b.unpack(lldp.port_id.sub_value.value)
            interface_b = switch_b.get_interface_by_port_no(port_no_b.value)

            interface_a.update_endpoint(interface_b)
            interface_b.update_endpoint(interface_a)

#    @listen_to('kyco/core.switches.new')
#    def install_lldp_flow(self, event):
#        """Install initial flow to forward any lldp to controller.
#
#        Args:
#            event (KycoSwitchUp): Switch connected to the controller
#        """
#        switch = event.content['switch']
#        log.debug("Installing LLDP Flow on Switch %s",
#                  switch.dpid)
#
#        flow_mod = FlowMod()
#        flow_mod.command = FlowModCommand.OFPFC_ADD
#        flow_mod.match = Match()
#        flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_DST
#        flow_mod.match.dl_type = LLDP_ETH_TYPE
#        flow_mod.priority = 65000  # a high number TODO: Review
#        flow_mod.actions.append(ActionOutput(port=Port.OFPP_CONTROLLER,
#                                             max_length=UBINT16_MAX_VALUE))
#        event_out = KycoEvent(name='kytos/of.lldp.messages.out.ofpt_flow_mod',
#                              content={'destination': switch.connection,
#                                       'message': flow_mod})
#
#        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        self.stop_signal = True
