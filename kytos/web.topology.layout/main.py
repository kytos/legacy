"""Module to manager the settings and layout of kyco web interface."""

import json
import logging
from os import listdir, makedirs
from os.path import isfile, join

from flask import request

from kyco.core.napps import KycoCoreNApp

log = logging.getLogger('KycoNApp')

TOPOLOGY_DIR = '/tmp/kytos/topologies/'
makedirs(TOPOLOGY_DIR, exist_ok=True)


class Main(KycoCoreNApp):
    """Main class for Web Topology Layout application.

    This app intends to update the links between machines and switches. It
    considers that if an interface is connected to another interface then this
    is a link. If not, it must be a connection to a server.
    """

    def setup(self):
        """Method used to create the web.topology.layout routes.

        This method will register the routes ['kytos/web/topology/layouts/',
        'web/topology/layouts/<name>'] to save and recover topologies.
        """
        self.name = 'kytos/web.topology.layout'
        self.current_controller = self.controller
        self.controller.register_rest_endpoint('/web/topology/layouts/',
                                               self.get_topologies,
                                               methods=['GET'])
        self.controller.register_rest_endpoint('/web/topology/layouts/<name>',
                                               self.topology,
                                               methods=['GET', 'POST'])

    def execute(self):
        """Do nothing."""
        pass

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')

    def topology(self, name):
        """Method used to save or load a topology layout.

        Paramters:
            name (string): mame of the topology to be saved or loaded.

        Returns:
            topology (string): topology using json format.
        """
        if request.method == 'POST':
            return self.save_topology(name)
        else:
            return self.get_topology(name)

    def save_topology(self, name):
        """Save a topology layout in a file.

        This method get a json topology from request and puts this in a file.

        Parameters:
            name (string): name of the topology to  be saved or loaded.

        Returns:
            topology (string): topology using json format.
        """
        if not request.is_json:
            return json.dumps('{"error": "gt was not a JSON request"}'), 400
        topology = request.get_json()
        with open(join(TOPOLOGY_DIR, name + '.json'), 'w') as outfile:
            json.dump(topology, outfile)
        return json.dumps({'response': 'Saved'}), 201

    def get_topology(self, name):
        """Method to read and return a topology from json file.

        Paramters:
            name (string): name of the topology to be saved or loaded.

        Returns:
            topology (string): topology using json format.
        """
        file = join(TOPOLOGY_DIR, name + '.json')
        if not isfile(file):
            return json.dumps('{"error": "Topology not found"}'), 400
        with open(join(TOPOLOGY_DIR, name + '.json'), 'r') as outfile:
            output = json.load(outfile)
        return json.dumps(output)

    def get_topologies(self):
        """Method used to returns all topologies.

        Returns:
            topologies (string): all topologies saved using json format.
        """
        files = listdir(TOPOLOGY_DIR)
        output = []
        for f in files:
            if isfile(join(TOPOLOGY_DIR, f)):
                output.append(f.replace('.json', ''))

        return json.dumps(output)
