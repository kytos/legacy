"""This App is the responsible for the main OpenFlow basic operations."""

from logging import getLogger

from kyco.core.events import KycoEvent
from kyco.core.flow import Flow
from kyco.core.napps import KycoCoreNApp
from kyco.core.switch import Interface
from kyco.utils import listen_to
from pyof.v0x01.common.utils import new_message_from_header
from pyof.v0x01.controller2switch.common import FlowStatsRequest
from pyof.v0x01.controller2switch.features_request import FeaturesRequest
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes
from pyof.v0x01.symmetric.echo_reply import EchoReply
from pyof.v0x01.symmetric.hello import Hello

log = getLogger('Kyco')
STATS_INTERVAL = 5


class Main(KycoCoreNApp):
    """Main class of KycoCoreNApp, responsible for the main OpenFlow basic
    operations.

    """

    def setup(self):
        """'Replaces' the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly."""
        # TODO: App information goes to app_name.json
        self.name = 'kytos/of.core'
        self.execute_as_loop(STATS_INTERVAL)
        self.controller.log_websocket.register_log(log)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        for switch in self.controller.switches.values():
            self._update_flow_list(switch)

    def _update_flow_list(self, switch):
        """Requests ofp_stats of the flow type"""
        body = FlowStatsRequest()  # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_FLOW, body=body)
        req.pack()
        event = KycoEvent(
            name='kytos/of.core.messages.out.ofpt_stats_request',
            content={'message': req, 'destination': switch.connection})
        self.controller.buffers.msg_out.put(event)

    @listen_to('kytos/of.core.messages.in.ofpt_stats_reply')
    def handle_flow_stats_reply(self, event):
        """Handles FlowStatsReply and updates the switch list with its
        flowstats"""
        msg = event.content['message']
        if msg.body_type == StatsTypes.OFPST_FLOW:
            switch = event.source.switch
            flows = []
            for flow_stat in msg.body:
                new_flow = Flow.from_flow_stats(flow_stat)
                flows.append(new_flow)
            switch.flows = flows

    @listen_to('kytos/of.core.messages.in.ofpt_features_reply')
    def handle_features_reply(self, event):
        """Handle received FeaturesReply event.

        Reads the FeaturesReply Event sent by the client, save this data and
        sends three new messages to the client:

            * SetConfig Message;
            * FlowMod Message with a FlowDelete command;
            * BarrierRequest Message;

        This is the end of the Handshake workflow of the OpenFlow Protocol.

        Args:
            event (KycoMessageInFeaturesReply):
        """
        log.debug('Handling KycoMessageInFeaturesReply Event')

        features = event.content['message']
        dpid = features.datapath_id.value

        switch = self.controller.get_switch_or_create(dpid=dpid,
                                                      connection=event.source)

        for port in features.ports:
            interface = Interface(name=port.name.value,
                                  address=port.hw_addr.value,
                                  port_number=port.port_no.value,
                                  switch=switch,
                                  state=port.state.value,
                                  features=port.curr)
            switch.update_interface(interface)

        switch.update_features(features)

    @listen_to('kyco/core.messages.openflow.new')
    def handle_new_openflow_message(self, event):
        """Handle a RawEvent and generate a KycoMessageIn event.

        Args:
            event (KycoRawOpenFlowMessage): RawOpenFlowMessage to be unpacked
        """
        log.debug('RawOpenFlowMessage received by RawOFMessage handler')

        # creates an empty OpenFlow Message based on the message_type defined
        # on the unpacked header.
        # TODO: Deal with openFlow version prior to message instantiation
        message = new_message_from_header(event.content['header'])
        binary_data = event.content['binary_data']

        # The unpack will happen only to those messages with body beyond header
        if binary_data and len(binary_data) > 0:
            message.unpack(binary_data)
        log.debug('RawOpenFlowMessage unpacked')

        name = message.header.message_type.name.lower()
        of_event = KycoEvent(name="kytos/of.core.messages.in.{}".format(name),
                             content={'message': message,
                                      'source': event.source})
        self.controller.buffers.msg_in.put(of_event)

    @listen_to('kytos/of.core.messages.in.ofpt_echo_request')
    def handle_echo_request(self, event):
        """Handle EchoRequest Event by Generating an EchoReply Answer

        Args:
            event (KycoMessageInEchoRequest): Received Event
        """
        log.debug("Echo Request message read")

        echo_request = event.content['message']
        echo_reply = EchoReply(xid=echo_request.header.xid)
        event_out = KycoEvent(name=('kytos/of.core.messages.out.'
                                    'ofpt_echo_reply'),
                              content={'message': echo_reply,
                                       'destination': event.source})
        self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/of.core.messages.in.ofpt_hello')
    def handle_openflow_in_hello(self, event):
        """Handle a Hello MessageIn Event and sends a Hello to the client.

        Args:
            event (KycoMessageInHello): KycoMessageInHelloEvent
        """
        log.debug('Handling kytos/of.core.messages.ofpt_hello')

        # TODO: Evaluate the OpenFlow version that will be used...
        hello = Hello(xid=event.content['message'].header.xid)
        event_out = KycoEvent(name='kytos/of.core.messages.out.ofpt_hello',
                              content={'message': hello,
                                       'destination': event.source})
        self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/of.core.messages.out.ofpt_hello',
               'kytos/of.core.messages.out.ofpt_echo_reply')
    def send_features_request(self, event):
        """Send a FeaturesRequest to the switch after a Hello Message.

        We consider here that the Hello is sent just during the Handshake
        processes, which means that, at this point, we do not have the switch
        `dpid`, just the `connection`.

        Args:
            event (KycoMessageOutHello): KycoMessageOutHello
        """
        log.debug('Sending a FeaturesRequest after responding to a Hello')

        event_out = KycoEvent(name=('kytos/of.core.messages.out.'
                                    'ofpt_features_request'),
                              content={'message': FeaturesRequest(),
                                       'destination': event.destination})
        self.controller.buffers.msg_out.put(event_out)

    def shutdown(self):
        log.debug('Shutting down...')
