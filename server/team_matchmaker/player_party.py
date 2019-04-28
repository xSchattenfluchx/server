from server.players import Player


class PlayerParty:
    def __init__(self, owner: Player):
        self._members = {owner}
        self.owner = owner

    @property
    def members(self):
        return frozenset(self._members)

    def add_player(self, player: Player):
        self._members.add(player)

        self.broadcast_party()

    def remove_player(self, player: Player):
        self._members.remove(player)

        self.broadcast_party()
        self.send_party(player)

    def broadcast_party(self):
        for player in self.members:
            self.send_party(player)

    def send_party(self, player: Player):
        player.lobby_connection.send({
            "command": "update_party",
            "owner": self.owner,
            "members": [m.id for m in self.members]
        })

    def is_disbanded(self) -> bool:
        return self.owner not in self.members

    def disband(self):
        members = self.members

        self._members = set()

        for member in members:
            self.send_party(member)
