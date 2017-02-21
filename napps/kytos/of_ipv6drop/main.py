"""NApp responsible for installing a DROP ipv6 flow on switch setup."""

from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand

from napps.kytos.of_ipv6drop import settings

log = settings.log


class Main(KycoCoreNApp):
    """Main class of of_ipv6drop NApp."""

    def setup(self):
        """Replace the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        self.controller.log_websocket.register_log(log)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly.
        """
        pass

    @listen_to('kyco/core.switches.new')
    def ipv6_drop(self, event):
        """Install a flow on the switch that drop all incoming ipv6 packets."""
        switch = event.content['switch']

        flow_mod = FlowMod()
        flow_mod.command = FlowModCommand.OFPFC_ADD
        flow_mod.match = Match()
        flow_mod.match.dl_type = 0x86dd  # ipv6
        event_out = KycoEvent(name=('kytos/of.ipv6disable.messages.out.'
                                    'ofpt_flow_mod'),
                              content={'destination': switch.connection,
                                       'message': flow_mod})
        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        """End of the application."""
        pass
