import json
import logging
from datetime import datetime

import cherrypy
from bson import json_util
from dateutil.relativedelta import relativedelta

from travelcheck.pricesretriever import kiwi

LOGGER = logging.getLogger(__name__)


class Prices(object):
    def __init__(self, db):
        self._db = db

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=['POST', 'OPTIONS'])
    def index(self):
        if not cherrypy.request.body.length:
            raise cherrypy.HTTPError(400, "Empty payload")

        json_input = cherrypy.request.json

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        subscription = {
            'origin': json_input['origin'],
            'destination': json_input['destination'],
            'earliest_date': today,
            'latest_date': today + relativedelta(months=+3),
            'min_days': 2,
            'max_days': 3,
            'landing': "search",
            'currency': "EUR",
            'locale': "en"
        }

        logging.info("Subscription: %s" % json.dumps(subscription, indent=4, default=json_util.default))

        price = self._db.get_price(subscription)

        if not price:
            logging.info("Adding subscription")
            price = kiwi.subscribe(subscription)
            subscription['price'] = price
            self._db.add_subscription(subscription)

        return {
            'origin': subscription['origin'],
            'destination': subscription['destination'],
            'currency': subscription['currency'],
            'price': price
        }
