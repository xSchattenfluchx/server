from server.players import Player


class PlayerParty:
    def __init__(self, team_matchmaking_service: "TeamMatchmakingService", owner: Player):
        self.team_matchmaking_service = team_matchmaking_service
        self._members = {owner}
        self.owner = owner

    @property
    def members(self):
        return frozenset(self._members)

    def add_player(self, player: Player):
        self._members.add(player)
        self.team_matchmaking_service.player_parties[player] = self

        self.broadcastParty()

    def remove_player(self, player: Player):
        self._members.remove(player)
        self.team_matchmaking_service.player_parties.pop(player)

        self.broadcastParty()
        self.sendParty(player)

    def broadcastParty(self):
        for player in self._members:
            self.sendParty(player)

    def sendParty(self, player: Player):
        player.lobby_connection.send({
            "command": "update_party",
            "owner": self.owner,
            "members": {m.id for m in self._members}
        })

    def isDisbanded(self) -> bool:
        return len(self._members) <= 1 or self.owner not in self._members

    def disband(self):
        for member in self.members:
            self.remove_player(member)
