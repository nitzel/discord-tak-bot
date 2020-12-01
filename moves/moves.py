from __future__ import annotations

import re
from typing import List, Tuple

from mytypes import Direction, ParseMoveError, StoneType


class Move():
    def __init__(self, x: str, y: str):
        if len(x) != 1:
            raise ValueError(f"x must be a single character but was '{x}'")
        if x < 'a' or x > 'i':
            raise ValueError(f"x must be a letter [a-i] but was '{x}'")

        iy = int(y)
        if iy not in range(1, 10):
            raise ValueError(f"y must be number in [1, 9] but was '{y}'")

        self.x = x
        self.y = iy

    def get_xy(self) -> Tuple[int, int]:
        """
        Returns x and y as zero based indices
        """
        return ord(self.x) - ord('a'), self.y - 1

    def __eq__(self, other) -> bool:
        return isinstance(other, Move)\
            and self.x == other.x\
            and self.y == other.y

    def __repr__(self):
        return self.__str__()


class PlaceStone(Move):
    def __init__(self, x: str, y: str, stoneType: StoneType):
        super().__init__(x, y)
        self.stoneType = stoneType

    def __str__(self):
        stoneType = "" if self.stoneType == StoneType.FLAT else self.stoneType.value
        return f"PLACE {stoneType}{self.x}{self.y}"

    def __eq__(self, other) -> bool:
        return isinstance(other, PlaceStone)\
            and super().__eq__(other)\
            and self.stoneType == other.stoneType


class MoveStack(Move):
    def __init__(self, x: str, y: str, direction: Direction, pickup: int | None = None, droppings: List[int] | None = None):
        """
        pickup=None means all/the entire stack
        droppings=None means all carried
        """
        super().__init__(x, y)
        self.direction = direction
        self.pickup = pickup
        self.droppings = droppings

    def __str__(self):
        pickup = self.pickup if self.pickup else ""
        droppings = "".join(str(drop) for drop in self.droppings) if self.droppings else ""
        return f"MOVE {pickup}{self.x}{self.y}{self.direction.value}{droppings}"

    def __eq__(self, other) -> bool:
        return isinstance(other, MoveStack)\
            and super().__eq__(other)\
            and self.direction == other.direction\
            and self.pickup == other.pickup\
            and self.droppings == other.droppings\

REGEX_STONE_TYPE = "(?P<stoneType>[CSF])"  # Type of the stone to put down
REGEX_POSITION = "(?P<x>[a-z])(?P<y>[1-9])"  # x/y position TODO limit to 8x8?

REGEX_PICKUP = "(?P<pickup>[1-9])"  # Number of stones to pick up, never more than board size so <10
REGEX_DIRECTION = r"(?P<direction>[\<\>\+\-])"  # Direction of a move
REGEX_DROPPINGS = "(?P<droppings>[0-9]+)"  # Number of stones dropped per field. Needs checking that 0 fails for accidental mistypes

# TODO add parsing for remarks like ? (questionable move), ! (surprise/good move), ?? ? ?! !? ! !!
#   ' (tak threat) and * (capstone flattens standing stone)
#   { this is a comment } (comments in curly braces)
REGEX_MOVE_STACK = re.compile(rf"^\s*{REGEX_PICKUP}?{REGEX_POSITION}{REGEX_DIRECTION}{REGEX_DROPPINGS}?")
REGEX_PLACE_STONE = re.compile(rf"^\s*{REGEX_STONE_TYPE}?{REGEX_POSITION}")


def parse_move(command: str) -> Move:
    match = REGEX_MOVE_STACK.match(command)
    if match is not None:
        groups = match.groupdict()

        pickup = int(groups["pickup"]) if groups["pickup"] else None
        droppings = list(map(lambda char: int(char), groups["droppings"])) if groups["droppings"] else None
        direction = Direction(groups["direction"])

        if droppings and 0 in droppings:
            raise ParseMoveError(f"Move {command} contains '0' droppings {droppings} but at least one stone must be dropped per field")

        return MoveStack(groups["x"], groups["y"], direction=direction, pickup=pickup, droppings=droppings)

    match = REGEX_PLACE_STONE.match(command)
    if match is not None:
        groups = match.groupdict()

        stoneType = StoneType(groups["stoneType"]) if groups["stoneType"] else StoneType.FLAT
        return PlaceStone(groups["x"], groups["y"], stoneType=stoneType)

    raise ParseMoveError(f"Unrecognized move '{command}'")

