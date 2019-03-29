"""
The team matchmaking system

Used to keep track of current player parties, manage players joining/leaving and matching them against each other
used for matchmaking in the global rating system
"""
from .matchmaker_queue import MatchmakerQueue
from .search import Search

#TODO
__all__ = [
    'MatchmakerQueue',
    'Search'
]
