"""
Shooting Game Module.

Self-contained 2D Pygame shooting gallery game featuring:
1. Two-Hand Dual Wielding with independent crosshairs and ammo gauges.
2. Reload gestures (pointing down & palm tapping) and reload animations.
3. Customizable procedural sound packs (Laser, Revolver, Silencer).
4. Boss Battles with multi-hit shielded enemies and counter-projectiles.
5. Power-ups (Freeze Time, Rapid Fire, Health Repair).
"""

from __future__ import annotations

import math
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import pygame

# Game Window Dimensions
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

# Color Palette
COLOR_BG = (16, 20, 28)
COLOR_GRID = (28, 36, 50)
COLOR_TEXT = (240, 244, 250)
COLOR_ACCENT = (0, 220, 180)
COLOR_GUN1 = (0, 240, 220)      # Primary gun (Cyan)
COLOR_GUN2 = (255, 140, 30)     # Secondary gun (Orange)
COLOR_CROSSHAIR_NOT_READY = (140, 145, 155)
COLOR_CROSSHAIR_FIRING = (255, 60, 60)
COLOR_TARGET_NORMAL = (240, 70, 70)
COLOR_TARGET_FAST = (255, 180, 40)
COLOR_TARGET_BONUS = (180, 80, 255)
COLOR_HEALTH_GOOD = (50, 220, 100)
COLOR_HEALTH_WARN = (255, 180, 0)
COLOR_HEALTH_DANGER = (240, 50, 50)
COLOR_BOSS_SHIELD = (0, 195, 255)
COLOR_BOSS_HULL = (255, 75, 75)
COLOR_FREEZE = (80, 220, 255)
COLOR_RAPID = (255, 210, 40)


