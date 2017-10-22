import logging
import signal

import cherrypy
# from cherrypy.lib import auth_digest

from travelcheck.adapter.sql_adapter import SqlDatabase
from travelcheck.prices import Prices

LOGGER = logging.getLogger(__name__)


class Root(object):
    @cherrypy.expose
    def ping(self):
        return {"answer": "pong"}


class Server(object):
    def __init__(self, config):
        self._db = SqlDatabase(config['sql'])

        # Digest auth:
        # self._conf = {
        #     '/': {
        #         'tools.auth_digest.on': True,
        #         'tools.auth_digest.realm': 'localhost',
        #         'tools.auth_digest.get_ha1': auth_digest.get_ha1_dict_plain(config['users']),
        #         'tools.auth_digest.key': config['key'],
        #         'tools.trailing_slash.on': False
        #     }
        # }

        self._conf = {
            '/': {
                'tools.trailing_slash.on': False
            }
        }

    @staticmethod
    def error_page(status, message, traceback, version):
        LOGGER.warning("status: %s, message: %s, traceback: %s" % (status, message, traceback))
        return """{"status": "KO", "message":"%s"}""" % message

    @staticmethod
    def signal_handler(signum, frame):
        print("Signal handler called with signal %s, exiting" % str(signum))
        cherrypy.engine.exit()

    @staticmethod
    def start(port):
        LOGGER.info("Starting server")

        cherrypy.config.update({
            'server.socket_host': "0.0.0.0",
            'server.socket_port': int(port)
        })

        cherrypy.engine.start()
        cherrypy.engine.block()

    def configure(self):
        signal.signal(signal.SIGINT, Server.signal_handler)

        cherrypy.config.update({
            'server.thread_pool': 30,
            'error_page.default': Server.error_page,
            'error_page.404': Server.error_page,
            'error_page.400': Server.error_page,
            'error_page.500': Server.error_page
        })

        cherrypy.tree.mount(Root(), "/", config=self._conf)
        cherrypy.tree.mount(Prices(self._db), "/prices", config=self._conf)
