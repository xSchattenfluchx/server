import mock
import pytest
from pytest import fixture
from server.lobbyconnection import ClientError
from server.players import Player
from server.party_service import PartyService
from server.team_matchmaker import PlayerParty


@fixture
def party_service(game_service):
    return PartyService(game_service)


def MockPlayer(id) -> Player:
    player = mock.create_autospec(Player)
    player.id = id
    player.foes = {}
    return player


def test_invite_player_to_party(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)


def test_invite_foe_to_party(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)
    receiver.foes = {1}

    with pytest.raises(ClientError):
        party_service.invite_player_to_party(sender, receiver)


def test_accept_invite(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    assert party_service.player_parties[sender].members == {sender}

    party_service.accept_invite(receiver, sender)
    assert party_service.player_parties[sender].members == {sender, receiver}


def test_accept_invite_nonexistent(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    with pytest.raises(ClientError):
        party_service.accept_invite(receiver, sender)


def test_accept_invite_two_invites(party_service):
    sender1 = MockPlayer(id=1)
    sender2 = MockPlayer(id=2)
    receiver = MockPlayer(id=3)

    party_service.invite_player_to_party(sender1, receiver)
    party_service.invite_player_to_party(sender2, receiver)
    party_service.accept_invite(receiver, sender1)

    with pytest.raises(ClientError):
        party_service.accept_invite(receiver, sender2)


def test_invite_player_to_party_not_owner(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.accept_invite(receiver, sender)

    with pytest.raises(ClientError):
        party_service.invite_player_to_party(receiver, sender)


def test_kick_player(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.accept_invite(receiver, sender)

    assert party_service.player_parties[sender].members == {sender, receiver}
    party_service.kick_player_from_party(sender, receiver)
    assert party_service.player_parties[sender].members == {sender}


def test_kick_player_nonexistent(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    with pytest.raises(ClientError):
        party_service.kick_player_from_party(sender, receiver)


def test_kick_player_not_in_party(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)

    party_service.kick_player_from_party(sender, receiver)
    sender.send_message.assert_called_once()


def test_kick_player_not_owner(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.accept_invite(receiver, sender)

    with pytest.raises(ClientError):
        party_service.kick_player_from_party(receiver, sender)


def test_leave_party(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.leave_party(sender)

    assert sender not in party_service.player_parties


def test_leave_party_twice(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.leave_party(sender)

    assert sender not in party_service.player_parties

    with pytest.raises(ClientError):
        party_service.leave_party(sender)


def test_leave_party_nonexistent(party_service):
    player = MockPlayer(id=1)

    with pytest.raises(ClientError):
        party_service.leave_party(player)


def test_ready_player(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)

    assert sender not in party_service.player_parties[sender].members_ready
    party_service.ready_player(sender)
    assert sender in party_service.player_parties[sender].members_ready


def test_ready_player_twice(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)

    assert sender not in party_service.player_parties[sender].members_ready
    party_service.ready_player(sender)
    assert sender in party_service.player_parties[sender].members_ready
    sender.send_message.assert_called_once()

    party_service.ready_player(sender)
    sender.send_message.call_count == 2


def test_ready_player_nonexistent(party_service):
    player = MockPlayer(id=1)

    with pytest.raises(ClientError):
        party_service.ready_player(player)


def test_unready_player(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.ready_player(sender)

    assert sender in party_service.player_parties[sender].members_ready
    party_service.unready_player(sender)
    assert sender not in party_service.player_parties[sender].members_ready


def test_unready_player_twice(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.ready_player(sender)

    assert sender in party_service.player_parties[sender].members_ready
    party_service.unready_player(sender)
    assert sender not in party_service.player_parties[sender].members_ready
    assert sender.send_message.call_count == 2

    party_service.unready_player(sender)
    assert sender.send_message.call_count == 3


def test_unready_player_nonexistent(party_service):
    player = MockPlayer(id=1)

    with pytest.raises(ClientError):
        party_service.unready_player(player)


def test_player_disconnected(party_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    party_service.invite_player_to_party(sender, receiver)
    party_service.on_player_disconnected(sender)

    assert sender not in party_service.player_parties


def test_remove_disbanded_parties(party_service):
    """ Artificially construct some inconsistent state and verify that
        `remove_disbanded_parties` cleans it up correctly """

    player = MockPlayer(id=1)
    player2 = MockPlayer(id=2)

    party = PlayerParty(player)

    disbanded_party = PlayerParty(player2)
    disbanded_party.disband()

    party_service.player_parties = {
        player: party,
        player2: disbanded_party
    }
    party_service.invite_player_to_party(player2, player)

    party_service.remove_disbanded_parties()

    assert party_service.player_parties == {
        player: party
    }

    with pytest.raises(ClientError):
        party_service.accept_invite(player, player2)
