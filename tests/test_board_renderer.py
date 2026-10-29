import chess
import pygame

from src.ui.board_renderer import BoardRenderer, STATUS_PANEL_HEIGHT


def test_board_renderer_resizes_board_and_piece_images() -> None:
    renderer = BoardRenderer.__new__(BoardRenderer)
    renderer.status_panel_height = STATUS_PANEL_HEIGHT
    renderer._source_piece_images = {
        (chess.PAWN, chess.WHITE): pygame.Surface((16, 16)),
    }

    renderer.resize(pygame.Surface((640, 480)))
    initial_square_size = renderer.square_size

    resized_screen = pygame.Surface((1000, 800))
    renderer.resize(resized_screen)

    assert renderer.screen is resized_screen
    assert renderer.square_size > initial_square_size
    assert renderer.piece_images[(chess.PAWN, chess.WHITE)].get_size() == (
        renderer.square_size,
        renderer.square_size,
    )
