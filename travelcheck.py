import argparse
import json
import logging
import os
from os.path import expanduser

from travelcheck.server import Server

LOGGER = logging.getLogger(__name__)


def main(config):
    server = Server(config)
    server.configure()
    server.start(config['port'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("TravelCheck: Start")

    parser = argparse.ArgumentParser(description='TravelCheck')

    home = expanduser("~")
    default_cfg = os.path.join(home, ".travelcheck.json")

    parser.add_argument('--port', required=False, help="http port", default=8080)

    parser.add_argument('--config', required=False, default=default_cfg,
                        help="Config file (default %s)" % default_cfg)

    parser.add_argument('--debug', required=False, help="Debug mode", action="store_true",
                        default=False)

    cmd_args = parser.parse_args()

    if cmd_args.debug:
        logging.basicConfig(level=logging.DEBUG)

    with open(cmd_args.config) as j_file:
        config = json.load(j_file)

    config['port'] = int(cmd_args.port)

    main(config)
