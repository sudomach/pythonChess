from dataclasses import dataclass, field

import chess
import pygame


LOCAL_TWO_PLAYER = "local"
PLAY_AGAINST_COMPUTER = "computer"

HELP_SLIDES = (
    (
        "Pawn",
        "Moves forward one square into an empty square. On its first move, it may move two squares if both are clear. It captures one square diagonally forward, never straight ahead.",
        "pawn",
    ),
    (
        "Knight",
        "Moves in an L shape: two squares in one direction and one perpendicular. Knights can jump over pieces. Capture by landing on an opponent's piece.",
        "knight",
    ),
    (
        "Bishop",
        "Slides any number of squares diagonally. It cannot jump over pieces; capture by landing on an opponent along a clear diagonal.",
        "bishop",
    ),
    (
        "Rook",
        "Slides any number of squares horizontally or vertically. It cannot jump over pieces; capture by landing on an opponent along a clear rank or file.",
        "rook",
    ),
    (
        "Queen",
        "Combines the rook and bishop: slides any number of squares horizontally, vertically, or diagonally. It cannot jump over pieces.",
        "queen",
    ),
    (
        "King",
        "Moves one square in any direction. It captures by landing on an opponent's piece, but may never move onto an attacked square.",
        "king",
    ),
    (
        "Check",
        "A king is in check when an opposing piece attacks its square. The player must escape check by moving the king, blocking the attack, or capturing the attacker.",
        "check",
    ),
    (
        "Checkmate",
        "A king is checkmated when it is in check and there is no legal move that gets it out of check. The game ends and the attacking side wins.",
        "checkmate",
    ),
    (
        "Castling",
        "Move the king two squares toward a rook; that rook moves to the square the king crossed. It is allowed only if neither piece has moved, the path is clear, and the king is not in, crossing, or entering check.",
        "castling",
    ),
    (
        "En passant",
        "If a pawn advances two squares from its starting square and lands beside an enemy pawn, that pawn may capture it as if it had moved one square. This capture must be made immediately on the next move.",
        "en_passant",
    ),
    (
        "Pawn promotion",
        "When a pawn reaches the farthest rank, it must promote to a queen, rook, bishop, or knight. Promotion can also happen after a pawn captures onto that rank.",
        "promotion",
    ),
)


@dataclass
class MenuSettings:
    sound_enabled: bool = True
    difficulty: str = "Medium"
    timed_games: bool = True
    time_limit_minutes: int = 5


@dataclass
class GameStatistics:
    games_played: int = 0
    white_wins: int = 0
    black_wins: int = 0
    draws: int = 0
    estimated_elo: float = 1200
    _white_scores: list[float] = field(default_factory=list, repr=False)

    def record(self, outcome: chess.Outcome) -> None:
        self.record_winner(outcome.winner)

    def record_winner(self, winner: chess.Color | None) -> None:
        self.games_played += 1
        if winner is None:
            self.draws += 1
            self._white_scores.append(0.5)
        elif winner == chess.WHITE:
            self.white_wins += 1
            self._white_scores.append(1.0)
        else:
            self.black_wins += 1
            self._white_scores.append(0.0)
        self._update_estimated_elo()

    def undo_last_result(self) -> None:
        if not self._white_scores:
            return

        score = self._white_scores.pop()
        self.games_played -= 1
        if score == 1.0:
            self.white_wins -= 1
        elif score == 0.0:
            self.black_wins -= 1
        else:
            self.draws -= 1
        self._update_estimated_elo()

    @property
    def win_percentage(self) -> float:
        return self._percentage(self.white_wins)

    @property
    def draw_percentage(self) -> float:
        return self._percentage(self.draws)

    @property
    def loss_percentage(self) -> float:
        return self._percentage(self.black_wins)

    def _percentage(self, count: int) -> float:
        if not self.games_played:
            return 0.0
        return count * 100 / self.games_played

    def _update_estimated_elo(self) -> None:
        rating = 1200.0
        for score in self._white_scores:
            expected_score = 1 / (1 + 10 ** ((1200 - rating) / 400))
            rating += 32 * (score - expected_score)
        self.estimated_elo = rating


