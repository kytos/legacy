"""This App is the responsible to install a drop ipv6 flow on switch setup."""

import hashlib
import json
import logging

from flask import Flask, request
from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp
from kyco.utils import listen_to
from pyof.v0x01.common.action import ActionOutput
from pyof.v0x01.common.flow_match import Match
from pyof.v0x01.controller2switch.common import StatsTypes
from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.controller2switch.stats_request import StatsRequest

STATS_INTERVAL = 30
log = logging.getLogger('flow_manager')


class Main(KycoCoreNApp):
    """Main class of KycoCoreNApp, responsible for the main OpenFlow basic
    operations.

    """

    def setup(self):
        """'Replaces' the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly."""
        flow_manager = FlowManager(self.controller)
        self.server = APIServer(port=5000, flow_manager=flow_manager)
        self._stopper = Event()

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        self.server.start()
        while not self._stopper.is_set():
            for switch in self.controller.switches.values():
                self.flow_manager.dump_flows()
            self._stopper.wait(STATS_INTERVAL)
        log.debug('Thread finished.')

    def shutdown(self):
        self.server.stop()


class FlowManager(object):
    """This class is responsible for manipulating flows at the switches"""
    def __init__(self, controller):
        self.controller = controller
        self.flows = []

    def install_new_flow(self, flow, dpid):
        """
        This method is responsible for creating a new flow_mod message from
        the Flow object received
        """
        switch = self.controller.get_switch_by_dpid(dpid)
        flow_mod = flow.as_flow_mod(FlowModCommand.OFPFC_ADD)

        event_out = KycoEvent(name=('kytos/of.flow-manager.messages.out.'
                                    'ofpt_flow_mod'),
                              content={'destination': switch.connection,
                                       'message': flow_mod})
        self.controller.buffers.msg_out.put(event_out)

    def dump_flows(self, dpid):
        """Rettrieves the list of flows installed in the Switch identified by
        dpid"""
        switch = self.controller.get_switch_by_dpid(dpid)
        stats_request = StatsRequest()
        stats_request.body_type = StatsTypes.OFPST_FLOW
        stats_request.match = Match()
        event_out = KycoEvent(name=('kytos/of.flow-manager.messages.out.'
                                    'ofpt_stats_request'),
                              content={'destination': switch.connection,
                                       'message': stats_request})
        self.controller.buffers.msg_out.put(event_out)

    def clear_flows(self, dpid):
        """Clear all flows from switch identified by dpid"""
        switch = self.controller.get_switch_by_dpid(dpid)
        for flow in self.flows:
            flow_mod = flow.as_flow_mod(FlowModCommand.OFPFC_DELETE)
            event_out = KycoEvent(name=('kytos/of.flow-manager.messages.out.'
                                        'ofpt_flow_mod'),
                                  content={'destination': switch.connection,
                                           'message': flow_mod})
            self.controller.buffers.msg_out.put(event_out)

    def delete_flow(self, dpid, flow_id):
        """Removes the flow identified by id from the switch identified by
        dpid"""
        switch = self.controller.get_switch_by_dpid(dpid)
        for flow in self.flows:
            if flow.id == flow_id:
                flow_mod = flow.as_flow_mod(FlowModCommand.OFPFC_DELETE)
                content = {'destination': switch.connection,
                           'message': flow_mod}
                event_out = KycoEvent(name=('kytos/of.flow-manager.'
                                            'messages.out.ofpt_flow_mod'),
                                      content=content)
                self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/of.core.messages.in.ofpt_stats_reply')
    def handle_flow_stats_reply(self, event):
        """Handle Flow Stats messages"""
        msg = event.content['message']
        if msg.body_type.value is StatsTypes.OFPST_FLOW:
            flow_stats = msg.body
            flows = self._get_flows(flow_stats)
            self.flows = flows

    def _get_flows(self, flow_stats):
        """
        Creates a list of flows from the body of a flow_stats_reply
        message
        """
        flows = []
        for flow_stat in flow_stats:
            flows.append(Flow.from_flow_stats(flow_stat))

        return flows


