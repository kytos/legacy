"""This App is the responsible to install a drop ipv6 flow on switch setup."""

import logging

from pyof.v0x01.controller2switch.stats_request import StatsRequest
from pyof.v0x01.controller2switch.common import StatsTypes, FlowStatsRequest
#from pyof.v0x01.common.flow_match import FlowWildCards, Match

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
    def stats_request(self, event):
        
        switch = event.content['switch']

        request = StatsRequest(body_type=StatsTypes.OFPST_FLOW,
                               body=FlowStatsRequest().pack())

        event_out = KycoEvent(name='kytos/of.flow-manager.messages.out.ofpt_stats_request',
                              content={'destination': switch.connection,
                                       'message': request})
        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        pass
