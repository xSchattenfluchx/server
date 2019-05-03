import mock
import pytest
from pytest import fixture
from server.lobbyconnection import ClientError
from server.players import Player
from server.team_matchmaking_service import TeamMatchmakingService
from server.team_matchmaker import PlayerParty


@fixture
def team_mm_service(game_service):
    return TeamMatchmakingService(game_service)


def MockPlayer(id) -> Player:
    player = mock.create_autospec(Player)
    player.id = id
    player.foes = {}
    return player


def test_invite_player_to_party(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)


def test_invite_foe_to_party(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)
    receiver.foes = {1}

    with pytest.raises(ClientError):
        team_mm_service.invite_player_to_party(sender, receiver)


def test_accept_invite(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    assert team_mm_service.player_parties[sender].members == {sender}

    team_mm_service.accept_invite(receiver, sender)
    assert team_mm_service.player_parties[sender].members == {sender, receiver}


def test_accept_invite_nonexistent(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    with pytest.raises(ClientError):
        team_mm_service.accept_invite(receiver, sender)


def test_accept_invite_two_invites(team_mm_service):
    sender1 = MockPlayer(id=1)
    sender2 = MockPlayer(id=2)
    receiver = MockPlayer(id=3)

    team_mm_service.invite_player_to_party(sender1, receiver)
    team_mm_service.invite_player_to_party(sender2, receiver)
    team_mm_service.accept_invite(receiver, sender1)

    with pytest.raises(ClientError):
        team_mm_service.accept_invite(receiver, sender2)


def test_invite_player_to_party_not_owner(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.accept_invite(receiver, sender)

    with pytest.raises(ClientError):
        team_mm_service.invite_player_to_party(receiver, sender)


def test_kick_player(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.accept_invite(receiver, sender)

    assert team_mm_service.player_parties[sender].members == {sender, receiver}
    team_mm_service.kick_player_from_party(sender, receiver)
    assert team_mm_service.player_parties[sender].members == {sender}


def test_kick_player_nonexistent(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    with pytest.raises(ClientError):
        team_mm_service.kick_player_from_party(sender, receiver)


def test_kick_player_not_in_party(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)

    team_mm_service.kick_player_from_party(sender, receiver)
    sender.send_message.assert_called_once()


def test_kick_player_not_owner(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.accept_invite(receiver, sender)

    with pytest.raises(ClientError):
        team_mm_service.kick_player_from_party(receiver, sender)


def test_leave_party(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.leave_party(sender)

    assert sender not in team_mm_service.player_parties


def test_leave_party_twice(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.leave_party(sender)

    assert sender not in team_mm_service.player_parties

    with pytest.raises(ClientError):
        team_mm_service.leave_party(sender)


def test_leave_party_nonexistent(team_mm_service):
    player = MockPlayer(id=1)

    with pytest.raises(ClientError):
        team_mm_service.leave_party(player)


def test_ready_player(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)

    assert sender not in team_mm_service.player_parties[sender].members_ready
    team_mm_service.ready_player(sender)
    assert sender in team_mm_service.player_parties[sender].members_ready


def test_ready_player_twice(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)

    assert sender not in team_mm_service.player_parties[sender].members_ready
    team_mm_service.ready_player(sender)
    assert sender in team_mm_service.player_parties[sender].members_ready
    sender.send_message.assert_called_once()

    team_mm_service.ready_player(sender)
    sender.send_message.call_count == 2


def test_ready_player_nonexistent(team_mm_service):
    player = MockPlayer(id=1)

    with pytest.raises(ClientError):
        team_mm_service.ready_player(player)


def test_unready_player(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.ready_player(sender)

    assert sender in team_mm_service.player_parties[sender].members_ready
    team_mm_service.unready_player(sender)
    assert sender not in team_mm_service.player_parties[sender].members_ready


def test_unready_player_twice(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.ready_player(sender)

    assert sender in team_mm_service.player_parties[sender].members_ready
    team_mm_service.unready_player(sender)
    assert sender not in team_mm_service.player_parties[sender].members_ready
    assert sender.send_message.call_count == 2

    team_mm_service.unready_player(sender)
    assert sender.send_message.call_count == 3


def test_unready_player_nonexistent(team_mm_service):
    player = MockPlayer(id=1)

    with pytest.raises(ClientError):
        team_mm_service.unready_player(player)


def test_player_disconnected(team_mm_service):
    sender = MockPlayer(id=1)
    receiver = MockPlayer(id=2)

    team_mm_service.invite_player_to_party(sender, receiver)
    team_mm_service.on_player_disconnected(sender)

    assert sender not in team_mm_service.player_parties


def test_remove_disbanded_parties(team_mm_service):
    """ Artificially construct some inconsistent state and verify that
        `remove_disbanded_parties` cleans it up correctly """

    player = MockPlayer(id=1)
    player2 = MockPlayer(id=2)

    party = PlayerParty(player)

    disbanded_party = PlayerParty(player2)
    disbanded_party.disband()

    team_mm_service.player_parties = {
        player: party,
        player2: disbanded_party
    }
    team_mm_service.invite_player_to_party(player2, player)

    team_mm_service.remove_disbanded_parties()

    assert team_mm_service.player_parties == {
        player: party
    }

    with pytest.raises(ClientError):
        team_mm_service.accept_invite(player, player2)
