import pytest

from mytypes import Direction, ParseMoveError, StoneType

from . import Move, MoveStack, PlaceStone, parse_move


class TestParseMove:
    @pytest.mark.parametrize("moveText, expected", [
        (" b3",  PlaceStone("b", "3", StoneType.FLAT)),
        ("b3",  PlaceStone("b", "3", StoneType.FLAT)),
        ("Fb3", PlaceStone("b", "3", StoneType.FLAT)),
        ("Cd4", PlaceStone("d", "4", StoneType.CAPSTONE)),
        ("Se5", PlaceStone("e", "5", StoneType.STANDING)),
    ])
    def test_valid_stone_placing(self, moveText: str, expected: Move):
        assert parse_move(moveText) == expected

    @pytest.mark.parametrize("moveText, expected", [
        # Simple moves
        ("b3<", MoveStack("b", "3", Direction.LEFT)),
        ("b3>", MoveStack("b", "3", Direction.RIGHT)),
        ("b3+", MoveStack("b", "3",  Direction.UP)),
        ("b3-", MoveStack("b", "3", Direction.DOWN)),
        # Pickup only
        ("1b3<", MoveStack("b", "3", Direction.LEFT, 1)),
        ("5b3<", MoveStack("b", "3", Direction.LEFT, 5)),
        # Pickup and droppings
        ("5b3<5", MoveStack("b", "3", Direction.LEFT, 5, [5])),
        ("6b3>321", MoveStack("b", "3", Direction.RIGHT, 6, [3,2,1])),
        ("7b3+43", MoveStack("b", "3",  Direction.UP, 7, [4,3])),
        ("8b3-11111111", MoveStack("b", "3", Direction.DOWN, 8, [1]*8)),
        # Droppings only
        ("b3<5", MoveStack("b", "3", Direction.LEFT, droppings=[5])),
        ("b3>321", MoveStack("b", "3", Direction.RIGHT, droppings=[3,2,1])),
        ("b3+43", MoveStack("b", "3",  Direction.UP, droppings=[4,3])),
        ("b3-11111111", MoveStack("b", "3", Direction.DOWN, droppings=[1]*8)),
    ])
    def test_valid_stack_movement(self, moveText: str, expected: Move):
        assert parse_move(moveText) == expected

    @pytest.mark.parametrize("moveText", [
        ("0b3<"),
        ("10b3<"),
    ])
    def test_invalid_stack_movement(self, moveText: str):
        with pytest.raises(ParseMoveError):
            parse_move(moveText)

    @pytest.mark.parametrize("pickup", [0, 10, 15])
    def test_invalid_pickup(self, pickup):
        with pytest.raises(ParseMoveError):
            parse_move(f"{pickup}b3>")

    @pytest.mark.parametrize("droppings", ["0", "10", "01", "101"])
    def test_invalid_droppings(self, droppings):
        with pytest.raises(ParseMoveError):
            parse_move(f"b3>{droppings}")


class TestMove:
    @pytest.mark.parametrize("x, y, expected_x, expected_y", [
        ("a", "1", 0, 0),
        ("b", "1", 1, 0),
        ("h", "1", 7, 0),
        ("a", "2", 0, 1),
        ("a", "8", 0, 7),
        ("i", "9", 8, 8), # on 9x9
    ])
    def test_get_xy(self, x: str, y: str, expected_x: int, expected_y: int):
        assert Move(x, y).get_xy() == (expected_x, expected_y)

    def test_eq(self):
        assert Move("a", "5") == Move("a", "5")

    @pytest.mark.parametrize("x", ["", "aa", "ab", "j", "k", "l", "m", "z", "A", "B", "0", "1", "2"])
    def test_invalid_x(self, x: str):
        with pytest.raises(BaseException):
            Move(x, "1")

    @pytest.mark.parametrize("y", ["a", "b", "0", "10", "11", ""])
    def test_invalid_y(self, y: str):
        with pytest.raises(BaseException):
            Move("a", y)

class TestPlaceStone:
    def test_eq(self):
        assert PlaceStone("a", "5", StoneType.CAPSTONE) == PlaceStone("a", "5", StoneType.CAPSTONE)
        assert PlaceStone("a", "5", StoneType.CAPSTONE) != Move("a", "5")
        assert PlaceStone("a", "5", StoneType.CAPSTONE) != MoveStack("a", "5", Direction.RIGHT)

class TestMoveStack:
    def test_eq(self):
        assert MoveStack("a", "5", Direction.RIGHT) == MoveStack("a", "5", Direction.RIGHT)
        assert MoveStack("a", "5", Direction.RIGHT) != Move("a", "5")
        assert MoveStack("a", "5", Direction.RIGHT) != PlaceStone("a", "5", StoneType.CAPSTONE)
