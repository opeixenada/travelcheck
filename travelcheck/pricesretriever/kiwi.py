import logging
from datetime import datetime
from urllib.parse import urlencode

import requests
from retrying import retry

from travelcheck.util import retry_if_result_none

LOGGER = logging.getLogger(__name__)


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000,
       retry_on_result=retry_if_result_none, stop_max_attempt_number=5)
def subscribe(subscription):
    host = "https://api.skypicker.com/flights"

    query = {
        'flyFrom': subscription['origin'],
        'to': subscription['destination'],
        'dateFrom': subscription['earliest'].strftime("%d/%m/%Y"),
        'dateTo': subscription['latest'].strftime("%d/%m/%Y"),
        'daysInDestinationFrom': subscription['minDays'],
        'daysInDestinationTo': subscription['maxDays'],
        'curr': subscription['currency'],
        'locale': subscription['locale'],
        'directFlights': 1,
        'partner': 'picky',
        'partner_market': 'de',
        'sort': 'price',
        'asc': 1
    }

    url = host + '?' + urlencode(query)

    logging.info("Requesting %s" % url)

    response = requests.get(url)

    if response.json() and response.json()['data']:
        first_result = response.json()['data'][0]
        subscription_response = dict()
        subscription_response['price'] = first_result['price']

        subscription_response['lastChecked'] = datetime.utcnow()

        subscription_response['outboundDate'] = datetime.utcfromtimestamp(first_result['dTimeUTC'])

        first_return_leg = next(leg for leg in first_result['route'] if leg['return'] == 1)
        subscription_response['inboundDate'] = datetime.utcfromtimestamp(
            first_return_leg['dTimeUTC'])

        subscription_response['deeplink'] = first_result.get('deep_link')

        return subscription_response

    return None
