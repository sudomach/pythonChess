from concurrent.futures import Future, ThreadPoolExecutor

import pygame
import chess
from src.ui.board_renderer import BoardRenderer
from src.services.engine_service import EngineService
from src.ui.menu import LOCAL_TWO_PLAYER, PLAY_AGAINST_COMPUTER, show_menu
from src.ui.sound_manager import SoundManager


def get_position_status(board: chess.Board) -> tuple[str, bool]:
    outcome = board.outcome(claim_draw=True)
    if outcome is not None:
        if outcome.termination == chess.Termination.CHECKMATE:
            winner = "White" if outcome.winner == chess.WHITE else "Black"
            return f"Checkmate - {winner} wins", True
        if outcome.termination == chess.Termination.STALEMATE:
            return "Draw - stalemate", True

        draw_reasons = {
            chess.Termination.INSUFFICIENT_MATERIAL: "insufficient material",
            chess.Termination.SEVENTYFIVE_MOVES: "75-move rule",
            chess.Termination.FIVEFOLD_REPETITION: "fivefold repetition",
            chess.Termination.FIFTY_MOVES: "50-move rule",
            chess.Termination.THREEFOLD_REPETITION: "threefold repetition",
        }
        reason = draw_reasons.get(outcome.termination, "draw")
        return f"Draw - {reason}", True

    if board.is_check():
        side_to_move = "White" if board.turn == chess.WHITE else "Black"
        return f"Check - {side_to_move} to move", False

    side_to_move = "White" if board.turn == chess.WHITE else "Black"
    return f"{side_to_move} to move", False