class SoundSynthesizer:
    """
    Generates procedural 8-bit / 16-bit sound effects using numpy and pygame,
    supporting 3 customizable sound packs: LASER, REVOLVER, and SILENCER.
    """

    PACKS = ["LASER", "REVOLVER", "SILENCER"]

    def __init__(self) -> None:
        self.sounds_available = False
        self.current_pack = "LASER"
        self.pack_index = 0

        # Sound dictionaries per pack
        self.sounds_shoot: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.sounds_hit: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.sounds_reload: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.sounds_empty: Dict[str, Optional[pygame.mixer.Sound]] = {}

        # Shared sounds
        self.snd_hurt: Optional[pygame.mixer.Sound] = None
        self.snd_boss_hit: Optional[pygame.mixer.Sound] = None
        self.snd_boss_destroy: Optional[pygame.mixer.Sound] = None
        self.snd_powerup: Optional[pygame.mixer.Sound] = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sounds_available = True
            self._generate_all_sounds()
        except Exception as e:
            print(f"[Audio] Sound initialization notice: {e}")
            self.sounds_available = False

    def _make_sound(self, audio_1d: Any) -> Optional[pygame.mixer.Sound]:
        """Convert 1D audio waveform into pygame Sound, respecting mono or stereo mixer."""
        try:
            import numpy as np
            init_info = pygame.mixer.get_init()
            if not init_info:
                return None
            channels = init_info[2]
            if channels == 2:
                stereo = np.column_stack((audio_1d, audio_1d))
                return pygame.sndarray.make_sound(stereo)
            return pygame.sndarray.make_sound(audio_1d)
        except Exception:
            return None

    def _generate_all_sounds(self) -> None:
        """Procedurally bake sound effects for all packs."""
        try:
            import numpy as np
            sr = 22050

            # 1. LASER PACK
            # Laser Shoot
            t = np.linspace(0, 0.12, int(sr * 0.12), False)
            freq = np.linspace(950, 220, len(t))
            wave = np.sin(2 * np.pi * freq * t)
            audio_laser = (wave * np.exp(-14 * t) * 24000).astype(np.int16)
            self.sounds_shoot["LASER"] = self._make_sound(audio_laser)

            # Laser Hit
            t_hit = np.linspace(0, 0.15, int(sr * 0.15), False)
            tone_hit = np.sin(2 * np.pi * np.linspace(480, 120, len(t_hit)) * t_hit)
            noise_hit = np.random.uniform(-0.5, 0.5, len(t_hit))
            audio_laser_hit = ((0.6 * tone_hit + 0.4 * noise_hit) * np.exp(-14 * t_hit) * 25000).astype(np.int16)
            self.sounds_hit["LASER"] = self._make_sound(audio_laser_hit)

            # Laser Reload (High-tech capacitor charge sweep)
            t_rel = np.linspace(0, 0.25, int(sr * 0.25), False)
            freq_rel = np.linspace(240, 880, len(t_rel))
            wave_rel = np.sin(2 * np.pi * freq_rel * t_rel)
            audio_laser_rel = (wave_rel * (1.0 - np.exp(-10 * t_rel)) * np.exp(-3 * t_rel) * 22000).astype(np.int16)
            self.sounds_reload["LASER"] = self._make_sound(audio_laser_rel)

            # Laser Empty
            t_emp = np.linspace(0, 0.08, int(sr * 0.08), False)
            buzz = np.sin(2 * np.pi * 120 * t_emp)
            audio_laser_emp = (buzz * np.exp(-15 * t_emp) * 18000).astype(np.int16)
            self.sounds_empty["LASER"] = self._make_sound(audio_laser_emp)

            # 2. REVOLVER PACK
            # Revolver Shoot (Punchy gunshot with low boom and noise crack)
            t_rev = np.linspace(0, 0.22, int(sr * 0.22), False)
            noise_rev = np.random.uniform(-1, 1, len(t_rev))
            boom_rev = np.sin(2 * np.pi * np.linspace(150, 45, len(t_rev)) * t_rev)
            audio_rev = ((0.75 * noise_rev + 0.6 * boom_rev) * np.exp(-12 * t_rev) * 28000).astype(np.int16)
            self.sounds_shoot["REVOLVER"] = self._make_sound(audio_rev)

            # Revolver Hit (Metallic impact ricochet)
            t_rh = np.linspace(0, 0.16, int(sr * 0.16), False)
            ring = np.sin(2 * np.pi * 840 * t_rh) + 0.5 * np.sin(2 * np.pi * 1680 * t_rh)
            audio_rev_hit = (ring * np.exp(-16 * t_rh) * 24000).astype(np.int16)
            self.sounds_hit["REVOLVER"] = self._make_sound(audio_rev_hit)

            # Revolver Reload (Cylinder spin & lock snap)
            t_rr = np.linspace(0, 0.28, int(sr * 0.28), False)
            click1 = np.sin(2 * np.pi * 500 * t_rr) * np.exp(-35 * np.abs(t_rr - 0.05))
            click2 = np.sin(2 * np.pi * 750 * t_rr) * np.exp(-40 * np.abs(t_rr - 0.18))
            audio_rev_rel = ((click1 + click2) * 26000).astype(np.int16)
            self.sounds_reload["REVOLVER"] = self._make_sound(audio_rev_rel)

            # Revolver Empty (Steel hammer dry fire)
            t_re = np.linspace(0, 0.06, int(sr * 0.06), False)
            dry = np.sin(2 * np.pi * 420 * t_re) * np.exp(-30 * t_re)
            self.sounds_empty["REVOLVER"] = self._make_sound((dry * 25000).astype(np.int16))

            # 3. SILENCER PACK
            # Silencer Shoot (Crisp tactical "pfft")
            t_sil = np.linspace(0, 0.09, int(sr * 0.09), False)
            noise_sil = np.random.uniform(-0.5, 0.5, len(t_sil))
            sub_pop = np.sin(2 * np.pi * np.linspace(380, 90, len(t_sil)) * t_sil)
            audio_sil = ((0.35 * noise_sil + 0.65 * sub_pop) * np.exp(-22 * t_sil) * 22000).astype(np.int16)
            self.sounds_shoot["SILENCER"] = self._make_sound(audio_sil)

            # Silencer Hit (Muffled shatter thud)
            t_sh = np.linspace(0, 0.12, int(sr * 0.12), False)
            audio_sil_hit = (np.random.uniform(-0.7, 0.7, len(t_sh)) * np.exp(-18 * t_sh) * 20000).astype(np.int16)
            self.sounds_hit["SILENCER"] = self._make_sound(audio_sil_hit)

            # Silencer Reload (Tactical slide rack)
            t_sr = np.linspace(0, 0.22, int(sr * 0.22), False)
            rack = np.random.uniform(-0.6, 0.6, len(t_sr)) * np.exp(-12 * t_sr)
            snap = np.sin(2 * np.pi * 650 * t_sr) * np.exp(-45 * np.abs(t_sr - 0.14))
            self.sounds_reload["SILENCER"] = self._make_sound(((rack * 0.5 + snap * 0.8) * 25000).astype(np.int16))

            # Silencer Empty
            t_se = np.linspace(0, 0.05, int(sr * 0.05), False)
            self.sounds_empty["SILENCER"] = self._make_sound((np.sin(2 * np.pi * 300 * t_se) * np.exp(-35 * t_se) * 16000).astype(np.int16))

            # 4. SHARED SOUND EFFECTS
            # Hurt / Life lost
            t_hurt = np.linspace(0, 0.25, int(sr * 0.25), False)
            wave_hurt = np.sin(2 * np.pi * np.linspace(220, 90, len(t_hurt)) * t_hurt)
            self.snd_hurt = self._make_sound((wave_hurt * np.exp(-8 * t_hurt) * 26000).astype(np.int16))

            # Boss Hit (Shield clash)
            t_bh = np.linspace(0, 0.20, int(sr * 0.20), False)
            shield_w = np.sin(2 * np.pi * 600 * t_bh) * np.sin(2 * np.pi * 45 * t_bh)
            self.snd_boss_hit = self._make_sound((shield_w * np.exp(-10 * t_bh) * 28000).astype(np.int16))

            # Boss Destroy (Massive multi-stage explosion)
            t_bd = np.linspace(0, 0.60, int(sr * 0.60), False)
            sub_boom = np.sin(2 * np.pi * np.linspace(90, 30, len(t_bd)) * t_bd)
            noise_bd = np.random.uniform(-1, 1, len(t_bd))
            self.snd_boss_destroy = self._make_sound(((0.6 * sub_boom + 0.6 * noise_bd) * np.exp(-5 * t_bd) * 30000).astype(np.int16))

            # Power-up Collect (Ascending arpeggio chime)
            t_pw = np.linspace(0, 0.32, int(sr * 0.32), False)
            chime = (
                np.sin(2 * np.pi * 440 * t_pw) * (t_pw < 0.08)
                + np.sin(2 * np.pi * 554 * t_pw) * ((t_pw >= 0.08) & (t_pw < 0.16))
                + np.sin(2 * np.pi * 659 * t_pw) * ((t_pw >= 0.16) & (t_pw < 0.24))
                + np.sin(2 * np.pi * 880 * t_pw) * (t_pw >= 0.24)
            )
            self.snd_powerup = self._make_sound((chime * np.exp(-5 * t_pw) * 22000).astype(np.int16))

        except Exception as e:
            print(f"[Audio] Sound synthesis error: {e}")

    def cycle_sound_pack(self) -> str:
        """Cycle through sound packs: LASER -> REVOLVER -> SILENCER."""
        self.pack_index = (self.pack_index + 1) % len(self.PACKS)
        self.current_pack = self.PACKS[self.pack_index]
        self.play_shoot()
        return self.current_pack

    def set_sound_pack(self, pack_name: str) -> None:
        if pack_name.upper() in self.PACKS:
            self.current_pack = pack_name.upper()
            self.pack_index = self.PACKS.index(self.current_pack)

    def play_shoot(self) -> None:
        if self.sounds_available and self.current_pack in self.sounds_shoot:
            snd = self.sounds_shoot[self.current_pack]
            if snd:
                snd.play()

    def play_hit(self) -> None:
        if self.sounds_available and self.current_pack in self.sounds_hit:
            snd = self.sounds_hit[self.current_pack]
            if snd:
                snd.play()

    def play_reload(self) -> None:
        if self.sounds_available and self.current_pack in self.sounds_reload:
            snd = self.sounds_reload[self.current_pack]
            if snd:
                snd.play()

    def play_empty(self) -> None:
        if self.sounds_available and self.current_pack in self.sounds_empty:
            snd = self.sounds_empty[self.current_pack]
            if snd:
                snd.play()

    def play_hurt(self) -> None:
        if self.sounds_available and self.snd_hurt:
            self.snd_hurt.play()

    def play_boss_hit(self) -> None:
        if self.sounds_available and self.snd_boss_hit:
            self.snd_boss_hit.play()

    def play_boss_destroy(self) -> None:
        if self.sounds_available and self.snd_boss_destroy:
            self.snd_boss_destroy.play()

    def play_powerup(self) -> None:
        if self.sounds_available and self.snd_powerup:
            self.snd_powerup.play()


