import logging

from kyco.constants import POOLING_TIME
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.foundation.basic_types import DPID, UBInt16
from pyof.foundation.network_types import LLDP, Ethernet
from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.controller2switch.packet_out import PacketOut

log = logging.getLogger(__name__)


class Main(KycoCoreNApp):
    """Main lldp app class."""

    def setup(self):
        """Create an empty dict to store the switches references and data."""
        self.name = 'kytos/of.lldp'
        self.execute_as_loop(POOLING_TIME)
        self.controller.log_websocket.register_log(log)

    def execute(self):
        """Implement a loop to check switches liveness."""
        for switch in self.controller.switches.values():
            # Gerar lldp para cada uma das portas do switch
            # Gerar o hash de cada um dos pacotes e armazenar

            for port in switch.features.ports:
                output_action = ActionOutput()
                output_action.port = port.port_no

                if port.port_no.value == 65534:
                    continue

                ethernet = Ethernet()
                ethernet.type = 0x88cc  # lldp
                ethernet.source = port.hw_addr
                ethernet.destination = '01:80:c2:00:00:0e'  # lldp multicast

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

            if interface_a is not None and interface_b is not None:
                interface_a.update_endpoint(interface_b)
                interface_b.update_endpoint(interface_a)

    def shutdown(self):
        pass
