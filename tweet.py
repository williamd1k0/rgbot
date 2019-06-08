
import os
from twitter import Api as Twitter

API_KEY = os.environ.get('TWITTER_API_KEY')
API_SECRET =  os.environ.get('TWITTER_API_SECRET')
TOKEN = os.environ.get('TWITTER_TOKEN')
TOKEN_SECRET = os.environ.get('TWITTER_TOKEN_SECRET')
twitter_api = None

if TOKEN and TOKEN_SECRET:
    twitter_api = Twitter(
        consumer_key=API_KEY, consumer_secret=API_SECRET,
        access_token_key=TOKEN, access_token_secret=TOKEN_SECRET
    )

class TweetRGB(object):
    api = None
    status = None
    poll_ref = None

    def __init__(self, api=twitter_api):
        self.api = api
        self.status = []

    def post(self, msg, img=None):
        reply_id = self.status[-1].id if len(self.status) > 0 else None
        self.status.append(self.api.PostUpdate(msg, in_reply_to_status_id=reply_id))

    def poll(self, a, b, expires=60*60):
        # Twitter does not provide a poll API ¯\_(シ)_/¯
        pass

if __name__ == '__main__':
    bot = TweetRGB()
    bot.post('ping')
