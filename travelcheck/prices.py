import json
import logging
from datetime import datetime
from urllib.parse import urlunparse, urlencode, urlparse, parse_qs

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
            deeplink_type = json_input['deeplink']
        else:
            deeplink_type = 'search'

        if 'earliest' in json_input:
            earliest = datetime.strptime(json_input['earliest'], "%Y-%m-%d")
        else:
            earliest = today

        if 'latest' in json_input:
            latest = datetime.strptime(json_input['latest'], "%Y-%m-%d")
        else:
            latest = earliest + relativedelta(months=+3)

        if earliest > latest:
            earliest = latest

        if 'minDays' in json_input:
            min_days = int(json_input['minDays'])
        else:
            min_days = 2

        if 'maxDays' in json_input:
            max_days = int(json_input['maxDays'])
        else:
            max_days = min_days + 1

        if max_days < min_days:
            max_days = min_days

        try:
            subscription = {
                'origin': origin,
                'destination': destination,
                'earliest': earliest,
                'latest': latest,
                'minDays': min_days,
                'maxDays': max_days,
                'currency': currency,
                'locale': locale
            }

            logging.info(
                "Subscription: %s" % json.dumps(subscription, indent=4, default=json_util.default))

            result = self._db.get_result(subscription)

            if not result:
                logging.info("Adding subscription")
                result = kiwi.subscribe(subscription)
                result.update(subscription)
                self._db.add_subscription(result)

            response = Prices.__get_response(result, deeplink_type)
            return response

        except Exception as err:
            logging.error("Error: %s" % err)
            return {
                'origin': origin,
                'destination': destination,
                'price': None,
                'currency': currency,
                'outboundDate': None,
                'inboundDate': None,
                'lastChecked': None,
                'deeplink': None,
                'locale': locale
            }

    @staticmethod
    def __get_response(result, deeplink_type):
        return {
            'origin': result['origin'],
            'destination': result['destination'],
            'price': result['price'],
            'currency': result['currency'],
            'outboundDate': result['outboundDate'].strftime("%d-%m-%Y"),
            'inboundDate': result['inboundDate'].strftime("%d-%m-%Y"),
            'lastChecked': result['lastChecked'].strftime("%d-%m-%Y"),
            'deeplink': Prices.__get_deeplink(result.get('deeplink'), deeplink_type),
            'locale': result['locale']
        }

    @staticmethod
    def __get_deeplink(link, deeplink_type):
        if deeplink_type == "flight":
            url = urlparse(link)
            query = parse_qs(url.query)
            query.pop('flightsId')
            query.pop('booking_token')
            return urlunparse(url._replace(query=urlencode(query, True)))
        else:
            return link
