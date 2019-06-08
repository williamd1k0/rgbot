
import csv
from configparser import RawConfigParser
from datetime import datetime
from random import random, randint, seed
from pony.orm import *


def load_configs(path='data/config.ini'):
    conf = RawConfigParser()
    conf.read(path)
    gen = conf['GEN'] if 'GEN' in conf else {}
    battle = conf['BATTLE'] if 'BATTLE' in conf else {}
    return {
        'gen': {
            'hp': [int(n) for n in gen.get('HP', '30..40').split('..')],
            'ap': [int(n) for n in gen.get('AP', '21..30').split('..')],
            'moves': int(gen.get('moves', '4')),
        },
        'battle': {
            'critical-chance': float(battle.get('critical-chance', '20%').replace('%', ''))/100,
            'critical-factor': float(battle.get('critical-factor', '2x').replace('x', '')),
        }
    }

def load_moves_data(path='data/moves.csv'):
    moves = {}
    with open(path, 'r', encoding='utf-8') as data:
        csv_data = csv.DictReader(data)
        for row in csv_data:
            moves[row['name']] = [
                int(row['damage']), int(row['cost']), row['message']
            ]
    data.close()
    return moves

def load_messages_data(path='data/messages.csv'):
    msgs = {}
    with open(path, 'r', encoding='utf-8') as data:
        csv_data = csv.DictReader(data)
        for row in csv_data:
            msgs[row['key']] = row['message']
    data.close()
    return msgs

def load_canon_roosters(path='data/roosters-canon.csv'):
    roosters = []
    with open(path, 'r', encoding='utf-8') as data:
        csv_data = csv.DictReader(data)
        for row in csv_data:
            roosters.append([row['name'], row['image']])
    data.close()
    return roosters

CONFIGS = load_configs()
CANON_ROOSTERS = load_canon_roosters()
ROOSTER_MOVES = load_moves_data()
TURN_MSG = load_messages_data()
db = Database()

class Rooster(db.Entity):
    id = PrimaryKey(int, auto=True)
    created = Optional(datetime, default=lambda: datetime.now())
    name = Optional(str, unique=True, default='Unnamed')
    sprite = Optional(str)
    HP = Required(int, default=0)
    AP = Required(int, default=0)
    hp = 0
    ap = 0
    moves = Set('Move')
    battles = Set('Battle', reverse='roosters')
    victories = Set('Battle', reverse='winner')

    @classmethod
    def init_canon(cls):
        for r in CANON_ROOSTERS:
            if cls.get(name=r[0]): continue
            data = {
                'name': r[0],
                'sprite': r[1],
                'HP': randint(*CONFIGS['gen']['hp']),
                'AP': randint(*CONFIGS['gen']['ap']),
                'moves': Move.select().random(CONFIGS['gen']['moves'])
            }
            cls(**data)
        commit()

    @classmethod
    def generate(cls, key=0, regen=False):
        seed()
        key = key or randint(0, len(CANON_ROOSTERS)-1)
        gen = cls.get(id=key)
        seed(key)
        if gen:
            if regen:
                gen.HP = randint(*CONFIGS['gen']['hp'])
                gen.AP = randint(*CONFIGS['gen']['ap'])
                gen.moves.clear()
                gen.moves.add(Move.select().random(CONFIGS['gen']['moves']))
                commit()
            gen.reset()
            return gen
        data = {
            'id': key,
            'name': CANON_ROOSTERS[key][0],
            'HP': randint(*CONFIGS['gen']['hp']),
            'AP': randint(*CONFIGS['gen']['ap']),
            'moves': Move.select().random(CONFIGS['gen']['moves'])
        }
        gen = cls(**data)
        commit()
        gen.reset()
        return gen

    def reset(self):
        self.revive()
        self.replenish()

    def replenish(self):
        self.ap = self.AP
    
    def revive(self):
        self.hp = self.HP

    def damage(self, d):
        self.hp -= d

    def attack(self, move):
        self.ap -= move.cost

    def is_dead(self):
        return self.hp <= 0


class Move(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str, default='Unnamed')
    damage = Required(int, default=0)
    cost = Required(int, default=0)
    roosters = Set(Rooster)
    msg = Optional(str, default='{a} -> {b}')

    @classmethod
    def import_data(cls):
        for k, mv in ROOSTER_MOVES.items():
            move = cls.get(name=k)
            if move:
                move.damage = mv[0]
                move.cost = mv[1]
            else:
                move = cls(name=k, damage=mv[0], cost=mv[1])
            move.msg = mv[2]
        commit()

class Battle(db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Optional(datetime, default=lambda: datetime.now())
    roosters = Set(Rooster, reverse='battles')
    winner = Optional(Rooster, reverse='victories')
    turns = Set('Turn')

    @classmethod
    def new(cls, roosters):
        for rt in roosters:
            rt.reset()
        bt = cls(roosters=roosters)
        commit()
        return bt

    @classmethod
    def get_turn_count(cls):
        return [len(t.turns) for t in cls.select()]

    def ko(self, winner):
        self.winner = winner
        commit()

class Turn(db.Entity):
    id = PrimaryKey(int, auto=True)
    which = Required(int)
    info = Optional(Json)
    battle = Optional(Battle)

