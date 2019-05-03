from server.players import Player


class PlayerParty:
    def __init__(self, owner: Player):
        self._members = {owner}
        self._members_ready = set()
        self.owner = owner

    @property
    def members(self):
        return frozenset(self._members)

    @property
    def members_ready(self):
        return frozenset(self._members_ready)

    @property
    def is_ready(self):
        return self._members_ready == self._members

    def add_player(self, player: Player):
        self._members.add(player)

        self.broadcast_party()

    def remove_player(self, player: Player):
        self._members.remove(player)

        self.broadcast_party()
        self.send_party(player)

    def ready_player(self, player: Player):
        self._members_ready.add(player)

        self.broadcast_party()

    def unready_player(self, player: Player):
        self._members_ready.remove(player)

        self.broadcast_party()

    def broadcast_party(self):
        for player in self.members:
            self.send_party(player)

    def send_party(self, player: Player):
        player.send_message({
            "command": "update_party",
            "owner": self.owner.id,
            "members": [m.id for m in self.members],
            "members_ready": [m.id for m in self.members_ready]
        })

    def is_disbanded(self) -> bool:
        return self.owner not in self.members

    def disband(self):
        members = self.members

        self._members = set()

        for member in members:
            self.send_party(member)
