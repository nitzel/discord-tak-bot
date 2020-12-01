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

    def has(self, stone_type: StoneType) -> bool:
        if stone_type == StoneType.CAPSTONE:
            return self.caps > 0
        if stone_type == StoneType.FLAT or stone_type == StoneType.STANDING:
            return self.flats > 0
        raise ValueError(f"Cannot play unknown stone of type '{stone_type}'")

    def take(self, stone_type: StoneType) -> Stone:
        if not self.has(stone_type):
            raise InvalidMoveError(f"Player '{self.player}' does not have sufficient pieces")

        if stone_type == StoneType.CAPSTONE:
            self.caps -= 1
        elif stone_type == StoneType.FLAT or stone_type == StoneType.STANDING:
            self.flats -= 1

        return Stone(player=self.player, stoneType=stone_type)
