from __future__ import annotations
from board.helpers.stone import Stone

from mytypes import InvalidMoveError, PlayerType, StoneType


class PieceReserve():
    def __init__(self, player: PlayerType, flats: int, caps: int):
        if flats < 1:
            raise ValueError(f"Player must start with a positive number of flats, but was given '{flats}'")
        if caps < 0:
            raise ValueError(f"Player must start with a zero or a positive number of capstones but was given '{caps}'")
        self.flats = flats
        self.caps = caps
        self.player = player

    def has(self, stoneType: StoneType) -> bool:
        if stoneType == StoneType.CAPSTONE:
            return self.caps > 0
        if stoneType == StoneType.FLAT or stoneType == StoneType.STANDING:
            return self.flats > 0
        raise ValueError(f"Cannot play unknown stone of type '{stoneType}'")

    def take(self, stoneType: StoneType) -> Stone:
        if not self.has(stoneType):
            raise InvalidMoveError(f"Player '{self.player}' does not have sufficient pieces")

        if stoneType == StoneType.CAPSTONE:
            self.caps -= 1
        elif stoneType == StoneType.FLAT or stoneType == StoneType.STANDING:
            self.flats -= 1

        return Stone(player=self.player, stoneType=stoneType)
