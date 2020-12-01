import pytest

from mytypes import PlayerType, StoneType

from .stone import Stone


def test_flatten_does_not_affect_stone():
    stone = Stone(PlayerType.BLACK, StoneType.STANDING)
    stone.flatten()
    assert stone.player == PlayerType.BLACK and stone.type == StoneType.STANDING

def test_flatten_returns_the_flattened_stone():
    assert Stone(PlayerType.BLACK, StoneType.STANDING).flatten() == Stone(PlayerType.BLACK, StoneType.FLAT)

def test_eq():
    assert Stone(PlayerType.BLACK, StoneType.STANDING) == Stone(PlayerType.BLACK, StoneType.STANDING)
    assert Stone(PlayerType.WHITE, StoneType.STANDING) == Stone(PlayerType.WHITE, StoneType.STANDING)
    assert Stone(PlayerType.WHITE, StoneType.FLAT) == Stone(PlayerType.WHITE, StoneType.FLAT)
    assert Stone(PlayerType.WHITE, StoneType.CAPSTONE) == Stone(PlayerType.WHITE, StoneType.CAPSTONE)

def test_not_eq():
    assert Stone(PlayerType.BLACK, StoneType.STANDING) != Stone(PlayerType.WHITE, StoneType.STANDING)
    assert Stone(PlayerType.WHITE, StoneType.STANDING) != Stone(PlayerType.WHITE, StoneType.FLAT)
    assert Stone(PlayerType.WHITE, StoneType.STANDING) != Stone(PlayerType.WHITE, StoneType.CAPSTONE)
    assert Stone(PlayerType.WHITE, StoneType.FLAT) != Stone(PlayerType.WHITE, StoneType.CAPSTONE)
