from __future__ import annotations

import json
from typing import Dict, TypeVar

T = TypeVar("T")


def index_dict_by_int(dictionary: Dict[str, T]) -> Dict[int, T]:
    return dict(map(lambda key: (int(key), dictionary[key]), dictionary))


class BoardConfig():
    def __init__(self, flats: int, caps: int):
        self.flats = flats
        self.caps = caps

    def __str__(self):
        return f"[Board Flats={self.flats} Caps={self.caps}]"


class TakConfig():
    def __init__(self, boards: Dict[int, BoardConfig]):
        self.boards = boards

    def __str__(self):
        return f"[Tak Boards={self.boards}"


class DiscordConfig():
    def __init__(self, token: str):
        self.token = token

    def __str__(self):
        return f"[Discord Token={'*' * len(self.token)}]"


class Config():
    def __init__(self, discord: DiscordConfig, tak: TakConfig):
        self.discord = discord
        self.tak = tak

    def __str__(self):
        return f"[Config {self.discord} {self.tak}"

    def load(filename: str) -> Config:
        def as_config(dct: Dict):
            if dct.get("token"):
                return DiscordConfig(**dct)
            if dct.get("flats"):
                return BoardConfig(**dct)
            if dct.get("boards"):
                return TakConfig(boards=index_dict_by_int(dct["boards"]))
            if dct.get("discord"):
                return Config(**dct)
            if type(list(dct.values())[0]) == BoardConfig:
                return dct
            raise ValueError(f"Unexpected object {dct}")

        with open(filename, 'r') as fp:
            return json.load(fp, object_hook=as_config)


if __name__ == "__main__":
    filename = "botsettings.json"
    print(f"Attempting to parse '{filename}'")
    config = Config.load(filename=filename)
    print(config)
