# test_vlc.py

import time
from pathlib import Path

import vlc  # python-vlc

# Tu zakładam strukturę:
# Hackathon/
#   assets/
#     sounds/
#       mexicanBit.mp3
BASE_DIR = Path(__file__).resolve().parent
AUDIO_PATH = BASE_DIR / "assets" / "sounds" / "mexicanBit.mp3"

print(f"[TEST] AUDIO_PATH = {AUDIO_PATH}")
print(f"[TEST] exists = {AUDIO_PATH.exists()}")

if not AUDIO_PATH.exists():
    print("[TEST] Plik nie istnieje -> przerwanie testu.")
    raise SystemExit(1)

instance = vlc.Instance()
player = instance.media_player_new()
media = instance.media_new(str(AUDIO_PATH))
player.set_media(media)

print("[TEST] play()...")
player.play()

# Dajemy VLC chwilę na start
time.sleep(1.0)

player.audio_set_volume(100)
print(f"[TEST] volume = {player.audio_get_volume()}")
print(f"[TEST] state = {player.get_state()}")

print("[TEST] Powinieneś teraz słyszeć muzykę przez ok. 10 sekund...")
time.sleep(10)

player.stop()
print("[TEST] Koniec.")
