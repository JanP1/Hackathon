# Level_level7/game_level1.py

import sys
import math
import random
import json
from pathlib import Path

import pygame

# -----------------------------
# Ścieżki i importy
# -----------------------------

CURRENT_DIR = Path(__file__).resolve().parent  # .../Hackathon/Level_level7
BASE_DIR = CURRENT_DIR.parent                  # .../Hackathon

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from base_level import BaseLevel

from objects.effects_manager import EffectsManager  # używany w BaseLevel, import zostawiony
from objects.smoke import SmokeTrail
from objects.bpm_counter import BPMCounter  # używany w BaseLevel
from objects.ranged_enemy import RangedEnemy
from objects.melee_enemy import MeleeEnemy
from objects.kamikaze_enemy import KamikazeEnemy
from objects.player_bullet import PlayerBullet
from objects.building import Building
from objects.game_object import GameObject
from objects.potion import Potion

from objects.audio_manager import Level1AudioManager  # już używany w BaseLevel
from objects.debugHUD import Level1DebugHUD          # jw.

# -----------------------------
# Stałe poziomu
# -----------------------------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
MUSIC_START_DELAY_SEC = 1.6

SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
BIT_MID_PATH = SOUNDS_DIR / "bit.mid"
MEXICAN_MP3_PATH = SOUNDS_DIR / "mexicanBit.mp3"

PICTURES_DIR = BASE_DIR / "assets" / "pictures"
MAIN_BG_PATH = PICTURES_DIR / "main_background.png"

LEVELS_DIR = BASE_DIR / "assets" / "levels"
BUILDINGS_JSON_PATH = LEVELS_DIR / "level7_buildings.json"


