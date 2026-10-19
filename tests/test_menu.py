from pathlib import Path
from unittest.mock import Mock, patch

import chess

from src.services.engine_service import EngineService
from src.ui.board_renderer import format_clock
from src.ui.menu import HELP_SLIDES, GameStatistics, MenuSettings


def test_help_slides_cover_piece_moves_and_special_rules() -> None:
    slide_titles = {title for title, _, _ in HELP_SLIDES}

    assert {
        "Pawn",
        "Knight",
        "Bishop",
        "Rook",
        "Queen",
        "King",
        "Check",
        "Checkmate",
        "Castling",
        "En passant",
        "Pawn promotion",
    } <= slide_titles
    assert all(description and diagram for _, description, diagram in HELP_SLIDES)


def test_statistics_track_wins_and_draws() -> None:
    statistics = GameStatistics()
    white_wins = chess.Board()
    for move in ("f3", "e5", "g4", "Qh4#"):
        white_wins.push_san(move)

    drawn_game = chess.Board()
    drawn_game.set_fen("7k/5K2/6Q1/8/8/8/8/8 b - - 0 1")

    statistics.record(white_wins.outcome())
    statistics.record(drawn_game.outcome())

    assert statistics.games_played == 2
    assert statistics.white_wins == 0
    assert statistics.black_wins == 1
    assert statistics.draws == 1
    assert statistics.win_percentage == 0
    assert statistics.loss_percentage == 50
    assert statistics.draw_percentage == 50
    assert statistics.estimated_elo < 1200


def test_statistics_estimate_rating_from_white_score() -> None:
    statistics = GameStatistics()
    white_win = chess.Board()
    for move in ("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"):
        white_win.push_san(move)

    statistics.record(white_win.outcome())

    assert statistics.estimated_elo == 1216
    assert statistics.win_percentage == 100
    assert statistics.draw_percentage == 0
    assert statistics.loss_percentage == 0


def test_undo_last_result_restores_session_statistics() -> None:
    statistics = GameStatistics()
    white_win = chess.Board()
    for move in ("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"):
        white_win.push_san(move)
    statistics.record(white_win.outcome())

    statistics.undo_last_result()

    assert statistics.games_played == 0
    assert statistics.white_wins == 0
    assert statistics.estimated_elo == 1200


def test_menu_settings_default_to_sound_enabled() -> None:
    assert MenuSettings().sound_enabled


def test_settings_include_clock_and_computer_difficulty_defaults() -> None:
    settings = MenuSettings()

    assert settings.difficulty == "Medium"
    assert settings.timed_games
    assert settings.time_limit_minutes == 5
    assert EngineService.skill_levels == {
        "Easy": 0,
        "Medium": 8,
        "Hard": 16,
        "Expert": 20,
    }


def test_engine_service_configures_selected_stockfish_skill() -> None:
    engine = Mock()
    with patch(
        "src.services.engine_service.chess.engine.SimpleEngine.popen_uci",
        return_value=engine,
    ):
        EngineService(engine_path=Path(__file__), difficulty="Expert")

    engine.configure.assert_called_once_with({"Skill Level": 20})


def test_clock_display_rounds_up_remaining_seconds() -> None:
    assert format_clock(300) == "05:00"
    assert format_clock(59.1) == "01:00"
    assert format_clock(0) == "00:00"


def test_timeout_win_and_insufficient_material_draw() -> None:
    from main import get_timeout_winner

    assert get_timeout_winner(chess.Board(), chess.WHITE) == chess.BLACK

    kings_only = chess.Board("7k/8/8/8/8/8/8/K7 w - - 0 1")
    assert get_timeout_winner(kings_only, chess.WHITE) is None
