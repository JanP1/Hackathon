@echo off
echo ==========================================
echo Budowanie gry HackathonGame...
echo ==========================================

REM Uruchomienie PyInstaller
REM --noconfirm: nie pytaj o potwierdzenie nadpisania
REM --onedir: utwórz folder z plikami (szybsze uruchamianie niż jeden duży plik)
REM --console: pokaż konsolę (do debugowania błędów)
REM --paths ".": dodaj obecny folder do ścieżek importu
REM --add-data "assets;assets": skopiuj folder assets do wynikowego folderu
REM --name "HackathonGame": nazwa pliku exe
REM --hidden-import "gl_postprocess": wymuś dołączenie modułu postprocessingu

python -m PyInstaller --noconfirm ^
 --onedir ^
 --console ^
 --paths "." ^
 --add-data "assets;assets" ^
 --name "HackathonGame" ^
 --hidden-import "gl_postprocess" ^
 --collect-all "numpy" ^
 --add-binary "C:\Users\KW\anaconda3\Library\bin\mkl_intel_thread.2.dll;." ^
 --add-binary "C:\Users\KW\anaconda3\Library\bin\libiomp5md.dll;." ^
 --add-binary "C:\Users\KW\anaconda3\Library\bin\mkl_core.2.dll;." ^
 --add-binary "C:\Users\KW\anaconda3\Library\bin\mkl_def.2.dll;." ^
 launcher.py

echo.
echo ==========================================
echo ZAKONCZONO!
echo Twoja gra znajduje sie w folderze: dist\HackathonGame
echo Uruchom plik: dist\HackathonGame\HackathonGame.exe
echo ==========================================
pause
