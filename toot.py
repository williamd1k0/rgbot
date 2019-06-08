
import os
from mastodon import Mastodon

TOKEN = os.environ.get('MSTDN_TOKEN')
URL = os.environ.get('MSTDN_URL')
mstdn_api = None

if TOKEN and URL:
    mstdn_api = Mastodon(access_token=TOKEN, api_base_url=URL)

class TootRGB(object):
    api = None
    status = None
    poll_ref = None

    def __init__(self, mstdn_api=mstdn_api):
        self.api = mstdn_api
        self.status = []

    def post(self, msg, img=None):
        reply_id = self.status[-1]['id'] if len(self.status) > 0 else None
        self.status.append(self.api.status_post(msg, in_reply_to_id=reply_id))

    def poll(self, a, b, msg='', expires=60*60):
        poll = self.api.make_poll([a, b], expires)
        reply_id = self.status[-1]['id']
        poll_ref = self.api.status_post(msg, in_reply_to_id=reply_id, poll=poll)
        self.status.append(poll_ref)

if __name__ == '__main__':
    bot = TootRGB()
    bot.post('ping')
