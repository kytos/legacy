"""NApp responsible for the main OpenFlow basic operations."""
from kytos.core import KytosEvent, KytosNApp, log
from kytos.core.connection import CONNECTION_STATE
from kytos.core.flow import Flow
from kytos.core.helpers import listen_to
from kytos.core.switch import Interface
from pyof.foundation.exceptions import UnpackException
from pyof.v0x01.asynchronous.error_msg import (ErrorMsg, ErrorType,
                                               HelloFailedCode)
from pyof.v0x01.common.header import Type as OFPTYPE
from pyof.v0x01.controller2switch.common import FlowStatsRequest
from pyof.v0x01.controller2switch.features_request import FeaturesRequest
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes
from pyof.v0x01.symmetric.echo_reply import EchoReply
from pyof.v0x01.symmetric.hello import Hello

from napps.kytos.of_core import settings
from napps.kytos.of_core.utils import unpack, of_slicer


class Main(KytosNApp):
    """Main class of the NApp responsible for OpenFlow basic operations."""

    def setup(self):
        """App initialization (used instead of ``__init__``).

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        self.name = 'kytos/of_core'
        self.versions = [0x01]
        self.execute_as_loop(settings.STATS_INTERVAL)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KytosNApp class.
        Users shouldn't call this method directly.
        """
        for switch in self.controller.switches.values():
            if switch.is_connected():
                self._update_flow_list(switch)

    def _update_flow_list(self, switch):
        """Method responsible for request stats of flow to switches.

        Args:
            switch(:class:`~kytos.core.switch.Switch`):
                target to send a stats request.
        """
        body = FlowStatsRequest()  # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_FLOW, body=body)
        req.pack()
        event = KytosEvent(
            name='kytos/of_core.messages.out.ofpt_stats_request',
            content={'message': req, 'destination': switch.connection})
        self.controller.buffers.msg_out.put(event)

    @staticmethod
    @listen_to('kytos/of_core.messages.in.ofpt_stats_reply')
    def handle_flow_stats_reply(event):
        """Handle flow stats reply message.

        This method updates the switches list with its Flow Stats.

        Args:
            event (:class:`~kytos.core.events.KytosEvent):
                Event with ofpt_stats_reply in message.
        """
        msg = event.content['message']
        if msg.body_type == StatsTypes.OFPST_FLOW:
            switch = event.source.switch
            flows = []
            for flow_stat in msg.body:
                new_flow = Flow.from_flow_stats(flow_stat)
                flows.append(new_flow)
            switch.flows = flows

    @listen_to('kytos/of_core.messages.in.ofpt_features_reply')
    def handle_features_reply(self, event):
        """Handle received kytos/of_core.messages.in.ofpt_features_reply event.

        Reads the KytosEvent with features reply message sent by the client,
        save this data and sends three new messages to the client:

            * SetConfig Message;
            * FlowMod Message with a FlowDelete command;
            * BarrierRequest Message;

        This is the end of the Handshake workflow of the OpenFlow Protocol.

        Args:
            event (KytosEvent): Event with features reply message.
        """

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

        if (event.source.state == CONNECTION_STATE.SETUP and
                event.source.protocol.state == 'waiting_features_reply'):
            event.source.protocol.state = 'handshake_complete'
            event.source.state = CONNECTION_STATE.ESTABLISHED
            log.info('Connection %s: OPENFLOW HANDSHAKE COMPLETE',
                     event.source.id)
            # # event to be generated in near future
            # event_raw = KytosEvent(name='kytos/of_core.handshake_complete',
            #                        content={'source': event.source})
            # self.controller.buffers.app.put(event_raw)

    @listen_to('kytos/core.openflow.raw.in')
    def handle_raw_in(self, event):
        """Handle a RawEvent and generate a kytos/core.messages.in.* event.

        Args:
            event (KytosEvent): RawEvent with openflow message to be unpacked
        """

        # If the switch is already known to the controller, update the
        # 'lastseen' attribute
        switch = event.source.switch
        if switch:
            switch.update_lastseen()

        connection = event.source
        if connection.state in (CONNECTION_STATE.FINISHED,
                                CONNECTION_STATE.FAILED):
            return

        data = connection.remaining_data + event.content['new_data']
        packets, connection.remaining_data = of_slicer(data)
        if not packets:
            return

        unprocessed_packets = []

        for packet in packets:
            log.debug('Connection %s: New Raw Openflow packet', connection.id)
            log.debug(packet.hex())

            try:
                message = unpack(packet)
            except UnpackException:
                connection.state = CONNECTION_STATE.FINISHED
                connection.close()
                return
            m_type = message.header.message_type

            log.debug('Connection %s: IN OFP, version: %s, type: %s, xid: %s',
                      connection.id,
                      message.header.version, m_type, message.header.xid)

            if connection.state == CONNECTION_STATE.NEW:
                if m_type != OFPTYPE.OFPT_HELLO:
                    log.debug('Connection %s: Invalid OF Hello message',
                              connection.id)
                    connection.protocol.state = 'hello_invalid'
                    connection.state = CONNECTION_STATE.FINISHED
                    connection.close()
                elif self._negotiate(connection, message):
                    connection.state = CONNECTION_STATE.SETUP
                    continue
                connection.state = CONNECTION_STATE.FAILED
                return

            elif connection.state == CONNECTION_STATE.SETUP:
                if not (m_type == OFPTYPE.OFPT_FEATURES_REPLY and
                        connection.protocol.state == 'waiting_features_reply'):
                    unprocessed_packets.append(packet)
                    continue

            self._emmit_message_in(connection, message)

        connection.remaining_data = b''.join(unprocessed_packets) + \
                                    connection.remaining_data

    def _emmit_message_in(self, connection, message):
        """Emits a KytosEvent for an incomming message containing the message
        and the source."""
        name = message.header.message_type.name.lower()
        of_event = KytosEvent(
            name="kytos/of_core.messages.in.{}".format(name),
            content={'message': message,
                     'source': connection})
        self.controller.buffers.msg_in.put(of_event)

    @listen_to('kytos/of_core.messages.in.ofpt_echo_request')
    def handle_echo_request(self, event):
        """Handle Echo Request Messages.

        This method will get a echo request sent by client and generate a
        echo reply as answer.

        Args:
            event (:class:`~kytos.core.events.KytosEvent`):
                Event with echo request in message.
        """

        echo_request = event.message
        echo_reply = EchoReply(xid=echo_request.header.xid,
                               data=echo_request.data)
        event_out = KytosEvent(
            name='kytos/of_core.messages.out.ofpt_echo_reply',
            content={'message': echo_reply,
                     'destination': event.source})
        self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/core.openflow.connection.new')
    def handle_core_new_connection(self, event):
        """Method called when a new switch is connected.

        This method will send a hello world message when a new switch is
        connected.
        """
        self._say_hello(event.source)

    def _say_hello(self, connection, xid=None):
        """Method used to send a hello messages."""
        # should be called once a new connection is established.
        # To be able to deal with of1.3 negotiation, hello should also
        # cary a version_bitmap.
        hello = Hello(xid=xid)
        event_out = KytosEvent(
            name='kytos/of_core.messages.out.ofpt_hello',
            content={'message': hello,
                     'destination': connection})
        self.controller.buffers.msg_out.put(event_out)

    def _negotiate(self, connection, message):
        """Handle hello messages.

        This method will handle the incomming hello message by client
        and deal with negotiation.

        Args:
            event (KytosMessageInHello): KytosMessageInHelloEvent
        """

        if message.header.version >= min(self.versions):
            connection.protocol.name = 'openflow'
            connection.protocol.version = min(message.header.version,
                                              max(self.versions))
            connection.protocol.state = 'sending_features'
            self.send_features_request(connection)
            log.debug('Connection %s: Hello complete', connection.id)
            return True
        else:
            connection.protocol.state = 'hello_failed'
            event_raw = KytosEvent(
                name='kytos/of_core.hello_failed',
                content={'source': connection})
            self.controller.buffers.app.put(event_raw)

            error_message = ErrorMsg(
                xid=message.header.xid,
                error_type=ErrorType.OFPET_HELLO_FAILED,
                code=HelloFailedCode.OFPHFC_INCOMPATIBLE)

            event_out = KytosEvent(
                name='kytos/of_core.messages.out.hello_failed',
                content={'destination': connection,
                         'message': error_message})

            self.controller.buffers.msg_out.put(event_out)
            return False

    # May be removed
    @listen_to('kytos/of_core.messages.out.ofpt_echo_reply')
    def handle_queued_openflow_echo_reply(self, event):
        """Method used to handle  echo reply messages.

        This method will send a feature request message if the variable
        SEND_FEATURES_REQUEST_ON_ECHO is True.By default this variable is
        False.
        """
        if settings.SEND_FEATURES_REQUEST_ON_ECHO:
            self.send_features_request(event.destination)

    def send_features_request(self, destination):
        """Send a feature request to the switch."""

        event_out = KytosEvent(
            name='kytos/of_core.messages.out.ofpt_features_request',
            content={'message': FeaturesRequest(),
                     'destination': destination})
        self.controller.buffers.msg_out.put(event_out)

    # ensure request has actually been sent before changing state
    @listen_to('kytos/of_core.messages.out.ofpt_features_request')
    def handle_features_request_sent(self, event):
        if event.destination.protocol.state == 'sending_features':
            event.destination.protocol.state = 'waiting_features_reply'

    @staticmethod
    @listen_to('kytos/of_core.messages.in.hello_failed',
               'kytos/of_core.messages.out.hello_failed')
    def handle_openflow_in_hello_failed(event):
        """Method used to close the connection when get a hello failed."""
        event.destination.close()
        log.debug("Connection %s: Connection closed.", event.destination.id)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')
