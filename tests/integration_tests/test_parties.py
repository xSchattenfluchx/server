from server.players import PlayerState

from .conftest import connect_and_sign_in, read_until_command


async def test_invite_party_workflow(loop, lobby_server):
    """ Simulates the lifecycle of a party.
        1. Player sends party invite
        2. Player accepts party invite
        3. Player readies up
        4. Player unreadies
        5. Player kicks other player from party
        6. Player leaves party
    """
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    rhiza_id, _, proto2 = await connect_and_sign_in(
        ('rhiza', 'puff_the_magic_dragon'), lobby_server
    )

    await read_until_command(proto, 'game_info')
    await read_until_command(proto2, 'game_info')

    proto.send_message({
        'command': 'invite_to_party',
        'recipient_id': rhiza_id,
    })

    msg = await read_until_command(proto2, 'party_invite')
    assert msg == {'command': 'party_invite', 'sender': test_id}

    proto2.send_message({
        'command': 'accept_party_invite',
        'sender_id': test_id,
    })

    msg1 = await read_until_command(proto, 'update_party')
    msg2 = await read_until_command(proto2, 'update_party')
    assert msg1 == msg2
    assert msg1 == {
        'command': 'update_party',
        'owner': test_id,
        'members': [test_id, rhiza_id],
        'members_ready': []
    }

    proto2.send_message({'command': 'ready_party'})

    msg1 = await read_until_command(proto, 'update_party')
    msg2 = await read_until_command(proto2, 'update_party')
    assert msg1 == msg2
    assert msg1 == {
        'command': 'update_party',
        'owner': test_id,
        'members': [test_id, rhiza_id],
        'members_ready': [rhiza_id]
    }

    proto2.send_message({'command': 'unready_party'})

    msg1 = await read_until_command(proto, 'update_party')
    msg2 = await read_until_command(proto2, 'update_party')
    assert msg1 == msg2
    assert msg1 == {
        'command': 'update_party',
        'owner': test_id,
        'members': [test_id, rhiza_id],
        'members_ready': []
    }

    proto.send_message({
        'command': 'kick_player_from_party',
        'kicked_player_id': rhiza_id,
    })

    msg1 = await read_until_command(proto, 'update_party')
    msg2 = await read_until_command(proto2, 'update_party')
    assert msg1 == msg2
    assert msg1 == {
        'command': 'update_party',
        'owner': test_id,
        'members': [test_id],
        'members_ready': []
    }

    proto.send_message({'command': 'leave_party'})

    msg = await read_until_command(proto, 'update_party')
    assert msg == {
        'command': 'update_party',
        'owner': test_id,
        'members': [],
        'members_ready': []
    }


async def test_invite_non_existent_player(loop, lobby_server):
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    await read_until_command(proto, 'game_info')

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

    await read_until_command(proto, 'game_info')

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

    await read_until_command(proto, 'game_info')

    proto.send_message({
        'command': 'kick_player_from_party',
        'kicked_player_id': 2,
    })

    msg = await proto.read_message()
    assert msg == {'command': 'notice', 'style': 'error', 'text': "The kicked player doesn't exist"}


async def test_party_while_queuing(loop, lobby_server):
    test_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    await read_until_command(proto, 'game_info')

    proto.send_message({
        'command': 'game_matchmaking',
        'state': 'start',
        'faction': 'uef'
    })

    proto.send_message({'command': 'invite_to_party'})
    msg = await proto.read_message()
    assert msg == {'command': 'invalid_state', 'state': PlayerState.SEARCHING_LADDER.value}

    proto.send_message({'command': 'accept_party_invite'})
    msg = await proto.read_message()
    assert msg == {'command': 'invalid_state', 'state': PlayerState.SEARCHING_LADDER.value}

    proto.send_message({'command': 'kick_player_from_party'})
    msg = await proto.read_message()
    assert msg == {'command': 'invalid_state', 'state': PlayerState.SEARCHING_LADDER.value}


async def test_join_party_after_disband(lobby_server):
    p1_id, _, proto = await connect_and_sign_in(
        ('test', 'test_password'), lobby_server
    )

    p2_id, _, proto2 = await connect_and_sign_in(
        ('rhiza', 'puff_the_magic_dragon'), lobby_server
    )

    await read_until_command(proto, 'game_info')
    await read_until_command(proto2, 'game_info')

    # Player 1 invites player 2
    proto.send_message({
        'command': 'invite_to_party',
        'recipient_id': p2_id,
    })

    await read_until_command(proto2, 'party_invite')

    proto2.send_message({
        'command': 'accept_party_invite',
        'sender_id': p1_id,
    })

    await read_until_command(proto, 'update_party')
    await read_until_command(proto2, 'update_party')

    proto2.send_message({'command': 'leave_party'})
    await read_until_command(proto, 'update_party')
    proto.send_message({'command': 'leave_party'})
    await proto.drain()

    # Now player 2 invites player 1
    proto2.send_message({
        'command': 'invite_to_party',
        'recipient_id': p1_id,
    })

    await read_until_command(proto, 'party_invite')

    proto.send_message({
        'command': 'accept_party_invite',
        'sender_id': p2_id,
    })

    await read_until_command(proto, 'update_party')
    await read_until_command(proto2, 'update_party')