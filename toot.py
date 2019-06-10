
import os
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
            print('\t[DummyMstdnApi]', args, kargs)
            return { 'id': randint(0, 999999999) }
        def make_poll(*args):
            return
    mstdn_api = DummyMstdnApi()

class TootRGB(SnsAPI):
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
        status = self.api.status_post(msg, in_reply_to_id=reply_id)
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
    from data import init_db, db_session
    init_db('sns.db')
    with db_session:
        bot = TootRGB.new()
        bot.post('ping')
