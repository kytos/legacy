"""NApp responsible for the main OpenFlow basic operations."""
from kytos.core import KytosEvent, KytosNApp, log
from kytos.core.connection import ConnectionState
from kytos.core.helpers import listen_to
from pyof.foundation.exceptions import UnpackException
from pyof.utils import unpack, PYOF_VERSION_LIBS

import pyof.v0x01.asynchronous.error_msg
import pyof.v0x01.common.header
import pyof.v0x01.common.utils
import pyof.v0x01.controller2switch.common
import pyof.v0x01.controller2switch.features_request
import pyof.v0x01.controller2switch.stats_request
import pyof.v0x01.symmetric.echo_reply
from pyof.v0x01.symmetric.hello import Hello as HelloV0x01

import pyof.v0x04.asynchronous.error_msg
import pyof.v0x04.common.header
import pyof.v0x04.common.utils
import pyof.v0x04.controller2switch.common
import pyof.v0x04.controller2switch.features_request
import pyof.v0x04.symmetric.echo_reply
from pyof.v0x04.controller2switch.common import MultipartTypes
from pyof.v0x04.symmetric.hello import Hello as HelloV0x04

from napps.kytos.of_core.v0x01 import utils as of_core_v0x01_utils
from napps.kytos.of_core.v0x04 import utils as of_core_v0x04_utils

from napps.kytos.of_core import settings
from napps.kytos.of_core.flow import Flow
from napps.kytos.of_core.utils import (emit_message_in, emit_message_out,
                                       GenericHello, NegotiationException,
                                       of_slicer)


