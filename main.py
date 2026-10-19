from concurrent.futures import Future, ThreadPoolExecutor

import pygame
import chess
from src.ui.board_renderer import (
    BoardRenderer,
    STATUS_PANEL_HEIGHT,
    format_clock,
)
from src.services.engine_service import EngineService
from src.ui.menu import (
    GameStatistics,
    LOCAL_TWO_PLAYER,
    MenuSettings,
    PLAY_AGAINST_COMPUTER,
    show_menu,
)
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
    board_origin: tuple[int, int] = (0, 0),
) -> tuple[int | None, chess.Move | None]:
    x = position[0] - board_origin[0]
    y = position[1] - board_origin[1]
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
    board_origin: tuple[int, int] = (0, 0),
) -> int | None:
    x = position[0] - board_origin[0]
    y = position[1] - board_origin[1]
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


def get_timeout_winner(
    board: chess.Board,
    flagged_color: chess.Color,
) -> chess.Color | None:
    winner = not flagged_color
    return None if board.has_insufficient_material(winner) else winner


def undo_last_turn(
    board: chess.Board,
    against_computer: bool,
    computer_last_move: chess.Move | None,
) -> bool:
    if not board.move_stack:
        return False

    move_count = (
        2
        if against_computer
        and len(board.move_stack) >= 2
        and board.peek() == computer_last_move
        else 1
    )
    for _ in range(move_count):
        board.pop()
    return True


