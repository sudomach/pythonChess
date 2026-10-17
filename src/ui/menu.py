import pygame


LOCAL_TWO_PLAYER = "local"
PLAY_AGAINST_COMPUTER = "computer"


def draw_menu(
    screen: pygame.Surface,
    message: str | None = None,
) -> dict[str, pygame.Rect]:
    width, height = screen.get_size()
    screen.fill((35, 42, 52))

    title_font = pygame.font.Font(None, max(36, min(58, width // 8)))
    button_font = pygame.font.Font(None, max(18, min(32, width // 18)))
    message_font = pygame.font.Font(None, max(18, min(26, width // 22)))

    title = title_font.render("Python Chess", True, (245, 245, 245))
    screen.blit(title, title.get_rect(center=(width // 2, height // 4)))

    button_width = min(width - 32, max(240, int(width * 0.78)))
    button_height = max(48, min(64, height // 10))
    first_button_y = height // 2 - button_height
    buttons = {
        "local": pygame.Rect(
            (width - button_width) // 2,
            first_button_y,
            button_width,
            button_height,
        ),
        "computer": pygame.Rect(
            (width - button_width) // 2,
            first_button_y + button_height + 20,
            button_width,
            button_height,
        ),
    }

    for key, label in (
        ("local", "Local Two Player Mode"),
        ("computer", "Play Against Computer"),
    ):
        color = (55, 135, 75) if key == "local" else (73, 99, 132)
        pygame.draw.rect(screen, color, buttons[key], border_radius=8)
        text = button_font.render(label, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=buttons[key].center))

    if message:
        rendered_message = message_font.render(message, True, (240, 200, 120))
        screen.blit(
            rendered_message,
            rendered_message.get_rect(
                center=(width // 2, height - max(28, height // 10))
            ),
        )

    return buttons


def show_menu(screen: pygame.Surface) -> str | None:
    pygame.display.set_caption("Python Chess - Main Menu")
    clock = pygame.time.Clock()
    message = None

    while True:
        buttons = draw_menu(screen, message)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if buttons["local"].collidepoint(event.pos):
                    return LOCAL_TWO_PLAYER
                if buttons["computer"].collidepoint(event.pos):
                    return PLAY_AGAINST_COMPUTER

        clock.tick(60)