class Target:
    """Moving target balloon/drone on the screen."""

    def __init__(self, screen_w: int, screen_h: int, difficulty_level: int = 1) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h

        r = random.random()
        if r < 0.65:
            self.type = "NORMAL"
            self.radius = random.randint(28, 36)
            self.points = 100
            self.color = COLOR_TARGET_NORMAL
            speed_mult = 1.0
        elif r < 0.88:
            self.type = "FAST"
            self.radius = random.randint(20, 26)
            self.points = 250
            self.color = COLOR_TARGET_FAST
            speed_mult = 1.6
        else:
            self.type = "BONUS"
            self.radius = random.randint(16, 22)
            self.points = 500
            self.color = COLOR_TARGET_BONUS
            speed_mult = 2.0

        side = random.choice(["LEFT", "RIGHT", "BOTTOM"])
        base_speed = (1.5 + 0.2 * difficulty_level) * speed_mult

        if side == "LEFT":
            self.x = -self.radius
            self.y = random.uniform(130, screen_h - 150)
            self.vx = base_speed * random.uniform(1.0, 1.8)
            self.vy = random.uniform(-1.0, 1.0)
        elif side == "RIGHT":
            self.x = screen_w + self.radius
            self.y = random.uniform(130, screen_h - 150)
            self.vx = -base_speed * random.uniform(1.0, 1.8)
            self.vy = random.uniform(-1.0, 1.0)
        else:  # BOTTOM
            self.x = random.uniform(100, screen_w - 100)
            self.y = screen_h + self.radius
            self.vx = random.uniform(-1.2, 1.2)
            self.vy = -base_speed * random.uniform(1.2, 2.0)

        self.wobble_freq = random.uniform(2.0, 4.0)
        self.wobble_amp = random.uniform(1.5, 3.0)
        self.created_at = time.time()
        self.alive = True

    def update(self, dt: float, speed_factor: float = 1.0) -> bool:
        effective_dt = dt * speed_factor
        self.x += self.vx * (effective_dt * 60)
        self.y += self.vy * (effective_dt * 60)

        t = time.time() - self.created_at
        self.y += math.sin(t * self.wobble_freq) * (self.wobble_amp * effective_dt * 60)

        margin = self.radius * 2 + 50
        if (
            self.x < -margin
            or self.x > self.screen_w + margin
            or self.y < -margin
            or self.y > self.screen_h + margin
        ):
            return False
        return True

    def is_hit(self, px: float, py: float) -> bool:
        dist = math.hypot(self.x - px, self.y - py)
        return dist <= self.radius

    def draw(self, surface: pygame.Surface) -> None:
        cx = int(self.x)
        cy = int(self.y)
        pygame.draw.circle(surface, self.color, (cx, cy), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), int(self.radius * 0.65))
        pygame.draw.circle(surface, self.color, (cx, cy), int(self.radius * 0.35))
        shine_pos = (int(cx - self.radius * 0.3), int(cy - self.radius * 0.3))
        pygame.draw.circle(surface, (255, 255, 255), shine_pos, max(2, int(self.radius * 0.15)))


class BossProjectile:
    """Energy orb fired by the Boss Enemy that player can intercept."""

    def __init__(self, x: float, y: float, speed: float = 2.4) -> None:
        self.x = x
        self.y = y
        self.speed = speed
        self.radius = 14
        self.alive = True
        self.color = (255, 60, 40)
        self.created_at = time.time()

    def update(self, dt: float, speed_factor: float = 1.0) -> bool:
        effective_dt = dt * speed_factor
        self.y += self.speed * (effective_dt * 60)
        t = time.time() - self.created_at
        self.x += math.sin(t * 5.0) * 1.2 * (effective_dt * 60)
        return self.y < WINDOW_HEIGHT + 20

    def is_hit(self, px: float, py: float) -> bool:
        return math.hypot(self.x - px, self.y - py) <= self.radius + 6

    def draw(self, surface: pygame.Surface) -> None:
        cx = int(self.x)
        cy = int(self.y)
        t = time.time() - self.created_at
        pulse = int(4 * math.sin(t * 12.0))
        r = max(10, self.radius + pulse)
        glow_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 80, 20, 90), (r + 5, r + 5), r + 4)
        surface.blit(glow_surf, (cx - r - 5, cy - r - 5))
        pygame.draw.circle(surface, (255, 120, 50), (cx, cy), self.radius)
        pygame.draw.circle(surface, (255, 255, 200), (cx, cy), int(self.radius * 0.45))


