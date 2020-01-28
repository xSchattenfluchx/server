from server.players import Player
from typing import List


class PartyMember:
    def __init__(self, player: Player, ready: bool):
        self.player = player
        self.ready = ready
        self.factions = [False, False, False, False]

    def serialize(self):
        return {
            "id": self.player.id,
            "ready": self.ready,
            "factions": self.factions
        }