class Main(KytosNApp):
    """Main class of the NApp responsible for OpenFlow basic operations."""

    def setup(self):
        """App initialization (used instead of ``__init__``).

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        self.name = 'kytos/of_core'
        self.of_core_version_utils = {0x01: of_core_v0x01_utils,
                                      0x04: of_core_v0x04_utils}
        self.execute_as_loop(settings.STATS_INTERVAL)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KytosNApp class.
        Users shouldn't call this method directly.
        """
        for switch in self.controller.switches.values():
            if switch.is_connected():
                version_utils = \
                    self.of_core_version_utils[switch.
                                               connection.protocol.version]
                version_utils.update_flow_list(self.controller, switch)
                if settings.SEND_ECHO_REQUESTS:
                    version_utils.send_echo(self.controller, switch)


    @staticmethod
    @listen_to('kytos/of_core.v0x01.messages.in.ofpt_stats_reply')
    def handle_flow_stats_reply(event):
        """Handle flow stats reply message.

        This method updates the switches list with its Flow Stats.

        Args:
            event (:class:`~kytos.core.events.KytosEvent):
                Event with ofpt_stats_reply in message.
        """
        msg = event.content['message']
        if msg.body_type == \
                pyof.v0x01.controller2switch.common.StatsTypes.OFPST_FLOW:
            switch = event.source.switch
            flows = []
            for flow_stat in msg.body:
                new_flow = Flow.from_flow_stats(flow_stat)
                flows.append(new_flow)
            switch.flows = flows

    @listen_to('kytos/of_core.v0x0[14].messages.in.ofpt_features_reply')
    def handle_features_reply(self, event):
        """Handle kytos/of_core.messages.in.ofpt_features_reply event.

        This is the end of the Handshake workflow of the OpenFlow Protocol.

        Args:
            event (KytosEvent): Event with features reply message.
        """
        connection = event.source
        version_utils = self.of_core_version_utils[connection.protocol.version]
        switch = version_utils.handle_features_reply(self.controller, event)

        if (connection.is_during_setup() and
                connection.protocol.state == 'waiting_features_reply'):
            connection.protocol.state = 'handshake_complete'
            connection.set_established_state()
            if settings.SEND_SET_CONFIG:
                version_utils.send_set_config(self.controller, switch)
            log.info('Connection %s, Switch %s: OPENFLOW HANDSHAKE COMPLETE',
                     connection.id, switch.dpid)
            # # event to be generated in near future
            # event_raw = KytosEvent(name='kytos/of_core.handshake_complete',
            #                        content={'source': connection})
            # self.controller.buffers.app.put(event_raw)

    @listen_to('kytos/of_core.v0x04.messages.in.ofpt_multipart_reply')
    def handle_port_desc_reply(self, event):
        """Handles Port Description Reply messages."""
        switch = event.source.switch
        reply = event.content['message']
        if reply.multipart_type == MultipartTypes.OFPMP_PORT_DESC:
            of_core_v0x04_utils.handle_port_desc(switch, reply.body)

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

        data = connection.remaining_data + event.content['new_data']
        packets, connection.remaining_data = of_slicer(data)
        if not packets:
            return

        unprocessed_packets = []

        for packet in packets:
            if not connection.is_alive():
                return
            log.debug('Connection %s: New Raw Openflow packet - %s',
                      connection.id, packet.hex())

            if connection.is_new():
                try:
                    message = GenericHello(packet=packet)
                    self._negotiate(connection, message)
                except (UnpackException, NegotiationException) as e:
                    if type(e) == UnpackException:
                        log.debug('Connection %s: Invalid hello message',
                                  connection.id)
                    else:
                        log.debug('Connection %s: Negotiation Failed',
                                  connection.id)
                    connection.protocol.state = 'hello_failed'
                    connection.close()
                    connection.state = ConnectionState.FAILED
                    return
                connection.set_setup_state()
                continue

            try:
                message = connection.protocol.unpack(packet)
            except (UnpackException, AttributeError) as e:
                log.debug(e)
                if type(e) == AttributeError:
                    debug_msg = 'connection closed before version negotiation'
                    log.debug('Connection %s: %s' , connection.id, debug_msg)
                connection.close()
                return

            log.debug('Connection %s: IN OFP, version: %s, type: %s, xid: %s',
                      connection.id,
                      message.header.version,
                      message.header.message_type,
                      message.header.xid)

            if connection.is_during_setup():
                if not (str(message.header.message_type) ==
                        'Type.OFPT_FEATURES_REPLY' and
                        connection.protocol.state == 'waiting_features_reply'):
                    unprocessed_packets.append(packet)
                    continue

            self.emit_message_in(connection, message)

        connection.remaining_data = b''.join(unprocessed_packets) + \
                                    connection.remaining_data

    def emit_message_in(self, connection, message):
        """Emit a KytosEvent for an incoming message containing the message
        and the source."""
        if connection.is_alive():
            emit_message_in(self.controller, connection, message)

    def emit_message_out(self, connection, message):
        """Emit a KytosEvent for an outgoing message containing the message
        and the destination."""
        if connection.is_alive():
            emit_message_out(self.controller, connection, message)

    @listen_to('kytos/of_core.v0x0[14].messages.in.ofpt_echo_request')
    def handle_echo_request(self, event):
        """Handle Echo Request Messages.

        This method will get a echo request sent by client and generate a
        echo reply as answer.

        Args:
            event (:class:`~kytos.core.events.KytosEvent`):
                Event with echo request in message.
        """

        pyof_lib = PYOF_VERSION_LIBS[event.source.protocol.version]
        echo_request = event.message
        echo_reply = pyof_lib.symmetric.echo_reply.EchoReply(
            xid=echo_request.header.xid,
            data=echo_request.data)
        self.emit_message_out(event.source, echo_reply)


    def _get_version_from_bitmask(self, message_versions):
        """Get common version from hello message version bitmap."""
        try:
            return max([version for version in message_versions
                        if version in settings.OPENFLOW_VERSIONS])
        except ValueError:
            return None

    def _get_version_from_header(self, message_version):
        """Get common version from hello message header version."""
        version = min(message_version, max(settings.OPENFLOW_VERSIONS))
        return version if version in settings.OPENFLOW_VERSIONS else None

    def _negotiate(self, connection, message):
        """Handle hello messages.

        This method will handle the incoming hello message by client
        and deal with negotiation.

        Parameters:
            event (KytosMessageInHello): KytosMessageInHelloEvent
        """

        if message.versions:
            version = self._get_version_from_bitmask(message.versions)
        else:
            version = self._get_version_from_header(message.header.version)

        log.debug('connection %s: negotiated version - %s',
                  connection.id, str(version))

        if version is None:
            self.fail_negotiation(connection, message)
            raise NegotiationException()

        version_utils = self.of_core_version_utils[version]
        version_utils.say_hello(self.controller, connection)

        connection.protocol.name = 'openflow'
        connection.protocol.version = version
        connection.protocol.unpack = unpack
        connection.protocol.state = 'sending_features'
        self.send_features_request(connection)
        log.debug('Connection %s: Hello complete', connection.id)

    def fail_negotiation(self, connection, hello_message):
        """Send Error message and emit event upon negotiation failure."""
        log.warning('connection %s: version negotiation failed',
                    connection.id)
        connection.protocol.state = 'hello_failed'
        event_raw = KytosEvent(
            name='kytos/of_core.hello_failed',
            content={'source': connection})
        self.controller.buffers.app.put(event_raw)

        version = max(settings.OPENFLOW_VERSIONS)
        pyof_lib = PYOF_VERSION_LIBS[version]

        error_message = pyof_lib.asynchronous.error_msg.ErrorMsg(
            xid=hello_message.header.xid,
            error_type=pyof_lib.asynchronous.error_msg.
            ErrorType.OFPET_HELLO_FAILED,
            code=pyof_lib.asynchronous.error_msg.HelloFailedCode.
            OFPHFC_INCOMPATIBLE)
        self.emit_message_out(connection, error_message)

    # May be removed
    @listen_to('kytos/of_core.v0x0[14].messages.out.ofpt_echo_reply')
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
        version = destination.protocol.version
        pyof_lib = PYOF_VERSION_LIBS[version]
        features_request = pyof_lib.controller2switch.\
            features_request.FeaturesRequest()
        self.emit_message_out(destination, features_request)

    @listen_to('kytos/of_core.v0x0[14].messages.out.ofpt_features_request')
    def handle_features_request_sent(self, event):
        """Ensure request has actually been sent before changing state."""
        if event.destination.protocol.state == 'sending_features':
            event.destination.protocol.state = 'waiting_features_reply'

    @staticmethod
    @listen_to('kytos/of_core.v0x[0-9a-f]{2}.messages.in.hello_failed',
               'kytos/of_core.v0x0[14].messages.out.hello_failed')
    def handle_openflow_in_hello_failed(event):
        """Close the connection upon hello failure."""
        event.destination.close()
        log.debug("Connection %s: Connection closed.", event.destination.id)

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')
