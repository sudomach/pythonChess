from pathlib import Path
import math
import pygame
import chess


STATUS_PANEL_HEIGHT = 64


def format_clock(seconds: float) -> str:
    total_seconds = max(0, math.ceil(seconds))
    minutes, remainder = divmod(total_seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


class BoardRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.status_panel_height = STATUS_PANEL_HEIGHT
        self.board_area_height = screen.get_height() - self.status_panel_height
        self.right_panel_width = max(220, self.board_area_height // 3)
        self.board_x = max(
            0,
            screen.get_width() - self.board_area_height - self.right_panel_width,
        )
        self.square_size = min(
            self.board_area_height,
            screen.get_width() - self.board_x - self.right_panel_width,
        ) // 8
        self.board_size = self.square_size * 8

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

            x = self.board_x + col * self.square_size
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
                    self.board_x + col * self.square_size,
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

        title_font = pygame.font.Font(None, max(28, self.square_size // 2))
        title = title_font.render(status, True, (255, 255, 255))
        board_center_x = self.board_x + self.board_size // 2
        title_rect = title.get_rect(
            center=(
                board_center_x,
                self.board_area_height // 2 - self.square_size // 3,
            )
        )
        self.screen.blit(title, title_rect)

    def draw_thinking(self) -> None:
        font = pygame.font.Font(None, max(24, self.square_size // 3))
        label = font.render("Stockfish is thinking...", True, (255, 255, 255))
        padding = max(12, self.square_size // 5)
        panel = label.get_rect(
            center=(
                self.board_x + self.board_size // 2,
                self.board_area_height - padding - label.get_height() // 2,
            )
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

    def control_button_rects(self) -> dict[str, pygame.Rect]:
        panel_width = max(1, self.board_x - 24)
        button_height = max(34, self.square_size // 2)
        gap = max(8, self.square_size // 8)
        total_height = 4 * button_height + 3 * gap
        y = max(48, (self.board_area_height - total_height) // 2)
        return {
            name: pygame.Rect(
                12,
                y + index * (button_height + gap),
                panel_width,
                button_height,
            )
            for index, name in enumerate(("undo", "menu", "reset", "sound"))
        }

    def draw_controls(self, muted: bool) -> dict[str, pygame.Rect]:
        buttons = self.control_button_rects()
        title_font = pygame.font.Font(None, max(20, self.square_size // 4))
        title = title_font.render("Controls", True, (230, 230, 230))
        self.screen.blit(title, (12, max(12, buttons["undo"].top - title.get_height() - 12)))
        labels = {
            "undo": "Undo",
            "menu": "Menu",
            "reset": "Reset",
            "sound": "Sound: Off" if muted else "Sound: On",
        }
        colors = {
            "undo": (73, 99, 132),
            "menu": (73, 99, 132),
            "reset": (145, 95, 55),
            "sound": (105, 65, 65) if muted else (55, 105, 75),
        }
        font = pygame.font.Font(None, max(16, self.square_size // 5))
        for name, button in buttons.items():
            pygame.draw.rect(self.screen, colors[name], button, border_radius=6)
            label = font.render(labels[name], True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=button.center))
        return buttons

    def move_list_rect(self) -> pygame.Rect:
        left = self.board_x + self.board_size + 12
        return pygame.Rect(
            left,
            12,
            max(1, self.screen.get_width() - left - 12),
            self.board_area_height - 24,
        )

    def draw_move_list(
        self,
        moves: list[str],
        scroll_offset: int = 0,
    ) -> None:
        panel = self.move_list_rect()
        pygame.draw.rect(self.screen, (40, 46, 56), panel, border_radius=8)
        inset = max(10, self.square_size // 8)
        title_font = pygame.font.Font(None, max(22, self.square_size // 3))
        title = title_font.render("Moves", True, (245, 245, 245))
        self.screen.blit(title, (panel.x + inset, panel.y + inset))

        row_height = max(22, self.square_size // 4)
        moves_top = panel.y + inset * 2 + title.get_height()
        visible_rows = max(0, (panel.bottom - inset - moves_top) // row_height)
        rows = [
            f"{index // 2 + 1}. {moves[index]}"
            + (f"  {moves[index + 1]}" if index + 1 < len(moves) else "")
            for index in range(0, len(moves), 2)
        ]
        start = max(0, len(rows) - visible_rows - scroll_offset)
        font = pygame.font.Font(None, max(18, self.square_size // 5))
        for row_index, text in enumerate(rows[start : start + visible_rows]):
            label = font.render(text, True, (225, 225, 225))
            self.screen.blit(
                label,
                (panel.x + inset, moves_top + row_index * row_height),
            )

    def draw_status_panel(
        self,
        side_to_move: chess.Color,
        in_check: bool,
        game_over_status: str | None = None,
        clock_times: tuple[float, float] | None = None,
    ) -> None:
        panel = pygame.Rect(
            0,
            self.board_area_height,
            self.screen.get_width(),
            self.status_panel_height,
        )
        pygame.draw.rect(self.screen, (28, 34, 43), panel)
        pygame.draw.line(
            self.screen,
            (90, 101, 116),
            panel.topleft,
            panel.topright,
            2,
        )

        if game_over_status is not None:
            text = game_over_status
            color = (245, 210, 135)
        else:
            side = "White" if side_to_move == chess.WHITE else "Black"
            text = f"Next move: {side}"
            color = (255, 110, 100) if in_check else (235, 240, 245)
            if in_check:
                text += f"  |  CHECK: {side} king is in check!"

        if clock_times is None:
            font = pygame.font.Font(None, max(22, self.status_panel_height // 2))
            label = font.render(text, True, color)
            self.screen.blit(label, label.get_rect(center=panel.center))
            return

        message_font = pygame.font.Font(None, max(20, self.status_panel_height // 3))
        message = message_font.render(text, True, color)
        self.screen.blit(
            message,
            message.get_rect(center=(panel.centerx, panel.y + panel.height // 3)),
        )
        clock_font = pygame.font.Font(None, max(20, self.status_panel_height // 3))
        for x, side, seconds in (
            (panel.width // 4, "White", clock_times[chess.WHITE]),
            (panel.width * 3 // 4, "Black", clock_times[chess.BLACK]),
        ):
            clock_text = f"{side}: {format_clock(seconds)}"
            clock_color = (
                (255, 110, 100)
                if seconds <= 10 and side_to_move == (side == "White")
                else (235, 240, 245)
            )
            label = clock_font.render(clock_text, True, clock_color)
            self.screen.blit(
                label,
                label.get_rect(center=(panel.x + x, panel.y + panel.height * 2 // 3)),
            )

    def draw_confirmation_dialog(self, message: str) -> dict[str, pygame.Rect]:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        width, height = self.screen.get_size()
        panel_width = min(width - 24, max(240, self.square_size * 5))
        panel_height = max(136, self.square_size * 2)
        panel = pygame.Rect(
            self.board_x + (self.board_size - panel_width) // 2,
            (self.board_area_height - panel_height) // 2,
            panel_width,
            panel_height,
        )
        pygame.draw.rect(self.screen, (40, 46, 56), panel, border_radius=10)

        message_font = pygame.font.Font(None, max(18, self.square_size // 3))
        message_label = message_font.render(message, True, (255, 255, 255))
        self.screen.blit(
            message_label,
            message_label.get_rect(center=(panel.centerx, panel.y + panel_height // 3)),
        )

        buttons = self.confirmation_button_rects()
        button_font = pygame.font.Font(None, max(18, self.square_size // 4))
        for name, label, color in (
            ("confirm", "Confirm", (145, 75, 65)),
            ("cancel", "Cancel", (73, 99, 132)),
        ):
            button = buttons[name]
            pygame.draw.rect(self.screen, color, button, border_radius=6)
            rendered_label = button_font.render(label, True, (255, 255, 255))
            self.screen.blit(rendered_label, rendered_label.get_rect(center=button.center))
        return buttons

    def confirmation_button_rects(self) -> dict[str, pygame.Rect]:
        width, height = self.screen.get_size()
        panel_width = min(width - 24, max(240, self.square_size * 5))
        panel_height = max(136, self.square_size * 2)
        panel = pygame.Rect(
            self.board_x + (self.board_size - panel_width) // 2,
            (self.board_area_height - panel_height) // 2,
            panel_width,
            panel_height,
        )
        button_width = min(100, (panel_width - 36) // 2)
        button_height = max(32, self.square_size // 3)
        button_y = panel.bottom - button_height - max(12, self.square_size // 6)
        return {
            "confirm": pygame.Rect(
                panel.centerx - button_width - 6,
                button_y,
                button_width,
                button_height,
            ),
            "cancel": pygame.Rect(
                panel.centerx + 6,
                button_y,
                button_width,
                button_height,
            ),
        }

    def promotion_choice_rects(self) -> dict[int, pygame.Rect]:
        button_size = self.square_size
        panel_padding = max(8, self.square_size // 8)
        panel_width = button_size * 4 + panel_padding * 2
        panel_height = button_size + panel_padding * 2
        panel = pygame.Rect(
            self.board_x + (self.board_size - panel_width) // 2,
            (self.board_area_height - panel_height) // 2,
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