class Flow(object):
    """
    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """
    def __init__(self, idle_timeout=0, hard_timeout=0, priority=0,
                 buffer_id=0xff, in_port=None, dl_src=None, dl_dst=None,
                 dl_vlan=None, dl_type=None, nw_proto=None, nw_src=None,
                 nw_dst=None, tp_src=None, tp_dst=None, actions=None):
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout
        self.priority = priority
        self.buffer_id = buffer_id
        self.in_port = in_port
        self.dl_src = dl_src
        self.dl_dst = dl_dst
        self.dl_vlan = dl_vlan
        self.dl_type = dl_type
        self.nw_proto = nw_proto
        self.nw_src = nw_src
        self.nw_dst = nw_dst
        self.tp_src = tp_src
        self.tp_dst = tp_dst
        self.actions = actions

    @property
    def id(self):
        """Returns the hash of the object"""
        return hash(self)

    def __hash__(self):
        """
        Calculates the hash of the object by using the hashlib we use md5 of
        strings.
        """
        hash_result = hashlib.md5()
        hash_result.update(str(self.idle_timeout).encode('utf-8'))
        hash_result.update(str(self.hard_timeout).encode('utf-8'))
        hash_result.update(str(self.priority).encode('utf-8'))
        hash_result.update(str(self.in_port).encode('utf-8'))
        hash_result.update(str(self.dl_src).encode('utf-8'))
        hash_result.update(str(self.dl_dst).encode('utf-8'))
        hash_result.update(str(self.dl_vlan).encode('utf-8'))
        hash_result.update(str(self.dl_type).encode('utf-8'))
        hash_result.update(str(self.nw_proto).encode('utf-8'))
        hash_result.update(str(self.nw_src).encode('utf-8'))
        hash_result.update(str(self.nw_dst).encode('utf-8'))
        hash_result.update(str(self.tp_src).encode('utf-8'))
        hash_result.update(str(self.tp_dst).encode('utf-8'))
        for action in self.actions:
            hash_result.update(str(hash(action)).encode('utf-8'))

        return hash_result.hexdigest()

    def as_json(self):
        """Returns the representation of a flow in a json format"""
        dictionary_rep = {"flow": {"self.id": self.id,
                                   "idle_timeout": self.idle_timeout,
                                   "hard_timeout": self.hard_timeout,
                                   "priority": self.priority,
                                   "in_port": self.in_port,
                                   "dl_src": self.dl_src,
                                   "dl_dst": self.dl_dst,
                                   "dl_vlan": self.dl_vlan,
                                   "dl_type": self.dl_type,
                                   "nw_src": self.nw_src,
                                   "nw_dst": self.nw_dst,
                                   "tp_src": self.tp_src,
                                   "tp_dst": self.tp_dst,
                                   "actions": self.actions}}

        actions = []
        for action in self.actions:
            actions.append(action.as_dict())

        dictionary_rep[self.id][actions] = actions

        return json.dumps(dictionary_rep)

    @staticmethod
    def from_json(json_content):
        """Builds a Flow object from a json"""
        dict_content = json.loads(json_content)
        return Flow.from_dict(dict_content)

    @staticmethod
    def from_dict(dict_content):
        """Builds a Flow object from a json"""
        flow_fields = dict_content['flow']
        flow = Flow()
        flow.idle_timeout = flow_fields['idle_timeout']
        flow.hard_timeout = flow_fields['hard_timeout']
        flow.priority = flow_fields['priority']
        flow.in_port = flow_fields['in_port']
        flow.dl_src = flow_fields['dl_src']
        flow.dl_dst = flow_fields['dl_dst']
        flow.dl_vlan = flow_fields['dl_vlan']
        flow.dl_type = flow_fields['dl_type']
        flow.nw_src = flow_fields['nw_src']
        flow.nw_dst = flow_fields['nw_dst']
        flow.tp_src = flow_fields['tp_src']
        flow.tp_dst = flow_fields['tp_dst']

        actions = []
        for dict_action in dict_content['actions']:
            action = OutputAction.from_dict(dict_action)  # Only Output
            actions.append(action)

        flow.actions = actions

    @staticmethod
    def from_flow_stats(flow_stats):
        """Builds a new Flow Object from a stats_reply """
        flow = Flow()
        flow.idle_timeout = flow_stats.idle_timeout
        flow.hard_timeout = flow_stats.hard_timeout
        flow.in_port = flow_stats.match.in_port
        flow.dl_src = flow_stats.match.dl_src
        flow.dl_dst = flow_stats.match.dl_dst
        flow.dl_vlan = flow_stats.match.dl_vlan
        flow.dl_type = flow_stats.match.dl_type
        flow.nw_src = flow_stats.match.nw_src
        flow.nw_dst = flow_stats.match.nw_dst
        flow.tp_src = flow_stats.match.tp_src
        flow.tp_dst = flow_stats.match.tp_dst
        return flow

    def as_flow_mod(self, flow_type):
        """Transform a Flow object into a flow_mod message"""
        flow_mod = FlowMod()
        flow_mod.command = flow_type
        flow_mod.buffer_id = self.buffer_id
        flow_mod.idle_timeout = self.idle_timeout
        flow_mod.hard_timeout = self.hard_timeout
        flow_mod.priority = self.priority
        flow_mod.match = Match()
        flow_mod.match.in_port = self.in_port
        flow_mod.match.dl_src = self.dl_src
        flow_mod.match.dl_dst = self.dl_dst
        flow_mod.match.dl_vlan = self.dl_vlan
        flow_mod.match.dl_type = self.dl_type
        flow_mod.match.nw_src = self.nw_src
        flow_mod.match.nw_dst = self.nw_dst
        flow_mod.match.tp_src = self.tp_src
        flow_mod.match.tp_dst = self.tp_dst
        flow_mod.match.fill_wildcards()
        for action in self.actions:
            flow_mod.actions.append(action.as_of_action())

        return flow_mod


