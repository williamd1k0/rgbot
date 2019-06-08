
import os
from mastodon import Mastodon

TOKEN = os.environ.get('MSTDN_TOKEN')
URL = os.environ.get('MSTDN_URL')
mstdn = None

if TOKEN and URL:
    mstdn = Mastodon(access_token=TOKEN, api_base_url=URL)

class MstdnRGB(object):
    toots = None
    poll_ref = None

    def __init__(self, mstdn_api=mstdn):
        self.mstdn = mstdn_api
        self.toots = []

    def post(self, msg, img=None):
        reply_id = self.toots[-1] if len(self.toots) > 0 else None
        self.toots.append(self.mstdn.status_post(msg, in_reply_to_id=reply_id))

    def poll(self, a, b, expires=60*60):
        WINNER_MSG = 'Quem vai ganhar essa luta?'
        poll = self.mstdn.make_poll([a, b], expires)
        reply_id = self.toots[-1]['id']
        poll_ref = self.mstdn.status_post(WINNER_MSG, in_reply_to_id=reply_id, poll=poll)
        self.toots.append(poll_ref)

if __name__ == '__main__':
    a = "Galinho Tico Liro"
    b = "Galo Ciborgue do SENAI"
    bot = MstdnRGB(mstdn)
    bot.post('A luta de hoje é entre {a} e {b}! Preparem-se!'.format(a=a, b=b))
    bot.poll(a, b)
