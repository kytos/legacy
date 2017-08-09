"""NApp responsible for installing or removing flows on the switches."""

import json

from flask import request

from kytos.core import KytosEvent, KytosNApp, log, rest

from pyof.v0x01.controller2switch.flow_mod import FlowModCommand

from napps.kytos.of_core.flow import Flow
from napps.kytos.of_flow_manager import settings


class Main(KytosNApp):
    """Main class of of_stats NApp."""

    def setup(self):
        """Replace the 'init' method for the KytosApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        self.flow_manager = FlowManager(self.controller)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KytosNApp class.
        Users shouldn't call this method directly.
        """
        pass

    def shutdown(self):
        """Shutdown routine of the NApp."""
        log.debug("flow-manager stopping")

    @rest('flows')
    @rest('flows/<dpid>')
    def retrieve_flows(self, dpid=None):
        """Retrieve all flows from a switch identified by dpid.

        If no dpid has been specified, returns the flows from all switches.
        """
        switch_flows = {}

        if dpid:
            target = [dpid]
        else:
            target = self.controller.switches

        for switch_dpid in target:
            switch = self.controller.get_switch_by_dpid(switch_dpid)
            flows = {}
            for flow in switch.flows:
                flow = (flow.as_dict()['flow'])
                flow_id = flow.pop('self.id', 0)
                flows[flow_id] = flow
            switch_flows[switch_dpid] = flows
        return json.dumps(switch_flows)

    @rest('flows', methods=['POST'])
    @rest('flows/<dpid>', methods=['POST'])
    def insert_flows(self, dpid=None):
        """Install new flows in the switch identified by dpid.

        If no dpid has been specified, install flows in all switches.
        """
        json_content = request.get_json()
        for json_flow in json_content:
            received_flow = Flow.from_dict(json_flow)
            if dpid:
                self.flow_manager.install_new_flow(received_flow, dpid)
            else:
                for switch_dpid in self.controller.switches:
                    self.flow_manager.install_new_flow(received_flow,
                                                       switch_dpid)

        return json.dumps({"response": "FlowMod Messages Sent"}), 201

    @rest('flows', methods=['DELETE'])
    @rest('flows/<dpid>', methods=['DELETE'])
    @rest('flows/<dpid>/<flow_id>', methods=['DELETE'])
    def delete_flows(self, flow_id=None, dpid=None):
        """Delete a flow from a switch identified by flow_id and dpid.

        If no flow_id has been specified, removes all flows from the switch.
        If no dpid or flow_id  has been specified, removes all flows from all
        switches.
        """
        if flow_id:
            self.flow_manager.delete_flow(flow_id, dpid)
        elif dpid:
            self.flow_manager.clear_flows(dpid)
        else:
            for switch_dpid in self.controller.switches:
                self.flow_manager.clear_flows(switch_dpid)

        return json.dumps({"response": "FlowMod Messages Sent"}), 202


class FlowManager(object):
    """Class responsible for manipulating flows at the switches."""

    def __init__(self, controller):
        """Init method."""
        self.controller = controller

    def install_new_flow(self, flow, dpid):
        """Create a new flow_mod message.

        This method is responsible for creating a new flow_mod message from
        the Flow object received.
        """
        switch = self.controller.get_switch_by_dpid(dpid)
        flow_mod = flow.as_flow_mod(FlowModCommand.OFPFC_ADD)

        event_out = KytosEvent(name=('kytos/of_flow-manager.messages.out.'
                                     'ofpt_flow_mod'),
                               content={'destination': switch.connection,
                                        'message': flow_mod})
        self.controller.buffers.msg_out.put(event_out)

    def clear_flows(self, dpid):
        """Clear all flows from switch identified by dpid."""
        switch = self.controller.get_switch_by_dpid(dpid)
        for flow in switch.flows:
            flow_mod = flow.as_flow_mod(FlowModCommand.OFPFC_DELETE)
            event_out = KytosEvent(name=('kytos/of_flow-manager.messages.out.'
                                         'ofpt_flow_mod'),
                                   content={'destination': switch.connection,
                                            'message': flow_mod})
            self.controller.buffers.msg_out.put(event_out)

    def delete_flow(self, flow_id, dpid):
        """Remove a flow from a switch identified by id and dpid."""
        switch = self.controller.get_switch_by_dpid(dpid)
        for flow in switch.flows:
            if flow.id == flow_id:
                flow_mod = flow.as_flow_mod(FlowModCommand.OFPFC_DELETE)
                content = {'destination': switch.connection,
                           'message': flow_mod}
                event_out = KytosEvent(name=('kytos/of_flow-manager.'
                                             'messages.out.ofpt_flow_mod'),
                                       content=content)
                self.controller.buffers.msg_out.put(event_out)

    @staticmethod
    def _get_flows(flow_stats):
        """Create a lista of flows.

        Creates a list of flows from the body of a flow_stats_reply message.
        """
        flows = []
        for flow_stat in flow_stats:
            flows.append(Flow.from_flow_stats(flow_stat))

        return flows
