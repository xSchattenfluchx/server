from server.players import Player


class PlayerParty:
    members: set[Player]
    owner: Player

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

        self.broadcast_party()

    def remove_player(self, player: Player):
        self.__remove_player_without_broadcast(player)

        self.broadcast_party()
        self.send_party(player)

    def __remove_player_without_broadcast(self, player: Player):
        self._members.remove(player)
        self.team_matchmaking_service.player_parties.pop(player)

    def broadcast_party(self):
        for player in self._members:
            self.send_party(player)

    def send_party(self, player: Player):
        player.lobby_connection.send({
            "command": "update_party",
            "owner": self.owner,
            "members": {m.id for m in self._members}
        })

    def is_disbanded(self) -> bool:
        return self.owner not in self._members

    def disband(self):
        for member in self.members:
            self.__remove_player_without_broadcast(member)
        for member in self.members:
            self.send_party(member)