def play_game(
    screen: pygame.Surface,
    engine_service: EngineService | None = None,
    settings: MenuSettings | None = None,
    statistics: GameStatistics | None = None,
) -> bool:
    renderer = BoardRenderer(screen)
    settings = settings if settings is not None else MenuSettings()
    sounds = SoundManager(muted=not settings.sound_enabled)
    board = chess.Board()
    selected_square = None
    pending_promotion: tuple[int, int] | None = None
    computer_last_move: chess.Move | None = None
    move_log: list[str] = []
    move_scroll_offset = 0
    position_status, game_over = get_position_status(board)
    mode_caption = " - Play Against Computer" if engine_service else ""
    engine_executor = (
        ThreadPoolExecutor(max_workers=1, thread_name_prefix="stockfish")
        if engine_service is not None
        else None
    )
    engine_future: Future[chess.Move | None] | None = None
    pending_confirmation: str | None = None
    return_to_menu = False
    clock_limit_seconds = settings.time_limit_minutes * 60
    clock_remaining = [float(clock_limit_seconds), float(clock_limit_seconds)]
    clock_history: list[tuple[float, float]] = []
    game_result_recorded = False
    timed_out_color: chess.Color | None = None
    last_clock_update = pygame.time.get_ticks()

    def update_caption() -> None:
        pygame.display.set_caption(
            f"Python Chess{mode_caption} - {position_status}"
        )

    def reset_game() -> None:
        nonlocal selected_square, pending_promotion, engine_future
        nonlocal computer_last_move, position_status, game_over, move_scroll_offset
        nonlocal game_result_recorded, timed_out_color

        if engine_future is not None:
            engine_future.cancel()
        board.reset()
        move_log.clear()
        clock_history.clear()
        clock_remaining[:] = (float(clock_limit_seconds), float(clock_limit_seconds))
        move_scroll_offset = 0
        selected_square = None
        pending_promotion = None
        engine_future = None
        computer_last_move = None
        game_result_recorded = False
        timed_out_color = None
        position_status, game_over = get_position_status(board)
        update_caption()

    def undo_turn() -> None:
        nonlocal selected_square, pending_promotion, engine_future
        nonlocal computer_last_move, position_status, game_over, move_scroll_offset
        nonlocal game_result_recorded, timed_out_color

        was_game_over = game_over
        if engine_future is not None:
            engine_future.cancel()
        engine_future = None
        selected_square = None
        pending_promotion = None
        if undo_last_turn(board, engine_service is not None, computer_last_move):
            move_count = len(board.move_stack)
            del move_log[len(board.move_stack):]
            if len(clock_history) > move_count:
                clock_remaining[:] = clock_history[move_count]
                del clock_history[move_count:]
            move_scroll_offset = 0
            computer_last_move = None
            position_status, game_over = get_position_status(board)
            if was_game_over and game_result_recorded and statistics is not None:
                statistics.undo_last_result()
                game_result_recorded = False
            timed_out_color = None
            update_caption()

    def apply_move(move: chess.Move, computer_move: bool = False) -> None:
        nonlocal position_status, game_over, computer_last_move, move_scroll_offset
        nonlocal game_result_recorded

        was_game_over = game_over
        was_capture = board.is_capture(move)
        was_promotion = move.promotion is not None
        clock_history.append((clock_remaining[0], clock_remaining[1]))
        move_log.append(board.san(move))
        board.push(move)
        move_scroll_offset = 0
        if computer_move:
            computer_last_move = move
        position_status, game_over = get_position_status(board)
        if game_over and not was_game_over and statistics is not None:
            outcome = board.outcome(claim_draw=True)
            if outcome is not None:
                statistics.record(outcome)
                game_result_recorded = True
        sounds.play(
            get_move_sound(
                board,
                was_capture,
                was_promotion=was_promotion,
            )
        )
        update_caption()

    update_caption()
    clock = pygame.time.Clock()

    try:
        running = True
        while running:
            now = pygame.time.get_ticks()
            elapsed = max(0, now - last_clock_update) / 1000
            last_clock_update = now
            if (
                settings.timed_games
                and not game_over
                and pending_confirmation is None
            ):
                clock_remaining[board.turn] = max(
                    0,
                    clock_remaining[board.turn] - elapsed,
                )
                if clock_remaining[board.turn] == 0:
                    timed_out_color = board.turn
                    winner = get_timeout_winner(board, timed_out_color)
                    side = "White" if timed_out_color == chess.WHITE else "Black"
                    position_status = (
                        f"{side} ran out of time"
                        if winner is None
                        else f"{side} ran out of time - "
                        f"{'White' if winner == chess.WHITE else 'Black'} wins"
                    )
                    game_over = True
                    if statistics is not None:
                        statistics.record_winner(winner)
                        game_result_recorded = True
                    update_caption()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                    and pending_confirmation is not None
                ):
                    pending_confirmation = None
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_r
                    and pending_confirmation is None
                ):
                    pending_confirmation = "reset"
                elif (
                    event.type == pygame.MOUSEWHEEL
                    and renderer.move_list_rect().collidepoint(pygame.mouse.get_pos())
                    and pending_confirmation is None
                ):
                    move_scroll_offset = max(0, move_scroll_offset - event.y)
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    if pending_confirmation is not None:
                        dialog_buttons = renderer.confirmation_button_rects()
                        if dialog_buttons["confirm"].collidepoint(event.pos):
                            if pending_confirmation == "reset":
                                reset_game()
                            else:
                                return_to_menu = True
                                running = False
                            pending_confirmation = None
                        elif dialog_buttons["cancel"].collidepoint(event.pos):
                            pending_confirmation = None
                    elif renderer.control_button_rects()["sound"].collidepoint(event.pos):
                        sounds.toggle_mute()
                        settings.sound_enabled = not sounds.muted
                    elif renderer.control_button_rects()["undo"].collidepoint(event.pos):
                        undo_turn()
                    elif renderer.control_button_rects()["menu"].collidepoint(event.pos):
                        pending_confirmation = "menu"
                    elif renderer.control_button_rects()["reset"].collidepoint(event.pos):
                        pending_confirmation = "reset"
                    elif (
                        engine_service is None
                        or board.turn == chess.WHITE
                    ) and not game_over:
                        if pending_promotion is not None:
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
                                (renderer.board_x, 0),
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
                                    (renderer.board_x, 0),
                                )
                                if move is not None:
                                    apply_move(move)

            if not running:
                break

            if (
                engine_executor is not None
                and engine_service is not None
                and not game_over
                and pending_confirmation is None
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
            pygame.draw.rect(
                screen,
                (35, 42, 52),
                pygame.Rect(0, 0, screen.get_width(), screen.get_height()),
            )
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
            renderer.draw_controls(sounds.muted)
            renderer.draw_move_list(move_log, move_scroll_offset)
            renderer.draw_status_panel(
                board.turn,
                board.is_check(),
                position_status if game_over else None,
                tuple(clock_remaining) if settings.timed_games else None,
            )
            if pending_confirmation is not None:
                message = (
                    "Reset this game?"
                    if pending_confirmation == "reset"
                    else "Return to the main menu?"
                )
                renderer.draw_confirmation_dialog(message)

            pygame.display.flip()
            clock.tick(60)
    finally:
        if engine_executor is not None:
            engine_executor.shutdown(wait=True, cancel_futures=True)
    return return_to_menu


def main() -> None:
    pygame.init()
    engine_service = None
    settings = MenuSettings()
    statistics = GameStatistics()
    try:
        display_info = pygame.display.Info()
        board_size = min(
            800,
            int(display_info.current_w * 0.8),
            int(display_info.current_h * 0.75),
        )
        board_size = (board_size // 8) * 8

        left_panel_width = max(140, board_size // 5)
        right_panel_width = max(220, board_size // 3)
        screen = pygame.display.set_mode(
            (
                left_panel_width + board_size + right_panel_width,
                board_size + STATUS_PANEL_HEIGHT,
            )
        )
        pygame.display.set_caption("Python Chess")

        while True:
            selected_mode = show_menu(screen, settings, statistics)
            if selected_mode is None:
                break
            if selected_mode == PLAY_AGAINST_COMPUTER:
                engine_service = EngineService(difficulty=settings.difficulty)
            try:
                return_to_menu = play_game(
                    screen,
                    engine_service,
                    settings,
                    statistics,
                )
            finally:
                if engine_service is not None:
                    engine_service.close()
                    engine_service = None
            if not return_to_menu:
                break
    finally:
        try:
            if engine_service is not None:
                engine_service.close()
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
