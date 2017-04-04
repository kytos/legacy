"""NApp responsible for installing or removing flows on the switches."""

import json

from flask import request
from kytos.core import log
from kytos.core.events import KytosEvent
from kytos.core.flow import Flow
from kytos.core.napps import KytosNApp
from pyof.v0x01.controller2switch.flow_mod import FlowModCommand

from napps.kytos.of_flow_manager import settings


class Main(KytosNApp):
    """Main class of of_stats NApp."""

    def setup(self):
        """Replace the 'init' method for the KytosApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        self.execute_as_loop(settings.STATS_INTERVAL)
        self.flow_manager = FlowManager(self.controller)
        endpoints = [('/flow-manager/<dpid>/flows', self.retrieve_flows,
                      ['GET']),
                     ('/flow-manager/flows', self.retrieve_flows,
                      ['GET']),
                     ('/flow-manager/<dpid>/flows-a', self.insert_flow,
                      ['POST']),
                     ('/flow-manager/<dpid>/<flow_id>/flows-d',
                      self.delete_flow, ['DELETE'])]
        for endpoint in endpoints:
            self.controller.register_rest_endpoint(*endpoint)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KytosNApp class.
        Users shouldn't call this method directly.
        """
        pass

    def shutdown(self):
        """Shutdown routine of the NApp."""
        log.debug("flow-manager stopping")

    def retrieve_flows(self, dpid=None):
        """Retrieve all flows from a sitch identified by dpid.

        If no dpid has been specified, returns the flows from all switches.
        """
        switch_flows = {}
        if dpid is not None:
            switch = self.controller.get_switch_by_dpid(dpid)
            flows = []
            for flow in switch.flows:
                flows.append(flow.as_dict())
            switch_flows[dpid] = flows
        else:
            for switch_dpid in self.controller.switches:
                switch = self.controller.get_switch_by_dpid(switch_dpid)
                flows = []
                for flow in switch.flows:
                    flows.append(flow.as_dict())
                switch_flows[switch_dpid] = flows
        return json.dumps(switch_flows)

    def insert_flow(self, dpid=None):
        """Insert a new flow to the switch identified by dpid.

        If no dpid has been specified, install flow in all switches.
        """
        json_content = request.get_json()
        for json_flow in json_content['flows']:
            received_flow = Flow.from_dict(json_flow)
            if dpid is not None:
                self.flow_manager.install_new_flow(received_flow, dpid)
            else:
                for switch_dpid in self.controller.switches:
                    self.flow_manager.install_new_flow(received_flow,
                                                       switch_dpid)

        return json.dumps({"response": "Flow Created"}), 201

    def clear_flows(self, dpid=None):
        """Clear flows from a switch identified by dpid.

        If no dpid has been specified, clear all flows from all switches.
        """
        if dpid is not None:
            self.flow_manager.clear_flows(dpid)
        else:
            for switch_dpid in self.controller.switches:
                self.flow_manager.clear_flows(switch_dpid)

    def delete_flow(self, flow_id, dpid=None):
        """Delete a flow from a switch identified by flow_id and dpid.

        If no dpid has been specified, removes all flows with the given flow_id
        from all switches.
        """
        if dpid is not None:
            self.flow_manager.delete_flow(flow_id, dpid)
        else:
            for switch_dpid in self.controller.switches:
                self.flow_manager.delete_flow(flow_id, switch_dpid)

        return json.dumps({"response": "Flow Removed"}), 202


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
