import mock
import pytest
from pytest import fixture
from server.lobbyconnection import ClientError, LobbyConnection
from server.players import Player
from server.team_matchmaking_service import TeamMatchmakingService


@fixture
def team_mm_service(game_service):
    return TeamMatchmakingService(game_service)


def MockPlayer(*args, **kwargs):
    player = Player(*args, **kwargs)
    player.lobby_connection = mock.create_autospec(LobbyConnection)
    assert player.lobby_connection
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

    with pytest.raises(ClientError):
        team_mm_service.kick_player_from_party(sender, receiver)


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