class BossEnemy:
    """
    Multi-hit shielded boss enemy with animated energy shield,
    armored hull, health bars, and counter-attacks.
    """

    def __init__(self, screen_w: int, screen_h: int, level: int = 1) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.width = 140
        self.height = 70
        self.x = screen_w / 2.0
        self.target_y = 150.0
        self.y = -80.0
        self.alive = True
        self.level = level

        self.max_shield = 6 + (level - 1) * 2
        self.shield = self.max_shield
        self.max_hull = 12 + (level - 1) * 3
        self.hull = self.max_hull

        self.last_attack_time = time.time()
        self.attack_interval = max(1.8, 3.2 - level * 0.25)
        self.projectiles: List[BossProjectile] = []

        self.hit_flash_timer = 0.0
        self.shield_flash_timer = 0.0
        self.created_at = time.time()
        self.shield_angle = 0.0

    def update(self, dt: float, speed_factor: float = 1.0) -> bool:
        effective_dt = dt * speed_factor

        if self.y < self.target_y:
            self.y += 120.0 * effective_dt
            if self.y > self.target_y:
                self.y = self.target_y

        t = time.time() - self.created_at
        self.x = (self.screen_w / 2.0) + math.sin(t * 0.9) * (self.screen_w * 0.35)
        self.y = self.target_y + math.cos(t * 1.8) * 15.0
        self.shield_angle += 1.5 * (effective_dt * 60)

        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        if self.shield_flash_timer > 0:
            self.shield_flash_timer = max(0.0, self.shield_flash_timer - dt)

        now = time.time()
        effective_interval = self.attack_interval / max(0.2, speed_factor)
        if self.y >= self.target_y and (now - self.last_attack_time >= effective_interval):
            self.last_attack_time = now
            self.projectiles.append(BossProjectile(self.x, self.y + 35, speed=2.5 + self.level * 0.2))

        self.projectiles = [p for p in self.projectiles if p.update(dt, speed_factor)]
        return self.hull > 0

    def is_hit(self, px: float, py: float) -> bool:
        dx = abs(self.x - px)
        dy = abs(self.y - py)
        hit_radius = max(self.width, self.height) * 0.55
        return math.hypot(dx, dy) <= hit_radius

    def take_hit(self) -> Tuple[bool, bool]:
        if self.shield > 0:
            self.shield -= 1
            self.shield_flash_timer = 0.15
            return (True, False)
        else:
            self.hull -= 1
            self.hit_flash_timer = 0.15
            if self.hull <= 0:
                self.alive = False
                return (False, True)
            return (False, False)

    def draw(self, surface: pygame.Surface) -> None:
        cx = int(self.x)
        cy = int(self.y)

        # Shield Barrier
        if self.shield > 0:
            shield_surf = pygame.Surface((self.width + 70, self.height + 60), pygame.SRCALPHA)
            sw, sh = self.width + 70, self.height + 60
            shield_alpha = 180 if self.shield_flash_timer > 0 else 90
            shield_col = (200, 250, 255, shield_alpha) if self.shield_flash_timer > 0 else (0, 195, 255, shield_alpha)
            pygame.draw.ellipse(shield_surf, shield_col, (10, 10, sw - 20, sh - 20), 3)

            for ang in range(0, 360, 60):
                rad = math.radians(ang + self.shield_angle)
                tx = (sw / 2) + math.cos(rad) * ((sw - 20) / 2)
                ty = (sh / 2) + math.sin(rad) * ((sh - 20) / 2)
                pygame.draw.circle(shield_surf, (150, 230, 255, 200), (int(tx), int(ty)), 4)

            surface.blit(shield_surf, (cx - sw // 2, cy - sh // 2))

        # Mothership Hull
        body_col = (255, 255, 255) if self.hit_flash_timer > 0 else (45, 55, 75)
        pts = [
            (cx - 70, cy),
            (cx - 30, cy - 25),
            (cx + 30, cy - 25),
            (cx + 70, cy),
            (cx + 40, cy + 25),
            (cx - 40, cy + 25),
        ]
        pygame.draw.polygon(surface, body_col, pts)
        pygame.draw.polygon(surface, (200, 70, 70) if self.shield == 0 else (0, 200, 220), pts, 2)

        # Core Reactor
        core_col = (255, 60, 60) if self.shield == 0 else (0, 240, 220)
        pygame.draw.circle(surface, core_col, (cx, cy), 16)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 6)

        # Thrusters
        pygame.draw.circle(surface, (255, 140, 0), (cx - 35, cy - 23), 5)
        pygame.draw.circle(surface, (255, 140, 0), (cx + 35, cy - 23), 5)

        # Bars above Boss
        bar_w = 120
        bar_h = 7
        bar_x = cx - bar_w // 2
        bar_y = cy - 45

        if self.max_shield > 0:
            pygame.draw.rect(surface, (30, 40, 50), (bar_x, bar_y - 10, bar_w, bar_h), border_radius=3)
            shield_frac = max(0.0, self.shield / self.max_shield)
            if shield_frac > 0:
                pygame.draw.rect(surface, COLOR_BOSS_SHIELD, (bar_x, bar_y - 10, int(bar_w * shield_frac), bar_h), border_radius=3)

        pygame.draw.rect(surface, (30, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        hull_frac = max(0.0, self.hull / self.max_hull)
        if hull_frac > 0:
            pygame.draw.rect(surface, COLOR_BOSS_HULL, (bar_x, bar_y, int(bar_w * hull_frac), bar_h), border_radius=3)

        for p in self.projectiles:
            p.draw(surface)


class PowerUpItem:
    """Floating collectible power-up capsule."""

    TYPES = ["FREEZE", "RAPID_FIRE", "HEALTH"]

    def __init__(self, x: float, y: float, power_type: Optional[str] = None) -> None:
        self.x = x
        self.y = y
        self.radius = 20
        self.type = power_type if power_type else random.choice(self.TYPES)
        self.created_at = time.time()
        self.alive = True
        self.vy = random.uniform(0.9, 1.5)
        self.vx = random.uniform(-0.5, 0.5)

        if self.type == "FREEZE":
            self.color = COLOR_FREEZE
            self.icon = "FREEZE"
        elif self.type == "RAPID_FIRE":
            self.color = COLOR_RAPID
            self.icon = "RAPID"
        else:
            self.color = COLOR_HEALTH_GOOD
            self.icon = "+LIFE"

    def update(self, dt: float) -> bool:
        self.y += self.vy * (dt * 60)
        self.x += self.vx * (dt * 60)
        t = time.time() - self.created_at
        self.x += math.sin(t * 3.0) * 0.8
        return self.y < WINDOW_HEIGHT + 30

    def is_hit(self, px: float, py: float) -> bool:
        return math.hypot(self.x - px, self.y - py) <= self.radius + 4

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        cx = int(self.x)
        cy = int(self.y)
        t = time.time() - self.created_at
        pulse = int(3 * math.sin(t * 8.0))

        pygame.draw.circle(surface, self.color, (cx, cy), self.radius + pulse, 2)
        inner_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(inner_surf, (*self.color, 140), (self.radius, self.radius), self.radius)
        surface.blit(inner_surf, (cx - self.radius, cy - self.radius))
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), self.radius, 1)

        txt = font.render(self.icon, True, (255, 255, 255))
        rect = txt.get_rect(center=(cx, cy))
        surface.blit(txt, rect)


class Particle:
    """Explosion / spark particle on target destroy."""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int], speed_mult: float = 1.0) -> None:
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.0, 7.5) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.3, 0.6)
        self.age = 0.0
        self.radius = random.randint(2, 5)

    def update(self, dt: float) -> bool:
        self.age += dt
        self.x += self.vx * (dt * 60)
        self.y += self.vy * (dt * 60)
        self.vy += 0.15 * (dt * 60)
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0.0, 1.0 - (self.age / self.lifetime))
        r = max(1, int(self.radius * alpha))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)


class FloatingText:
    """Floating score / reload / power-up popup."""

    def __init__(self, x: float, y: float, text: str, color: Tuple[int, int, int], size: int = 24) -> None:
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.lifetime = 0.9
        self.age = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        self.y -= 35 * dt
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        alpha_frac = max(0.0, 1.0 - (self.age / self.lifetime))
        txt_surf = font.render(self.text, True, self.color)
        txt_surf.set_alpha(int(255 * alpha_frac))
        rect = txt_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt_surf, rect)


