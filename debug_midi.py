import sys
from pathlib import Path

import mido


def main():
    if len(sys.argv) < 2:
        print("Użycie: python debug_midi.py assets/sounds/bit.mid")
        return

    midi_path = Path(sys.argv[1])
    if not midi_path.exists():
        print(f"Nie znaleziono pliku: {midi_path}")
        return

    mid = mido.MidiFile(midi_path)
    current_time = 0.0

    print(f"Plik: {midi_path}")
    print(f"ticks_per_beat: {mid.ticks_per_beat}")
    print("Wiadomości note_on (czas narastający w sekundach):")
    print("-" * 60)

    for msg in mid:
        current_time += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            print(
                f"time={current_time:8.3f}s | note={msg.note:3d} "
                f"velocity={msg.velocity:3d} channel={msg.channel}"
            )


if __name__ == "__main__":
    main()
