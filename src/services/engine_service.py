import chess
import chess.engine
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

STOCKFISH_PATH = (
    PROJECT_ROOT
    / "engines"
    / "stockfish-windows-x86-64-universal.exe"
)

class EngineService:
    skill_levels = {
        "Easy": 0,
        "Medium": 8,
        "Hard": 16,
        "Expert": 20,
    }

    def __init__(self, engine_path=STOCKFISH_PATH, difficulty="Medium"):
        if not engine_path.exists():
            raise FileNotFoundError(
                f"Stockfish executable not found: {engine_path}"
            )

        self.engine = chess.engine.SimpleEngine.popen_uci(
            str(engine_path)
        )
        self.engine.configure({"Skill Level": self.skill_levels[difficulty]})

    def get_best_move(self, board, time_limit=1.0):
        """Return Stockfish's best move for the current position."""
        result = self.engine.play(
            board,
            chess.engine.Limit(time=time_limit)
        )
        return result.move

    def close(self):
        """Shut down Stockfish cleanly."""
        if self.engine is not None:
            self.engine.quit()
            self.engine = None
