
import os
import tweepy
from tempfile import NamedTemporaryFile
from data import CONFIGS, SnsAPI, SnsStatus, commit

API_KEY = os.environ.get('TWITTER_API_KEY')
API_SECRET =  os.environ.get('TWITTER_API_SECRET')
TOKEN = os.environ.get('TWITTER_TOKEN')
TOKEN_SECRET = os.environ.get('TWITTER_TOKEN_SECRET')
twitter_api = None

if TOKEN and TOKEN_SECRET:
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    auth.set_access_token(TOKEN, TOKEN_SECRET)
    twitter_api = tweepy.API(auth)
else:
    from random import randint
    from collections import namedtuple
    StatusModel = namedtuple('Status', ['id'])
    MediaModel = namedtuple('Media', ['media_id'])
    class DummyTwitterApi(object):
        def update_status(self, *args, **kargs):
            print('[DummyTwitterApi/update_status]', args, kargs)
            return StatusModel(randint(0, 999999999))
        def media_upload(self, *args, **kargs):
            print('[DummyTwitterApi/media_upload]', args, kargs)
            return MediaModel(randint(0, 999999999))
    twitter_api = DummyTwitterApi()

class RGBotTweet(SnsAPI):
    api = None
    poll_ref = None

    @classmethod
    def new(cls, battle=None, twitter_api=twitter_api):
        api = cls(battle=battle)
        api.set_api(twitter_api)
        commit()
        return api

    def set_api(self, twitter_api=twitter_api):
        self.api = twitter_api

    def post(self, msg, img=None, reply=True, pin=False):
        reply_id = self.last_status_id() if reply and len(self.status) > 0 else None
        media_id = None
        if img:
            fileim = NamedTemporaryFile(suffix='.png', delete=False)
            img.save(fileim, 'png')
            fileim.close()
            media = self.api.media_upload(fileim.name)
            media_id = [media.media_id]
            os.unlink(fileim.name)
        tags = ''
        for tag in CONFIGS['sns']['hashtags']:
            tags += '\n#%s' % tag
        if tags:
            msg += '\n' + tags
        status = self.api.update_status(msg, in_reply_to_status_id=reply_id, media_ids=media_id)
        SnsStatus(status_id=status.id, sns_api=self.id)
        commit()
        if pin:
            self.pin(status.id)
        return status.id

    def pin(self, status_id, unpin_all=True):
        if unpin_all:
            self.unpin_all()
        print('RGBotTweet.pin', NotImplemented)

    def unpin_all(self):
        print('RGBotTweet.unpin_all', NotImplemented)

    def poll(self, a, b, expires=CONFIGS['sns']['poll-duration']):
        # Twitter does not provide a poll API ¯\_(シ)_/¯
        print('RGBotTweet.poll', NotImplemented)


if __name__ == '__main__':
    from PIL import Image
    from data import init_db, db_session

    init_db('data/sns.db')
    with db_session:
        bot = RGBotTweet.new()
        bot.post('ping', Image.open('devel/test-img.png'), pin=True)
