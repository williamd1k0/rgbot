
import os, sys, time
import tkimg
import imgen
from enum import IntEnum
from random import choice, random
from data import *
from toot import RGBotToot
from tweet import RGBotTweet


class BattleTurns(object):
    battle = None
    a = None
    b = None
    turn = 0
    toot = None
    tweet = None

    def __init__(self, battle):
        self.battle = battle
        self.a, self.b = battle.roosters.select()
        self.turn = battle.turns.count()

    def is_done(self):
        return bool(self.battle.winner)

    def msg(self, key, var=None):
        key = key.upper().replace('-', '_')
        if key == 'NEW':
            roosters = {
               'a': self.a.name,
               'b': self.b.name,
            }
            return TURN_MSG['NEW'].format(**roosters)
        elif 'STATS' in key:
            rt = None
            if key == 'A_STATS':
                rt = self.a
            elif key == 'B_STATS':
                rt = self.b
            args = {
                'rt': rt.name,
                'hp': rt.HP,
                'ap': rt.AP,
                'mv': [mv.name for mv in rt.moves.select()]
            }
            return TURN_MSG[key].format(**args)
        elif key == 'REPLENISHED':
            # var is Rooster
            return TURN_MSG['REPLENISHED'].format(a=var.name)
        elif key in ('ATK_HIT', 'ATK_FAIL', 'ATK_CRITICAL'):
            # var is [Rooster, Rooster, Move]
            return (var[2].msg+TURN_MSG[key]).format(a=var[0].name, b=var[1].name)
        elif key == 'DAMAGE':
            # var is [Rooster, int]
            return TURN_MSG[key].format(b=var[0].name, x=var[1])
        elif key == 'BONUS':
            # var is Rooster
            return TURN_MSG[key].format(a=var.name)
        elif key == 'KO':
            if self.a == self.battle.winner:
                a = self.a.name
                b = self.b.name
            else:
                a = self.b.name
                b = self.a.name
            return TURN_MSG[key].format(a=a, b=b)
    
    def serialize_info(self, info):
        data = { 'states': [] }
        for inf in info:
            dt = {
                'type': inf[0],
                'info': []
            }
            args = inf[1:]
            for arg in args:
                if isinstance(arg, Rooster) or isinstance(arg, Move):
                    dt['info'].append(arg.name)
                else:
                    dt['info'].append(arg)
            data['states'].append(dt)
        return data

    def next(self):
        result = list(self._next())
        self.battle.turns.create(which=self.turn, info=self.serialize_info(result))
        commit()
        return result

    def _next(self):
        self.turn += 1
        print('\n\t[Turno {0}] {a.name}({a.hp}/{a.ap}) vs ({b.hp}/{b.ap}){b.name}\n'.format(self.turn, a=self.a, b=self.b))
        both = [self.a, self.b]
        current = choice(both)
        other = both[0] if both.index(current) == 1 else both[1]
        if current.ap < 0:
            current.replenish()
            yield 'REPLENISHED', current
            return
        move = choice(tuple(current.moves.select()))
        if move.cost > current.ap:
            current.attack(move)
            yield 'ATK_FAIL', current, other, move
            return
        else:
            dmg = move.damage
            current.attack(move)
            critical = random() <= CONFIGS['battle']['critical-chance']
            if critical:
                yield 'ATK_CRITICAL', current, other, move
                dmg = int(dmg*CONFIGS['battle']['critical-factor'])
            else:
                yield 'ATK_HIT', current, other, move
            other.damage(dmg)
            yield 'DAMAGE', other, dmg
            if current.ap == 0:
                current.replenish()
                yield 'BONUS', current
            if other.is_dead():
                self.battle.ko(current)
                yield 'KO',


class InteractionMode(IntEnum):
    INPUT, WAIT, ONE_SHOT = range(3)

    @classmethod
    def from_args(cls, args):
        return cls.WAIT if args.wait else cls.ONE_SHOT if args.one_shot else cls.INPUT

