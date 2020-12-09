import pytest
from _pytest.fixtures import get_parametrized_fixture_keys

from board.helpers import Stone
from moves.moves import PlaceStone, parse_move
from mytypes import InvalidMoveError, ParseMoveError, PlayerType, StoneType
from readconfig.readconfig import BoardConfig, TakConfig

from . import Board

tak_config = TakConfig({
    3: BoardConfig(33, 3),
    4: BoardConfig(44, 4),
    5: BoardConfig(55, 5),
    6: BoardConfig(66, 6),
    7: BoardConfig(77, 7),
    8: BoardConfig(88, 8),
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
        (PlayerType.BLACK, "a1"),  # Black can't move first
        # Must be a flat
        (PlayerType.WHITE, "Ca1"),
        (PlayerType.WHITE, "Sa1"),
    ])
    def test_illegal_first_moves(self, player: PlayerType, move: str):
        with pytest.raises(InvalidMoveError):
            self.board.do_move(player, parse_move(move))

    @pytest.mark.parametrize("player, move", [
        (PlayerType.WHITE, "a1"),  # White can't move second
        # Must be a flat
        (PlayerType.BLACK, "Ca1"),
        (PlayerType.BLACK, "Sa1"),
        (PlayerType.BLACK, "b1"),  # can't place on top of other stone
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


class TestPlacingIsOnlyAllowedOnEmptyFields:
    @pytest.fixture(autouse=True)
    def init_board(self):
        self.board = Board(tak_config, 4)
        self.board.do_move(PlayerType.WHITE, parse_move("b1"))
        self.board.do_move(PlayerType.BLACK, parse_move("a1"))
        self.board.do_move(PlayerType.WHITE, parse_move("Sa2"))
        self.board.do_move(PlayerType.BLACK, parse_move("Sb2"))
        self.board.do_move(PlayerType.WHITE, parse_move("Ca3"))
        self.board.do_move(PlayerType.BLACK, parse_move("Cb3"))

    @pytest.mark.parametrize("player, move", [
        # On white stones
        # White flat
        (PlayerType.WHITE, "a1"),  # on flat
        (PlayerType.WHITE, "a2"),  # on standing
        (PlayerType.WHITE, "a3"),  # on cap
        # white standing
        (PlayerType.WHITE, "Sa1"),  # on flat
        (PlayerType.WHITE, "Sa2"),  # on standing
        (PlayerType.WHITE, "Sa3"),  # on cap
        # white  capstone
        (PlayerType.WHITE, "Sa1"),  # on flat
        (PlayerType.WHITE, "Sa2"),  # on standing
        (PlayerType.WHITE, "Sa3"),  # on cap
        # Black flat
        (PlayerType.BLACK, "a1"),  # on flat
        (PlayerType.BLACK, "a2"),  # on standing
        (PlayerType.BLACK, "a3"),  # on cap
        # Black standing
        (PlayerType.BLACK, "Sa1"),  # on flat
        (PlayerType.BLACK, "Sa2"),  # on standing
        (PlayerType.BLACK, "Sa3"),  # on cap
        # Black  capstone
        (PlayerType.BLACK, "Sa1"),  # on flat
        (PlayerType.BLACK, "Sa2"),  # on standing
        (PlayerType.BLACK, "Sa3"),  # on cap
        # On black stones
        # White flat
        (PlayerType.WHITE, "b1"),  # on flat
        (PlayerType.WHITE, "b2"),  # on standing
        (PlayerType.WHITE, "b3"),  # on cap
        # white standing
        (PlayerType.WHITE, "Sb1"),  # on flat
        (PlayerType.WHITE, "Sb2"),  # on standing
        (PlayerType.WHITE, "Sb3"),  # on cap
        # white  capstone
        (PlayerType.WHITE, "Sb1"),  # on flat
        (PlayerType.WHITE, "Sb2"),  # on standing
        (PlayerType.WHITE, "Sb3"),  # on cap
        # Black flat
        (PlayerType.BLACK, "b1"),  # on flat
        (PlayerType.BLACK, "b2"),  # on standing
        (PlayerType.BLACK, "b3"),  # on cap
        # Black standing
        (PlayerType.BLACK, "Sb1"),  # on flat
        (PlayerType.BLACK, "Sb2"),  # on standing
        (PlayerType.BLACK, "Sb3"),  # on cap
        # Black  capstone
        (PlayerType.BLACK, "Sb1"),  # on flat
        (PlayerType.BLACK, "Sb2"),  # on standing
        (PlayerType.BLACK, "Sb3"),  # on cap
    ])
    def test_placing_on_other_stones_fails(self, player: PlayerType, move: str):
        if player == PlayerType.BLACK:
            self.board.do_move(PlayerType.WHITE, parse_move("a4"))
        with pytest.raises(InvalidMoveError):
            self.board.do_move(player, parse_move(move))

    @pytest.mark.parametrize("player, move", [
        # White
        (PlayerType.WHITE, "c1"),  # flat
        (PlayerType.WHITE, "Sc1"),  # standing
        (PlayerType.WHITE, "Cc1"),  # cap
        # Black
        (PlayerType.BLACK, "c1"),  # flat
        (PlayerType.BLACK, "Sc1"),  # standing
        (PlayerType.BLACK, "Cc1"),  # cap
    ])
    def test_placing_on_empty_fields_is_valid(self, player: PlayerType, move: str):
        if player == PlayerType.BLACK:
            self.board.do_move(PlayerType.WHITE, parse_move("a4"))
        self.board.do_move(player, parse_move(move))

    @pytest.mark.parametrize("player, move", [
        # White
        (PlayerType.WHITE, "e1"),
        (PlayerType.WHITE, "Se5"),
        (PlayerType.WHITE, "Ca5"),
        # Black
        (PlayerType.BLACK, "e1"),
        (PlayerType.BLACK, "Se5"),
        (PlayerType.BLACK, "Ca5"),
    ])
    def test_placing_outside_the_board_fails(self, player: PlayerType, move: str):
        if player == PlayerType.BLACK:
            self.board.do_move(PlayerType.WHITE, parse_move("a4"))
        with pytest.raises(InvalidMoveError):
            self.board.do_move(player, parse_move(move))

    def test_white_cant_play_twice(self):
        self.board.do_move(PlayerType.WHITE, parse_move("c1"))
        with pytest.raises(InvalidMoveError):
            self.board.do_move(PlayerType.WHITE, parse_move("c2"))

    def test_black_cant_play_twice(self):
        with pytest.raises(InvalidMoveError):
            self.board.do_move(PlayerType.BLACK, parse_move("c1"))


class TestMovingStacks:
    @pytest.mark.parametrize("board_size", [3, 4, 5, 6, 7, 8])
    def test_move_more_than_carry_limit_fails(self, board_size):
        board = Board(tak_config, board_size=board_size)
        board.get_stack(0, 0).extend([
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
        ])
        with pytest.raises(InvalidMoveError):
            board.do_move(PlayerType.WHITE, parse_move(f"{board_size+1}a1>1{board_size}"))

    @pytest.mark.parametrize("carry", [1, 2, 3, 4, 5, 6])
    def test_move_less_than_carry_limit(self, carry):
        stack = [
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
        ]
        board = Board(tak_config, board_size=6)
        board.initial_moves = False
        board.get_stack(0, 0).extend(stack)
        board.do_move(PlayerType.WHITE, parse_move(f"{carry}a1>{carry}"))
        assert board.get_stack(0, 0) == stack[:-carry]  # except last n
        assert board.get_stack(1, 0) == stack[-carry:]  # last n

    def test_move_works_as_expected(self):
        board = Board(tak_config, board_size=6)
        board.initial_moves = False
        board.get_stack(0, 0).extend([
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.FLAT),
            Stone(PlayerType.BLACK, StoneType.FLAT),
            Stone(PlayerType.WHITE, StoneType.CAPSTONE),
        ])
        board.get_stack(0, 1).extend([Stone(PlayerType.BLACK, StoneType.FLAT)])
        board.get_stack(0, 2).extend([Stone(PlayerType.WHITE, StoneType.FLAT)])
        board.get_stack(0, 3).extend([Stone(PlayerType.WHITE, StoneType.FLAT), Stone(PlayerType.BLACK, StoneType.FLAT)])
        board.get_stack(0, 4).extend([Stone(PlayerType.BLACK, StoneType.FLAT), Stone(PlayerType.WHITE, StoneType.STANDING)])
        board.do_move(PlayerType.WHITE, parse_move(f"6a1+2211"))
        assert board.get_stack(0, 0) == [Stone(PlayerType.BLACK, StoneType.FLAT)]
        assert board.get_stack(0, 1) == [Stone(PlayerType.BLACK, StoneType.FLAT), Stone(PlayerType.BLACK, StoneType.FLAT), Stone(PlayerType.WHITE, StoneType.FLAT)]
        assert board.get_stack(0, 2) == [Stone(PlayerType.WHITE, StoneType.FLAT), Stone(PlayerType.WHITE, StoneType.FLAT), Stone(PlayerType.WHITE, StoneType.FLAT)]
        assert board.get_stack(0, 3) == [Stone(PlayerType.WHITE, StoneType.FLAT), Stone(PlayerType.BLACK, StoneType.FLAT), Stone(PlayerType.BLACK, StoneType.FLAT)]
        assert board.get_stack(0, 4) == [Stone(PlayerType.BLACK, StoneType.FLAT), Stone(PlayerType.WHITE, StoneType.FLAT), Stone(PlayerType.WHITE, StoneType.CAPSTONE)]


# TODO test..
# - moving stacks works
#  - cant move over caps/standings
#  - can't move out of board
# - flattening works