class FlowAction(object):
    """The instances of this class represent action to be executed once a flow
    is activated"""

    @staticmethod
    def from_dict(dict_content):
        """Builds one of the FlowActions from a dictionary"""
        pass


class OutputAction(FlowAction):
    """This class represents the action of forwarding network packets into a
    given port"""
    def __init__(self, output_port):
        self.output_port = output_port

    def as_of_action(self):
        """Builds a Action Output from this action"""
        return ActionOutput(port=self.output_port)

    def as_dict(self):
        """Returns this action as a dict"""
        return {"type": "action_output",
                "port": self.output_port}

    @staticmethod
    def from_dict(dict_content):
        """Builds an Output Action from a dictionary"""
        return OutputAction(output_port=dict_content['port'])

    def __hash__(self):
        """Returns the (unambiguous) representation of the Object"""
        hash_result = hashlib.md5()
        hash_result.update("OutputAction(output_port={})".encode('utf-8'))
        return hash_result.hexdigest()


class DLChangeAction(FlowAction):
    """This action represents the change in the packet hw source/destination
    address"""
    def __init__(self, dl_src=None, dl_dst=None):
        self.dl_src = dl_src
        self.dl_dst = dl_dst


class NWChangeAction(FlowAction):
    """This action represents the change in the packet ip source/destination
    address"""
    def __init__(self, nw_src, nw_dst):
        self.nw_src = nw_src
        self.nw_dst = nw_dst


class APIServer(object):
    """This class is responsible for starting the REST api server and listening
    for requests"""

    app = Flask(__name__)

    def __init__(self, port=5000, flow_manager=None):
        self.port = port
        self.flow_manager = flow_manager

    def start(self, debug=True):
        """This method is responsible for starting a flask server at the given
        port"""
        APIServer.app.run(debug=debug)

    def stop(self):
        """This method is reponsible for stoping the flask server"""
        server_shutdown = request.environ.get('werkzeug.server.shutdown')
        if server_shutdown is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        server_shutdown()

    @app.route('/<dpid>/flows', methods=['GET'])
    @app.route('/flows', methods=['GET'])
    def retrieve_flows(self, dpid=None):
        """docstring for retrieve_flows"""

    @app.route('/<dpid>/flows', methods=['POST'])
    def insert_flow(self, dpid=None):
        """docstring for  create_flow"""
        json_content = request.get_json()
        received_flow = Flow.from_json(json_content)
        self.flow_manager.install_new_flow(received_flow, dpid)