class SeasonManager(object):
    ACTIVE, NEW, DONE = range(3)
    mode = None
    current = None
    turns = None
    toot = None
    tweet = None
    tk = False

    @db_session
    def __init__(self, mode=InteractionMode.INPUT, tweet=False, toot=False, tk_debug=False):
        self.mode = mode
        if toot:
            self.toot = RGBotToot.new()
        if tweet:
            self.tweet = TweetRGB.new()
        with db_session:
            self.current = Season.last()
        if tk_debug:
            self.tk = tk_debug
            tkimg.init_tk()

    def post_msg(self, msg, img=None, title=None, subtitle='', battle=True, reply=True):
        toot = self.get_toot(battle)
        if toot:
            toot.post(msg, img, reply=reply)
        tweet = self.get_tweet(battle)
        if tweet:
            tweet.post(msg, img, reply=reply)
        if title:
            msg = '\n\t[%s] %s\n%s' % title, subtitle, msg
        print(msg)
        if self.tk and img:
            tkimg.show_img(img)
            self.interaction(5)

    def get_toot(self, battle=True):
        return self.toot if not battle else self.turns.toot if self.turns else None

    def get_tweet(self, battle=True):
        return self.tweet if not battle else self.turns.tweet if self.turns else None

    @db_session
    def loop(self):
        while True:
            state = self.check_state()
            if state == self.ACTIVE:
                if not self.turns:
                    self.recover_battle()
                if not self.turns or self.turns.is_done():
                    self.new_battle()
                else:
                    self.next_turn()
            elif state == self.NEW:
                self.new_season()
            elif state == self.DONE:
                self.season_done()
            sys.stdout.flush()
            self.interaction()

    def interaction(self, override_time=None):
        if self.mode == InteractionMode.WAIT:
            t = override_time if override_time else CONFIGS['battle']['event-interval']
            time.sleep(t)
        elif self.mode == InteractionMode.INPUT:
            input()
            os.system('cls')
            os.system('clear')
        elif self.mode == InteractionMode.ONE_SHOT:
            if self.tk:
                input()
            sys.exit(0)

    def new_battle(self):
        # TODO: rooster selection stuff
        roosters = Rooster.select().random(2)
        battle = Battle.new(roosters)
        self.turns = BattleTurns(battle)
        if self.toot:
            self.turns.toot = RGBotToot.new(battle)
        if self.tweet:
            self.turns.tweet = RGBotTweet.new(battle)
        self.post_msg(self.turns.msg('new'), imgen.create_battle(self.turns.a, self.turns.b))

        self.post_msg(self.turns.msg('a-stats'), imgen.create_highlight(self.turns.a, self.turns.b, self.turns.a))
        self.post_msg(self.turns.msg('b-stats'), imgen.create_highlight(self.turns.a, self.turns.b, self.turns.b))

        poll_msg = TURN_MSG['POLL']
        if self.toot:
            self.get_toot().poll(*[r.name for r in roosters], poll_msg, CONFIGS['battle']['poll-duration'])
        # if self.tweet:
        #     self.get_tweet().poll(*[r.name for r in roosters], poll_msg, CONFIGS['battle']['poll-duration'])

    def recover_battle(self):
        bt = Battle.last_battle()
        if not bt or bt.winner:
            return
        self.turns = BattleTurns(bt)
        if self.toot:
            self.turns.toot = RGBotToot.get(battle=bt)
            self.turns.toot.set_api()
        if self.tweet:
            self.turns.tweet = RGBotTweet.get(battle=bt)
            self.turns.tweet.set_api()

    def recover_sns_status(self):
        if self.toot:
            self.toot

    def next_turn(self):
        # Helper info
        # REPLENISHED, ATK_FAIL, ATK_CRITICAL, ATK_HIT, DAMAGE, BONUS, KO
        # create_highlight(a:Rooster, b:Rooster, highlight=None)
        # create_battle_hit(a:Rooster, b:Rooster, hit=None, hit_type=None, attack=None, done=False)
        states = self.turns.next()
        done = False
        hit = None
        hit_type = None
        attack = None
        attack_msg = ''
        a, b = self.turns.a, self.turns.b
        hit_types = {
            'ATK_FAIL': imgen.HitType.FAIL,
            'ATK_HIT': imgen.HitType.HIT,
            'ATK_CRITICAL': imgen.HitType.CRITICAL,
        }
        all_keys = [state[0] for state in states]
        for s in states:
            key = s[0]
            args = s[1:]
            if len(args) == 1:
                args = args[0]
            if key == 'REPLENISHED':
                msg = self.turns.msg(key, args)
                im = imgen.create_highlight(a, b, highlight=args)
                self.post_msg(msg, im)
            elif key in ('ATK_FAIL', 'ATK_HIT', 'ATK_CRITICAL'):
                attack = args[2]
                hit = args[1]
                hit_type = hit_types[key]
                attack_msg += self.turns.msg(key, args) + '\n'
            elif key == 'DAMAGE':
                attack_msg += self.turns.msg(key, args) + '\n'
            elif key == 'BONUS' and not 'KO' in all_keys:
                # Ignore Bonus msg in the last turn
                attack_msg += self.turns.msg(key, args) + '\n'
            elif key == 'KO':
                done = True
                attack_msg += self.turns.msg(key, args) + '\n'
        if attack:
            im = imgen.create_battle_hit(a, b, hit=hit, hit_type=hit_type, attack=attack, done=done)
        if attack_msg:
            self.post_msg(attack_msg.strip(), im)

    def check_state(self):
        if not self.current:
            return self.NEW
        if self.current.is_done():
            return self.DONE
        return self.ACTIVE

    def season_done(self):
        winner = self.current.winner()
        if winner:
            self.post_msg(TURN_MSG['SEASON_FINALE'].format(t=self.current.id, win=winner.name), battle=False, reply=False)
        self.current = None

    def new_season(self):
        self.current = Season()
        Rooster.randomize()
        commit()
        self.post_msg(TURN_MSG['NEW_SEASON'].format(t=self.current.id), battle=False, reply=False)


def main(args):
    sql_debug(args.sqldebug)
    init_db(args.db, not args.clear, args.sqldebug)
    if args.clear:
        clear_db()
    else:
        mode = InteractionMode.from_args(args)
        man = SeasonManager(mode, args.tweet, args.toot, args.tk)
        man.loop()


if __name__ == '__main__':
    from argparse import ArgumentParser
    argp = ArgumentParser('rgbot', description='Rinha de Galo BOT')
    modearg = argp.add_mutually_exclusive_group()
    modearg.add_argument('-w', '--wait', action='store_true', help='use interval between events instead of user input')
    modearg.add_argument('-o', '--one-shot', action='store_true', help='execute next event and exit')
    argp.add_argument('-T', '--toot', action='store_true', help='enable Mastodon posts')
    argp.add_argument('-t', '--tweet', action='store_true', help='enable Twitter posts (no polls)')
    argp.add_argument('-k', '--tk', action='store_true', help='enable Tk for image debug')
    argp.add_argument('-d', '--db', type=str, default='data/rgb.db', metavar='*.db|postgres', help='set database file/provider')
    argp.add_argument('-D', '--sqldebug', action='store_true', help='enable SQL debug')
    argp.add_argument('-c', '--clear', action='store_true', help='clear database and exit')
    main(argp.parse_args())
