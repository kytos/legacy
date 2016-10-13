"""This App is the responsible to install a drop ipv6 flow on switch setup."""

import json
import logging

from flask import Flask
from flask import request

from kyco.core.events import KycoEvent
from kyco.core.napps import KycoCoreNApp

log = logging.getLogger('Kyco')


class Main(KycoCoreNApp):
    """Main class of KycoCoreNApp, responsible for the main OpenFlow basic
    operations.

    """

    def setup(self):
        """'Replaces' the 'init' method for the KycoApp subclass.

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly."""
        self.server = APIServer()

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KycoNApp class.
        Users shouldn't call this method directly."""
        self.server.start()

    def shutdown(self):
        self.server.stop()


class FlowManager(object):
    """This class is responsible for manipulating flows at the switches"""
    def __init__(self):
        pass

    def install_new_flow(self, flow, dpid):
        """
        This method is responsible for creating a new flow_mod message from
        the Flow object received
        """
        pass

    def dump_flows(self, dpid):
        """Rettrieves the list of flows installed in the Switch identified by
        dpid"""
        pass

    def clear_flows(self, dpid):
        """Clear all flows from switch identified by dpid"""
        pass

    def delete_flow(self, dpid, id):
        """Removes the flow identified by id from the switch identified by
        dpid"""
        pass


class Flow(object):
    """
    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """
    def __init__(self, in_port=None, dl_src=None, dl_dst=None, dl_vlan=None,
                 dl_vlan_pcp=None, dl_type=None, nw_src=None, nw_dst=None,
                 tp_src=None, tp_dst=None, actions=[]):
        self.in_port = in_port
        self.dl_src = dl_src
        self.dl_dst = dl_dst
        self.dl_vlan = dl_vlan
        self.dl_vlan_pcp = dl_vlan_pcp
        self.dl_type = dl_type
        self.nw_src = nw_src
        self.nw_dst = nw_dst
        self.tp_src = tp_src
        self.tp_dst = tp_dst
        self.actions = []
        self.id = None

    def as_json(self):
        """Returns the representation of a flow in a json format"""
        return json.dumps({self.id: {"in_port": self.in_port,
                                     "dl_src": self.dl_src,
                                     "dl_dst": self.dl_dst,
                                     "dl_vlan": self.dl_vlan,
                                     "dl_vlan_pcp": self.dl_vlan_pcp,
                                     "dl_type": self.dl_type,
                                     "nw_src": self.nw_src,
                                     "nw_dst": self.nw_dst,
                                     "tp_src": self.tp_src,
                                     "tp_dst": self.tp_dst,
                                     "actions": self.actions}})


class FlowAction(object):
    """The instances of this class represent action to be executed once a flow
    is activated"""

    def __init__(self):
        pass


class OutputAction(object):
    """This class represents the action of forwarding network packets into a
    given port"""
    def __init__(self, output_port):
        self.output_port = output_port


class DLChangeAction(object):
    """This action represents the change in the packet hw source/destination
    address"""
    def __init__(self, dl_src=None, dl_dst=None):
        self.dl_src = dl_src
        self.dl_dst = dl_dst


class NWChangeAction(object):
    """This action represents the change in the packet ip source/destination
    address"""
    def __init__(self, nw_src, nw_dst):
        self.nw_src = nw_src
        self.nw_dst = nw_dst


class APIServer(object):
    """This class is responsible for starting the REST api server and listening
    for requests"""

    app = Flask(__name__)

    def __init__(self, port=5000):
        self.port = port
        self.flow_manager = FlowManager()

    def start(self, debug=True):
        """This method is responsible for starting a flask server at the given
        port"""
        app.run(debug=debug)

    def stop(self):
        """This method is reponsible for stoping the flask server"""
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route('/<dpid>/flows', methods=['GET'])
    @app.route('/flows', methods=['GET'])
    def retrieve_flows(self, dpid=None):
        """docstring for retrieve_flows"""
