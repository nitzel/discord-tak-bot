from enum import Enum


class InvalidMoveError(BaseException):
    pass


class ParseMoveError(BaseException):
    pass


class PlayerType(Enum):
    WHITE = "White"
    BLACK = "Black"


def get_opponent(player: PlayerType):
    if player == PlayerType.WHITE:
        return PlayerType.BLACK
    return PlayerType.WHITE


class StoneType(Enum):
    FLAT = "F"
    STANDING = "S"
    CAPSTONE = "C"


class Direction(Enum):
    LEFT = "<"
    RIGHT = ">"
    UP = "+"
    DOWN = "-"
