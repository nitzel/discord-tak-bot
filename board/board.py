from __future__ import annotations

from typing import Dict, List, Tuple, TypeVar

from PIL import ImageDraw

from moves import Move, MoveStack, PlaceStone
from mytypes import (Direction, InvalidMoveError, PlayerType, StoneType,
                     get_opponent)
from readconfig import BoardConfig, TakConfig

from .helpers import PieceReserve, Stone

BOARD_SIZE = 6  # choose from 3-8

TILE_WIDTH = 50  # px
STONE_WIDTH = TILE_WIDTH * 2 // 3  # px


def apply_direction(x: int, y: int, direction: Direction, delta: int = 1) -> Tuple[int, int]:
    if direction == Direction.LEFT:
        return x - delta, y
    if direction == Direction.RIGHT:
        return x + delta, y
    if direction == Direction.UP:
        return x, y + delta
    if direction == Direction.DOWN:
        return x, y - delta
    raise ValueError(f"Unkwnon direction '{direction}'")


T = TypeVar('T')


def split_by_counts(array: List[T], counts: List[int]) -> List[List[T]]:
    if sum(counts) != len(array):
        raise ValueError(f"Cannot split list with {len(array)} items into {len(counts)} groups with an accumulated size of {sum(counts)}")

    groups: List[List[T]] = []
    already_taken = 0
    for to_take in counts:
        groups.append(array[already_taken: already_taken + to_take])
        already_taken += to_take
    return groups


