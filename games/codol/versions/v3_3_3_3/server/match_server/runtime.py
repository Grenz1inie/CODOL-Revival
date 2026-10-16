"""Start the independently built Rust match server; Python owns the lobby only."""
from .process import NativeMatchProcess
from .matchmaking import IndependentMatchmaking


def load_matchmaking(directory, *, port=28970, record=None):
    process=NativeMatchProcess(directory,port=port,record=record)
    return IndependentMatchmaking(process,record=record)
