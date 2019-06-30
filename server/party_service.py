import time
from typing import NamedTuple, Optional

from .decorators import with_logger
from .game_service import GameService
from .lobbyconnection import ClientError
from .players import Player
from .team_matchmaker.player_party import PlayerParty

GroupInvite = NamedTuple('GroupInvite', [("sender", Player), ("recipient", Player), ("party", PlayerParty), ("created_at", float)])

PARTY_INVITE_TIMEOUT = 60 * 60 * 24  # secs


@with_logger
class PartyService:
    """
    Service responsible for managing the global team matchmaking. Does grouping, matchmaking, updates statistics, and
    launches the games.
    """

    def __init__(self, games_service: GameService):
        self.game_service = games_service
        self.player_parties: dict[Player, PlayerParty] = dict()
        self._pending_invites: dict[(Player, Player), GroupInvite] = dict()

    def get_party(self, owner: Player) -> Optional[PlayerParty]:
        self.player_parties.get(owner)

    def invite_player_to_party(self, sender: Player, recipient: Player):
        if sender not in self.player_parties:
            self.player_parties[sender] = PlayerParty(sender)

        party = self.player_parties[sender]

        if party.owner != sender:
            raise ClientError("You do not own this party.", recoverable=True)

        if sender.id in recipient.foes:
            raise ClientError("This person doesn't accept invites from you.", recoverable=True)

        self._pending_invites[(sender, recipient)] = GroupInvite(sender, recipient, party, time.time())
        recipient.send_message({
            "command": "party_invite",
            "sender": sender.id
        })

    def accept_invite(self, recipient: Player, sender: Player):
        if (sender, recipient) not in self._pending_invites:
            raise ClientError("You're not invited to a party", recoverable=True)

        if recipient in self.player_parties:
            raise ClientError("You're already in a party", recoverable=True)

        pending_invite = self._pending_invites.pop((sender, recipient))

        if pending_invite.party != self.player_parties.get(sender):
            recipient.send_message({'command': 'party_disbanded'})
            return

        self.player_parties[recipient] = pending_invite.party
        pending_invite.party.add_player(recipient)

        self.remove_disbanded_parties()

    def kick_player_from_party(self, owner: Player, kicked_player: Player):
        if owner not in self.player_parties:
            raise ClientError("You're not in a party.", recoverable=True)

        party = self.player_parties[owner]

        if party.owner != owner:
            raise ClientError("You do not own that party.", recoverable=True)

        if kicked_player not in party.members:
            # Ensure client state is up to date
            party.send_party(owner)
            return

        party.remove_player(kicked_player)
        kicked_player.send_message({"command": "kicked_from_party"})

    def leave_party(self, player: Player):
        if player not in self.player_parties:
            raise ClientError("You are not in a party.", recoverable=True)

        self.player_parties[player].remove_player(player)
        self.player_parties.pop(player)

        self.remove_disbanded_parties()

    def ready_player(self, player: Player):
        if player not in self.player_parties:
            raise ClientError("You are not in a party.", recoverable=True)

        party = self.player_parties[player]

        if player in party.members_ready:
            # Ensure client state is up to date
            party.send_party(player)
            return

        party.ready_player(player)

    def unready_player(self, player: Player):
        if player not in self.player_parties:
            raise ClientError("You are not in a party.", recoverable=True)

        party = self.player_parties[player]

        if player not in party.members_ready:
            # Ensure client state is up to date
            party.send_party(player)
            return

        party.unready_player(player)

    def clear_invites(self):
        invites = filter(
            lambda inv: time.time() - inv.created_at >= PARTY_INVITE_TIMEOUT or
            inv.sender not in self.player_parties,
            self._pending_invites.values()
        )

        for invite in list(invites):
            self._pending_invites.pop((invite.sender, invite.recipient))

    def remove_party(self, party):
        # Remove all players who were in the party
        party_members = map(
            lambda i: i[0],
            filter(
                lambda i: party == i[1],
                self.player_parties.items()
            )
        )
        for player in list(party_members):
            self.player_parties.pop(player)

        # Remove all invites to the party
        invites = filter(
            lambda inv: inv.party == party,
            self._pending_invites.values()
        )
        for invite in list(invites):
            self._pending_invites.pop((invite.sender, invite.recipient))

        party.disband()

    def remove_disbanded_parties(self):
        disbanded_parties = filter(
            lambda party: party.is_disbanded(),
            self.player_parties.values()
        )

        for party in list(disbanded_parties):
            # This will call disband again therefore removing all players and informing them
            self.remove_party(party)

        self.clear_invites()

    def on_player_disconnected(self, player):
        if player in self.player_parties:
            self.leave_party(player)
