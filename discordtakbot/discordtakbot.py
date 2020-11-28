from io import BytesIO
from typing import List

import discord
from PIL import Image, ImageDraw

from board import Board
from moves import parse_move
from mytypes import InvalidMoveError, ParseMoveError
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


class DiscordTakBot(discord.Client):
    def __init__(self, tak_config: TakConfig, initial_moves: List[str] = []):
        super().__init__()
        self.tak_config = tak_config
        self.board = Board(self.tak_config, 6)

        # Prepare board
        for move in initial_moves:
            self.board.do_move(self.board.next_player, parse_move(move))

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
