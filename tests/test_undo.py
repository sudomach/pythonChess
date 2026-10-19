import chess

from main import undo_last_turn


def test_undo_in_local_game_removes_one_move() -> None:
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")

    assert undo_last_turn(board, against_computer=False, computer_last_move=None)
    assert board.peek() == chess.Move.from_uci("e2e4")
    assert len(board.move_stack) == 1


def test_undo_against_computer_removes_completed_turn_pair() -> None:
    board = chess.Board()
    board.push_san("e4")
    computer_move = board.parse_san("e5")
    board.push(computer_move)

    assert undo_last_turn(board, against_computer=True, computer_last_move=computer_move)
    assert not board.move_stack


def test_undo_against_computer_removes_pending_human_move_only() -> None:
    board = chess.Board()
    board.push_san("e4")

    assert undo_last_turn(board, against_computer=True, computer_last_move=None)
    assert not board.move_stack


def test_undo_on_new_game_is_a_noop() -> None:
    assert not undo_last_turn(chess.Board(), against_computer=False, computer_last_move=None)
