import pygame
import chess
from src.ui.board_renderer import BoardRenderer

pygame.init()

display_info = pygame.display.Info()
board_size = min(
    800,
    int(display_info.current_w * 0.8),
    int(display_info.current_h * 0.75),
)
board_size = (board_size // 8) * 8

screen = pygame.display.set_mode((board_size, board_size))
pygame.display.set_caption("Python Chess")

renderer = BoardRenderer(screen)
board = chess.Board()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))
    renderer.draw_board()
    renderer.draw_pieces(board)

    pygame.display.flip()

pygame.quit()