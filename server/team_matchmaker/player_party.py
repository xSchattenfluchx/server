from server.players import Player
from server.team_matchmaker import PartyMember

class PlayerParty:
    def __init__(self, owner: Player):
        self._members = {PartyMember(owner, False)}
        self.owner = owner

    @property
    def members(self):
        return frozenset(self._members)

    @property
    def is_ready(self):
        return all(member.ready for member in self._members)

    def get_member_by_player(self, player: Player):
        return next([member for member in self._members if member.player == player])

    def add_player(self, player: Player):
        self._members.add(PartyMember(player))

        self.broadcast_party()

    def remove_player(self, player: Player):
        self._members = list(filter(lambda m: m.player != player, self._members))

        self.broadcast_party()
        self.send_party(player)

    def ready_player(self, player: Player):
        for member in [m for m in self._members if m.player == player]:
            member.ready = True

        self.broadcast_party()

    def unready_player(self, player: Player):
        for member in [m for m in self._members if m.player == player]:
            member.ready = False

        self.broadcast_party()

    def broadcast_party(self):
        for member in self.members:
            self.send_party(member.player)

    def send_party(self, player: Player):
        player.send_message({
            "command": "update_party",
            "owner": self.owner.id,
            "members": [m.serialize() for m in self._members]
        })

    def is_disbanded(self) -> bool:
        return not any([m.player == self.owner for m in self._members])

    def disband(self):
        members = self.members

        self._members = set()

        for member in members:
            self.send_party(member.player)