def handle_board_click(
    position: tuple[int, int],
    board: chess.Board,
    selected_square: int | None,
    square_size: int,
) -> tuple[int | None, chess.Move | None]:
    x, y = position
    board_size = square_size * 8
    if not (0 <= x < board_size and 0 <= y < board_size):
        return selected_square, None

    file_index = x // square_size
    rank_index = 7 - (y // square_size)
    clicked_square = chess.square(file_index, rank_index)
    clicked_piece = board.piece_at(clicked_square)

    if selected_square is None:
        if clicked_piece is not None and clicked_piece.color == board.turn:
            return clicked_square, None
        return None, None

    legal_moves = [
        move
        for move in board.legal_moves
        if move.from_square == selected_square and move.to_square == clicked_square
    ]
    if legal_moves:
        move = next(
            (move for move in legal_moves if move.promotion == chess.QUEEN),
            legal_moves[0],
        )
        return None, move

    if clicked_piece is not None and clicked_piece.color == board.turn:
        return clicked_square, None
    return None, None


def square_at_position(
    position: tuple[int, int],
    square_size: int,
) -> int | None:
    x, y = position
    board_size = square_size * 8
    if not (0 <= x < board_size and 0 <= y < board_size):
        return None
    return chess.square(x // square_size, 7 - y // square_size)


def get_move_sound(
    board: chess.Board,
    was_capture: bool,
    was_promotion: bool = False,
) -> str:
    if board.is_game_over(claim_draw=True):
        return "game_end"
    if board.is_check():
        return "check"
    if was_capture:
        return "capture"
    if was_promotion:
        return "promotion"
    return "move"


def play_game(
    screen: pygame.Surface,
    engine_service: EngineService | None = None,
) -> None:
    renderer = BoardRenderer(screen)
    sounds = SoundManager()
    board = chess.Board()
    selected_square = None
    pending_promotion: tuple[int, int] | None = None
    computer_last_move: chess.Move | None = None
    position_status, game_over = get_position_status(board)
    mode_caption = " - Play Against Computer" if engine_service else ""
    engine_executor = (
        ThreadPoolExecutor(max_workers=1, thread_name_prefix="stockfish")
        if engine_service is not None
        else None
    )
    engine_future: Future[chess.Move | None] | None = None

    def update_caption() -> None:
        pygame.display.set_caption(
            f"Python Chess{mode_caption} - {position_status}"
        )

    def apply_move(move: chess.Move, computer_move: bool = False) -> None:
        nonlocal position_status, game_over, computer_last_move

        was_capture = board.is_capture(move)
        was_promotion = move.promotion is not None
        board.push(move)
        if computer_move:
            computer_last_move = move
        position_status, game_over = get_position_status(board)
        sounds.play(
            get_move_sound(
                board,
                was_capture,
                was_promotion=was_promotion,
            )
        )
        update_caption()

    update_caption()

    try:
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and (
                        engine_service is None
                        or board.turn == chess.WHITE
                        or game_over
                    )
                ):
                    if game_over:
                        if renderer.restart_button_rect().collidepoint(event.pos):
                            board.reset()
                            selected_square = None
                            pending_promotion = None
                            engine_future = None
                            computer_last_move = None
                            position_status, game_over = get_position_status(board)
                            update_caption()
                    elif pending_promotion is not None:
                        for piece_type, rect in renderer.promotion_choice_rects().items():
                            if rect.collidepoint(event.pos):
                                from_square, to_square = pending_promotion
                                apply_move(
                                    chess.Move(
                                        from_square,
                                        to_square,
                                        promotion=piece_type,
                                    )
                                )
                                pending_promotion = None
                                break
                    else:
                        clicked_square = square_at_position(
                            event.pos,
                            renderer.square_size,
                        )
                        promotion_moves = (
                            [
                                move
                                for move in board.legal_moves
                                if move.from_square == selected_square
                                and move.to_square == clicked_square
                                and move.promotion is not None
                            ]
                            if selected_square is not None
                            and clicked_square is not None
                            else []
                        )
                        if promotion_moves:
                            pending_promotion = (selected_square, clicked_square)
                            selected_square = None
                        else:
                            selected_square, move = handle_board_click(
                                event.pos,
                                board,
                                selected_square,
                                renderer.square_size,
                            )
                            if move is not None:
                                apply_move(move)
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_r
                    and game_over
                ):
                    board.reset()
                    selected_square = None
                    pending_promotion = None
                    engine_future = None
                    computer_last_move = None
                    position_status, game_over = get_position_status(board)
                    update_caption()

            if not running:
                break

            if (
                engine_executor is not None
                and engine_service is not None
                and not game_over
            ):
                if board.turn == chess.BLACK and engine_future is None:
                    engine_future = engine_executor.submit(
                        engine_service.get_best_move,
                        board.copy(),
                    )
                if engine_future is not None and engine_future.done():
                    move = engine_future.result()
                    engine_future = None
                    if move is None or move not in board.legal_moves:
                        raise RuntimeError(
                            f"Stockfish returned an invalid move: {move}"
                        )
                    apply_move(move, computer_move=True)
                    selected_square = None

            legal_destinations = set()
            if selected_square is not None:
                legal_destinations = {
                    move.to_square
                    for move in board.legal_moves
                    if move.from_square == selected_square
                }

            screen.fill((255, 255, 255))
            check_square = board.king(board.turn) if board.is_check() else None
            renderer.draw_board(
                selected_square,
                legal_destinations,
                check_square,
                computer_last_move,
            )
            renderer.draw_pieces(board)
            if pending_promotion is not None:
                renderer.draw_promotion_choices(board.turn)
            if engine_future is not None:
                renderer.draw_thinking()
            if game_over:
                renderer.draw_game_over(position_status)

            pygame.display.flip()
            clock.tick(60)
    finally:
        if engine_executor is not None:
            engine_executor.shutdown(wait=True, cancel_futures=True)


def main() -> None:
    pygame.init()
    engine_service = None
    try:
        display_info = pygame.display.Info()
        board_size = min(
            800,
            int(display_info.current_w * 0.8),
            int(display_info.current_h * 0.75),
        )
        board_size = (board_size // 8) * 8

        screen = pygame.display.set_mode((board_size, board_size))
        pygame.display.set_caption("Python Chess")

        selected_mode = show_menu(screen)
        if selected_mode == LOCAL_TWO_PLAYER:
            play_game(screen)
        elif selected_mode == PLAY_AGAINST_COMPUTER:
            engine_service = EngineService()
            play_game(screen, engine_service)
    finally:
        try:
            if engine_service is not None:
                engine_service.close()
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
