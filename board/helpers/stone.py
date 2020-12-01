from __future__ import annotations

from typing import Dict, Tuple

from PIL import ImageDraw

from mytypes import InvalidMoveError, PlayerType, StoneType


class Stone():
    def __init__(self, player: PlayerType, stone_type: StoneType):
        if type(player) != PlayerType:
            raise TypeError(f"player must be {PlayerType}", player)
        if type(stone_type) != StoneType:
            raise TypeError(f"stoneType must be {StoneType}", stone_type)

        self.player = player
        self.type = stone_type

    def draw(self, draw: ImageDraw.ImageDraw, offset: Tuple[int, int], colors: Dict[PlayerType, Tuple[int, int]], stone_width: int):
        fill, outline = colors[self.player]

        x, y = offset
        if self.type == StoneType.FLAT:
            rectangle = [x, y, x + stone_width, y + stone_width]
            draw.rectangle(rectangle, fill=fill, outline=outline, width=3)
        if self.type == StoneType.STANDING:
            rectangle = [x + stone_width//3, y, x + stone_width*2//3, y + stone_width]
            draw.rectangle(rectangle, fill=fill, outline=outline, width=3)
        if self.type == StoneType.CAPSTONE:
            rectangle = [x, y, x + stone_width, y + stone_width]
            draw.ellipse(rectangle, fill=fill, outline=outline, width=3)

    def flatten(self) -> Stone:
        if self.type != StoneType.STANDING:
            raise InvalidMoveError(f"Cannot flatten a {self.type} stone")
        return Stone(self.player, StoneType.FLAT)

    def __eq__(self, other):
        return isinstance(other, Stone)\
            and self.player == other.player\
            and self.type == other.type
