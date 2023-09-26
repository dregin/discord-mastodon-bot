from mastodon import Mastodon, StreamListener
from discord import SyncWebhook
import os

# Load the ENV vars
discord_webhook = SyncWebhook.from_url(os.environ['DISCORD_WEBHOOK']) # https://discord.com/api/webhooks/123123qasdawsdasd/Na_-asdasdasdasd
mastodon_base_url  =os.environ['MASTODON_BASE_URL'] # https://mastodon.ie
mastodon_access_token = os.environ['MASTODON_ACCESS_TOKEN']

m = Mastodon(access_token = mastodon_access_token, api_base_url = mastodon_base_url)

class Listener(StreamListener):
    def on_notification(self, notification):
        if notification['type'] == 'admin.report':
            text = f"""Report received from {notification['account']['username']} against {notification['report']['target_account']['acct']}.
Note: {notification['report']['comment']}

Link: {mastodon_base_url}/admin/reports/{notification['report']['id']}"""
            discord_webhook.send(text)

m.stream_user(Listener())
