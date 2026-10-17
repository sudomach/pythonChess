from pathlib import Path
import pygame
import chess


class BoardRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.square_size = min(screen.get_size()) // 8

        self.light_color = (240, 217, 181)
        self.dark_color = (181, 136, 99)
        self.selected_highlight = pygame.Surface(
            (self.square_size, self.square_size),
            pygame.SRCALPHA,
        )
        self.selected_highlight.fill((255, 215, 0, 110))
        self.destination_highlight = pygame.Surface(
            (self.square_size, self.square_size),
            pygame.SRCALPHA,
        )
        self.destination_highlight.fill((50, 180, 70, 100))
        self.check_highlight = pygame.Surface(
            (self.square_size, self.square_size),
            pygame.SRCALPHA,
        )
        self.check_highlight.fill((220, 35, 35, 155))
        self.last_move_highlight = pygame.Surface(
            (self.square_size, self.square_size),
            pygame.SRCALPHA,
        )
        self.last_move_highlight.fill((245, 205, 55, 115))

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

    def draw_board(
        self,
        selected_square: int | None = None,
        legal_destinations: set[int] | None = None,
        check_square: int | None = None,
        last_move: chess.Move | None = None,
    ):
        for row in range(8):
            for col in range(8):
                color = (
                    self.light_color
                    if (row + col) % 2 == 0
                    else self.dark_color
                )
                square_rect = (
                    col * self.square_size,
                    row * self.square_size,
                    self.square_size,
                    self.square_size,
                )
                pygame.draw.rect(
                    self.screen,
                    color,
                    square_rect,
                )
                square = chess.square(col, 7 - row)
                if last_move is not None and square in (
                    last_move.from_square,
                    last_move.to_square,
                ):
                    self.screen.blit(self.last_move_highlight, square_rect[:2])
                if square == selected_square:
                    self.screen.blit(self.selected_highlight, square_rect[:2])
                elif legal_destinations is not None and square in legal_destinations:
                    self.screen.blit(self.destination_highlight, square_rect[:2])
                if square == check_square:
                    self.screen.blit(self.check_highlight, square_rect[:2])

    def draw_game_over(self, status: str) -> pygame.Rect:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        width, height = self.screen.get_size()
        title_font = pygame.font.Font(None, max(28, self.square_size // 2))
        button_font = pygame.font.Font(None, max(22, self.square_size // 3))
        title = title_font.render(status, True, (255, 255, 255))
        title_rect = title.get_rect(center=(width // 2, height // 2 - self.square_size // 3))
        self.screen.blit(title, title_rect)

        button = self.restart_button_rect()
        pygame.draw.rect(self.screen, (55, 135, 75), button, border_radius=8)
        label = button_font.render("Play again", True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=button.center))
        return button

    def draw_thinking(self) -> None:
        width, height = self.screen.get_size()
        font = pygame.font.Font(None, max(24, self.square_size // 3))
        label = font.render("Stockfish is thinking...", True, (255, 255, 255))
        padding = max(12, self.square_size // 5)
        panel = label.get_rect(
            center=(width // 2, height - padding - label.get_height() // 2)
        ).inflate(
            padding * 2, padding * 2
        )
        background = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(
            background,
            (35, 42, 52, 150),
            background.get_rect(),
            border_radius=8,
        )
        self.screen.blit(background, panel)
        self.screen.blit(label, label.get_rect(center=panel.center))

    def restart_button_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        button_width = min(width - 32, self.square_size * 3)
        button_height = max(36, self.square_size // 2)
        return pygame.Rect(
            (width - button_width) // 2,
            height // 2 + self.square_size // 6,
            button_width,
            button_height,
        )

    def promotion_choice_rects(self) -> dict[int, pygame.Rect]:
        width, height = self.screen.get_size()
        button_size = self.square_size
        panel_padding = max(8, self.square_size // 8)
        panel_width = button_size * 4 + panel_padding * 2
        panel_height = button_size + panel_padding * 2
        panel = pygame.Rect(
            (width - panel_width) // 2,
            (height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        piece_types = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
        return {
            piece_type: pygame.Rect(
                panel.x + panel_padding + index * button_size,
                panel.y + panel_padding,
                button_size,
                button_size,
            )
            for index, piece_type in enumerate(piece_types)
        }

    def draw_promotion_choices(self, color: chess.Color) -> dict[int, pygame.Rect]:
        button_rects = self.promotion_choice_rects()
        panel_padding = max(8, self.square_size // 8)
        first_button = button_rects[chess.QUEEN]
        panel = pygame.Rect(
            first_button.x - panel_padding,
            first_button.y - panel_padding,
            self.square_size * 4 + 2 * panel_padding,
            self.square_size + 2 * panel_padding,
        )
        pygame.draw.rect(self.screen, (35, 35, 35), panel, border_radius=8)
        for piece_type, rect in button_rects.items():
            pygame.draw.rect(self.screen, (225, 225, 225), rect)
            image = self.piece_images[(piece_type, color)]
            self.screen.blit(image, rect)
        return button_rects