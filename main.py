from __future__ import annotations

import re
from enum import Enum
from io import BytesIO
from typing import Dict, List, Tuple, TypeVar

import discord
from PIL import Image, ImageDraw

from readconfig import BoardConfig, Config, TakConfig

# Configs are attempted to be read in this order until one succeeds.
# This allows a dev to have a config that isn't checked in to the repository
CONFIG_FILES = ["botsettings.dev.json", "botsettings.json"]

BOARD_SIZE = 6  # choose from 3-8

TILE_WIDTH = 50  # px
STONE_WIDTH = TILE_WIDTH * 2 // 3  # px


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


class Move():
    def __init__(self, x: str, y: str):
        if len(x) != 1:
            raise ValueError(f"x must be a single character but was '{x}'")

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


class PlaceStone(Move):
    def __init__(self, x: str, y: str, stoneType: StoneType):
        super().__init__(x, y)
        self.stoneType = stoneType

    def __str__(self):
        stoneType = "" if self.stoneType == StoneType.FLAT else self.stoneType.value
        return f"PLACE {stoneType}{self.x}{self.y}"


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


class Stone():
    def __init__(self, player: PlayerType, stoneType: StoneType):
        if type(player) != PlayerType:
            raise TypeError(f"player must be {PlayerType}", player)
        if type(stoneType) != StoneType:
            raise TypeError(f"stoneType must be {StoneType}", stoneType)

        self.player = player
        self.stoneType = stoneType

    def draw(self, draw: ImageDraw.ImageDraw, offset: Tuple[int, int], colors: Dict[PlayerType, Tuple[int, int]]):
        fill, outline = colors[self.player]

        x, y = offset
        if self.stoneType == StoneType.FLAT:
            rectangle = [x, y, x + STONE_WIDTH, y + STONE_WIDTH]
            draw.rectangle(rectangle, fill=fill, outline=outline, width=3)
        if self.stoneType == StoneType.STANDING:
            rectangle = [x + STONE_WIDTH//3, y, x + STONE_WIDTH*2//3, y + STONE_WIDTH]
            draw.rectangle(rectangle, fill=fill, outline=outline, width=3)
        if self.stoneType == StoneType.CAPSTONE:
            rectangle = [x, y, x + STONE_WIDTH, y + STONE_WIDTH]
            draw.ellipse(rectangle, fill=fill, outline=outline, width=3)

    def flatten(self) -> Stone:
        if self.stoneType != StoneType.STANDING:
            raise InvalidMoveError(f"Cannot flatten a {self.stoneType} stone")
        return Stone(self.player, StoneType.FLAT)


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
        return [self.get_stack(*apply_direction(x, y, direction)) for _ in range(count)]

    def place_stone(self, player: PlayerType, x: int, y: int, stoneType: StoneType) -> None:
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
                    stone.draw(draw, (x + stone_offset, y + stone_offset + y_add - i * vertical_lift), self.colors)


REGEX_STONE_TYPE = "(?P<stoneType>[CSF])"  # Type of the stone to put down
REGEX_POSITION = "(?P<x>[a-z])(?P<y>[1-9])"  # x/y position TODO limit to 8x8?

REGEX_PICKUP = "(?P<pickup>[1-9][0-9]*)"  # Number of stones to pick up
REGEX_DIRECTION = r"(?P<direction>[\<\>\+\-])"  # Direction of a move
REGEX_DROPPINGS = "(?P<droppings>[1-9]+)"  # Number of stones dropped per field

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

        return MoveStack(groups["x"], groups["y"], direction=direction, pickup=pickup, droppings=droppings)

    match = REGEX_PLACE_STONE.match(command)
    if match is not None:
        groups = match.groupdict()

        stoneType = StoneType(groups["stoneType"]) if groups["stoneType"] else StoneType.FLAT
        return PlaceStone(groups["x"], groups["y"], stoneType=stoneType)

    raise ParseMoveError(f"Unrecognized move '{command}'")


# # TODO convert these to tests
# # # Placements
# print(parse_move("Ce1"))
# print(parse_move("Fa3"))
# print(parse_move("Sf5"))
# print(parse_move(" d4"))
# # # Moves
# print(parse_move("a3>"))
# print(parse_move("a3<"))
# print(parse_move("a3+"))
# print(parse_move("a3-"))
# print(parse_move("5a3>212"))
# print(parse_move("7a3<115"))
# print(parse_move("7a3<"))
# print(parse_move("a3<324"))

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

async def send_board_image(board: Board, channel: discord.abc.Messageable, content: str = ""):
    embed = discord.Embed(title="Game State", description=content, color=0xfc9a04)
    with Image.new("RGB", board.get_dimensions(), "white") as im:
        draw: ImageDraw.ImageDraw = ImageDraw.ImageDraw(im)
        board.draw(draw)
        with BytesIO() as image_binary:
            im.save(image_binary, 'PNG')
            image_binary.seek(0)

            file = discord.File(fp=image_binary, filename="board.png")
            embed.set_image(url="attachment://board.png")
            await channel.send(file=file, embed=embed, delete_after=60)


class MyClient(discord.Client):
    def __init__(self, tak_config: TakConfig):
        super().__init__()
        self.tak_config = tak_config
        self.board = Board(self.tak_config, 6)

        # # Prepare board
        # moves = [
        #     "a2", "a1",
        #     "b1", "a2-",
        #     "b1<", "b1",
        #     "Ca2", "b2",
        #     "a2-", "b3",
        #     "3a1>111"
        # ]
        # for move in moves:
        #     self.board.do_move(self.board.next_player, parse_move(move))

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        print(f'Message from {message.author} on channel id {message.channel.id}: {message.content}')
        if message.author == self.user:
            return

        if message.content.startswith('$'):
            command = message.content[1:]
            board = self.board
            if command == "show":
                await send_board_image(board, message.channel, f"{self.board.next_player.value} is next")
                return await message.delete()

            try:
                move = parse_move(command)
                print(f"Parsed move {move}")
                try:
                    board.do_move(board.next_player, move)
                    await send_board_image(board, message.channel, f"{message.author.mention} executed move {move}")
                    return await message.delete()
                except InvalidMoveError as error:
                    return await message.channel.send(f"Failed to apply move {move}: {error}", delete_after=60)
            except ParseMoveError as error:
                return await message.channel.send(f"Failed to parse command {message.content}: {error}", delete_after=60)


if __name__ == "__main__":
    config = None
    for config_file in CONFIG_FILES:
        print(f"Attempting to read config from '{config_file}'")
        try:
            config = Config.load(config_file)
            print(f"Successfully read config from '{config_file}'")
            break
        except FileNotFoundError:
            print(f"Cannot read config from '{config_file}' because it does not exist'")
    if not config:
        exit("Failed read configuration")

    client = MyClient(config.tak)
    client.run(config.discord.token)
