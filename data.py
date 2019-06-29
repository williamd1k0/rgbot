
import csv, re, os
from configparser import RawConfigParser
from datetime import datetime
from random import random, randint, seed
from pony.orm import *


def load_configs(path='data/config.ini'):
    def parse_percent(p):
        return float(p.replace('%', ''))/100
    def parse_times(x):
        return float(x.replace('x', ''))
    def parse_range(r):
        return [int(n) for n in r.split('..')]
    def parse_seconds(t):
        t = t.strip()
        if 'h' in t:
            tm = t.split('h')
            if tm[1] == '':
                return int(tm[0])*60*60
            else:
                return int(tm[0])*60*60+int(tm[1].replace('min', ''))*60
        if 'min' in t:
            return int(t.replace('min', ''))*60
        return int(t.replace('s', ''))

    conf = RawConfigParser()
    conf.read(path)
    gen = conf['GEN'] if 'GEN' in conf else {}
    battle = conf['BATTLE'] if 'BATTLE' in conf else {}
    return {
        'gen': {
            'hp': parse_range(gen.get('HP', '30..40')),
            'ap': parse_range(gen.get('AP', '21..30')),
            'moves': int(gen.get('moves', '4')),
        },
        'battle': {
            'critical-chance': parse_percent(battle.get('critical-chance', '20%')),
            'critical-factor': parse_times(battle.get('critical-factor', '2x')),
            'season-duration': int(battle.get('season-duration', '10')),
            'event-interval': parse_seconds(battle.get('event-interval', '10min')),
            'poll-duration': parse_seconds(battle.get('poll-duration', '3h'))
        }
    }

def load_moves_data(path='data/moves.csv'):
    moves = []
    with open(path, 'r', encoding='utf-8') as data:
        csv_data = csv.DictReader(data)
        for row in csv_data:
            moves.append([
                row['name'], int(row['damage']), int(row['cost']), row['message']
            ])
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
            roosters.append([row['name'], row['image'], row['mask'] or 'distort-mask.png'])
    data.close()
    return roosters

CONFIGS = load_configs()
CANON_ROOSTERS = load_canon_roosters()
ROOSTER_MOVES = load_moves_data()
TURN_MSG = load_messages_data()
DB = Database()


class Rooster(DB.Entity):
    id = PrimaryKey(int, auto=True)
    created = Optional(datetime, default=lambda: datetime.now())
    name = Optional(str, unique=True, default='Unnamed')
    sprite = Optional(str)
    mask = Optional(str)
    HP = Required(int, column='hp_total', default=0)  # Total HP
    hp = Optional(int, column='hp_current')  # Current HP
    hp_prev = Optional(int, column='hp_prev')  # Previous HP
    AP = Required(int, column='ap_total', default=0)  # Total AP
    ap = Optional(int, column='ap_current')  # Current AP
    ap_prev = Optional(int, column='ap_prev')  # Previous AP
    is_canon = Optional(bool, default=False)
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
                'mask': r[2],
                'HP': randint(*CONFIGS['gen']['hp']),
                'AP': randint(*CONFIGS['gen']['ap']),
                'moves': Move.select().random(CONFIGS['gen']['moves']),
                'is_canon': True,
            }
            cls(**data)
        commit()

    @classmethod
    def randomize(cls):
        for rt in cls.select():
            cls.generate(rt.id, True)

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
        self.ap_prev = self.AP
        commit()
    
    def revive(self):
        self.hp = self.hp_prev = self.HP
        commit()

    def damage(self, d):
        self.ap_prev = self.ap
        self.hp_prev = self.hp
        self.hp -= int(d)
        commit()

    def attack(self, move):
        self.hp_prev = self.hp
        self.ap_prev = self.ap
        self.ap -= int(move.cost)
        commit()

    def is_dead(self):
        return self.hp <= 0


class Move(DB.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str, default='Unnamed')
    damage = Required(int, default=0)
    cost = Required(int, default=0)
    roosters = Set(Rooster)
    msg = Optional(str, default='{a} -> {b}')

    @classmethod
    def import_data(cls):
        for i, mv in enumerate(ROOSTER_MOVES):
            move = cls.get(id=i+1)
            if move:
                move.name = mv[0]
                move.damage = mv[1]
                move.cost = mv[2]
            else:
                move = cls(name=mv[0], damage=mv[1], cost=mv[2])
            move.msg = mv[3]
        commit()

class Battle(DB.Entity):
    id = PrimaryKey(int, auto=True)
    date = Optional(datetime, default=lambda: datetime.now())
    season = Required('Season')
    roosters = Set(Rooster, reverse='battles')
    winner = Optional(Rooster, reverse='victories')
    turns = Set('Turn')
    sns = Set('SnsAPI')

    @classmethod
    def new(cls, roosters):
        for rt in roosters:
            rt.reset()
        bt = cls(roosters=roosters, season=Season.last())
        commit()
        return bt

    @classmethod
    def get_turn_count(cls):
        return [len(t.turns) for t in cls.select()]

    @classmethod
    def last_battle(cls):
        return cls.select().sort_by(-1).first()

    def ko(self, winner):
        self.winner = winner
        commit()

    def last_turn(self):
        return select(t for t in Turn if t.battle==self).sort_by(-1).first()

class Turn(DB.Entity):
    id = PrimaryKey(int, auto=True)
    which = Required(int)
    info = Optional(Json)
    battle = Optional(Battle)

class Season(DB.Entity):
    id = PrimaryKey(int, auto=True)
    battles = Set(Battle)

    @classmethod
    def last(cls):
        return cls.select().sort_by(-1).first()

    def is_done(self):
        battles = select(b for b in Battle if b.season==self and b.winner)
        return battles.count() >= CONFIGS['battle']['season-duration']

    def winner(self):
        battles = select(b for b in Battle if b.season==self and b.winner)
        winners = select(b.winner for b in battles)
        winners_filtered = []
        for w in winners:
            wcount = count(b for b in battles if b.winner==w)
            winners_filtered.append([w, wcount])
        winners_sorted = sorted(winners_filtered, key=lambda w: w[1])
        # if winners_sorted[-1][1] != winners_sorted[-2][1]:
        return  winners_sorted[-1][0]


class SnsAPI(DB.Entity):
    id = PrimaryKey(int, auto=True)
    status = Set('SnsStatus')
    battle = Optional(Battle)

    def last_status_id(self):
        status = self.status.select().sort_by(-1).first()
        if status:
            return status.status_id

class SnsStatus(DB.Entity):
    id = PrimaryKey(int, auto=True)
    status_id = Optional(int, size=64)
    sns_api = Optional(SnsAPI)


def init_db(db_name=':memory:', import_data=True, debug=False):
    sql_debug(debug)
    if re.match(r':memory:|.*\.(db|sqlite)', db_name):
        DB.bind(provider='sqlite', filename=db_name, create_db=True)
    elif db_name == 'postgres':
        config = {
            'user': os.environ.get('RGB_DBUSER', ''),
            'password': os.environ.get('RGB_DBPASS', ''),
            'host': os.environ.get('RGB_DBHOST'),
            'port': os.environ.get('RGB_DBPORT'),
            'database': os.environ.get('RGB_DBNAME', ''),
        }
        DB.bind(provider='postgres', **config)
    else:
        raise Exception(db_name, NotImplemented)
    DB.generate_mapping(create_tables=True)
    if import_data:
        with db_session:
            Move.import_data()
            Rooster.init_canon()

def clear_db():
    DB.drop_all_tables(with_all_data=True)
    print('Database was successfully cleared.')
