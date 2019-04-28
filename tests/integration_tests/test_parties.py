from .conftest import connect_and_sign_in, read_until
import asyncio


async def test_invite_party_workflow(loop, lobby_server):
    """ Simulates the lifecycle of a party.
        1. Player sends party invite
        2. Player accepts party invite
        3. Player kicks other player from party
        4. Player leaves party
    """
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    rhiza_id, _, proto2 = await connect_and_sign_in(
        ('rhiza', 'puff_the_magic_dragon'), lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')
    await read_until(proto2, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'invite_to_party',
        'recipient_id': rhiza_id,
    })

    msg = await read_until(proto2, lambda msg: msg['command'] == 'party_invite')
    assert msg == {'command': 'party_invite', 'sender': test_id}

    proto2.send_message({
        'command': 'accept_party_invite',
        'sender_id': test_id,
    })

    msg1 = await read_until(proto, lambda msg: msg['command'] == 'update_party')
    msg2 = await read_until(proto2, lambda msg: msg['command'] == 'update_party')
    assert msg1 == msg2
    assert msg1 == {'command': 'update_party', 'owner': test_id, 'members': [test_id, rhiza_id]}

    proto.send_message({
        'command': 'kick_player_from_party',
        'kicked_player_id': rhiza_id,
    })

    msg1 = await read_until(proto, lambda msg: msg['command'] == 'update_party')
    msg2 = await read_until(proto2, lambda msg: msg['command'] == 'update_party')
    assert msg1 == msg2
    assert msg1 == {'command': 'update_party', 'owner': test_id, 'members': [test_id]}

    proto.send_message({'command': 'leave_party'})

    msg = await read_until(proto, lambda msg: msg['command'] == 'update_party')
    assert msg == {'command': 'update_party', 'owner': test_id, 'members': []}


async def test_invite_non_existent_player(loop, lobby_server):
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'invite_to_party',
        'recipient_id': 2,
    })

    msg = await proto.read_message()
    assert msg == {'command': 'notice', 'style': 'error', 'text': "The invited player doesn't exist"}


async def test_accept_invite_non_existent(loop, lobby_server):
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'accept_party_invite',
        'sender_id': 2,
    })

    msg = await proto.read_message()
    assert msg == {'command': 'notice', 'style': 'error', 'text': "The inviting player doesn't exist"}


async def test_kick_player_non_existent(loop, lobby_server):
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'kick_player_from_party',
        'kicked_player_id': 2,
    })

    msg = await proto.read_message()
    assert msg == {'command': 'notice', 'style': 'error', 'text': "The kicked player doesn't exist"}
