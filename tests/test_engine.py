import chess

from src.services.engine_service import EngineService

board = chess.Board()
engine_service = None

try:
    engine_service = EngineService()

    move = engine_service.get_best_move(board)

    print("Stockfish selected:", move)
    print("Move in chess notation:", board.san(move))

    board.push(move)
    print(board)

except Exception as error:
    print("Engine error:", error)

finally:
    if engine_service is not None:
        engine_service.close()
