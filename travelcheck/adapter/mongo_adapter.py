import logging

from pymongo import MongoClient

LOGGER = logging.getLogger(__name__)


class MongoDatabase(object):
    def __init__(self, host, db):
        self._client = MongoClient(host)
        self._db = self._client[db]

    def get_price(self, subscription):
        item = self._db.prices.find_one(subscription)
        if item:
            return item['price']
        return None

    def add_subscription(self, subscription):
        self._db.prices.insert(subscription)
