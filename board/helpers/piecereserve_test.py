import pytest

from board.helpers.stone import Stone
from mytypes import InvalidMoveError, PlayerType, StoneType

from . import PieceReserve


@pytest.mark.parametrize("caps", [-1, -5])
def test_invalid_cap_count(caps: int):
    with pytest.raises(ValueError):
        PieceReserve(PlayerType.BLACK, flats=15, caps=caps)

@pytest.mark.parametrize("flats", [0, -1])
def test_invalid_flats_count(flats: int):
    with pytest.raises(ValueError):
        PieceReserve(PlayerType.BLACK, flats=flats, caps=15)

@pytest.mark.parametrize("player_type", [PlayerType.WHITE, PlayerType.BLACK])
def test_init_assigns_player_type(player_type):
    assert PieceReserve(player_type, 1, 0).player == player_type


class TestGivenNoFlatsButCaps:
    @pytest.fixture(autouse=True)
    def init_reserve(self):
        # Cannot init with flats=0 so start with 1 and then remove it
        self.reserve = PieceReserve(PlayerType.BLACK, flats=1, caps=15)
        self.reserve.take(StoneType.FLAT)

    @pytest.mark.parametrize("stone_type", [StoneType.FLAT, StoneType.STANDING])
    def test_has_returns_false(self, stone_type):
        assert self.reserve.has(stone_type) == False

    @pytest.mark.parametrize("stone_type", [StoneType.FLAT, StoneType.STANDING])
    def test_take_throws(self, stone_type):
        with pytest.raises(InvalidMoveError):
            self.reserve.take(stone_type)

    def test_can_take_capstone(self):
        assert self.reserve.take(StoneType.CAPSTONE) == Stone(PlayerType.BLACK, StoneType.CAPSTONE)

    def test_taking_capstone_reduces_caps_count(self):
        caps_count = self.reserve.caps
        self.reserve.take(StoneType.CAPSTONE)
        assert self.reserve.caps == caps_count - 1


class TestGivenNoCapsButFlats:
    @pytest.fixture(autouse=True)
    def init_reserve(self):
        self.reserve = PieceReserve(PlayerType.BLACK, flats=15, caps=0)

    def test_has_returns_false(self):
        assert self.reserve.has(StoneType.CAPSTONE) == False

    def test_take_throws(self):
        with pytest.raises(InvalidMoveError):
            self.reserve.take(StoneType.CAPSTONE)

    def test_can_take_flat(self):
        assert self.reserve.take(StoneType.FLAT) == Stone(PlayerType.BLACK, StoneType.FLAT)

    def test_can_take_standing(self):
        assert self.reserve.take(StoneType.STANDING) == Stone(PlayerType.BLACK, StoneType.STANDING)

    def test_taking_standing_stone_reduces_flats_count(self):
        flats_count = self.reserve.flats
        self.reserve.take(StoneType.STANDING)
        assert self.reserve.flats == flats_count - 1
