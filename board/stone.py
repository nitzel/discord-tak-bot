from __future__ import annotations

from typing import Dict, Tuple

from PIL import ImageDraw

from mytypes import InvalidMoveError, PlayerType, StoneType


class Stone():
    def __init__(self, player: PlayerType, stoneType: StoneType):
        if type(player) != PlayerType:
            raise TypeError(f"player must be {PlayerType}", player)
        if type(stoneType) != StoneType:
            raise TypeError(f"stoneType must be {StoneType}", stoneType)

        self.player = player
        self.stoneType = stoneType

    def draw(self, draw: ImageDraw.ImageDraw, offset: Tuple[int, int], colors: Dict[PlayerType, Tuple[int, int]], stone_width: int):
        fill, outline = colors[self.player]

        x, y = offset
        if self.stoneType == StoneType.FLAT:
            rectangle = [x, y, x + stone_width, y + stone_width]
            draw.rectangle(rectangle, fill=fill, outline=outline, width=3)
        if self.stoneType == StoneType.STANDING:
            rectangle = [x + stone_width//3, y, x + stone_width*2//3, y + stone_width]
            draw.rectangle(rectangle, fill=fill, outline=outline, width=3)
        if self.stoneType == StoneType.CAPSTONE:
            rectangle = [x, y, x + stone_width, y + stone_width]
            draw.ellipse(rectangle, fill=fill, outline=outline, width=3)

    def flatten(self) -> Stone:
        if self.stoneType != StoneType.STANDING:
            raise InvalidMoveError(f"Cannot flatten a {self.stoneType} stone")
        return Stone(self.player, StoneType.FLAT)
