import logging
import json

from flask import abort, request
from os import listdir, makedirs
from os.path import isfile, join

from kyco.core.napps import KycoCoreNApp


log = logging.getLogger('KycoNApp')

TOPOLOGY_DIR = '/tmp/kytos/topologies/'
makedirs(TOPOLOGY_DIR, exist_ok=True)

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
        self.controller.register_rest_endpoint('/web/topology/layouts/',
                                               self.get_topologies,
                                               methods=['GET'])
        self.controller.register_rest_endpoint('/web/topology/layouts/<name>',
                                               self.topology,
                                               methods=['GET', 'POST'])

    def execute(self):
        """ Do nothing, only wait for packet-in messages"""
        pass

    def shutdown(self):
        self.stop_signal = True

    def topology(self, name):
        if request.method == 'POST':
            return self.save_topology(name)
        else:
            return self.get_topology(name)

    def save_topology(self, name):
        if not request.is_json:
            abort(400)
        topology = request.get_json()
        with open(join(TOPOLOGY_DIR, name + '.json'), 'w') as outfile:
            json.dump(topology, outfile)
        return 'OK'

    def get_topology(self, name):
        file = join(TOPOLOGY_DIR, name + '.json')
        if not isfile(file):
            return None
        with open(join(TOPOLOGY_DIR, name + '.json'), 'r') as outfile:
            output = json.load(outfile)
        return json.dumps(output)

    def get_topologies(self):
        files = listdir(TOPOLOGY_DIR)
        output = [f for f in files if isfile(join(TOPOLOGY_DIR, f))]
        return json.dumps(output)