class GunShooterGame:
    """
    Main Pygame Shooter Game Engine with Two-Hand Dual Wielding,
    Reload Gestures, Sound Packs, Boss Battles, and Power-ups.
    """

    def __init__(
        self,
        width: int = WINDOW_WIDTH,
        height: int = WINDOW_HEIGHT,
        control_mode: str = "HAND",
        debug_mode: bool = False,
    ) -> None:
        pygame.init()
        pygame.font.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Hand Gun Gesture Shooter - Dual Wield Edition")

        self.clock = pygame.time.Clock()
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_mid = pygame.font.Font(None, 26)
            self.font_small = pygame.font.Font(None, 19)
            self.font_mono = pygame.font.Font(None, 16)
        except Exception:
            self.font_large = pygame.font.SysFont("sans-serif", 44)
            self.font_mid = pygame.font.SysFont("sans-serif", 24)
            self.font_small = pygame.font.SysFont("sans-serif", 17)
            self.font_mono = pygame.font.SysFont("monospace", 14)

        self.sound = SoundSynthesizer()

        # Settings
        self.control_mode = control_mode.upper()
        self.debug_mode = debug_mode
        self.running = True

        # Game State
        self.state = "PLAYING"
        self.score = 0
        self.lives = 5
        self.max_lives = 5
        self.shots_fired = 0
        self.shots_hit = 0
        self.combo = 0
        self.max_combo = 0
        self.screen_shake = 0.0

        # Spawning & Milestones
        self.level = 1
        self.start_time = time.time()
        self.last_spawn_time = 0.0
        self.spawn_interval = 1.3
        self.next_boss_score = 2500

        # Entities
        self.targets: List[Target] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []
        self.powerups: List[PowerUpItem] = []
        self.boss: Optional[BossEnemy] = None

        # Power-Up Timers
        self.freeze_timer: float = 0.0
        self.rapid_fire_timer: float = 0.0

        # Dual Crosshairs Display State (Gun 0 = Primary/Right, Gun 1 = Secondary/Left)
        self.guns_display: List[Dict[str, Any]] = [
            {
                "gun_id": 0,
                "label": "RIGHT GUN",
                "color": COLOR_GUN1,
                "aim_x": width / 2.0 + 50,
                "aim_y": height / 2.0,
                "gun_ready": True,
                "flash_timer": 0.0,
                "ammo": 8,
                "max_ammo": 8,
                "is_reloading": False,
                "reload_progress": 0.0,
                "active": True,
            },
            {
                "gun_id": 1,
                "label": "LEFT GUN",
                "color": COLOR_GUN2,
                "aim_x": width / 2.0 - 50,
                "aim_y": height / 2.0,
                "gun_ready": True,
                "flash_timer": 0.0,
                "ammo": 8,
                "max_ammo": 8,
                "is_reloading": False,
                "reload_progress": 0.0,
                "active": False,
            },
        ]

        # Mini Webcam PiP
        self.camera_surface: Optional[pygame.Surface] = None
        self.last_gesture: str = "NO_GUN"
        self.last_confidence: float = 0.0

    def reset_game(self) -> None:
        """Reset game state for a new match."""
        self.score = 0
        self.lives = self.max_lives
        self.shots_fired = 0
        self.shots_hit = 0
        self.combo = 0
        self.max_combo = 0
        self.level = 1
        self.start_time = time.time()
        self.next_boss_score = 2500
        self.freeze_timer = 0.0
        self.rapid_fire_timer = 0.0
        self.screen_shake = 0.0

        self.targets.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.powerups.clear()
        self.boss = None

        for g in self.guns_display:
            g["ammo"] = g["max_ammo"]
            g["is_reloading"] = False
            g["flash_timer"] = 0.0

        self.state = "PLAYING"

    def set_camera_frame(self, bgr_frame: Optional[Any]) -> None:
        """Update picture-in-picture mini webcam HUD."""
        if bgr_frame is None:
            self.camera_surface = None
            return
        try:
            import cv2
            pip_w, pip_h = 180, 135
            small = cv2.resize(bgr_frame, (pip_w, pip_h))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self.camera_surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        except Exception:
            self.camera_surface = None

    def spawn_entities_if_needed(self) -> None:
        """Spawn targets, power-ups, and bosses based on progression."""
        now = time.time()
        elapsed = now - self.start_time
        self.level = 1 + int(self.score // 1000) + int(elapsed // 30)

        # 1. Boss Spawning Check
        if self.boss is None and self.score >= self.next_boss_score:
            self.boss = BossEnemy(self.width, self.height, self.level)
            self.floating_texts.append(
                FloatingText(self.width / 2, 220, "⚠️ WARNING: BOSS INCOMING! ⚠️", (255, 60, 60), size=32)
            )

        # 2. Regular Targets
        max_targets = 4 if self.boss else min(7, 3 + int(self.level // 2))
        self.spawn_interval = max(0.50, 1.4 - (self.level * 0.07))

        if len(self.targets) < max_targets and (now - self.last_spawn_time >= self.spawn_interval):
            self.targets.append(Target(self.width, self.height, self.level))
            self.last_spawn_time = now

            if len(self.powerups) < 2 and random.random() < 0.15:
                px = random.uniform(100, self.width - 100)
                self.powerups.append(PowerUpItem(px, -25))

    def trigger_reload_all(self) -> None:
        """Reload all player guns."""
        reloaded_any = False
        for g in self.guns_display:
            if g["ammo"] < g["max_ammo"] and not g["is_reloading"]:
                g["is_reloading"] = True
                g["reload_progress"] = 0.0
                reloaded_any = True

        if reloaded_any:
            self.sound.play_reload()
            self.floating_texts.append(
                FloatingText(self.width / 2, self.height - 120, "+RELOADED!", COLOR_ACCENT)
            )

    def shoot_at(self, x: float, y: float, gun_id: int = 0) -> bool:
        """
        Execute a shot at (x, y) from gun_id.
        Both guns can shoot on the same frame independently!
        """
        self.shots_fired += 1
        if 0 <= gun_id < len(self.guns_display):
            self.guns_display[gun_id]["flash_timer"] = 0.12

        self.sound.play_shoot()

        # 1. Check Power-Ups Hit
        for p in list(self.powerups):
            if p.is_hit(x, y):
                self.powerups.remove(p)
                self.sound.play_powerup()
                self._activate_powerup(p.type, p.x, p.y)
                return True

        # 2. Check Boss Projectiles Hit
        if self.boss:
            for proj in list(self.boss.projectiles):
                if proj.is_hit(x, y):
                    self.boss.projectiles.remove(proj)
                    self.sound.play_hit()
                    self.score += 50
                    for _ in range(8):
                        self.particles.append(Particle(proj.x, proj.y, (255, 120, 50)))
                    self.floating_texts.append(FloatingText(proj.x, proj.y, "+50 INTERCEPT", COLOR_ACCENT))
                    return True

        # 3. Check Boss Hit
        if self.boss and self.boss.is_hit(x, y):
            self.shots_hit += 1
            shield_hit, hull_dead = self.boss.take_hit()

            if shield_hit:
                self.sound.play_boss_hit()
                for _ in range(12):
                    self.particles.append(Particle(x, y, COLOR_BOSS_SHIELD))
                self.floating_texts.append(FloatingText(x, y, "SHIELD HIT!", COLOR_BOSS_SHIELD))
            else:
                self.sound.play_hit()
                for _ in range(15):
                    self.particles.append(Particle(x, y, COLOR_BOSS_HULL))
                self.floating_texts.append(FloatingText(x, y, "HULL DAMAGED!", COLOR_BOSS_HULL))

            if hull_dead:
                self.sound.play_boss_destroy()
                self.screen_shake = 0.4
                boss_pts = 3000
                self.score += boss_pts
                self.next_boss_score = self.score + 3500

                for _ in range(50):
                    col = random.choice([COLOR_BOSS_HULL, COLOR_BOSS_SHIELD, COLOR_ACCENT, (255, 255, 200)])
                    self.particles.append(Particle(self.boss.x, self.boss.y, col, speed_mult=1.8))

                self.floating_texts.append(
                    FloatingText(self.boss.x, self.boss.y - 20, f"+{boss_pts} BOSS DEFEATED!", (255, 220, 0), size=30)
                )

                self.powerups.append(PowerUpItem(self.boss.x, self.boss.y))
                self.boss = None

            return True

        # 4. Check Regular Targets Hit
        hit_target: Optional[Target] = None
        for target in reversed(self.targets):
            if target.is_hit(x, y):
                hit_target = target
                break

        if hit_target:
            self.shots_hit += 1
            self.combo += 1
            if self.combo > self.max_combo:
                self.max_combo = self.combo

            multiplier = 1.0 + (self.combo - 1) * 0.25
            points_awarded = int(hit_target.points * multiplier)
            self.score += points_awarded

            self.sound.play_hit()
            for _ in range(18):
                self.particles.append(Particle(hit_target.x, hit_target.y, hit_target.color))

            label = f"+{points_awarded}"
            if self.combo > 1:
                label += f" ({self.combo}x Combo!)"
            self.floating_texts.append(FloatingText(hit_target.x, hit_target.y, label, COLOR_ACCENT))

            self.targets.remove(hit_target)
            return True
        else:
            if self.rapid_fire_timer <= 0:
                if self.combo > 2:
                    self.floating_texts.append(FloatingText(x, y, "Combo Broken", (240, 100, 100)))
                self.combo = 0
            return False

    def _activate_powerup(self, ptype: str, x: float, y: float) -> None:
        """Trigger power-up effect."""
        for _ in range(25):
            self.particles.append(Particle(x, y, (255, 255, 255)))

        if ptype == "FREEZE":
            self.freeze_timer = 6.0
            self.floating_texts.append(FloatingText(x, y, "⏳ TIME FROZEN! (6s)", COLOR_FREEZE))
        elif ptype == "RAPID_FIRE":
            self.rapid_fire_timer = 7.0
            for g in self.guns_display:
                g["ammo"] = g["max_ammo"]
            self.floating_texts.append(FloatingText(x, y, "⚡ RAPID FIRE ACTIVATED!", COLOR_RAPID))
        elif ptype == "HEALTH":
            if self.lives < self.max_lives:
                self.lives += 1
                self.floating_texts.append(FloatingText(x, y, "+1 LIFE RESTORED!", COLOR_HEALTH_GOOD))
            else:
                self.score += 500
                self.floating_texts.append(FloatingText(x, y, "+500 BONUS POINTS!", COLOR_ACCENT))

    def handle_events(self) -> None:
        """Process keyboard, mouse, and sound pack events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_m:
                    self.control_mode = "MOUSE" if self.control_mode == "HAND" else "HAND"
                    print(f"[Mode] Control mode switched to: {self.control_mode}")
                elif event.key == pygame.K_s:
                    pack = self.sound.cycle_sound_pack()
                    self.floating_texts.append(
                        FloatingText(self.width / 2, 90, f"SOUND PACK: {pack}", COLOR_ACCENT)
                    )
                elif event.key == pygame.K_SPACE:
                    self.trigger_reload_all()
                elif event.key == pygame.K_d:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_r:
                    self.reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN and self.control_mode == "MOUSE":
                mx, my = pygame.mouse.get_pos()
                if self.state == "PLAYING":
                    # Left Click = Gun 0, Right Click = Gun 1
                    target_gun = 0 if event.button == 1 else 1
                    g = self.guns_display[target_gun]
                    if g["ammo"] > 0 or self.rapid_fire_timer > 0:
                        if self.rapid_fire_timer <= 0:
                            g["ammo"] -= 1
                        self.shoot_at(float(mx), float(my), gun_id=target_gun)
                    else:
                        self.sound.play_empty()
                        self.floating_texts.append(FloatingText(mx, my, "CLICK! RELOAD", (255, 80, 80)))
                elif self.state == "GAME_OVER":
                    self.reset_game()

    def update(self, dt: float, control_state: Optional[Dict[str, Any]] = None) -> None:
        """Advance game physics and inputs."""
        speed_factor = 1.0
        if self.freeze_timer > 0:
            self.freeze_timer = max(0.0, self.freeze_timer - dt)
            speed_factor = 0.25

        if self.rapid_fire_timer > 0:
            self.rapid_fire_timer = max(0.0, self.rapid_fire_timer - dt)

        if self.screen_shake > 0:
            self.screen_shake = max(0.0, self.screen_shake - dt)

        if self.control_mode == "MOUSE":
            mx, my = pygame.mouse.get_pos()
            self.guns_display[0]["aim_x"] = float(mx)
            self.guns_display[0]["aim_y"] = float(my)
            self.guns_display[0]["gun_ready"] = True
            self.guns_display[0]["active"] = True

            for g in self.guns_display:
                if g["is_reloading"]:
                    g["reload_progress"] = min(1.0, g["reload_progress"] + dt / 0.6)
                    if g["reload_progress"] >= 1.0:
                        g["ammo"] = g["max_ammo"]
                        g["is_reloading"] = False
                        self.floating_texts.append(
                            FloatingText(g["aim_x"], g["aim_y"] - 30, "+RELOADED!", COLOR_ACCENT)
                        )

            self.last_gesture = "MOUSE"
            self.last_confidence = 1.0

        elif control_state is not None:
            # Multi-gun tracking updates - handles BOTH guns on the same frame
            guns_data = control_state.get("guns", [])
            for i, gun_data in enumerate(guns_data):
                if i < len(self.guns_display):
                    gd = self.guns_display[i]
                    gd["aim_x"] = gun_data["aim_x"]
                    gd["aim_y"] = gun_data["aim_y"]
                    gd["gun_ready"] = gun_data["gun_ready"]
                    gd["ammo"] = gun_data["ammo"]
                    gd["max_ammo"] = gun_data["max_ammo"]
                    gd["is_reloading"] = gun_data["is_reloading"]
                    gd["reload_progress"] = gun_data["reload_progress"]
                    gd["active"] = gun_data["active"]
                    gd["label"] = gun_data.get("label", gd["label"])

                    # Firing event from this hand (both can shoot simultaneously!)
                    if gun_data.get("shoot", False):
                        if self.state == "PLAYING":
                            self.shoot_at(gd["aim_x"], gd["aim_y"], gun_id=i)
                        elif self.state == "GAME_OVER":
                            self.reset_game()
                    elif gun_data.get("empty_click", False):
                        self.sound.play_empty()
                        self.floating_texts.append(
                            FloatingText(gd["aim_x"], gd["aim_y"], "CLICK! RELOAD", (255, 80, 80))
                        )

            if control_state.get("reload_started", False):
                self.sound.play_reload()
            if control_state.get("reloaded_complete", False):
                self.floating_texts.append(
                    FloatingText(self.width / 2, self.height - 120, "+RELOADED!", COLOR_ACCENT)
                )

            self.last_gesture = control_state.get("gesture", "NO_GUN")
            self.last_confidence = control_state.get("confidence", 0.0)

        for g in self.guns_display:
            if g["flash_timer"] > 0:
                g["flash_timer"] = max(0.0, g["flash_timer"] - dt)

        if self.state != "PLAYING":
            return

        self.spawn_entities_if_needed()

        for target in list(self.targets):
            alive = target.update(dt, speed_factor)
            if not alive:
                self.targets.remove(target)
                self.lives -= 1
                self.combo = 0
                self.sound.play_hurt()
                self.screen_shake = 0.2
                self.floating_texts.append(
                    FloatingText(self.width / 2, self.height / 2, "TARGET ESCAPED! -1 LIFE", (255, 60, 60))
                )
                if self.lives <= 0:
                    self.state = "GAME_OVER"

        if self.boss:
            alive = self.boss.update(dt, speed_factor)
            if alive:
                for proj in list(self.boss.projectiles):
                    if proj.y >= self.height - 10:
                        self.boss.projectiles.remove(proj)
                        self.lives -= 1
                        self.sound.play_hurt()
                        self.screen_shake = 0.25
                        self.floating_texts.append(
                            FloatingText(self.width / 2, self.height / 2, "BOSS ATTACK HIT! -1 LIFE", (255, 60, 60))
                        )
                        if self.lives <= 0:
                            self.state = "GAME_OVER"

        self.powerups = [p for p in self.powerups if p.update(dt)]
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

    def draw_crosshairs(self, surface: pygame.Surface) -> None:
        """Render independent crosshairs with circular ammo pips and reload arcs."""
        for g in self.guns_display:
            if not g["active"]:
                continue

            cx = int(g["aim_x"])
            cy = int(g["aim_y"])
            gun_color = g["color"]

            if g["flash_timer"] > 0:
                reticle_color = COLOR_CROSSHAIR_FIRING
            elif g["gun_ready"]:
                reticle_color = (
                    COLOR_RAPID if self.rapid_fire_timer > 0 else gun_color
                )
            else:
                reticle_color = COLOR_CROSSHAIR_NOT_READY

            if g["flash_timer"] > 0:
                flash_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 100, 50, 130), (60, 60), 55)
                pygame.draw.circle(flash_surf, (255, 255, 200, 210), (60, 60), 28)
                surface.blit(flash_surf, (cx - 60, cy - 60))

            radius = 24
            pygame.draw.circle(surface, reticle_color, (cx, cy), radius, 2)
            pygame.draw.circle(surface, reticle_color, (cx, cy), 3)

            gap = 7
            tick = 10
            pygame.draw.line(surface, reticle_color, (cx, cy - radius - tick), (cx, cy - gap), 2)
            pygame.draw.line(surface, reticle_color, (cx, cy + gap), (cx, cy + radius + tick), 2)
            pygame.draw.line(surface, reticle_color, (cx - radius - tick, cy), (cx - gap, cy), 2)
            pygame.draw.line(surface, reticle_color, (cx + gap, cy), (cx + radius + tick, cy), 2)

            max_ammo = g["max_ammo"]
            cur_ammo = g["ammo"]
            ammo_radius = radius + 15

            if g["is_reloading"]:
                progress = g.get("reload_progress", 0.0)
                arc_surf = pygame.Surface((ammo_radius * 2 + 10, ammo_radius * 2 + 10), pygame.SRCALPHA)
                start_ang = time.time() * 8.0
                end_ang = start_ang + max(0.5, progress * 2 * math.pi)
                pygame.draw.arc(
                    arc_surf,
                    COLOR_ACCENT,
                    (5, 5, ammo_radius * 2, ammo_radius * 2),
                    start_ang,
                    end_ang,
                    3,
                )
                surface.blit(arc_surf, (cx - ammo_radius - 5, cy - ammo_radius - 5))
                rl_txt = self.font_mono.render("RELOADING", True, COLOR_ACCENT)
                surface.blit(rl_txt, (cx - 30, cy + radius + 18))
            else:
                for i in range(max_ammo):
                    angle = (i / max_ammo) * 2 * math.pi - (math.pi / 2)
                    px = cx + math.cos(angle) * ammo_radius
                    py = cy + math.sin(angle) * ammo_radius

                    if i < cur_ammo:
                        pip_col = COLOR_RAPID if self.rapid_fire_timer > 0 else reticle_color
                        pygame.draw.circle(surface, pip_col, (int(px), int(py)), 3)
                    else:
                        pygame.draw.circle(surface, (80, 85, 95), (int(px), int(py)), 2)

                if cur_ammo == 0:
                    blink = int(time.time() * 6) % 2 == 0
                    if blink:
                        empty_txt = self.font_mono.render("POINT DOWN TO RELOAD", True, (255, 60, 60))
                        surface.blit(empty_txt, (cx - 65, cy + radius + 18))

            lbl = self.font_mono.render(g["label"], True, reticle_color)
            surface.blit(lbl, (cx - 25, cy - radius - 22))

    def draw_hud(self, surface: pygame.Surface) -> None:
        """Render top score bar, health indicators, active power-ups, and HUD badges."""
        top_bar = pygame.Surface((self.width, 58), pygame.SRCALPHA)
        top_bar.fill((10, 14, 20, 220))
        surface.blit(top_bar, (0, 0))
        pygame.draw.line(surface, COLOR_GRID, (0, 58), (self.width, 58), 2)

        score_txt = self.font_mid.render(f"SCORE: {self.score:,}", True, COLOR_TEXT)
        surface.blit(score_txt, (18, 16))

        if self.combo > 1:
            combo_txt = self.font_mid.render(f"COMBO {self.combo}x", True, COLOR_ACCENT)
            surface.blit(combo_txt, (200, 16))

        level_txt = self.font_small.render(f"LVL {self.level}", True, (180, 190, 210))
        surface.blit(level_txt, (340, 20))

        pack_lbl = f"SOUND: {self.sound.current_pack} [S]"
        pack_txt = self.font_small.render(pack_lbl, True, (255, 215, 80))
        surface.blit(pack_txt, (410, 20))

        lives_x = self.width - 200
        lives_lbl = self.font_small.render("LIVES:", True, COLOR_TEXT)
        surface.blit(lives_lbl, (lives_x, 20))
        for i in range(self.max_lives):
            pip_x = lives_x + 55 + i * 22
            pip_y = 18
            pip_color = COLOR_HEALTH_GOOD if i < self.lives else (60, 60, 70)
            pygame.draw.circle(surface, pip_color, (pip_x, pip_y + 8), 7)

        badge_y = 66
        if self.freeze_timer > 0:
            f_txt = self.font_small.render(f"⏳ FREEZE: {self.freeze_timer:.1f}s", True, COLOR_FREEZE)
            surface.blit(f_txt, (20, badge_y))
            badge_y += 20

        if self.rapid_fire_timer > 0:
            r_txt = self.font_small.render(f"⚡ RAPID FIRE: {self.rapid_fire_timer:.1f}s", True, COLOR_RAPID)
            surface.blit(r_txt, (20, badge_y))

        bot_bar = pygame.Surface((self.width, 36), pygame.SRCALPHA)
        bot_bar.fill((10, 14, 20, 220))
        surface.blit(bot_bar, (0, self.height - 36))

        mode_color = COLOR_ACCENT if self.control_mode == "HAND" else (255, 200, 60)
        mode_txt = self.font_small.render(
            f"MODE: {self.control_mode} ([M] Toggle) | [SPACE] Reload | [S] Sound Pack | [R] Restart",
            True,
            mode_color,
        )
        surface.blit(mode_txt, (18, self.height - 26))

        if self.control_mode == "HAND" and self.camera_surface:
            pip_x = self.width - 190
            pip_y = self.height - 180
            pygame.draw.rect(surface, (40, 50, 70), (pip_x - 3, pip_y - 3, 186, 141), 2)
            surface.blit(self.camera_surface, (pip_x, pip_y))
            tag = self.font_mono.render("DUAL CAM FEED", True, (0, 255, 200))
            surface.blit(tag, (pip_x + 6, pip_y + 6))

    def draw_game_over(self, surface: pygame.Surface) -> None:
        """Render Game Over overlay dialog."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 220))
        surface.blit(overlay, (0, 0))

        center_x = self.width // 2
        center_y = self.height // 2

        title = self.font_large.render("GAME OVER", True, (255, 70, 70))
        surface.blit(title, title.get_rect(center=(center_x, center_y - 100)))

        score_surf = self.font_mid.render(f"Final Score: {self.score:,}", True, COLOR_TEXT)
        surface.blit(score_surf, score_surf.get_rect(center=(center_x, center_y - 40)))

        acc_pct = (self.shots_hit / max(1, self.shots_fired)) * 100.0
        stats_str = f"Max Combo: {self.max_combo}x  |  Accuracy: {acc_pct:.1f}%  |  Level Reached: {self.level}"
        stats_surf = self.font_small.render(stats_str, True, (180, 190, 210))
        surface.blit(stats_surf, stats_surf.get_rect(center=(center_x, center_y + 10)))

        prompt_surf = self.font_mid.render("Pull Thumb Trigger / Click / Press [R] to Play Again", True, COLOR_ACCENT)
        surface.blit(prompt_surf, prompt_surf.get_rect(center=(center_x, center_y + 70)))

    def render(self) -> None:
        """Draw everything to the game display."""
        ox, oy = 0, 0
        if self.screen_shake > 0:
            intensity = int(self.screen_shake * 12)
            ox = random.randint(-intensity, intensity)
            oy = random.randint(-intensity, intensity)

        render_surf = pygame.Surface((self.width, self.height))
        render_surf.fill(COLOR_BG)

        grid_step = 60
        for gx in range(0, self.width, grid_step):
            pygame.draw.line(render_surf, COLOR_GRID, (gx, 0), (gx, self.height), 1)
        for gy in range(0, self.height, grid_step):
            pygame.draw.line(render_surf, COLOR_GRID, (0, gy), (self.width, gy), 1)

        if self.freeze_timer > 0:
            frost = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            frost.fill((0, 180, 255, 25))
            render_surf.blit(frost, (0, 0))

        for target in self.targets:
            target.draw(render_surf)

        if self.boss:
            self.boss.draw(render_surf)

        for p in self.powerups:
            p.draw(render_surf, self.font_mono)

        for particle in self.particles:
            particle.draw(render_surf)

        for ft in self.floating_texts:
            ft.draw(render_surf, self.font_mid)

        self.draw_crosshairs(render_surf)
        self.draw_hud(render_surf)

        if self.state == "GAME_OVER":
            self.draw_game_over(render_surf)

        self.screen.blit(render_surf, (ox, oy))
        pygame.display.flip()

    def run_standalone(self) -> None:
        """Run game independently in MOUSE mode for immediate testing."""
        print("\nStarting Hand Gun Game in Dual-Wield Standalone Mode...")
        print("Controls: Left Click = Gun 1 | Right Click = Gun 2 | [SPACE] = Reload | [S] = Sound Pack | [R] = Restart")
        self.control_mode = "MOUSE"

        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()


if __name__ == "__main__":
    game = GunShooterGame(control_mode="MOUSE", debug_mode=True)
    game.run_standalone()
