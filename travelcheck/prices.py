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

        if json_input.get('origin'):
            origin = json_input['origin']
        else:
            raise cherrypy.HTTPError(400, "'origin' not defined")

        if json_input.get('destination'):
            destination = json_input['destination']
        else:
            raise cherrypy.HTTPError(400, "'destination' not defined")

        if json_input.get('currency'):
            currency = json_input['currency']
        else:
            currency = 'EUR'

        if json_input.get('locale'):
            locale = json_input['locale']
        else:
            locale = 'en'

        if json_input.get('deeplink') and (
                json_input['deeplink'] == "search" or json_input['deeplink'] == "flight"):
            deeplink_type = json_input['deeplink']
        else:
            deeplink_type = 'search'

        if json_input.get('earliest'):
            earliest = datetime.strptime(json_input['earliest'], "%Y-%m-%d")
        else:
            earliest = today

        if json_input.get('latest'):
            latest = datetime.strptime(json_input['latest'], "%Y-%m-%d")
        else:
            latest = earliest + relativedelta(months=+3)

        if earliest > latest:
            earliest = latest

        if json_input.get('minDays'):
            min_days = int(json_input['minDays'])
        else:
            min_days = 2

        if json_input.get('maxDays'):
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
            'outboundDate': result['outboundDate'].strftime("%Y-%m-%d"),
            'inboundDate': result['inboundDate'].strftime("%Y-%m-%d"),
            'lastChecked': result['lastChecked'].strftime("%Y-%m-%d"),
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
