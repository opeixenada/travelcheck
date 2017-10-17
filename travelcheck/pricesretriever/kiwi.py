import logging
from urllib.parse import urlencode

import requests
import schedule

LOGGER = logging.getLogger(__name__)


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
        return response.json()['data'][0]['price']

    return None
