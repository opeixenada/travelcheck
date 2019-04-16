import logging
from datetime import datetime
from urllib.parse import urlencode

import requests
from retrying import retry

from travelcheck.util import retry_if_result_none

LOGGER = logging.getLogger(__name__)


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000,
       retry_on_result=retry_if_result_none, stop_max_attempt_number=3)
def request_kiwi(subscription, config):
    
    host = "https://api.skypicker.com/flights"

    query = {
        'partner': config['apiKey'],
        'partner_market': config['market'],
        'fly_from': subscription['origin'],
        'fly_to': subscription['destination'],
        'date_from': subscription['earliest'].strftime("%d/%m/%Y"),
        'date_to': subscription['latest'].strftime("%d/%m/%Y"),
        'nights_in_dst_from': subscription['minDays'],
        'nights_in_dst_to': subscription['maxDays'],
        'max_stopovers': subscription['maxStops'],
        'curr': subscription['currency'],
        'locale': subscription['locale'],
        'sort': 'price',
        'asc': 1,
        'limit': 1
    }

    url = host + '?' + urlencode(query)

    logging.info("Requesting %s" % url)

    response = requests.get(url)

    if response.json() and response.json()['data']:
        return response.json()

    return None

def subscribe(subscription, config):
    
    # Call the Kiwi API
    response_json = request_kiwi(subscription, config)

    # Extract the relevant price details
    first_result = response_json['data'][0]
    subscription_response = dict()
    subscription_response['price'] = first_result['price']

    subscription_response['lastChecked'] = datetime.utcnow()

    subscription_response['outboundDate'] = datetime.utcfromtimestamp(first_result['dTimeUTC'])

    first_return_leg = next(leg for leg in first_result['route'] if leg['return'] == 1)
    subscription_response['inboundDate'] = datetime.utcfromtimestamp(
        first_return_leg['dTimeUTC'])

    subscription_response['deeplink'] = make_deeplink(subscription, config)

    return subscription_response

def make_deeplink(subscription, config):

        # Assemble the landing page using the original request parameters and Kiwi config

        deeplink_host = 'https://www.kiwi.com/deep'
        
        deeplink_params = (
            ('from', subscription['origin']),
            ('to', subscription['destination']),
            ('departure', subscription['earliest'].strftime("%d-%m-%Y") + '_' + subscription['latest'].strftime("%d-%m-%Y")),
            ('return', str(subscription['minDays']) + '-' + str(subscription['maxDays'])),
            ('lang', subscription['locale']),
            ('currency', subscription['currency']),
            ('affilid', config['deeplinksId'])
        )

        deeplink = deeplink_host + '?' + urlencode(deeplink_params)

        logging.info("Assembled deeplink: %s", deeplink)

        return deeplink
