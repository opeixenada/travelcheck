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
    def __init__(self, db, config_kiwi):
        self._db = db
        self._config_kiwi = config_kiwi

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=['POST', 'OPTIONS'])
    def index(self):
        if not cherrypy.request.body.length:
            raise cherrypy.HTTPError(400, "Empty payload")

        json_input = cherrypy.request.json

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Parsing basic and required parameters in our API request

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

        # Reserved for later: What kind of deeplink to return

        # if json_input.get('deeplink') and (
        #        json_input['deeplink'] == "search" or json_input['deeplink'] == "book"):
        #    deeplink_type = json_input['deeplink']
        #else:
        #    deeplink_type = 'search'

        # Departure dates; default today - +3 months

        earliest = earliest = today
        latest = earliest + relativedelta(months=+3)

        if json_input.get('earliest') and json_input.get('latest'):
            earliest = datetime.strptime(json_input['earliest'], "%Y-%m-%d")
            latest = datetime.strptime(json_input['latest'], "%Y-%m-%d")
            if earliest >= latest:
                raise cherrypy.HTTPError(400, "'earliest' must be before 'latest'")

        elif json_input.get('earliest'):
            earliest = datetime.strptime(json_input['earliest'], "%Y-%m-%d")
            latest = earliest + relativedelta(months=+3)

        elif json_input.get('latest'):
            latest = datetime.strptime(json_input['latest'], "%Y-%m-%d")
            earliest = latest - relativedelta(months=+3)

        # Min & max trip duration, default 2 to 3 days

        min_days = 2
        max_days = 3

        if json_input.get('minDays') and json_input.get('maxDays'):
            min_days = int(json_input['minDays'])
            max_days = int(json_input['maxDays'])
            if min_days > max_days:
                raise cherrypy.HTTPError(400, "'minDays' must be not greater than 'maxDays'")

        elif json_input.get('minDays'):
            min_days = int(json_input['minDays'])
            max_days = min_days + 1

        elif json_input.get('maxDays'):
            max_days = int(json_input['maxDays'])
            min_days = 1

        # Direct-only flights, default false

        if json_input.get('maxStops'):
            max_stops = json_input['maxStops']
            if max_stops < 0:
                raise cherrypy.HTTPError(400, "'maxStops' must be 0 or more")
        else:
            max_stops = 0
        
        # Finding subscription; otherwise, requesting price from Kiwi and saving

        try:
            subscription = {
                'origin': origin,
                'destination': destination,
                'earliest': earliest,
                'latest': latest,
                'minDays': min_days,
                'maxDays': max_days,
                'currency': currency,
                'locale': locale,
                'maxStops': max_stops
            }

            logging.info(
                "Subscription: %s" % json.dumps(subscription, indent=4, default=json_util.default))

            result = self._db.get_result(subscription)

            if not result:
                logging.info("Adding subscription")
                result = kiwi.subscribe(subscription, self._config_kiwi)
                result.update(subscription)
                self._db.add_subscription(result)
            else:
                logging.info(
                    "Found subscription: %s" % json.dumps(result, indent=4, default=json_util.default))

            response = Prices.__make_response(result)
            return response

        # Return the following in case of a failed request to Kiwi
        # To do: return the search deeplink instead of none

        except Exception as err:
            
            #logging.error("Error: %s" % err)
            logging.exception(err)

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
    def __make_response(result):

        return {
            'origin': result['origin'],
            'destination': result['destination'],
            'price': result['price'],
            'currency': result['currency'],
            'outboundDate': result['outboundDate'].strftime("%Y-%m-%d"),
            'inboundDate': result['inboundDate'].strftime("%Y-%m-%d"),
            'lastChecked': result['lastChecked'].strftime("%Y-%m-%d"),
            'deeplink': result['deeplink'],
            'locale': result['locale']
        }
