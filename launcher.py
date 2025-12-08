import sys
import traceback
import os

# Wymuszenie natychmiastowego wypisywania (bez buforowania)
def log(msg):
    print(msg, flush=True)

log("--- LAUNCHER START (v3) ---")

# FIX: PyInstaller 6+ w trybie --onedir wrzuca pliki do folderu _internal
# Musimy zmienić katalog roboczy na _internal, żeby gra widziała folder assets
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(base_dir, "_internal")
    if os.path.exists(internal_dir):
        log(f"Zmiana katalogu roboczego na: {internal_dir}")
        os.chdir(internal_dir)
    else:
        log(f"Nie znaleziono folderu _internal w {base_dir}. Pozostaję w katalogu exe.")

try:
    log("Krok 1: Próba importu modułu 'game'...")
    import game
    log("Krok 2: Moduł 'game' zaimportowany pomyślnie.")
    
    log("Krok 3: Uruchamianie game.main()...")
    game.main()
    
except Exception:
    log("\n!!! CRITICAL ERROR IN LAUNCHER !!!\n")
    traceback.print_exc()
    log("\n")
except SystemExit as e:
    log(f"SystemExit caught: {e}")
finally:
    log("--- LAUNCHER END ---")
    try:
        input("Naciśnij ENTER aby zamknąć...")
    except:
        pass



