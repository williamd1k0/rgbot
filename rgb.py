
import os
from random import seed, choice, random
from data import *
from mstdn import MstdnRGB

class BattleTurns(object):
    battle = None
    a = None
    b = None
    turn = 0
    seed = None
    last_winner = None
    toot = None
    toot_enabled = False

    def __init__(self, battle, seed=None, toot=False):
        self.battle = battle
        roosters = tuple(battle.roosters.select())
        self.a = roosters[0]
        self.b = roosters[1]
        self.seed = seed
        self.toot_enabled = toot

    def start(self):
        seed(self.seed)
        if self.toot_enabled:
            self.toot = MstdnRGB()
        self.post_msg(self.msg('new'))
        self.post_msg(self.msg('a-stats'))
        self.post_msg(self.msg('b-stats'))
        if self.toot_enabled:
            self.toot.poll(self.a.name, self.b.name)

    def post_msg(self, msg, title=None, subtitle=''):
        if self.toot_enabled:
            self.toot.post(msg)
        if title:
            msg = '\n\t[%s] %s\n%s' % title, subtitle, msg
        print(msg)

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

    def next_msg(self):
        done = False
        states = self.next()
        for s in states:
            key = s[0]
            args = s[1:]
            if key == 'KO':
                done = True
            if len(args) == 1:
                args = args[0]
            self.post_msg(self.msg(key, args))
        return done


def init_db(db_file=':memory:'):
    db.bind(provider='sqlite', filename=db_file, create_db=True)
    db.generate_mapping(create_tables=True)
    with db_session:
        Move.import_data()

def gen_test_data():
    with db_session:
        for i in range(len(ROOSTER_NAMES)):
            Rooster.generate(i)

def clear():
    os.system('cls')
    os.system('clear')

def test():
    import sys

    clear()
    init_db('.test.db')
    gen_test_data()
    with db_session:
        turns= BattleTurns(Battle.new(Rooster.select().random(2)), toot='--toot' in sys.argv)
        turns.start()
        if not '-y' in sys.argv:
            input()
            clear()
        while not turns.next_msg():
            if not '-y' in sys.argv:
                input()
                clear()

if __name__ == '__main__':
    test()