class Game(BaseLevel):
    """
    Level 7:

    - dziedziczy po BaseLevel wszystkie wspólne systemy:
        * time_scale (scroll),
        * audio (Level1AudioManager + MIDI),
        * BPMCounter,
        * EffectsManager (waves/bullets),
        * Player z time_scale + effects_manager,
        * wspólny on_beat() dla wrogów,
        * Debug HUD.
    - specyficzne dla level7:
        * tło z obrazka,
        * specjalny strzał (prawy przycisk myszy) – piłka z dymem,
        * kurczenie wrogów po trafieniu + chmura dymu,
        * integracja z GLPostProcessor (dane z EffectsManagera).
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        level_name: str,
        player_speed: float,
        bg_color: tuple[int, int, int],
    ):
        # inicjalizacja części wspólnej (BaseLevel)
        super().__init__(
            screen=screen,
            clock=clock,
            level_name=level_name,
            player_speed=player_speed,
            bg_color=bg_color,
            bpm=120,
            bit_mid_path=BIT_MID_PATH,
            mexican_mp3_path=MEXICAN_MP3_PATH,
            enable_background_mp3=True,
            music_start_delay=MUSIC_START_DELAY_SEC,
        )

        # ------------------------
        # WCZYTYWANIE DANYCH POZIOMU (JSON)
        # ------------------------
        self.buildings_data = []
        self.bg_filename = "main_background.png"
        
        if BUILDINGS_JSON_PATH.exists():
            try:
                with open(BUILDINGS_JSON_PATH, "r") as f:
                    data = json.load(f)
                    # Obsługa nowego formatu (dict) i starego (list)
                    if isinstance(data, dict):
                        self.buildings_data = data.get("buildings", [])
                        self.bg_filename = data.get("background", "main_background.png")
                    elif isinstance(data, list):
                        self.buildings_data = data
                        self.bg_filename = "main_background.png"
                        
                print(f"[LEVEL] Wczytano dane poziomu. Tło: {self.bg_filename}, Budynki: {len(self.buildings_data)}")
            except Exception as e:
                print(f"[LEVEL][WARN] Błąd parsowania JSON: {e}")

        # ------------------------
        # TŁO – obraz zamiast jednolitego koloru
        # ------------------------
        # UWAGA: Zakładamy, że obraz tła ma rozmiar mapy, np. 4096x4096
        self.map_width, self.map_height = 4096, 4096

        self.background_image: pygame.Surface | None = None
        
        # Próbujemy załadować tło wskazane w JSON (z folderu backgrounds lub pictures)
        # Szukamy najpierw w assets/pictures/backgrounds, potem w assets/pictures
        bg_path = BASE_DIR / "assets" / "pictures" / "backgrounds" / self.bg_filename
        if not bg_path.exists():
             bg_path = BASE_DIR / "assets" / "pictures" / self.bg_filename
             
        try:
            if bg_path.exists():
                img = pygame.image.load(str(bg_path)).convert()
                self.background_image = pygame.transform.scale(
                    img, (self.map_width, self.map_height)
                )
                print(f"[BG] Załadowano tło: {bg_path}")
            else:
                print(f"[BG][WARN] Nie znaleziono pliku tła: {bg_path}")
                # Fallback to MAIN_BG_PATH if different
                if bg_path != MAIN_BG_PATH and MAIN_BG_PATH.exists():
                     img = pygame.image.load(str(MAIN_BG_PATH)).convert()
                     self.background_image = pygame.transform.scale(
                        img, (self.map_width, self.map_height)
                     )
                     print(f"[BG] Załadowano tło domyślne: {MAIN_BG_PATH}")

            if self.background_image:
                # Ustawiamy rozmiar mapy w BaseLevel, żeby kamera wiedziała, jak się poruszać
                self.set_map_size(self.map_width, self.map_height)
                # Gracz na środku mapy
                self.player.rect.center = (self.map_width // 2, self.map_height // 2)
                
        except Exception as e:
            print(f"[BG][WARN] Błąd ładowania tła: {e}")
            self.background_image = None

        # ------------------------
        # SPECYFICZNE DLA LEVEL7
        # ------------------------
        
        # Dźwięk time_stop
        self.sound_time_stop = None
        try:
            self.sound_time_stop = pygame.mixer.Sound("assets/sounds/time_stop.mp3")
            self.sound_time_stop.set_volume(0.6)
        except Exception as e:
            print(f"[WARN] Game sound time_stop.mp3 error: {e}")
        
        # Timer do spawnowania wrogów
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_interval = 2.5 # Średnio co 2.5s (losowo 2-3s)
        
        # Cooldown na prawy przycisk myszy (specjalny strzał)
        self.special_attack_cooldown = 0.0
        self.special_attack_max_cooldown = 1.0 # 1 sekunda

                # jeden RangedEnemy na start
        ranged = RangedEnemy(
            600,
            400,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            1.0,            # scale
            self.player,    # target
        )
        ranged.map_width = self.map_width
        ranged.map_height = self.map_height
        ranged.set_attack_cooldown(4)
        self.add_enemy(ranged)

        # jeden MeleeEnemy na start
        melee = MeleeEnemy(
            800,
            400,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            1.0,
            self.player
        )
        melee.map_width = self.map_width
        melee.map_height = self.map_height
        melee.set_attack_cooldown(2)
        self.add_enemy(melee)

        # ------------------------
        # BUDYNKI
        # ------------------------
        self.buildings: list[Building] = []
        
        if self.buildings_data:
            try:
                for b_data in self.buildings_data:
                    bx = b_data["x"]
                    by = b_data["y"]
                    b_type = b_data.get("type", "house.png")
                    b_scale = b_data.get("scale", 1.0)
                    # Opcjonalnie scale, type itp.
                    b = Building(bx, by, SCREEN_WIDTH, SCREEN_HEIGHT, scale=b_scale, sprite_name=b_type)
                    if self.camera:
                        b.camera = self.camera
                    self.buildings.append(b)
                print(f"[LEVEL] Utworzono {len(self.buildings)} obiektów budynków.")
            except Exception as e:
                print(f"[LEVEL][WARN] Błąd tworzenia budynków: {e}")
        
        # Jeśli nie ma pliku lub pusty, dodaj przykładowy (opcjonalnie)
        if not self.buildings:
            b = Building(800, 600, SCREEN_WIDTH, SCREEN_HEIGHT, scale=1.0)
            if self.camera:
                b.camera = self.camera
            self.buildings.append(b)

        # pociski gracza (specjal skill – prawy przycisk myszy)
        self.player_bullets: list[PlayerBullet] = []

        # dymy eksplozji na wrogach
        self.smoke_explosions: list[SmokeTrail] = []

        # loot
        self.potions: list[Potion] = []

        # Dźwięk prawego przycisku
        self.sound_right = None
        try:
            self.sound_right = pygame.mixer.Sound("assets/sounds/right.mp3")
            self.sound_right.set_volume(0.5)
        except Exception as e:
            print(f"[WARN] Game sound right.mp3 error: {e}")

        # Dźwięk fail (do użycia przy prawym przycisku)
        self.sound_fail = None
        try:
            self.sound_fail = pygame.mixer.Sound("assets/sounds/fail.mp3")
            self.sound_fail.set_volume(0.5)
        except Exception as e:
            print(f"[WARN] Game sound fail.mp3 error: {e}")

        # --- Slow Time Logic ---
        self.slow_time_active = False
        self.slow_time_end_ms = 0
        self.pre_slow_time_scale = 1.0

    # ======================================================================
    # EVENTY SPECYFICZNE DLA LEVEL7
    # ======================================================================

    def handle_event_level(self, event: pygame.event.Event) -> None:
        """
        Tu reagujemy na eventy specyficzne dla tego poziomu.
        Wspólne rzeczy (ESC, scroll) są w BaseLevel.handle_events().
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # prawy przycisk -> strzał kulą z dymem
            if event.button == 3:
                self._shoot_special()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._try_activate_slow_time()

    def _try_activate_slow_time(self) -> None:
        if self.slow_time_active:
            return
        
        if self.player.slow_time_charge >= self.player.max_slow_time_charge:
            # Activate
            self.player.slow_time_charge = 0
            self.slow_time_active = True
            
            # Zapisujemy obecny time_scale, żeby potem przywrócić (lub po prostu ustawiamy 0.5)
            # Ale uwaga: BaseLevel.time_scale może być zmieniane scrollem.
            # Jeśli chcemy "zwolnić o połowę", to bierzemy current * 0.5.
            # Ale jeśli user zmieni scrollem w trakcie, to co?
            # Przyjmijmy, że slow time wymusza 0.5x względem tego co było w momencie aktywacji
            # i blokuje zmianę scrollem? Albo po prostu ustawia 0.5.
            # User: "czas zwalnia o połowę na 10 sekund".
            # Interpretacja: time_scale = time_scale * 0.5
            
            self.pre_slow_time_scale = self.time_scale
            new_scale = self.time_scale * 0.5
            # Ustawiamy w BaseLevel (to zaktualizuje TimeManager i obiekty)
            self.time_scale = new_scale
            self.time_manager.set_time_scale(self.time_scale)
            self._apply_time_scale_to_objects()
            if self.audio_manager:
                self.audio_manager.set_time_scale(self.time_scale)
            
            self.slow_time_end_ms = self.time_manager.time + 10000 # 10s in game time? Or real time?
            # "na 10 sekund" - zazwyczaj real time, bo jak zwolnimy czas gry, to 10s gry będzie trwało 20s.
            # Użyjmy pygame.time.get_ticks() dla real time duration.
            self.slow_time_end_real_ms = pygame.time.get_ticks() + 10000
            
            self.player.is_slow_time_active = True
            
            if self.sound_time_stop:
                self.sound_time_stop.play()
                
            print("[GAME] Slow Time ACTIVATED!")

    def _update_slow_time(self) -> None:
        if not self.slow_time_active:
            return
            
        now = pygame.time.get_ticks()
        if now >= self.slow_time_end_real_ms:
            # Deactivate
            self.slow_time_active = False
            self.player.is_slow_time_active = False
            
            # Restore time scale
            # Opcjonalnie: przywracamy to co było, albo po prostu mnożymy x2
            # self.time_scale = self.pre_slow_time_scale 
            # Ale jeśli user scrolował? BaseLevel.handle_events pozwala scrolować.
            # Jeśli pozwolimy scrolować w trakcie slow motion, to przywrócenie starej wartości może być dziwne.
            # Przywróćmy po prostu x2, zakładając że to "odwrócenie" efektu.
            self.time_scale = self.time_scale * 2.0
            
            # Clamp to limits defined in BaseLevel
            self.time_scale = max(self.min_time_scale, min(self.max_time_scale, self.time_scale))
            
            self.time_manager.set_time_scale(self.time_scale)
            self._apply_time_scale_to_objects()
            if self.audio_manager:
                self.audio_manager.set_time_scale(self.time_scale)
            
            print("[GAME] Slow Time ENDED.")

    # ======================================================================
    # SPECJALNY STRZAŁ GRACZA (piłka + smoke)
    # ======================================================================

    def _shoot_special(self) -> None:
        # Sprawdzenie cooldownu
        if self.special_attack_cooldown > 0:
            if self.sound_fail:
                self.sound_fail.play()
            return

        # Sprawdzenie beatu
        is_on_beat = False
        if self.bpm_counter:
            is_on_beat = self.bpm_counter.is_on_beat()

        if not is_on_beat:
            if self.sound_fail:
                self.sound_fail.play()
            return

        # Trafienie w beat -> PERFECT!
        self.player.perfect_text_timer_ms = 600
        
        # Trigger guitar hit animation
        self.player.is_attacking_anim = True
        self.player.attack_anim_index = 0.0
        
        # Reset cooldownu
        self.special_attack_cooldown = self.special_attack_max_cooldown

        # pozycja gracza
        px, py = self.player.rect.center

        # Dźwięk
        if self.sound_right:
            self.sound_right.play()

        # kierunek = celowanie w pozycję myszy (uwzględniając kamerę)
        mx, my = pygame.mouse.get_pos()
        # Przeliczamy pozycję myszy na współrzędne świata
        world_mx = mx + self.camera.x
        world_my = my + self.camera.y

        dx = world_mx - px
        dy = world_my - py
        length = math.hypot(dx, dy)
        if length == 0:
            return

        dir_x = dx / length
        dir_y = dy / length

        # prędkość bazowa pocisku (px/s)
        bullet_speed = 900.0

        bullet = PlayerBullet(
            x=px,
            y=py,
            vx=dir_x * bullet_speed,
            vy=dir_y * bullet_speed,
        )
        self.player_bullets.append(bullet)

        # Rejestrujemy pocisk w EffectsManagerze (do shadera)
        self.effects_manager.add_bullet(bullet)

    # ======================================================================
    # UPDATE LOGIKI SPECYFICZNEJ DLA LEVEL7
    # ======================================================================

    def update_level(self, scaled_dt: float, raw_dt: float) -> None:
        """
        scaled_dt – sekundy * time_scale,
        raw_dt    – sekundy bez time_scale.
        BaseLevel zrobił już:
        - effects_manager.update(),
        - _apply_time_scale_to_objects(),
        - bpm_counter.update(),
        - audio_manager.update(),
        - player.update(),
        - enemies.update() + target na gracza,
        - wspólny on_beat() dla enemies.
        Tu dokładamy:
        - ruch pocisków,
        - kolizje z wrogami,
        - kurczenie wrogów po trafieniu,
        - dymy eksplozji.
        """
        # --- Pociski gracza ---
        for bullet in self.player_bullets:
            bullet.update(scaled_dt)

        # kolizje pocisków z wrogami
        self._handle_bullet_enemy_collisions()

        # sprzątanie pocisków – zostawiamy tylko żywe
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        # UWAGA: EffectsManager sam filtruje martwe pociski w get_bullets_data()

        # --- Kurczenie wrogów trafionych specjalnym strzałem ---
        self._update_enemy_shrink(scaled_dt)
        
        # --- Kolizje fal z wrogami ---
        self._handle_wave_enemy_collisions()

        # --- Sprawdzanie śmierci wrogów (z dowolnego źródła) ---
        self._check_enemy_deaths()

        # --- Loot (Potions) ---
        self._update_loot()

        # --- Kolizje z budynkami ---
        self._handle_building_collisions()

        # --- Dymy eksplozji na wrogach ---
        for trail in self.smoke_explosions:
            trail.update()
        self.smoke_explosions = [
            t for t in self.smoke_explosions if len(t.particles) > 0
        ]
        
        # --- Slow Time Update ---
        self._update_slow_time()
        
        # --- Cooldown Update ---
        if self.special_attack_cooldown > 0:
            self.special_attack_cooldown -= scaled_dt
        
        # --- Spawnowanie wrogów ---
        self.enemy_spawn_timer -= scaled_dt
        if self.enemy_spawn_timer <= 0:
            self._spawn_enemy()
            # Losowy czas do następnego spawnu: 2.0 - 3.0 sekundy
            self.enemy_spawn_timer = random.uniform(2.0, 3.0)

    def _spawn_enemy(self) -> None:
        """Tworzy nowego wroga w losowym miejscu mapy (bezpiecznym)."""
        
        # Próbujemy znaleźć bezpieczne miejsce (max 10 prób)
        for _ in range(10):
            x = random.randint(0, self.map_width)
            y = random.randint(0, self.map_height)
            
            # 1. Sprawdź dystans do gracza (nie za blisko)
            px, py = self.player.rect.center
            dist = math.hypot(x - px, y - py)
            if dist < 800: # Minimum 800px od gracza
                continue
                
            # 2. Sprawdź kolizję z budynkami
            # Tworzymy tymczasowy rect wroga (zakładamy rozmiar np. 60x60)
            enemy_rect = pygame.Rect(0, 0, 60, 60)
            enemy_rect.center = (x, y)
            
            collides = False
            for b in self.buildings:
                # Sprawdzamy kolizję z collision_rect budynku
                if b.collision_rect.colliderect(enemy_rect):
                    collides = True
                    break
            
            if collides:
                continue
                
            # Jeśli przeszło testy -> tworzymy wroga
            # Losujemy typ wroga: 40% Ranged, 40% Melee, 20% Kamikaze
            rand_val = random.random()
            enemy = None
            
            if rand_val < 0.4:
                enemy = RangedEnemy(
                    x, y,
                    SCREEN_WIDTH, SCREEN_HEIGHT,
                    1.0,
                    self.player
                )
                enemy.set_attack_cooldown(4)
            elif rand_val < 0.8:
                enemy = MeleeEnemy(
                    x, y,
                    SCREEN_WIDTH, SCREEN_HEIGHT,
                    1.0,
                    self.player
                )
                enemy.set_attack_cooldown(2)
            else:
                enemy = KamikazeEnemy(
                    x, y,
                    SCREEN_WIDTH, SCREEN_HEIGHT,
                    1.0,
                    self.player
                )
                enemy.effects_manager = self.effects_manager
                enemy.game_enemies = self.enemies

            if enemy:
                enemy.map_width = self.map_width
                enemy.map_height = self.map_height
                self.add_enemy(enemy)
            return

    def _handle_bullet_enemy_collisions(self) -> None:
        enemies_hit = set()

        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            b_rect = bullet.get_rect()

            for enemy in self.enemies:
                if getattr(enemy, "destroying", False):
                    continue
                if not hasattr(enemy, "rect"):
                    continue

                if b_rect.colliderect(enemy.rect):
                    bullet.alive = False
                    enemies_hit.add(enemy)
                    break

        for enemy in enemies_hit:
            # Zadajemy obrażenia zamiast natychmiastowego zabicia
            # Zakładamy max_health=60, więc 30 dmg = 2 strzały
            enemy.take_damage(30)

    def _check_enemy_deaths(self) -> None:
        """
        Sprawdza, czy któryś wróg umarł (hp <= 0) i nie jest jeszcze w trakcie niszczenia.
        Jeśli tak, odpala animację śmierci.
        """
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue
            
            # Jeśli wróg nie żyje (hp <= 0), zaczynamy animację
            if not enemy.is_alive or enemy.current_health <= 0:
                self._start_enemy_destruction(enemy)

    def _start_enemy_destruction(self, enemy) -> None:
        """
        Rozpoczyna animację niszczenia wroga:
        - odpalamy na nim dym (SmokeTrail)
        - zaczynamy animację kurczenia do zera.
        """
        if getattr(enemy, "destroying", False):
            return

        # Dodajemy kill dla gracza (monety + ładunek wave)
        self.player.add_kill()

        # Szansa na drop potki (1/5)
        if random.random() < 0.2:
            self._spawn_potion(enemy.rect.centerx, enemy.rect.centery)

        enemy.destroying = True
        enemy.destroy_scale = 1.0
        enemy.original_rect = enemy.rect.copy()

        ex, ey = enemy.rect.center

        # duża chmura smoke przy trafieniu
        explosion = SmokeTrail(border=1)
        for _ in range(80):
            dx = random.uniform(-1.0, 1.0)
            dy = random.uniform(-1.0, 1.0)
            explosion.add_particle(ex, ey, dx, dy)
        self.smoke_explosions.append(explosion)

    def _spawn_potion(self, x, y):
        potion = Potion(x, y, SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.camera:
            potion.camera = self.camera
        self.potions.append(potion)

    def _update_loot(self):
        to_remove = []
        for potion in self.potions:
            # Check collision with player
            if potion.rect.colliderect(self.player.rect):
                # Heal player
                if self.player.current_health < self.player.max_health:
                    self.player.current_health = min(self.player.max_health, self.player.current_health + potion.heal_amount)
                    # Opcjonalnie dźwięk podniesienia
                    to_remove.append(potion)
            
        for p in to_remove:
            if p in self.potions:
                self.potions.remove(p)

    def _hit_enemy_with_special(self, enemy) -> None:
        # Ta metoda jest teraz zastąpiona przez _start_enemy_destruction
        # wywoływaną w _check_enemy_deaths po zadaniu obrażeń.
        pass

    def _update_enemy_shrink(self, scaled_dt: float) -> None:
        """
        Powolne kurczenie wrogów po trafieniu. Gdy rozmiar spadnie do zera – usuwamy.
        """
        to_remove = []

        for enemy in self.enemies:
            if not getattr(enemy, "destroying", False):
                continue

            # inicjalizacja oryginalnego rect, gdyby nie było
            orig = getattr(enemy, "original_rect", enemy.rect)

            # zmniejszamy skalę
            scale_speed = 1.5  # ile "skali" na sekundę
            enemy.destroy_scale -= scale_speed * scaled_dt

            if enemy.destroy_scale <= 0.0:
                to_remove.append(enemy)
                continue

            # przeskalowany rect wokół środka
            cx, cy = orig.center
            new_w = max(1, int(orig.width * enemy.destroy_scale))
            new_h = max(1, int(orig.height * enemy.destroy_scale))

            enemy.rect = pygame.Rect(0, 0, new_w, new_h)
            enemy.rect.center = (cx, cy)

        if to_remove:
            self.enemies = [e for e in self.enemies if e not in to_remove]

    def _handle_wave_enemy_collisions(self) -> None:
        """
        Sprawdza kolizje fal dźwiękowych gracza z wrogami.
        Zadaje obrażenia, jeśli wróg jest w zasięgu fali.
        """
        for wave in self.player.sound_waves:
            wave_radius = wave["radius"]
            wave_thickness = wave["thickness"]
            wave_pos = wave["pos"]
            damage = wave["damage"]
            hit_enemies = wave.setdefault("hit_enemies", set())
            
            wx, wy = wave_pos

            for enemy in self.enemies:
                if getattr(enemy, "destroying", False):
                    continue
                if enemy in hit_enemies:
                    continue
                
                # Sprawdzamy dystans do środka wroga
                ex, ey = enemy.rect.center
                dist = math.hypot(ex - wx, ey - wy)
                
                # Kolizja: jeśli dystans jest mniejszy niż promień fali + margines (np. promień wroga)
                # i większy niż promień wewnętrzny (żeby fala "przeszła" przez wroga tylko raz)
                # Upraszczając: jeśli wróg jest w pierścieniu fali lub tuż przed nim
                enemy_radius = 30 # przybliżony promień wroga
                
                if dist < wave_radius + enemy_radius and dist > wave_radius - wave_thickness - enemy_radius:
                    # Wave niszczy przeciwnika od razu
                    enemy.take_damage(enemy.max_health + 999)
                    hit_enemies.add(enemy)
                    # Opcjonalnie: efekt trafienia, odrzut itp.

    def _handle_building_collisions(self) -> None:
        """
        Sprawdza kolizje gracza i wrogów z budynkami.
        Wypycha ich, jeśli weszli w collision_rect budynku.
        """
        # 1. Gracz
        for b in self.buildings:
            self._resolve_building_collision(self.player, b)

        # 2. Wrogowie
        for enemy in self.enemies:
            if getattr(enemy, "destroying", False):
                continue
            for b in self.buildings:
                self._resolve_building_collision(enemy, b)

    def _resolve_building_collision(self, mover, building) -> None:
        # Modyfikujemy hitbox budynku pod konkretnego movera
        collision_rect = building.collision_rect.copy()
        
        # Skracamy hitbox od dołu o wysokość postaci - 10px
        # Dzięki temu postać może wejść "na" budynek, aż jej stopy (bottom)
        # dotkną oryginalnego dołu budynku (z tolerancją 10px).
        offset = mover.rect.height - 10
        if offset > 0:
            collision_rect.height = max(0, collision_rect.height - offset)
            
        self._resolve_collision(mover, collision_rect)

    def _resolve_collision(self, mover, static_rect: pygame.Rect) -> None:
        """
        Prosta rezolucja kolizji AABB -> wypchnięcie movera z static_rect
        w stronę najmniejszego nakładania się.
        """
        if not mover.rect.colliderect(static_rect):
            return

        # Obliczamy overlap z każdej strony
        overlap_left = mover.rect.right - static_rect.left
        overlap_right = static_rect.right - mover.rect.left
        overlap_top = mover.rect.bottom - static_rect.top
        overlap_bottom = static_rect.bottom - mover.rect.top

        # Znajdujemy najmniejsze wypchnięcie
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if min_overlap == overlap_left:
            mover.rect.right = static_rect.left
        elif min_overlap == overlap_right:
            mover.rect.left = static_rect.right
        elif min_overlap == overlap_top:
            mover.rect.bottom = static_rect.top
        elif min_overlap == overlap_bottom:
            mover.rect.top = static_rect.bottom

    # ======================================================================
    # RYSOWANIE SPECYFICZNE DLA LEVEL7
    # ======================================================================

    def draw_level(self) -> None:
        """
        BaseLevel.draw() dorysuje BPM + HUD.
        Tu rysujemy wszystko co „wizualne” dla poziomu.
        Kolejność jak w oryginalnym level7 (prawie 1:1).
        """
        # --- Camera Shake Application ---
        shake_offset_x = 0
        shake_offset_y = 0
        if self.player.shake_timer > 0:
             shake_strength = 15.0 * (self.player.shake_timer / 300.0)
             shake_offset_x = random.uniform(-shake_strength, shake_strength)
             shake_offset_y = random.uniform(-shake_strength, shake_strength)
             
             if self.camera:
                 self.camera.x += shake_offset_x
                 self.camera.y += shake_offset_y

        # tło: najpierw obrazek, jak nie ma to kolor
        if self.background_image is not None:
            # Rysujemy tło z przesunięciem kamery
            cam_x = self.camera.x if self.camera else 0
            cam_y = self.camera.y if self.camera else 0
            self.screen.blit(self.background_image, (-cam_x, -cam_y))
        else:
            self.screen.fill(self.bg_color)

        # Budynki (rysowane przed postaciami, żeby postacie mogły wejść "przed" nie,
        # ale uwaga na sortowanie Y - w prostym 2D bez Y-sort budynki mogą zasłaniać
        # albo być zasłaniane nienaturalnie. Na razie rysujemy "pod" postaciami.)
        # Idealnie byłoby posortować wszystko (gracz, wrogowie, budynki) po Y.
        # Ale trzymając się prostej struktury:
        
        # Rysujemy budynki
        for b in self.buildings:
            b.draw(self.screen)

        # pociski (w tym ich dym)
        for bullet in self.player_bullets:
            bullet.draw(self.screen, self.camera)

        # wrogowie (część może być w fazie kurczenia – rect już zmniejszony)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # dymy eksplozji na wrogach
        for trail in self.smoke_explosions:
            trail.draw(self.screen, self.camera)

        # loot
        for potion in self.potions:
            potion.draw(self.screen)

        # gracz
        self.player.draw(self.screen)
        
        # --- Restore Camera (Undo Shake) ---
        if self.camera and (shake_offset_x != 0 or shake_offset_y != 0):
            self.camera.x -= shake_offset_x
            self.camera.y -= shake_offset_y


# -----------------------------
# Standalone test – z postprocess GL
# -----------------------------

level7_player_speed = 400.0
level7_bg_color = (10, 40, 90)


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Level 7 - GL postprocess")

    # okno z kontekstem OpenGL
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF,
    )

    clock = pygame.time.Clock()

    # offscreen surface, na którym rysuje cała gra
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()

    # postprocess GL
    from gl_postprocess import GLPostProcessor

    gl_post = GLPostProcessor(SCREEN_WIDTH, SCREEN_HEIGHT)

    # UWAGA: do Game (BaseLevel) przekazujemy game_surface jako "screen"
    game = Game(
        screen=game_surface,
        clock=clock,
        level_name="level7",
        player_speed=level7_player_speed,
        bg_color=level7_bg_color,
    )

    running = True
    while running and not game.want_quit:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # --- Camera Shake Logic ---
        # REMOVED: Logic moved to draw_level to avoid overwriting camera updates
        
        # logika + rysowanie NA game_surface (CPU)
        game.run_frame(dt, events)
        
        # Dane dla shadera bierzemy z EffectsManagera, ale musimy je
        # przesunąć o pozycję kamery, żeby zgadzały się z tym, co widać na ekranie.
        cam_x = game.camera.x if game.camera else 0
        cam_y = game.camera.y if game.camera else 0

        # Przesuwamy pociski
        bullets_data = game.effects_manager.get_bullets_data()
        bullets_data_screen = [
            (x - cam_x, y - cam_y, vx, vy) for x, y, vx, vy in bullets_data
        ]

        # Przesuwamy fale
        waves_data = game.effects_manager.get_waves_data()
        waves_data_screen = [
            (cx - cam_x, cy - cam_y, start_time, thickness)
            for cx, cy, start_time, thickness in waves_data
        ]

        # Przekazujemy też aktualny czas do shadera, aby mógł animować fale
        # Używamy czasu z effects_manager, który uwzględnia time_scale
        current_time_ms = game.effects_manager.current_time
        
        # Efekty postprocess
        invert = game.slow_time_active
        distortion = 1.0 if game.slow_time_active else 0.0
        
        # Damage tint (red screen)
        damage_tint = 0.0
        if game.player.damage_tint_timer > 0:
            # Fade out from red
            # damage_tint_timer is in ms (starts at 200)
            damage_tint = min(1.0, game.player.damage_tint_timer / 200.0) * 0.6 # max 0.6 opacity

        # Black Hole Data
        bh_active = game.effects_manager.black_hole_active
        bh_pos = (0.0, 0.0)
        bh_strength = 0.0
        
        if bh_active:
            bh_timer = game.effects_manager.black_hole_timer
            bh_duration = game.effects_manager.black_hole_duration
            # Strength 0..1
            bh_strength = bh_timer / bh_duration
            
            # Adjust pos by camera
            raw_pos = game.effects_manager.black_hole_pos
            bh_pos = (raw_pos[0] - cam_x, raw_pos[1] - cam_y)

        gl_post.render(
            game_surface, 
            bullets_data_screen, 
            waves_data_screen, 
            current_time_ms,
            invert=invert,
            distortion_strength=distortion,
            damage_tint=damage_tint,
            black_hole_pos=bh_pos,
            black_hole_strength=bh_strength
        )

        pygame.display.flip()

    game.stop_audio()
    pygame.quit()
    sys.exit()
