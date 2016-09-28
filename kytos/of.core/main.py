"""This App is the responsible for the main OpenFlow basic operations."""

import logging
from random import randint

from pyof.v0x01.controller2switch import flow_mod
from pyof.v0x01.controller2switch.common import ListOfActions
from pyof.v0x01.common import header as of_header
from pyof.v0x01.common import action
from pyof.v0x01.common import flow_match
from pyof.v0x01.common import phy_port


from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.common.header import Type
from pyof.v0x01.common.utils import new_message_from_header
from pyof.v0x01.controller2switch.barrier_request import BarrierRequest
from pyof.v0x01.controller2switch.common import ConfigFlags
from pyof.v0x01.controller2switch.features_request import FeaturesRequest
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.controller2switch.set_config import SetConfig
from pyof.v0x01.symmetric.echo_reply import EchoReply
from pyof.v0x01.symmetric.hello import Hello

#from kyco.core.events import (KycoMessageIn, KycoMessageInEchoRequest,
#                              KycoMessageInFeaturesReply, KycoMessageInHello,
#                              KycoMessageOutBarrierRequest,
#                              KycoMessageOutEchoReply,
#                              KycoMessageOutFeaturesRequest,
#                              KycoMessageOutHello, KycoMessageOutSetConfig,
#                             KycoSwitchUp)

from kyco.core.events import KycoEvent

from kyco.core.switch import KycoSwitch
from kyco.utils import KycoCoreNApp, listen_to

log = logging.getLogger('Kyco')


class Main(KycoCoreNApp):
    """Main class of KycoCoreNApp, responsible for the main OpenFlow basic
    operations.

    """

    def setup(self):
        """'Replaces' the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly."""
        # TODO: App information goes to app_name.json
        self.name = 'core.openflow'

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        pass

#    @listen_to('KycoMessageInFeaturesReply')
#    def features_reply_in(self, event):
#        """Handle received FeaturesReply event.
#
#        Reads the FeaturesReply Event sent by the client, save this data and
#        sends three new messages to the client:
#
#            * SetConfig Message;
#            * FlowMod Message with a FlowDelete command;
#            * BarrierRequest Message;
#
#        This is the end of the Handshake workflow of the OpenFlow Protocol.
#
#        Args:
#            event (KycoMessageInFeaturesReply):
#        """
#        log.debug('Handling KycoMessageInFeaturesReply Event')
#
#        # Processing the FeaturesReply Message
#        message = event.content['message']
#        if event.dpid is not None:
#            # In this case, the switch has already been instantiated and this
#            # is just a update of switch features.
#            self.controller.switches[event.dpid].features = message
#        else:
#            # This is the first features_reply for the switch, which means
#            # that we are on the Handshake process and so we need to create a
#            # new switch as save it on the controller.
#            connection = self.controller.connections[event.connection_id]
#            # TODO: Should an App be able to 'create' a new switch object?
#            switch = KycoSwitch(dpid=str(message.datapath_id),
#                                socket=connection['socket'],
#                                connection_id=event.connection_id,
#                                ofp_version=message.header.version,
#                                features=message)
#            self.controller.add_new_switch(switch)
#
#        # TODO: Should an App be able to 'create' a new switch object?
#        new_event = KycoSwitchUp(dpid=switch.dpid, content={})
#        self.controller.buffers.app.put(new_event)
#
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
                                      'destination': event.source})
        self.controller.buffers.msg_in.put(of_event)

#        # Now we create a new MessageInEvent based on the message_type
#        if message.header.message_type == Type.OFPT_HELLO:
#            new_event = KycoMessageInHello(content=content)
#        elif message.header.message_type == Type.OFPT_FEATURES_REPLY:
#            new_event = KycoMessageInFeaturesReply(content=content)
#        elif message.header.message_type == Type.OFPT_ECHO_REQUEST:
#            new_event = KycoMessageInEchoRequest(content=content)
#        elif message.header.message_type == Type.OFPT_PACKET_IN:
#            new_event = KycoPacketIn(content=content)
#        else:
#            new_event = KycoMessageIn(content=content)

    @listen_to('kytos/of.core.messages.in.ofpt_echo_request')
    def handle_echo_request(self, event):
        """Handle EchoRequest Event by Generating an EchoReply Answer

        Args:
            event (KycoMessageInEchoRequest): Received Event
        """
        log.debug("Echo Request message read")

        echo_request = event.content['message']
        echo_reply = EchoReply(xid=echo_request.header.xid)
        event_out = KycoEvent(name='kytos/of.core.messages.out.ofpt_echo_reply',
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


#    def send_barrier_request(self, dpid):
#        """Send a BarrierRequest Message to the client"""
#        content = {'message': BarrierRequest()}
#        event_out = KycoMessageOutBarrierRequest(dpid, content)
#        self.controller.buffers.msg_out.put(event_out)
#
    @listen_to('kytos/of.core.messages.out.ofpt_hello')
    def send_features_request(self, event):
        """Send a FeaturesRequest to the switch after a Hello Message.

        We consider here that the Hello is sent just during the Handshake
        processes, which means that, at this point, we do not have the switch
        `dpid`, just the `connection`.

        Args:
            event (KycoMessageOutHello): KycoMessageOutHello
        """
        log.debug('Sending a FeaturesRequest after responding to a Hello')

        event_out = KycoEvent(name='kytos/of.core.messages.out.ofpt_features_request',
                              content={'message': FeaturesRequest(),
                                       'destination': event.source})
        self.controller.buffers.msg_out.put(event_out)
#
#    def send_flow_delete(self, dpid):
#        """Sends a FlowMod message with FlowDelete command"""
#        # Sending a 'FlowDelete' (FlowMod) message to the client
#        message_out = FlowMod(xid=randint(1, 100), match=Match(),
#                              command=FlowModCommand.OFPFC_DELETE,
#                              priority=12345, out_port=65535, flags=0)
#        # TODO: The match attribute need to be fulfilled
#        # TODO: How to decide the priority
#        # TODO: How to decide the out_port
#        # TODO: How to decide the flags
#        content = {'message': message_out}
#        features_request_out = KycoMessageOutFeaturesRequest(dpid, content)
#        self.controller.buffers.msg_out.put(features_request_out)
#
#    def send_switch_config(self, dpid):
#        """Sends a SwitchConfig message to the client"""
#        # Sending a SetConfig message to the client.
#        message_out = SetConfig(xid=randint(1, 65000),
#                                flags=ConfigFlags.OFPC_FRAG_NORMAL,
#                                miss_send_len=128)
#        # TODO: Define the miss_send_len value
#        content = {'message': message_out}
#        event_out = KycoMessageOutSetConfig(dpid, content)
#        self.controller.buffers.msg_out.put(event_out)
#
    def shutdown(self):
        pass
