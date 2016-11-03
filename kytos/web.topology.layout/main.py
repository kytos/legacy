import logging
import json

from flask import request
from os import listdir, getcwd
from os.path import isfile, join

from kyco.core.napps import KycoCoreNApp


log = logging.getLogger('KycoNApp')


class Main(KycoCoreNApp):
    """
    This app intends to update the links between machines and switches. It
    considers that if an interface is connected to another interface then this
    is a link. If not, it must be a connection to a server
    """

    def setup(self):
        """Creates an empty dict to store the switches references and the
        information about the hosts"""

        self.name = 'kytos/web.topology.layout'
        self.stop_signal = False
        self.current_controller = self.controller
        self.controller.register_rest_endpoint('/webtopo/', self.get_topologies,
                                               methods=['GET'])
        self.controller.register_rest_endpoint('/webtopo/<topo_name>',
                                               self.save_topology,
                                               methods=['POST'])
        self.controller.register_rest_endpoint('/webtopo/<topo_name>',
                                               self.get_topologies,
                                               methods=['GET'])

    def execute(self):
        """ Do nothing, only wait for packet-in messages"""
        pass

    def shutdown(self):
        self.stop_signal = True

    def save_topology(self, topo_name):
        topo_dir = join(getcwd(), 'topologies')
        topology = request.get_json()
        with open(join(topo_dir, topo_name + '.json'), 'w') as outfile:
            json.dump(topology, outfile)

    def get_topologies(self, topo_name=None):
        topos = join(getcwd(), 'topologies')
        if topo_name is None:
            output = [f for f in listdir(topos) if isfile(join(topos, f))]
        else:
            try:
                with open(join(topos, topo_name + '.json'), 'r') as outfile:
                    output = json.load(outfile.read())
            except (FileNotFoundError, json.JSONDecodeError):
                output = None
        return json.dumps(output)
