import discord
import json
import logging
import os
import pika

from discord.ext import commands, tasks
from pymongo import MongoClient

# Load the ENV vars from .env
discord_token = os.environ['DISCORD_TOKEN']
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)

snooper_channel_name = os.environ['DISCORD_SNOOPER_CHANNEL_NAME']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

mongo_uri = 'mongodb://mongo:27017/'
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client.config
mongo_trans = mongo_db.transactions

rmq_url = 'amqp://guest:guest@rabbit/%2f'
rmq_params = pika.URLParameters(rmq_url)
rmq_params.socket_timeout = 5

@bot.group(invoke_without_command=True)
async def snooper(ctx):
    return


@snooper.command()
async def add(ctx, username):
    # TODO: Validate username is actually active on the mastodon instance
    doc = {'purpose': 'user_tracking', 'username': username}
    mongo_trans.update_one(doc, { '$set': doc }, upsert=True)
    await ctx.send(f"user: {username} added to watch list.")

@snooper.command()
async def remove(ctx, username):
    rem_filter = {'username': username}
    try:
        tracked_masto_users = mongo_trans.delete_one(rem_filter)
        await ctx.send(f'Successfully removed {username}')
    except Exception as e:
        logging.error(e)

@snooper.command()
async def list(ctx):
    try:
        doc_filter = {'purpose': 'user_tracking'}
        tracked_masto_users = mongo_trans.find(doc_filter)
        message = '\n'.join([user['username'] for user in tracked_masto_users])
        message = message if message else "No users being tracked."
        await ctx.send(message)
    except Exception as e:
        logging.error(e)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    mastodon_post_loop.start()

@tasks.loop(seconds=10)
async def mastodon_post_loop():
    # Periodically check for any mastodon posts that need to be posted to discord

    # RabbitMQ setup
    try:
        connection = pika.BlockingConnection(rmq_params)
        rmq_channel = connection.channel()
        rmq_channel.queue_declare(queue='masto_posts_to_snoop')
    except pika.exceptions.AMQPConnectionError:
        return

    logging.debug("Checking RMQ for messages")
    try:
        method_frame, header_frame, body = rmq_channel.basic_get('masto_posts_to_snoop')
        if method_frame:
            logging.debug(body)
            status = json.loads(body)
            logging.info(f"Got a message: {body}")
            for channel in bot.get_all_channels():
                if channel.name == channel_name:
                    channel_id = channel.id
                    break
            discord_channel = bot.get_channel(channel_id)
            embed = discord.Embed()
            embed.description = f"<html>{status['message']}</html>"
#            await discord_channel.send(f"{status['username']} posted the following:", embed=embed)
            await discord_channel.send(status['url'])
            rmq_channel.basic_ack(method_frame.delivery_tag)
    except pika.exceptions.ChannelClosedByBroker:
        return
    connection.close()

bot.run(discord_token)
