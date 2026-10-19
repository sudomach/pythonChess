from src.ui.sound_manager import SoundManager


class FakeSound:
    def __init__(self) -> None:
        self.play_count = 0

    def play(self) -> None:
        self.play_count += 1


def test_muting_suppresses_sound_and_unmuting_resumes_it() -> None:
    sounds = SoundManager.__new__(SoundManager)
    move_sound = FakeSound()
    sounds.sounds = {"move": move_sound}
    sounds.muted = False

    sounds.play("move")
    sounds.toggle_mute()
    sounds.play("move")
    sounds.toggle_mute()
    sounds.play("move")

    assert move_sound.play_count == 2
    assert not sounds.muted
