
import os
from io import BytesIO
from mastodon import Mastodon
from data import SnsAPI, SnsStatus, commit


TOKEN = os.environ.get('MSTDN_TOKEN')
URL = os.environ.get('MSTDN_URL')
mstdn_api = None

if TOKEN and URL:
    mstdn_api = Mastodon(access_token=TOKEN, api_base_url=URL)
else:
    from random import randint
    class DummyMstdnApi(object):
        def status_post(self, *args, **kargs):
            print('\t[DummyMstdnApi/status_post]', args, kargs)
            return { 'id': randint(0, 999999999) }
        def make_poll(self, *args):
            return
        def media_post(self, *args, **kargs):
            print('\t[DummyMstdnApi/media_post]', args, kargs)
            return { 'id': randint(0, 999999999) }
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

    def post(self, msg, img=None, reply=True):
        reply_id = self.last_status_id() if reply and len(self.status) > 0 else None
        media_id = None
        if img:
            fileim = BytesIO()
            img.save(fileim, 'png')
            fileim.seek(0)
            media_id = self.api.media_post(fileim, mime_type='image/png')['id']
        status = self.api.status_post(msg, in_reply_to_id=reply_id, media_ids=media_id)
        SnsStatus(status_id=status['id'], sns_api=self.id)
        commit()
        return status['id']

    def poll(self, a, b, msg='', expires=60*60):
        poll = self.api.make_poll([a, b], expires)
        reply_id = self.last_status_id()
        status = self.api.status_post(msg, in_reply_to_id=reply_id, poll=poll)
        SnsStatus(status_id=status['id'], sns_api=self.id)
        return status['id']

if __name__ == '__main__':
    from PIL import Image
    from data import init_db, db_session

    init_db('data/sns.db')
    with db_session:
        bot = RGBotToot.new()
        bot.post('ping', Image.open('devel/test-img.png'))
