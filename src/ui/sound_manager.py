from pathlib import Path
import warnings

import pygame


class SoundManager:
    def __init__(self) -> None:
        self.sounds: dict[str, pygame.mixer.Sound] = {}
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

        sound_dir = Path(__file__).resolve().parents[2] / "assets" / "sound"
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

    def play(self, name: str) -> None:
        if self.sounds:
            self.sounds[name].play()
