from src.profile_manager import ProfileManager
from src.ui.menu import GameStatistics, MenuSettings


def test_profile_manager_persists_credentials_settings_and_stats(tmp_path) -> None:
    profile_path = tmp_path / "players.json"
    manager = ProfileManager(profile_path)

    created = manager.create_account("alice", "secure-pass")
    assert created["password_hash"]
    assert manager.authenticate("alice", "secure-pass") is not None
    assert manager.authenticate("alice", "wrong-pass") is None

    settings = MenuSettings(sound_enabled=False, difficulty="Hard", timed_games=False, time_limit_minutes=10)
    stats = GameStatistics(games_played=3, white_wins=1, black_wins=1, draws=1, estimated_elo=1234.0)
    stats._white_scores = [1.0, 0.0, 0.5]
    stats.history = [
        {"date": "2026-10-29T10:00+03:00", "result": "Draw", "mode": "local"}
    ]

    manager.save_profile("alice", settings.to_dict(), stats.to_dict())

    reloaded = ProfileManager(profile_path)
    profile = reloaded.list_profiles()["alice"]

    assert profile["settings"]["sound_enabled"] is False
    assert profile["settings"]["difficulty"] == "Hard"
    assert profile["settings"]["time_limit_minutes"] == 10
    assert profile["stats"]["games_played"] == 3
    assert profile["stats"]["white_wins"] == 1
    assert profile["stats"]["draws"] == 1
    assert profile["stats"]["estimated_elo"] == 1234.0
    assert profile["stats"]["history"] == stats.history


def test_match_history_round_trips_and_undo_removes_the_result() -> None:
    import chess

    white_win = chess.Board()
    for move in ("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"):
        white_win.push_san(move)

    stats = GameStatistics()
    stats.record(white_win.outcome(), "computer")
    saved_stats = GameStatistics.from_dict(stats.to_dict())

    assert saved_stats.history == stats.history
    assert saved_stats.history[0]["mode"] == "computer"
    assert saved_stats.history[0]["result"] == "White win"

    saved_stats.undo_last_result()

    assert saved_stats.history == []
    assert saved_stats.games_played == 0


def test_profile_manager_ranks_and_deletes_accounts(tmp_path) -> None:
    manager = ProfileManager(tmp_path / "players.json")
    manager.create_account("alice", "alice-pass")
    manager.create_account("bob", "bob-pass")
    manager.save_profile(
        "bob",
        MenuSettings().to_dict(),
        GameStatistics(games_played=2, estimated_elo=1350).to_dict(),
    )

    assert [username for username, _ in manager.leaderboard()] == ["bob", "alice"]

    manager.delete_account("bob")

    assert [username for username, _ in manager.leaderboard()] == ["alice"]
    assert manager.authenticate("bob", "bob-pass") is None