def _draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    color: tuple[int, int, int] = (73, 99, 132),
) -> None:
    pygame.draw.rect(screen, color, rect, border_radius=8)
    font = pygame.font.Font(None, max(18, min(30, screen.get_width() // 22)))
    text = font.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=rect.center))


def _draw_page(
    screen: pygame.Surface,
    title_text: str,
    lines: list[str],
) -> dict[str, pygame.Rect]:
    width, height = screen.get_size()
    screen.fill((35, 42, 52))
    title_font = pygame.font.Font(None, max(36, min(58, width // 8)))
    line_font = pygame.font.Font(None, max(20, min(30, width // 24)))
    title = title_font.render(title_text, True, (245, 245, 245))
    screen.blit(title, title.get_rect(center=(width // 2, height // 4)))

    for index, line in enumerate(lines):
        label = line_font.render(line, True, (225, 230, 235))
        screen.blit(
            label,
            label.get_rect(center=(width // 2, height // 2 + index * 34)),
        )

    button_width = min(width - 32, max(220, int(min(width, height) * 0.55)))
    button_height = max(44, min(58, height // 10))
    back_button = pygame.Rect(
        (width - button_width) // 2,
        height - button_height - max(24, height // 12),
        button_width,
        button_height,
    )
    _draw_button(screen, back_button, "Back to Menu", (55, 135, 75))
    return {"back": back_button}


def _draw_settings_page(
    screen: pygame.Surface,
    settings: MenuSettings,
) -> dict[str, pygame.Rect]:
    width, height = screen.get_size()
    screen.fill((35, 42, 52))
    title_font = pygame.font.Font(None, max(36, min(58, width // 8)))
    title = title_font.render("Settings", True, (245, 245, 245))
    screen.blit(title, title.get_rect(center=(width // 2, height // 6)))

    row_height = max(40, min(52, height // 12))
    button_width = min(width - 32, max(230, int(min(width, height) * 0.52)))
    left = (width - button_width) // 2
    row_gap = max(12, height // 35)
    first_row = height // 3
    rows = {
        name: pygame.Rect(left, first_row + index * (row_height + row_gap), button_width, row_height)
        for index, name in enumerate(("sound", "difficulty", "timed", "time"))
    }
    _draw_button(
        screen,
        rows["sound"],
        f"Sound: {'On' if settings.sound_enabled else 'Off'}",
        (55, 135, 75) if settings.sound_enabled else (145, 75, 65),
    )
    _draw_button(
        screen,
        rows["difficulty"],
        f"Computer difficulty: {settings.difficulty}",
    )
    _draw_button(
        screen,
        rows["timed"],
        f"Timed games: {'On' if settings.timed_games else 'Off'}",
        (55, 135, 75) if settings.timed_games else (73, 99, 132),
    )

    time_width = (button_width - row_gap) // 2
    time_buttons = {
        "time_decrease": pygame.Rect(left, rows["time"].y, time_width, row_height),
        "time_increase": pygame.Rect(
            left + time_width + row_gap,
            rows["time"].y,
            time_width,
            row_height,
        ),
    }
    time_label_font = pygame.font.Font(None, max(18, min(26, width // 28)))
    time_label = time_label_font.render("Time per player", True, (225, 230, 235))
    screen.blit(
        time_label,
        time_label.get_rect(
            center=(width // 2, rows["time"].top - time_label.get_height() // 2 - 4)
        ),
    )
    _draw_button(
        screen,
        time_buttons["time_decrease"],
        f"-  {settings.time_limit_minutes} min",
        (73, 99, 132) if settings.timed_games else (75, 78, 84),
    )
    _draw_button(
        screen,
        time_buttons["time_increase"],
        f"+  {settings.time_limit_minutes} min",
        (73, 99, 132) if settings.timed_games else (75, 78, 84),
    )

    back_height = max(40, min(52, height // 12))
    back_width = min(width - 32, max(220, int(min(width, height) * 0.55)))
    back = pygame.Rect(
        (width - back_width) // 2,
        height - back_height - max(24, height // 12),
        back_width,
        back_height,
    )
    _draw_button(screen, back, "Back to Menu", (55, 135, 75))
    rows.update(time_buttons)
    rows["back"] = back
    return rows


def _wrap_text(
    text: str,
    font: pygame.font.Font,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current_line = ""
    for word in text.split():
        candidate = f"{current_line} {word}".strip()
        if current_line and font.size(candidate)[0] > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = candidate
    if current_line:
        lines.append(current_line)
    return lines


def _draw_piece_diagram(
    screen: pygame.Surface,
    rect: pygame.Rect,
    piece_name: str,
) -> None:
    background = pygame.Rect(rect.x, rect.y, rect.width, rect.height)
    pygame.draw.rect(screen, (40, 46, 56), background, border_radius=10)
    cell_size = min((rect.width - 32) // 5, (rect.height - 32) // 5)
    grid_size = cell_size * 5
    left = rect.centerx - grid_size // 2
    top = rect.centery - grid_size // 2

    offsets: set[tuple[int, int]] = set()
    captures: set[tuple[int, int]] = set()
    if piece_name == "pawn":
        offsets = {(0, -1), (0, -2)}
        captures = {(-1, -1), (1, -1)}
    elif piece_name == "knight":
        offsets = {
            (dx, dy)
            for dx, dy in (
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1),
            )
        }
        captures = offsets.copy()
    elif piece_name in ("bishop", "rook", "queen"):
        directions = {
            "bishop": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
            "rook": ((-1, 0), (1, 0), (0, -1), (0, 1)),
            "queen": (
                (-1, -1), (-1, 1), (1, -1), (1, 1),
                (-1, 0), (1, 0), (0, -1), (0, 1),
            ),
        }[piece_name]
        offsets = {
            (dx * distance, dy * distance)
            for dx, dy in directions
            for distance in range(1, 5)
        }
        captures = offsets.copy()
    elif piece_name == "king":
        offsets = {
            (dx, dy)
            for dx in range(-1, 2)
            for dy in range(-1, 2)
            if (dx, dy) != (0, 0)
        }
        captures = offsets.copy()

    for row in range(5):
        for column in range(5):
            square = pygame.Rect(
                left + column * cell_size,
                top + row * cell_size,
                cell_size,
                cell_size,
            )
            white = (row + column) % 2 == 0
            color = (232, 220, 197) if white else (140, 122, 102)
            offset = (column - 2, row - 2)
            if offset == (0, 0):
                color = (218, 177, 75)
            elif offset in captures:
                color = (190, 86, 79)
            elif offset in offsets:
                color = (91, 165, 111)
            pygame.draw.rect(screen, color, square)

    symbols = {
        "pawn": "P",
        "knight": "N",
        "bishop": "B",
        "rook": "R",
        "queen": "Q",
        "king": "K",
    }
    if piece_name in symbols:
        symbol_font = pygame.font.Font(None, max(24, cell_size * 2 // 3))
        symbol = symbol_font.render(symbols[piece_name], True, (30, 35, 40))
        screen.blit(
            symbol,
            symbol.get_rect(center=(left + 2 * cell_size + cell_size // 2,
                                    top + 2 * cell_size + cell_size // 2)),
        )
    elif piece_name == "castling":
        font = pygame.font.Font(None, max(20, rect.width // 9))
        label = font.render("King: e1 -> g1   Rook: h1 -> f1", True, (235, 240, 245))
        screen.blit(label, label.get_rect(center=rect.center))
        return
    else:
        font = pygame.font.Font(None, max(20, rect.width // 8))
        labels = {
            "check": "KING ATTACKED",
            "checkmate": "CHECK + NO ESCAPE",
            "en_passant": "e.p.",
            "promotion": "P -> Q / R / B / N",
        }
        label = font.render(labels.get(piece_name, ""), True, (235, 240, 245))
        screen.blit(label, label.get_rect(center=rect.center))
        return

    legend_y = min(rect.bottom - 12, top + grid_size + 16)
    legend_font = pygame.font.Font(None, max(16, rect.width // 14))
    for center_x, color, text in (
        (rect.centerx - rect.width // 6, (91, 165, 111), "Move"),
        (rect.centerx + rect.width // 6, (190, 86, 79), "Capture"),
    ):
        pygame.draw.circle(screen, color, (center_x - 24, legend_y), 6)
        legend = legend_font.render(text, True, (230, 230, 230))
        screen.blit(legend, legend.get_rect(midleft=(center_x - 14, legend_y)))


def _draw_help_slide(
    screen: pygame.Surface,
    slide_index: int,
) -> dict[str, pygame.Rect]:
    width, height = screen.get_size()
    title_text, description, diagram_name = HELP_SLIDES[slide_index]
    screen.fill((35, 42, 52))

    title_font = pygame.font.Font(None, max(36, min(58, width // 8)))
    title = title_font.render(title_text, True, (245, 245, 245))
    screen.blit(title, title.get_rect(center=(width // 2, max(40, height // 12))))

    content_top = max(90, height // 6)
    button_height = max(44, min(58, height // 10))
    button_y = height - button_height - max(24, height // 12)
    content_bottom = button_y - 18
    content_height = max(100, content_bottom - content_top)
    side_margin = max(20, width // 24)
    diagram_width = min(width // 3, content_height)
    diagram_rect = pygame.Rect(
        side_margin,
        content_top + (content_height - diagram_width) // 2,
        diagram_width,
        min(diagram_width, content_height),
    )
    _draw_piece_diagram(screen, diagram_rect, diagram_name)

    text_left = diagram_rect.right + max(20, width // 30)
    text_width = max(1, width - text_left - side_margin)
    body_font = pygame.font.Font(None, max(20, min(30, width // 24)))
    lines = _wrap_text(description, body_font, text_width)
    line_height = body_font.get_linesize() + 8
    text_y = content_top + max(0, (content_height - len(lines) * line_height) // 2)
    for line in lines:
        rendered = body_font.render(line, True, (225, 230, 235))
        screen.blit(rendered, (text_left, text_y))
        text_y += line_height

    button_width = min(width // 4, max(120, width // 6))
    gap = max(8, width // 80)
    back_width = min(width // 3, max(150, width // 5))
    center = width // 2
    buttons = {
        "previous": pygame.Rect(
            center - button_width - back_width // 2 - gap,
            button_y,
            button_width,
            button_height,
        ),
        "back": pygame.Rect(
            center - back_width // 2,
            button_y,
            back_width,
            button_height,
        ),
        "next": pygame.Rect(
            center + back_width // 2 + gap,
            button_y,
            button_width,
            button_height,
        ),
    }
    _draw_button(
        screen,
        buttons["previous"],
        "Previous",
        (73, 99, 132) if slide_index > 0 else (75, 78, 84),
    )
    _draw_button(screen, buttons["back"], "Back to Menu", (55, 135, 75))
    _draw_button(
        screen,
        buttons["next"],
        "Next",
        (73, 99, 132) if slide_index < len(HELP_SLIDES) - 1 else (75, 78, 84),
    )
    counter_font = pygame.font.Font(None, max(18, width // 40))
    counter = counter_font.render(
        f"{slide_index + 1} / {len(HELP_SLIDES)}",
        True,
        (190, 198, 208),
    )
    screen.blit(counter, counter.get_rect(center=(center, button_y - 14)))
    return buttons


def draw_menu(
    screen: pygame.Surface,
    message: str | None = None,
) -> dict[str, pygame.Rect]:
    width, height = screen.get_size()
    screen.fill((35, 42, 52))

    title_font = pygame.font.Font(None, max(36, min(58, width // 8)))
    message_font = pygame.font.Font(None, max(18, min(26, width // 22)))

    title = title_font.render("Python Chess", True, (245, 245, 245))
    screen.blit(title, title.get_rect(center=(width // 2, height // 5)))

    labels = (
        ("local", "Local Two Player Mode", (55, 135, 75)),
        ("computer", "Play Against Computer", (73, 99, 132)),
        ("settings", "Settings", (73, 99, 132)),
        ("stats", "Stats", (73, 99, 132)),
        ("help", "Help", (73, 99, 132)),
        ("quit", "Quit", (145, 75, 65)),
    )
    button_width = min(width - 32, max(240, int(min(width, height) * 0.68)))
    button_height = max(40, min(52, height // 12))
    gap = max(7, height // 90)
    total_height = len(labels) * button_height + (len(labels) - 1) * gap
    first_button_y = max(height // 3, (height - total_height) // 2)
    buttons = {
        key: pygame.Rect(
            (width - button_width) // 2,
            first_button_y + index * (button_height + gap),
            button_width,
            button_height,
        )
        for index, (key, _, _) in enumerate(labels)
    }

    for key, label, color in labels:
        _draw_button(screen, buttons[key], label, color)

    if message:
        rendered_message = message_font.render(message, True, (240, 200, 120))
        screen.blit(
            rendered_message,
            rendered_message.get_rect(
                center=(width // 2, height - max(18, height // 35))
            ),
        )

    return buttons


def show_menu(
    screen: pygame.Surface,
    settings: MenuSettings | None = None,
    statistics: GameStatistics | None = None,
) -> str | None:
    settings = settings if settings is not None else MenuSettings()
    statistics = statistics if statistics is not None else GameStatistics()
    pygame.display.set_caption("Python Chess - Main Menu")
    clock = pygame.time.Clock()
    page = "main"
    help_slide_index = 0

    while True:
        if page == "main":
            buttons = draw_menu(screen)
        elif page == "settings":
            buttons = _draw_settings_page(screen, settings)
        elif page == "stats":
            buttons = _draw_page(
                screen,
                "Session Statistics",
                [
                    f"Games played: {statistics.games_played}",
                    f"Estimated Elo: {statistics.estimated_elo:.0f}",
                    "Elo estimate: White perspective vs assumed 1200-rated opponents",
                    f"Wins (White): {statistics.win_percentage:.1f}%",
                    f"Draws: {statistics.draw_percentage:.1f}%",
                    f"Losses (Black): {statistics.loss_percentage:.1f}%",
                ],
            )
        elif page == "help":
            buttons = _draw_help_slide(screen, help_slide_index)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if page == "help":
                    if event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                        help_slide_index = min(
                            len(HELP_SLIDES) - 1,
                            help_slide_index + 1,
                        )
                    elif event.key == pygame.K_LEFT:
                        help_slide_index = max(0, help_slide_index - 1)
                    elif event.key == pygame.K_ESCAPE:
                        page = "main"
                continue
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            if page == "main":
                if buttons["local"].collidepoint(event.pos):
                    return LOCAL_TWO_PLAYER
                if buttons["computer"].collidepoint(event.pos):
                    return PLAY_AGAINST_COMPUTER
                if buttons["settings"].collidepoint(event.pos):
                    page = "settings"
                elif buttons["stats"].collidepoint(event.pos):
                    page = "stats"
                elif buttons["help"].collidepoint(event.pos):
                    page = "help"
                    help_slide_index = 0
                elif buttons["quit"].collidepoint(event.pos):
                    return None
            elif page == "settings":
                if buttons["sound"].collidepoint(event.pos):
                    settings.sound_enabled = not settings.sound_enabled
                elif buttons["difficulty"].collidepoint(event.pos):
                    difficulties = ("Easy", "Medium", "Hard", "Expert")
                    settings.difficulty = difficulties[
                        (difficulties.index(settings.difficulty) + 1)
                        % len(difficulties)
                    ]
                elif buttons["timed"].collidepoint(event.pos):
                    settings.timed_games = not settings.timed_games
                elif buttons["time_decrease"].collidepoint(event.pos):
                    if settings.timed_games:
                        limits = (3, 5, 10, 15)
                        index = limits.index(settings.time_limit_minutes)
                        settings.time_limit_minutes = limits[max(0, index - 1)]
                elif buttons["time_increase"].collidepoint(event.pos):
                    if settings.timed_games:
                        limits = (3, 5, 10, 15)
                        index = limits.index(settings.time_limit_minutes)
                        settings.time_limit_minutes = limits[
                            min(len(limits) - 1, index + 1)
                        ]
                elif buttons["back"].collidepoint(event.pos):
                    page = "main"
            elif page == "help":
                if buttons["previous"].collidepoint(event.pos):
                    help_slide_index = max(0, help_slide_index - 1)
                elif buttons["next"].collidepoint(event.pos):
                    help_slide_index = min(
                        len(HELP_SLIDES) - 1,
                        help_slide_index + 1,
                    )
                elif buttons["back"].collidepoint(event.pos):
                    page = "main"
            elif buttons["back"].collidepoint(event.pos):
                page = "main"

        clock.tick(60)
