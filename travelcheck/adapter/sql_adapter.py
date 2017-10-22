import logging

import MySQLdb

LOGGER = logging.getLogger(__name__)


class SqlDatabase(object):
    def __init__(self, config):
        self._db = MySQLdb.connect(host=config['host'], port=config['port'], user=config['user'],
                                   passwd=config['pswd'], db=config['db'])

    def check_connection(self):
        self._db.ping(True)

    def get_price(self, subscription):
        query = "SELECT * FROM subscriptions WHERE origin='%s' AND destination='%s' AND " \
                "min_days=%s AND max_days=%s AND earliest_date='%s' AND latest_date='%s' AND " \
                "currency='%s'" % (
                    subscription['origin'],
                    subscription['destination'],
                    subscription['min_days'],
                    subscription['max_days'],
                    subscription['earliest_date'],
                    subscription['latest_date'],
                    subscription['currency'])

        self.check_connection()
        cursor = self._db.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            return row[4]

        return None

    def add_subscription(self, subscription):
        query = "INSERT INTO subscriptions(origin, destination, min_days, max_days, price, " \
                "earliest_date, latest_date, currency) " \
                "VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s)" % (
                    subscription['origin'],
                    subscription['destination'],
                    subscription['min_days'],
                    subscription['max_days'],
                    subscription['price'],
                    subscription['earliest_date'],
                    subscription['latest_date'],
                    subscription['currency'])

        self.check_connection()
        cursor = self._db.cursor()
        try:
            # Execute the SQL command
            cursor.execute(query)
            # Commit your changes in the database
            self._db.commit()
        except:
            # Rollback in case there is any error
            self._db.rollback()
