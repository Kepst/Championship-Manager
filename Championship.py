from abc import ABCMeta, abstractmethod

import random
import networkx as nx
import itertools
from collections import defaultdict
import pickle
import sqlite3

class Championship(metaclass=ABCMeta):
    def __init__(self, win_points=3, draw_points=1, lose_points=0):
        self.player_num = 0
        self.players = {}
        self.active = []
        self.removed = []
        self.matches = []
        self.pairings = []
        self.round = 0
        self.results = {}
        self.win_points = win_points
        self.draw_points = draw_points
        self.lose_points = lose_points
        self.champ_id = 0
        self.finished = False

    def add_player(self, player, number=None):
        """
        Adds player to this championship
        """
        self.player_num += 1
        self.players[player] = {"Name": player, "Number": number, "score": 0}
        self.active.append(player)

    def remove_player(self, player):
        """
        Removes a player from the available players on this championship
        :param player:
        :return:
        """
        self.player_num -= 1
        self.active.remove(player)
        self.removed.append(player)

    def show_players(self):
        """
        Show all players, including removed
        """
        for player in self.players:
            for key in self.players[player]:
                print(key, self.players[player][key], end='\t')
            print()

    def show_active_players(self):
        for player in self.active:
            for key in self.players[player]:
                print(key, self.players[player][key], end='\t')
            print()

    def show_removed_players(self):
        for player in self.removed:
            for key in self.players[player]:
                print(key, self.players[player][key], end='\t')
            print()

    @abstractmethod
    def next_round(self):
        pass

    def match_result(self, p1, p2, score):
        self.results[self.round].append((p1, p2, score))
        self.matches.append((p1, p2))
        if score[0] > score[1]:
            self.players[p1]["score"] += self.win_points
            self.players[p2]["score"] += self.lose_points
        elif score[0] < score[1]:
            self.players[p1]["score"] += self.lose_points
            self.players[p2]["score"] += self.win_points
        else:
            self.players[p1]["score"] += self.draw_points
            self.players[p2]["score"] += self.draw_points

    def get_result(self):
        result = []
        for player in self.players:
            result.append((player, self.players[player]["score"]))
        
        result = sorted(result, key=lambda tup: -tup[1])
        return result


class SingleElimination(Championship):
    def __init__(self):
        super().__init__()
        self.champ_type = "SingleElimination"

    def next_round(self):
        pairings = []
        if self.round == 0:
            random.shuffle(self.active)
            for p1, p2 in zip(self.active[::2], self.active[1::2]):
                pairings.append((p1, p2))
        else:
            dropped = []
            for (p1, p2, score) in self.results[self.round]:
                if score[0] > score[1]:
                    dropped.append(p2)
                else:
                    dropped.append(p1)
            for player in dropped:
                self.remove_player(player)
            for p1, p2 in zip(self.active[::2], self.active[1::2]):
                pairings.append((p1, p2))
        self.round += 1
        self.results[self.round] = []
        self.pairings = pairings


class Swiss(Championship):
    def __init__(self):
        super().__init__()
        self.champ_type = "Swiss"

    def next_round(self):
        G = nx.Graph()
        G.add_nodes_from(self.players)
        for p1, p2 in itertools.combinations(self.players, 2):
            if not ((p1, p2) in self.matches or (p2, p1) in self.matches):
                score_diff = abs(self.players[p1]["score"] - self.players[p2]["score"])
                G.add_edge(p1, p2, weight=score_diff)
        pairings = nx.max_weight_matching(G, True)
        
        pairings = list(pairings)
        self.round += 1
        self.results[self.round] = []
        self.pairings = pairings


def createDB():
    conn = sqlite3.connect("champ.db")
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS champs")
    c.execute("DROP TABLE IF EXISTS players")
    c.execute("CREATE TABLE IF NOT EXISTS players (player_id INTEGER PRIMARY KEY AUTOINCREMENT, player_name TEXT NOT NULL, password TEXT NOT NULL, email TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS champs (champ_id INTEGER PRIMARY KEY AUTOINCREMENT, champ_type TEXT NOT NULL, champ_data BLOB NOT NULL, owner INTEGER, FOREIGN KEY(owner) REFERENCES players(player_id))")
    conn.commit()
    conn.close()


def save_champ(champ):
    # initiate database connection
    conn = sqlite3.connect("champ.db")
    c = conn.cursor()

    champ_data = pickle.dumps(champ.__dict__)
    champ_id = champ.champ_id
    # saves to SQLite database, with key champ_id and type blob, and on another database with the type

    c.execute("UPDATE champs SET champ_data=? WHERE champ_id=?", (champ_data, champ_id))
    conn.commit()
    conn.close()

def load_champ(champ_id):
    # initiate database connection
    conn = sqlite3.connect("champ.db")
    c = conn.cursor()
    c.execute("SELECT * FROM champs WHERE champ_id=?", (champ_id,))

    data = c.fetchone()
    if data is None:
        return None
    
    champ_id, champ_type, champ_data = data
    conn.close()

    champ_data = pickle.loads(champ_data)

    if champ_type == "Swiss":
        champ = Swiss()
        champ.__dict__ = champ_data
    if champ_type == "SingleElimination":
        champ = SingleElimination()
        champ.__dict__ = champ_data
    return champ

def createChamp(champ_type:str):
    if champ_type == "Swiss":
        champ = Swiss()
    elif champ_type == "SingleElimination":
        champ = SingleElimination()
    # initiate database connection
    conn = sqlite3.connect("champ.db")
    c = conn.cursor()

    champ_data = pickle.dumps(champ.__dict__)
    c.execute("INSERT INTO champs (champ_type, champ_data) VALUES (?, ?)", (champ_type, champ_data))
    champ_id = c.lastrowid
    champ.champ_id = champ_id
    conn.commit()
    conn.close()
    
    return champ, champ_id

def createUser(name, password, email):
    conn = sqlite3.connect("champ.db")
    c = conn.cursor()
    c.execute("INSERT INTO players (player_name, password, email) VALUES (?, ?, ?)", (name, password, email))
    conn.commit()
    c.execute("SELECT * FROM players WHERE player_id=?", (c.lastrowid,))
    result = c.fetchone()
    conn.close()
    return result

createDB()