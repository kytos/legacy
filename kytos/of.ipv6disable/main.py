"""This App is the responsible to install a drop ipv6 flow on switch setup."""

import logging

from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.common.flow_match import FlowWildCards, Match

from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to


log = logging.getLogger('Kyco')


class Main(KycoCoreNApp):
    """Main class of KycoCoreNApp, responsible for the main OpenFlow basic
    operations.

    """

    def setup(self):
        """'Replaces' the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly."""
        pass

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        pass

    @listen_to('kyco/core.switches.new')
    def disable_ipv6(self, event):
        
        switch = event.content['switch']

        flow_mod = FlowMod()
        flow_mod.command = FlowModCommand.OFPFC_ADD
        flow_mod.match = Match()
        flow_mod.match.wildcards -= FlowWildCards.OFPFW_DL_TYPE
        flow_mod.match.dl_type = 0x86dd # ipv6
        event_out = KycoEvent(name='kytos/of.ipv6disable.messages.out.ofpt_flow_mod',
                              content={'destination': switch.connection,
                                       'message': flow_mod})
        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        pass
