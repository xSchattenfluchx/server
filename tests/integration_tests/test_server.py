from server import VisibilityState
from server.players import PlayerState

from .conftest import (connect_and_sign_in, connect_client, perform_login,
                       read_until)

TEST_ADDRESS = ('127.0.0.1', None)


async def test_server_invalid_login(loop, lobby_server):
    proto = await connect_client(lobby_server)
    await perform_login(proto, ('Cat', 'epic'))
    msg = await proto.read_message()
    assert msg == {'command': 'authentication_failed',
                   'text': 'Login not found or password incorrect. They are case sensitive.'}
    proto.close()


async def test_server_ban(loop, lobby_server):
    proto = await connect_client(lobby_server)
    await perform_login(proto, ('Dostya', 'vodka'))
    msg = await proto.read_message()
    assert msg == {
        'command': 'notice',
        'style': 'error',
        'text': 'You are banned from FAF for 981 years.\n Reason :\n Test permanent ban'}
    proto.close()


async def test_server_valid_login(loop, lobby_server):
    proto = await connect_client(lobby_server)
    await perform_login(proto, ('test', 'test_password'))
    msg = await proto.read_message()
    assert msg == {'command': 'welcome',
                   'me': {'clan': '678',
                          'country': '',
                          'global_rating': [2000.0, 125.0],
                          'id': 1,
                          'ladder_rating': [2000.0, 125.0],
                          'login': 'test',
                          'number_of_games': 5},
                   'id': 1,
                   'login': 'test'}
    lobby_server.close()
    proto.close()
    await lobby_server.wait_closed()


async def test_player_info_broadcast(loop, lobby_server):
    p1 = await connect_client(lobby_server)
    p2 = await connect_client(lobby_server)

    await perform_login(p1, ('test', 'test_password'))
    await perform_login(p2, ('Rhiza', 'puff_the_magic_dragon'))

    await read_until(
        p2, lambda m: 'player_info' in m.values()
        and any(map(lambda d: ('login', 'test') in d.items(), m['players']))
    )
    p1.close()
    p2.close()


async def test_host_missing_fields(loop, lobby_server):
    player_id, session, proto = await connect_and_sign_in(
        ('test', 'test_password'),
        lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'game_host',
        'mod': '',
        'visibility': VisibilityState.to_string(VisibilityState.PUBLIC),
        'title': ''
    })
    await proto.drain()

    msg = await read_until(proto, lambda msg: msg['command'] == 'game_info')

    assert msg['title'] == 'test&#x27;s game'
    assert msg['mapname'] == 'scmp_007'
    assert msg['map_file_path'] == 'maps/scmp_007.zip'
    assert msg['featured_mod'] == 'faf'


async def test_old_client_error(loop, lobby_server):
    error_msg = {
        'command': 'notice',
        'style': 'error',
        'text': 'Cannot join game. Please update your client to the newest version.'
    }
    player_id, session, proto = await connect_and_sign_in(
        ('test', 'test_password'),
        lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'InitiateTest',
        'target': 'connectivity'
    })
    msg = await proto.read_message()
    assert msg == {
        'command': 'notice',
        'style': 'error',
        'text': 'Your client version is no longer supported. Please update to the newest version: https://faforever.com'
    }

    proto.send_message({'command': 'game_host'})
    msg = await proto.read_message()
    assert msg == error_msg

    proto.send_message({'command': 'game_join'})
    msg = await proto.read_message()
    assert msg == error_msg

    proto.send_message({'command': 'game_matchmaking', 'state': 'start'})
    msg = await proto.read_message()
    assert msg == error_msg


async def test_play_game_while_queueing(loop, lobby_server):
    player_id, session, proto = await connect_and_sign_in(
        ('test', 'test_password'),
        lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'game_matchmaking',
        'state': 'start',
        'faction': 'uef'
    })

    proto.send_message({'command': 'game_host'})
    msg = await proto.read_message()
    assert msg == {'command': 'invalid_state', 'state': PlayerState.SEARCHING_LADDER.value}

    proto.send_message({'command': 'game_join'})
    msg = await proto.read_message()
    assert msg == {'command': 'invalid_state', 'state': PlayerState.SEARCHING_LADDER.value}

    proto.send_message({
        'command': 'game_matchmaking',
        'state': 'start',
        'faction': 'cybran'
    })
    msg = await proto.read_message()
    assert msg == {'command': 'invalid_state', 'state': PlayerState.SEARCHING_LADDER.value}
