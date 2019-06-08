
import os
import tweepy

API_KEY = os.environ.get('TWITTER_API_KEY')
API_SECRET =  os.environ.get('TWITTER_API_SECRET')
TOKEN = os.environ.get('TWITTER_TOKEN')
TOKEN_SECRET = os.environ.get('TWITTER_TOKEN_SECRET')
twitter_api = None

if TOKEN and TOKEN_SECRET:
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    auth.set_access_token(TOKEN, TOKEN_SECRET)
    twitter_api = tweepy.API(auth)

class TweetRGB(object):
    api = None
    status = None
    poll_ref = None

    def __init__(self, api=twitter_api):
        self.api = api
        self.status = []

    def post(self, msg, img=None):
        reply_id = self.status[-1].id if len(self.status) > 0 else None
        self.status.append(self.api.update_status(msg, in_reply_to_status_id=reply_id))

    def poll(self, a, b, expires=60*60):
        # Twitter does not provide a poll API ¯\_(シ)_/¯
        pass

if __name__ == '__main__':
    bot = TweetRGB()
    bot.post('ping')
