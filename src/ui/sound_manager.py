import warnings

import pygame

from src.settings import get_resource_path


class SoundManager:
    def __init__(self, muted: bool = False) -> None:
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.muted = muted
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error as error:
                warnings.warn(
                    f"Game sounds are unavailable: {error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                return

        sound_dir = get_resource_path("assets", "sound")
        self.sounds = {
            name: pygame.mixer.Sound(str(sound_dir / f"{name}.wav"))
            for name in (
                "move",
                "capture",
                "check",
                "game_end",
                "promotion",
            )
        }

    def toggle_mute(self) -> None:
        self.muted = not self.muted

    def play(self, name: str) -> None:
        if self.sounds and not self.muted:
            self.sounds[name].play()
