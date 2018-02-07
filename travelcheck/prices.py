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

        if 'origin' in json_input:
            origin = json_input['origin']
        else:
            raise cherrypy.HTTPError(400, "'origin' not defined")

        if 'destination' in json_input:
            destination = json_input['destination']
        else:
            raise cherrypy.HTTPError(400, "'destination' not defined")

        if 'currency' in json_input:
            currency = json_input['currency']
        else:
            currency = 'EUR'

        if 'locale' in json_input:
            locale = json_input['locale']
        else:
            locale = 'en'

        if 'deeplink' in json_input and (
                json_input['deeplink'] == "search" or json_input['deeplink'] == "flight"):
            deeplink = json_input['deeplink']
        else:
            deeplink = 'search'

        if 'earliest_date' in json_input:
            earliest_date = datetime.strptime(json_input['earliest_date'])
        else:
            earliest_date = today

        if 'latest_date' in json_input:
            latest_date = datetime.strptime(json_input['latest_date'])
        else:
            latest_date = today + relativedelta(months=+3)

        if 'min_days' in json_input:
            min_days = int(json_input['min_days'])
        else:
            min_days = 2

        if 'max_days' in json_input:
            max_days = int(json_input['max_days'])
        else:
            max_days = 3

        try:
            subscription = {
                'origin': origin,
                'destination': destination,
                'earliest_date': earliest_date,
                'latest_date': latest_date,
                'min_days': min_days,
                'max_days': max_days,
                'currency': currency,
                'locale': locale,
                'deeplink': deeplink
            }

            logging.info(
                "Subscription: %s" % json.dumps(subscription, indent=4, default=json_util.default))

            price = self._db.get_price(subscription)

            if not price:
                logging.info("Adding subscription")
                price = kiwi.subscribe(subscription)
                subscription['price'] = price
                self._db.add_subscription(subscription)
            else:
                subscription['price'] = price

            return subscription

        except Exception as err:
            logging.error("Error: %s" % err)
            return {
                'origin': origin,
                'destination': destination,
                'currency': currency,
                'price': None
            }
