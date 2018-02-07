import logging
from urllib.parse import urlencode

import requests
from retrying import retry

from travelcheck.util import retry_if_result_none

LOGGER = logging.getLogger(__name__)


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000,
       retry_on_result=retry_if_result_none)
def subscribe(subscription):
    host = "https://api.skypicker.com/flights"

    query = {
        'flyFrom': subscription['origin'],
        'to': subscription['destination'],
        'dateFrom': subscription['earliest_date'].strftime("%d/%m/%Y"),
        'dateTo': subscription['latest_date'].strftime("%d/%m/%Y"),
        'daysInDestinationFrom': subscription['min_days'],
        'daysInDestinationTo': subscription['max_days'],
        'directFlights': 1,
        # 'partner': 'picky',
        'partner_market': 'de',
        'sort': 'price',
        'asc': 1
    }

    url = host + '?' + urlencode(query)

    response = requests.get(url)

    if response.json() and response.json()['data']:
        first_result = response.json()['data'][0]
        subscription_response = dict()
        subscription_response['price'] = first_result['price']
        subscription_response['deep_link'] = first_result['deep_link']
        return response.json()['data'][0]['price']

    return None
