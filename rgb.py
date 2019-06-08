
import os, sys, time
from random import seed, choice, random
from data import *
from mstdn import MstdnRGB

class BattleTurns(object):
    battle = None
    a = None
    b = None
    turn = 0

    def __init__(self, battle, seed=None):
        self.battle = battle
        self.a, self.b = tuple(battle.roosters.select())
        self.turn = count(t for t in Turn if t.battle == battle)

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
        data = []
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
            data.append(dt)
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
        move = current.moves.select().random(2)[0]
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
                dmg *= CONFIGS['battle']['critical-factor']
            else:
                yield 'ATK_HIT', current, other, move
            other.damage(dmg)
            yield 'DAMAGE', other, dmg
            if current.ap == 0:
                yield 'BONUS', current
            if other.is_dead():
                self.battle.ko(current)
                yield 'KO',


class SeasonManager(object):
    ACTIVE, NEW, DONE = range(3)
    TIMER, INPUT = range(2)
    mode = None
    current = None
    turns = None
    toot = None

    def __init__(self, mode=0, toot=False):
        self.mode = mode
        if toot:
            self.toot = MstdnRGB()
        with db_session:
            self.current = Season.last()

    def post_msg(self, msg, title=None, subtitle=''):
        if self.toot:
            self.toot.post(msg)
        if title:
            msg = '\n\t[%s] %s\n%s' % title, subtitle, msg
        print(msg)

    @db_session
    def loop(self):
        while True:
            state = self.check_state()
            if state == self.ACTIVE:
                if not self.turns or self.turns.is_done():
                    self.new_battle()
                else:
                    self.next_turn()
            elif state == self.NEW:
                self.new_season()
            elif state == self.DONE:
                self.season_done()
            sys.stdout.flush()
            if self.mode == self.TIMER:
                time.sleep(CONFIGS['battle']['event-interval'])
            elif self.mode == self.INPUT:
                input()
                os.system('cls')
                os.system('clear')

    def new_battle(self):
        # TODO: rooster selection stuff
        roosters = Rooster.select().random(2)
        self.turns = BattleTurns(Battle.new(roosters))
        self.post_msg(self.turns.msg('new'))
        self.post_msg(self.turns.msg('a-stats'))
        self.post_msg(self.turns.msg('b-stats'))
        if self.toot:
            self.toot.poll(*[r.name for r in roosters])

    def recover_battle(self):
        # TODO?
        rec = Battle.select().sort_by(-1).first()
        if not rec or rec.winner:
            return
        return BattleTurns(rec)

    def next_turn(self):
        states = self.turns.next()
        for s in states:
            key = s[0]
            args = s[1:]
            if key == 'KO':
                done = True
            if len(args) == 1:
                args = args[0]
            self.post_msg(self.turns.msg(key, args))

    def check_state(self):
        if not self.current:
            return self.NEW
        if self.current.is_done():
            return self.DONE
        return self.ACTIVE

    def season_done(self):
        self.post_msg('A temporada %s terminou! O grande vencedor foi {winner #TODO}!')
        self.current = None

    def new_season(self):
        self.current = Season()
        commit()
        self.post_msg('A temporada %s irá começar!' % self.current.id)


def main(args):
    init_db(args.db)
    mode = SeasonManager.TIMER if args.timer else SeasonManager.INPUT
    man = SeasonManager(mode, args.toot)
    man.loop()


if __name__ == '__main__':
    from argparse import ArgumentParser
    argp = ArgumentParser('rgb', description='Rinha de Galo BOT')
    argp.add_argument('-t', '--timer', action='store_true', help='use interval timer mode instead of user input mode')
    argp.add_argument('-T', '--toot', action='store_true', help='enable Mastodon posts')
    argp.add_argument('-d', '--db', type=str, default='data/rgb.db', metavar='*.db', help='set database file')
    main(argp.parse_args())
