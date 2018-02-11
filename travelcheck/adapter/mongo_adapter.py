import logging

from pymongo import MongoClient
from datetime import datetime

LOGGER = logging.getLogger(__name__)


class MongoDatabase(object):
    def __init__(self, config):
        client = MongoClient("mongo")
        db = client[config['db']]

        self._prices = db.prices
        self._prices.ensure_index("createdAt", expireAfterSeconds=60 * 60 * 24)

        self.__status()

    def __status(self):
        LOGGER.info("Cached %s prices" % self._prices.count({}))

    def get_result(self, subscription):
        item = self._prices.find_one(subscription)
        if item:
            item.pop('_id')
            return item
        return None

    def add_subscription(self, subscription):
        subscription['createdAt'] = datetime.utcnow()
        self._prices.insert(subscription)
