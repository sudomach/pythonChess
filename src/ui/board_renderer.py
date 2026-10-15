from pathlib import Path
import pygame
import chess


class BoardRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.square_size = min(screen.get_size()) // 8

        self.light_color = (240, 217, 181)
        self.dark_color = (181, 136, 99)

        project_root = Path(__file__).resolve().parents[2]
        pieces_dir = project_root / "assets" / "pieces" / "vector-chess-pieces" / "Flat"

        self.piece_images = {}

        piece_names ={
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }

        for piece_type, name in piece_names.items():
            for color in ["white", "black"]:
                key =  (piece_type, color == "white")

                image_path = (pieces_dir / f"{name} Flat {color} 288px.png")

                image = pygame.image.load(str(image_path)).convert_alpha()

                self.piece_images[key] = pygame.transform.smoothscale(image, (self.square_size, self.square_size))

    def draw_pieces(self, board):
        for square in chess.SQUARES:
            piece = board.piece_at(square)

            if piece is None:
                continue

            key = (piece.piece_type, piece.color)
            image = self.piece_images[key]

            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)

            x = col * self.square_size
            y = row * self.square_size

            self.screen.blit(image, (x, y))

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = (
                    self.light_color
                    if (row + col) % 2 == 0
                    else self.dark_color
                )
                #creating each square of the chess board
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        col * self.square_size,
                        row * self.square_size,
                        self.square_size,
                        self.square_size
                    )
                )