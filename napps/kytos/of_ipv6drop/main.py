"""NApp responsible for installing a DROP ipv6 flow on switch setup."""

from kytos.core import KytosEvent, KytosNApp, log
from kytos.core.helpers import listen_to
from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand


class Main(KytosNApp):
    """Main class of of_ipv6drop NApp."""

    def setup(self):
        """Replace the 'init' method for the KytosApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        pass

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KytosNApp class.
        Users shouldn't call this method directly.
        """
        pass

    @listen_to('kytos/core.switch.new')
    def ipv6_drop(self, event):
        """Install a flow on the switch that drop all incoming ipv6 packets."""
        switch = event.content['switch']
        if switch.connection.protocol.version is not 0x01:
            return

        flow_mod = FlowMod()
        flow_mod.command = FlowModCommand.OFPFC_ADD
        flow_mod.match = Match()
        flow_mod.match.dl_type = 0x86dd  # ipv6
        event_out = KytosEvent(name=('kytos/of_ipv6drop.messages.out.'
                                     'ofpt_flow_mod'),
                               content={'destination': switch.connection,
                                        'message': flow_mod})
        log.info('Sending "IPv6 DROP" flow to switch %s', switch.id)
        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        """End of the application."""
        pass
