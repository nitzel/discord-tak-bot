from __future__ import annotations

import random
from io import BytesIO
from typing import Dict, List, Union

import discord
from discord import mentions
from discord.channel import TextChannel
from PIL import Image, ImageDraw

import board
from board import Board
from moves import parse_move
from mytypes import InvalidMoveError, ParseMoveError, PlayerType, get_opponent
from readconfig import TakConfig


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


async def make_channel(ctx: discord.Message, opponent: discord.Member, public_read: bool = False, public_write: bool = False) -> TextChannel:
    guild = ctx.guild
    creator = ctx.author
    if not isinstance(creator, discord.Member):
        raise Exception("Author is not a member")

    if guild.me == None:
        raise Exception("guild.me is None")

    overwrites: Dict[Union[discord.Role, discord.Member], discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(read_messages=public_read, send_messages=public_write),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        creator: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),  # manage so that he can delete/rename
        opponent: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=False),
    }
    channel = await guild.create_text_channel(f"game_{creator.display_name}_vs_{opponent.display_name}", overwrites=overwrites)

    await channel.send(f"Welcome {creator.mention} and @{opponent.mention} to {channel.mention}. You can create a game via e.g. `$start <board_size> <optional:white|black>`")
    return channel


class Game:
    def __init__(self, white: discord.Member, black: discord.Member, board: Board):
        self.board = board
        self.white = white
        self.black = black

    def next_player_mention(self) -> str:
        next = self.white if self.board.next_player == PlayerType.WHITE else self.black
        return f"{next.mention}({self.board.next_player.value})"

    def other_player_mention(self) -> str:
        other = self.black if self.board.next_player == PlayerType.WHITE else self.white
        return f"{other.mention}({get_opponent(self.board.next_player).value})"


class DiscordTakBot(discord.Client):
    def __init__(self, tak_config: TakConfig, initial_moves: List[str] = []):
        super().__init__()
        self.tak_config = tak_config

        self.games: Dict[int, Game] = {}  # channel ID -> Game

        # self.board = Board(self.tak_config, 6)

        # Prepare board
        # for move in initial_moves:
        #    self.board.do_move(self.board.next_player, parse_move(move))

    async def create(self, message: discord.Message, command: str, opponent: discord.Member):
        secret = "-secret" in command
        public = "-public" in command
        if secret and public:
            raise Exception("`-secret` and `-public` are mutually exclusive")

        black = "-black" in command
        white = "-white" in command
        userandom = "-random" in command
        if white + black + userandom >= 2:
            raise Exception("`-black`, `-white` and `-random` are mutually exclusive")
        if white + black + userandom == 0:
            raise Exception("Choose a colour by specifying `-black`, `-white` and `-random`")

        board_size = None
        for size in self.tak_config.boards.keys():
            if f"-s{size}" in command:
                board_size = int(size)
        if board_size == None:
            raise Exception("Specify board size as `-s4` or `-s5` etc.")

        if userandom:
            white = bool(random.randint(0, 1))

        author = message.author
        if not isinstance(author, discord.Member):
            raise Exception("Author must be a member")

        white, black = (author, opponent) if white else (opponent, author)

        channel = await make_channel(message, opponent, True, False)

        game = Game(white, black, Board(self.tak_config, board_size))
        self.games[channel.id] = game

        return await send_board_image(game.board, channel, f"{game.next_player_mention()} vs {game.other_player_mention()}")

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        try:
            await self._on_message(message)
        except Exception as ex:
            return await message.channel.send(f"Error: {ex}")

    async def _on_message(self, message: discord.Message):
        print(f'Message from {message.author} on channel id {message.channel.id}: {message.content}')
        if message.author == self.user:
            return

        if message.content.startswith('$'):
            command = message.content[1:]
            game = self.games.get(message.channel.id)

            if command == "show":
                if not game:
                    raise Exception("Channel doesn't have a game")
                await send_board_image(game.board, message.channel, f"{game.next_player_mention()} is next")
                return await message.delete()

            if command.startswith("create"):
                if len(message.mentions) == 0:
                    raise Exception("Must mention only your opponent")
                opponent = message.mentions[0]
                if not isinstance(opponent, discord.Member):
                    raise Exception(f"Opponent is not a member but a {type(opponent)}")

                await self.create(message, command, opponent)
                return await message.delete()

            try:
                move = parse_move(command)
                if not game:
                    raise Exception("Channel doesn't have a game")
                print(f"Parsed move {move}")

                if message.author == game.white:
                    player = PlayerType.WHITE
                elif message.author == game.black:
                    player = PlayerType.BLACK
                else:
                    raise Exception(f"You are not a player. Only {game.next_player_mention()} and {game.other_player_mention()} can do moves")

                try:
                    game.board.do_move(player, move)
                    await send_board_image(game.board, message.channel, f"{message.author.mention}({player.value}) executed move {move}")
                    return await message.delete()
                except InvalidMoveError as error:
                    return await message.channel.send(f"Failed to apply move {move}: {error}", delete_after=60)
            except ParseMoveError as error:
                return await message.channel.send(f"Failed to parse command {message.content}: {error}", delete_after=60)
