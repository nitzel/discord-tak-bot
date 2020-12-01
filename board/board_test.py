import pytest

from board.helpers import Stone
from moves.moves import PlaceStone, parse_move
from mytypes import InvalidMoveError, PlayerType, StoneType
from readconfig.readconfig import BoardConfig, TakConfig

from . import Board

tak_config = TakConfig({
    4: BoardConfig(44, 4),
    5: BoardConfig(55, 5),
    6: BoardConfig(66, 6),
})

class TestBoardSize:
    @pytest.mark.parametrize("board_size", [4, 5, 6])
    def test_valid_board_sizes(self, board_size):
        assert Board(tak_config, board_size).board_size == board_size

    @pytest.mark.parametrize("board_size, flats, caps", [
        (4, 44, 4),
        (5, 55, 5),
        (6, 66, 6)]
    )
    def test_infers_caps_and_flats_from_board_size_and_config(self, board_size, flats, caps):
        board = Board(tak_config, board_size)
        assert board.player_reserves[PlayerType.WHITE].flats == flats
        assert board.player_reserves[PlayerType.WHITE].caps == caps
        assert board.player_reserves[PlayerType.BLACK].flats == flats
        assert board.player_reserves[PlayerType.BLACK].caps == caps

class TestFirstMovesRule:
    @pytest.fixture(autouse=True)
    def init_board(self):
        self.board = Board(tak_config, 4)

    @pytest.mark.parametrize("player, move", [
        (PlayerType.BLACK, "a1"), # Black can't move first
        # Must be a flat
        (PlayerType.WHITE, "Ca1"),
        (PlayerType.WHITE, "Sa1"),
    ])
    def test_illegal_first_moves(self, player: PlayerType, move: str):
        with pytest.raises(InvalidMoveError):
            self.board.do_move(player, parse_move(move))

    @pytest.mark.parametrize("player, move", [
        (PlayerType.WHITE, "a1"), # White can't move second
        # Must be a flat
        (PlayerType.BLACK, "Ca1"),
        (PlayerType.BLACK, "Sa1"),
        (PlayerType.BLACK, "b1"), # can't place on top of other stone
    ])
    def test_illegal_second_moves(self, player: PlayerType, move: str):
        self.board.do_move(PlayerType.WHITE, parse_move("b1"))
        with pytest.raises(InvalidMoveError):
            self.board.do_move(player, parse_move(move))

    def test_first_move_by_white_is_a_black_flat(self):
        move = parse_move("a1")
        self.board.do_move(PlayerType.WHITE, move)
        stack = self.board.get_stack(*move.get_xy())
        assert stack == [Stone(PlayerType.BLACK, StoneType.FLAT)]

    def test_first_move_by_black_is_a_white_flat(self):
        self.board.do_move(PlayerType.WHITE, parse_move("b1"))

        move = parse_move("a1")
        self.board.do_move(PlayerType.BLACK, move)
        stack = self.board.get_stack(*move.get_xy())
        assert stack == [Stone(PlayerType.WHITE, StoneType.FLAT)]


# TODO test..
# - all StoneTypes are now allowed on empty fields only!
# - moving stacks works
#  - cant move over caps/standings
#  - can't move out of board
# - flattening works
# - can't place out of board
# - players play alternating