class Board():
    def __init__(self, tak_config: TakConfig, board_size: int) -> None:
        self.board: List[List[Stone]] = [[] for _ in range(board_size * board_size)]
        self.board_size = board_size
        self.tak_config = tak_config

        self.colors: Dict[PlayerType, Tuple[int, int]] = {
            PlayerType.WHITE: (0xf0f0f0, 0xe0e0e0),
            PlayerType.BLACK: (0x606060, 0x404040)
        }

        piece_count = Board._get_piece_count(self.tak_config, self.board_size)
        self.player_reserves: Dict[PlayerType, PieceReserve] = {
            PlayerType.WHITE: PieceReserve(PlayerType.WHITE, flats=piece_count.flats, caps=piece_count.caps),
            PlayerType.BLACK: PieceReserve(PlayerType.BLACK, flats=piece_count.flats, caps=piece_count.caps),
        }

        self.next_player = PlayerType.WHITE
        self.initial_moves = True  # The first two pieces are played with opponent's pieces

    @staticmethod
    def _get_piece_count(tak_config: TakConfig, board_size: int) -> BoardConfig:
        piece_count = tak_config.boards.get(board_size)
        if piece_count:
            return piece_count
        raise ValueError(f"Board size '{board_size}' is not supported. Supported board sizes are: {list(tak_config.boards.keys())}")

    def get_dimensions(self) -> Tuple[int, int]:
        return self.board_size * TILE_WIDTH, self.board_size * TILE_WIDTH

    def get_stack(self, x: int, y: int) -> List[Stone]:
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            raise InvalidMoveError(f"{x}/{y} is not on the board (board size {self.board_size})")
        return self.board[x + y * self.board_size]

    def get_stacks(self, x: int, y: int, direction: Direction, count: int) -> List[List[Stone]]:
        """
          Returns the n=count stacks that start next to x/y in direction. The first one is the direct neighbour of x/y
        """
        return [self.get_stack(*apply_direction(x, y, direction, i + 1)) for i in range(count)]

    def place_stone(self, player: PlayerType, x: int, y: int, stoneType: StoneType) -> None:
        if self.initial_moves and stoneType != StoneType.FLAT:
            raise InvalidMoveError("Only flats can be placed during the first turn.")

        stack = self.get_stack(x, y)
        if len(stack) > 0:
            raise InvalidMoveError("Stones can only be placed on empty fields")

        stone = self.player_reserves[player].take(stoneType=stoneType)
        stack.append(stone)

    def do_move(self, acting_player: PlayerType, move: Move) -> None:
        if acting_player != self.next_player:
            raise InvalidMoveError("It's {self.next_player}'s turn")

        # switch to opponent stones if still in the initial move sequence
        player = acting_player if not self.initial_moves else get_opponent(acting_player)

        if isinstance(move, PlaceStone):
            self.place_stone(player, *move.get_xy(), move.stoneType)
        if isinstance(move, MoveStack):
            x, y = move.get_xy()
            start_stack = self.get_stack(x, y)
            top_stone = start_stack[-1] if len(start_stack) > 0 else None

            if not top_stone:
                raise InvalidMoveError(f"There is no stack on {x}/{y} to move")
            if top_stone.player != player:
                raise InvalidMoveError(f"Stack on {x}/{y} belongs to {top_stone.player} and not to {player}")

            # If no stack was defined, pick up as much as the carry limit allows
            pickup = move.pickup if move.pickup else min(len(start_stack), self.board_size)
            if pickup > self.board_size:
                raise InvalidMoveError(f"The carry limit is {self.board_size} (tried to pick up {move.pickup})")
            if pickup > len(start_stack):
                raise InvalidMoveError(f"Stack on {x}/{y} has only {len(start_stack)} pieces (tried to pick up {move.pickup})")

            carried_stones = start_stack[-pickup:]
            for _ in range(pickup):  # remove stones from stack
                start_stack.pop()

            # If no droppings were defined, drop all at once
            droppings = move.droppings if move.droppings else [pickup]

            if pickup != sum(droppings):
                raise InvalidMoveError(f"Cannot pickup {pickup} stones and drop a total of {droppings}")

            dropped_stones = split_by_counts(carried_stones, droppings)

            drop_reach = len(droppings)  # number of fields stones will be dropped on
            drop_stacks = self.get_stacks(x, y, move.direction, drop_reach)
            for stack, stones in zip(drop_stacks, dropped_stones):
                top_stone = stack[-1] if len(stack) > 0 else None
                dropping_capstone_only = stones[0].stoneType == StoneType.CAPSTONE
                if top_stone and top_stone.stoneType == StoneType.CAPSTONE:
                    raise InvalidMoveError("Can't drop stones on a {top_stone.stoneType}")
                if top_stone and top_stone.stoneType == StoneType.STANDING:
                    if dropping_capstone_only:
                        stack[-1] = top_stone.flatten()
                    else:
                        raise InvalidMoveError("Standing stones can only be flattened with a capstone alone")
                stack.extend(stones)

        if self.initial_moves and acting_player == PlayerType.BLACK:
            self.initial_moves = False
        self.next_player = get_opponent(self.next_player)

    def draw(self, draw: ImageDraw.ImageDraw, offset: Tuple[int, int] = (0, 0)):
        for iy in range(self.board_size):
            for ix in range(self.board_size):
                color = "gray" if (ix + iy) % 2 == 0 else "blue"
                x = offset[0] + ix * TILE_WIDTH
                y = offset[1] + (self.board_size - iy - 1) * TILE_WIDTH  # Rows are numbered from 1-n from the bottom up
                rectangle = [x, y, x + TILE_WIDTH, y + TILE_WIDTH]
                draw.rectangle(rectangle, fill=color, width=0)

                stone_offset = (TILE_WIDTH - STONE_WIDTH) // 2

                vertical_lift = 5
                stones = self.get_stack(ix, iy)
                y_add = len(stones) // 2 * vertical_lift  # todo make sure we're not exiting the field
                for i, stone in enumerate(stones):
                    stone.draw(draw, (x + stone_offset, y + stone_offset + y_add - i * vertical_lift), self.colors, STONE_WIDTH)


# TODO convert these to tests
# board = Board(BOARD_SIZE)
# board.do_move(PlayerType.WHITE, parse_move("a1"))
# board.do_move(PlayerType.BLACK, parse_move("a2"))
# board.do_move(PlayerType.WHITE, parse_move("a3"))
# board.do_move(PlayerType.BLACK, parse_move("a4"))
# Show the rendered board in an image viewer
# with Image.new("RGB", board.get_dimensions(), "white") as im:
#   draw = ImageDraw.Draw(im)
#   board.draw(draw)
#   im.show()
# exit(0)
