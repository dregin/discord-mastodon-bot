import json
import logging
import os
import pika

from mastodon import Mastodon, StreamListener
from pymongo import MongoClient

# Load the ENV vars from .env
mastodon_base_url = os.environ['MASTODON_BASE_URL'] # https://mastodon.ie
mastodon_access_token = os.environ['MASTODON_ACCESS_TOKEN']
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)

rmq_url = 'amqp://guest:guest@rabbit/%2f'
rmq_params = pika.URLParameters(rmq_url)
rmq_params.socket_timeout = 5

m = Mastodon(access_token = mastodon_access_token, api_base_url = mastodon_base_url)

mongo_uri = 'mongodb://mongo:27017/'
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client.config
mongo_trans = mongo_db.transactions

# Get a list of the mastodon users we're tracking
try:
    tracked_masto_users = mongo_trans.find({'purpose': 'user_tracking'})
except Exception as e:
    logging.error(e)

for user in tracked_masto_users:
    logging.info(f"following: {user}")

class Listener(StreamListener):
    # A mastodon status has appeared.
    def on_update(self, status):
#        message = f"{status['account']['username']}: {status['content']}: {status['url']}"
        logging.debug(status)
        print("1")

        # TODO: Add persistent store.
        # TODO: Check for user in list of users in persistent store.
		# Get a list of the mastodon users we're tracking
        try:
            tracked_masto_users = mongo_trans.find({'purpose': 'user_tracking'})
            print("2")
            tracked_masto_users = [user['username'] for user in tracked_masto_users]
            print("3")
        except Exception as e:
            logging.error(e)

        user = status['account']['username']
#        message = status['content']
#        message_url = status['url']

        if user not in tracked_masto_users:
            return

        # RabbitMQ Setup
        connection = pika.BlockingConnection(rmq_params)
        channel = connection.channel()
        channel.queue_declare(queue='masto_posts_to_snoop')
        payload = {}
        payload['username'] = status['account']['username']
        payload['message'] = status['content']
        payload['url'] = status['url']
        try:
            print("4")
            # Send the mastodon post to RabbitMQ to be picked up and posted to Discord
#            channel.basic_publish(exchange='', routing_key='masto_posts_to_snoop', body=f'user:{user} message:{message}')
            channel.basic_publish(exchange='', routing_key='masto_posts_to_snoop', body=f'{json.dumps(payload)}')
            print("5")
        except Exception as e:
            print(e)
        connection.close

m.stream_public(Listener(), local=True)
