
import os
from io import BytesIO
from mastodon import Mastodon
from data import CONFIGS, SnsAPI, SnsStatus, commit


TOKEN = os.environ.get('MSTDN_TOKEN')
URL = os.environ.get('MSTDN_URL')
mstdn_api = None

if TOKEN and URL:
    mstdn_api = Mastodon(access_token=TOKEN, api_base_url=URL)
else:
    from random import randint
    from collections import namedtuple
    UserModel = namedtuple('User', ['id'])
    StatusModel = namedtuple('Status', ['id'])
    MediaModel = namedtuple('Media', ['id'])
    class DummyMstdnApi(object):
        def status_post(self, *args, **kargs):
            print('[DummyMstdnApi/status_post]', args, kargs)
            return StatusModel(randint(0, 999999999))
        def make_poll(self, *args, **kargs):
            print('[DummyMstdnApi/make_poll]', args, kargs)
            return
        def media_post(self, *args, **kargs):
            print('[DummyMstdnApi/media_post]', args, kargs)
            return MediaModel(randint(0, 999999999))
        def status_pin(self, id):
            print('[DummyMstdnApi/status_pin]', id)
            return StatusModel(id)
        def status_unpin(self, id):
            print('[DummyMstdnApi/status_unpin]', id)
            return StatusModel(id)
        def account_verify_credentials(self):
            print('[DummyMstdnApi/account_verify_credentials]')
            return UserModel(randint(0, 999999999))
        def account_statuses(self, *args, **kargs):
            print('[DummyMstdnApi/account_statuses]', args, kargs)
            return [StatusModel(randint(0, 999999999))]
    mstdn_api = DummyMstdnApi()

class RGBotToot(SnsAPI):
    api = None

    @classmethod
    def new(cls, battle=None, mstdn_api=mstdn_api):
        api = cls(battle=battle)
        api.set_api(mstdn_api)
        commit()
        return api

    def set_api(self, mstdn_api=mstdn_api):
        self.api = mstdn_api

    def post(self, msg, img=None, reply=True, pin=False):
        reply_id = self.last_status_id() if reply and len(self.status) > 0 else None
        media_id = None
        if img:
            fileim = BytesIO()
            img.save(fileim, 'png')
            fileim.seek(0)
            media_id = self.api.media_post(fileim, mime_type='image/png').id
        tags = ''
        for tag in CONFIGS['sns']['hashtags']:
            tags += '\n#%s' % tag
        if tags:
            msg += '\n' + tags
        status = self.api.status_post(msg, in_reply_to_id=reply_id, media_ids=media_id)
        SnsStatus(status_id=status.id, sns_api=self.id)
        commit()
        if pin:
            self.pin(status.id)
        return status.id

    def pin(self, status_id, unpin_all=True):
        if unpin_all:
            self.unpin_all()
        self.api.status_pin(status_id)

    def unpin_all(self):
        user_id = self.api.account_verify_credentials().id
        for status in self.api.account_statuses(user_id, pinned=True):
            self.api.status_unpin(status.id)

    def poll(self, a, b, msg='', expires=CONFIGS['sns']['poll-duration']):
        poll = self.api.make_poll([a, b], expires)
        reply_id = self.last_status_id()
        tags = ''
        for tag in CONFIGS['sns']['hashtags']:
            tags += '\n#%s' % tag
        if tags:
            msg += '\n' + tags
        status = self.api.status_post(msg, in_reply_to_id=reply_id, poll=poll)
        SnsStatus(status_id=status.id, sns_api=self.id)
        return status.id


if __name__ == '__main__':
    from PIL import Image
    from data import init_db, db_session

    init_db('data/sns.db')
    with db_session:
        bot = RGBotToot.new()
        bot.post('ping', Image.open('devel/test-img.png'), pin=True)
