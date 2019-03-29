from typing import NamedTuple

from server import GameService
from server.decorators import with_logger
from server.lobbyconnection import ClientError
from server.players import Player
from server.team_matchmaker.player_party import PlayerParty

MapDescription = NamedTuple('Map', [("id", int), ("name", str), ("path", str)])
GroupInvite = NamedTuple('GroupInvite', [("inviting", Player), ("invited", Player), ("party", PlayerParty)])


@with_logger
class TeamMatchmakingService:
    """
    Service responsible for managing the global team matchmaking. Does grouping, matchmaking, updates statistics, and
    launches the games.
    """

    def __init__(self, games_service: GameService):
        self.game_service = games_service
        self.player_parties = dict() # player -> current party
        self._pending_invites = dict() # invited player -> current pending invite to this player

    def invite_player_to_group(self, inviting_player: Player, invited_player: Player):
        if inviting_player not in self.player_parties:
            self.player_parties[inviting_player] = PlayerParty(self, inviting_player)

        inviting_party = self.player_parties.get(inviting_player)

        if not inviting_party.owner == inviting_player:
            raise ClientError("You do not own this party.", recoverable=True)

        if inviting_player not in invited_player.friends:
            raise ClientError("This person hasn't befriended you.", recoverable=True)

        self.clear_invites_to(invited_player)

        self._pending_invites.add(GroupInvite(inviting_player, invited_player, inviting_party))
        invited_player.lobby_connection.send({
            "command": "party_invite",
            "inviting_player": inviting_player.id
        })

    def accept_invite(self, accepting_player: Player, inviting_player: Player):
        if accepting_player not in self._pending_invites:
            raise ClientError("You're not invited to a party", recoverable=True)

        pending_invite = self._pending_invites.get(accepting_player)
        if pending_invite.inviting != inviting_player:
            raise ClientError("Please request a new invite to that party.", recoverable=True)

        if pending_invite.party not in self.player_parties:
            raise ClientError("The party you're trying to join doesn't exist anymore.", recoverable=True)

        if accepting_player in self._pending_invites:
            self._pending_invites.pop(accepting_player)

        pending_invite.party.add_player(accepting_player)

        self.remove_disbanded_parties()

    def kick_player_from_party(self, owner: Player, kicked_player: Player):
        if owner not in self.player_parties:
            raise ClientError("You're not in a party.", recoverable=True)

        party = self.player_parties.get(owner)

        if party.owner != owner:
            raise ClientError("You do not own that party.", recoverable=True)

        if kicked_player not in party.members:
            raise ClientError("The kicked player is not in your party.", recoverable=True)

        party.remove_player(kicked_player)

    def leave_party(self, player: Player):
        if player not in self.player_parties:
            raise ClientError("You are not in a party.", recoverable=True)

        self.player_parties.get(player).remove_player(player)
        self.remove_disbanded_parties()

    def clear_invites_to(self, player: Player):
        invites = {invite for invite in self._pending_invites if invite.invited == player}

        for invite in invites:
            self._pending_invites.pop(invite.invited)

    def remove_party(self, party):
        # party is removed from player_parties dict by disband() removing the key value pair for each player

        party_invites = {invite for invite in self._pending_invites if invite.party == party}
        for invite in party_invites:
            self._pending_invites.pop(invite.invited)

        party.disband()

    def remove_disbanded_parties(self):
        disbanded_parties = {party for party in self.player_parties if party.isDisbanded()}

        for party in disbanded_parties:
            self.remove_party(party)

    # - accept group invite:  client->server
    # - invite to group:  client->server
    # - kick from group:  client->server
    # - leave group:  client->server
    #
    # - group update:  server->client
    #
    #
    #
    #
    #
    #
    #
