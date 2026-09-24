"""
Shooting Game Module.

Self-contained 2D Pygame shooting gallery game.
Supports both HAND MODE (webcam gesture) and MOUSE MODE (mouse + click).
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
COLOR_CROSSHAIR_READY = (50, 255, 120)
COLOR_CROSSHAIR_NOT_READY = (150, 150, 160)
COLOR_CROSSHAIR_FIRING = (255, 60, 60)
COLOR_TARGET_NORMAL = (240, 70, 70)
COLOR_TARGET_FAST = (255, 180, 40)
COLOR_TARGET_BONUS = (180, 80, 255)
COLOR_HEALTH_GOOD = (50, 220, 100)
COLOR_HEALTH_WARN = (255, 180, 0)
COLOR_HEALTH_DANGER = (240, 50, 50)


class SoundSynthesizer:
    """
    Generates procedural 8-bit sound effects using numpy/pygame arrays,
    ensuring sound works out of the box with zero external audio assets.
    """

    def __init__(self) -> None:
        self.sounds_available = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.sounds_available = True
            self.snd_shoot = self._make_laser()
            self.snd_hit = self._make_explosion()
            self.snd_hurt = self._make_hurt()
        except Exception:
            self.sounds_available = False

    def _make_laser(self) -> Optional[pygame.mixer.Sound]:
        """Generate a sci-fi laser shot sound."""
        try:
            import numpy as np
            sample_rate = 22050
            duration = 0.12
            n_samples = int(sample_rate * duration)
            t = np.linspace(0, duration, n_samples, False)
            freq = np.linspace(900, 250, n_samples)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-14 * t)
            audio = (wave * envelope * 24000).astype(np.int16)
            return pygame.sndarray.make_sound(audio)
        except Exception:
            return None

    def _make_explosion(self) -> Optional[pygame.mixer.Sound]:
        """Generate a hit / pop sound."""
        try:
            import numpy as np
            sample_rate = 22050
            duration = 0.18
            n_samples = int(sample_rate * duration)
            t = np.linspace(0, duration, n_samples, False)
            noise = np.random.uniform(-1, 1, n_samples)
            freq = np.linspace(350, 80, n_samples)
            tone = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-12 * t)
            audio = ((0.6 * noise + 0.4 * tone) * envelope * 26000).astype(np.int16)
            return pygame.sndarray.make_sound(audio)
        except Exception:
            return None

    def _make_hurt(self) -> Optional[pygame.mixer.Sound]:
        """Generate life lost sound."""
        try:
            import numpy as np
            sample_rate = 22050
            duration = 0.25
            n_samples = int(sample_rate * duration)
            t = np.linspace(0, duration, n_samples, False)
            freq = np.linspace(220, 100, n_samples)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-8 * t)
            audio = (wave * envelope * 28000).astype(np.int16)
            return pygame.sndarray.make_sound(audio)
        except Exception:
            return None

    def play_shoot(self) -> None:
        if self.sounds_available and self.snd_shoot:
            self.snd_shoot.play()

    def play_hit(self) -> None:
        if self.sounds_available and self.snd_hit:
            self.snd_hit.play()

    def play_hurt(self) -> None:
        if self.sounds_available and self.snd_hurt:
            self.snd_hurt.play()


class Target:
    """
    Moving target balloon/drone on the screen.
    """

    def __init__(self, screen_w: int, screen_h: int, difficulty_level: int = 1) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Determine target type
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

        # Movement physics
        side = random.choice(["LEFT", "RIGHT", "BOTTOM"])
        base_speed = (1.5 + 0.2 * difficulty_level) * speed_mult

        if side == "LEFT":
            self.x = -self.radius
            self.y = random.uniform(120, screen_h - 150)
            self.vx = base_speed * random.uniform(1.0, 1.8)
            self.vy = random.uniform(-1.0, 1.0)
        elif side == "RIGHT":
            self.x = screen_w + self.radius
            self.y = random.uniform(120, screen_h - 150)
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

    def update(self, dt: float) -> bool:
        """Update position. Return False if off-screen and should be removed."""
        self.x += self.vx * (dt * 60)
        self.y += self.vy * (dt * 60)

        # Add sinusoidal wobble
        t = time.time() - self.created_at
        self.y += math.sin(t * self.wobble_freq) * (self.wobble_amp * dt * 60)

        # Check bounds
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
        """Check if aim coordinate hits inside the target circle."""
        dist = math.hypot(self.x - px, self.y - py)
        return dist <= self.radius

    def draw(self, surface: pygame.Surface) -> None:
        """Draw concentric circle target."""
        cx = int(self.x)
        cy = int(self.y)
        # Outer ring
        pygame.draw.circle(surface, self.color, (cx, cy), self.radius)
        # White middle ring
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), int(self.radius * 0.65))
        # Center bullseye
        pygame.draw.circle(surface, self.color, (cx, cy), int(self.radius * 0.35))
        # Small specular shine
        shine_pos = (int(cx - self.radius * 0.3), int(cy - self.radius * 0.3))
        pygame.draw.circle(surface, (255, 255, 255), shine_pos, max(2, int(self.radius * 0.15)))


class Particle:
    """Explosion / spark particle on target destroy."""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.0, 7.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.3, 0.6)
        self.age = 0.0
        self.radius = random.randint(2, 5)

    def update(self, dt: float) -> bool:
        self.age += dt
        self.x += self.vx * (dt * 60)
        self.y += self.vy * (dt * 60)
        self.vy += 0.15 * (dt * 60)  # Gravity
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0.0, 1.0 - (self.age / self.lifetime))
        r = max(1, int(self.radius * alpha))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)


class FloatingText:
    """Floating score popup on hit."""

    def __init__(self, x: float, y: float, text: str, color: Tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 0.8
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
    Main Pygame Shooter Game Engine.
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
        pygame.display.set_caption("Hand Gun Gesture Shooter")

        self.clock = pygame.time.Clock()
        # Use built-in portable font (avoids macOS PermissionError on /Users/.../Library/Fonts)
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_mid = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 20)
            self.font_mono = pygame.font.Font(None, 18)
        except Exception:
            self.font_large = pygame.font.SysFont("sans-serif", 42)
            self.font_mid = pygame.font.SysFont("sans-serif", 24)
            self.font_small = pygame.font.SysFont("sans-serif", 16)
            self.font_mono = pygame.font.SysFont("monospace", 15)

        self.sound = SoundSynthesizer()

        # Settings
        self.control_mode = control_mode.upper()  # 'HAND' or 'MOUSE'
        self.debug_mode = debug_mode
        self.running = True

        # Game State
        self.state = "PLAYING"  # 'START', 'PLAYING', 'GAME_OVER'
        self.score = 0
        self.lives = 5
        self.max_lives = 5
        self.shots_fired = 0
        self.shots_hit = 0
        self.combo = 0
        self.max_combo = 0

        # Difficulty & Spawning
        self.level = 1
        self.start_time = time.time()
        self.last_spawn_time = 0.0
        self.spawn_interval = 1.3

        # Game Entities
        self.targets: List[Target] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []

        # Crosshair Reticle State
        self.aim_x: float = width / 2.0
        self.aim_y: float = height / 2.0
        self.is_gun_ready: bool = True
        self.flash_timer: float = 0.0  # Muzzle flash timer
        self.last_gesture: str = "NO_GUN"
        self.last_confidence: float = 0.0

        # Mini Webcam Picture-in-Picture
        self.camera_surface: Optional[pygame.Surface] = None

    def reset_game(self) -> None:
        """Reset scores and entities for a new round."""
        self.score = 0
        self.lives = self.max_lives
        self.shots_fired = 0
        self.shots_hit = 0
        self.combo = 0
        self.max_combo = 0
        self.level = 1
        self.start_time = time.time()
        self.targets.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.state = "PLAYING"

    def set_camera_frame(self, bgr_frame: Optional[Any]) -> None:
        """Update the picture-in-picture webcam frame in HUD."""
        if bgr_frame is None:
            self.camera_surface = None
            return
        try:
            import cv2
            # Resize for PiP corner display (e.g. 180x135)
            pip_w, pip_h = 180, 135
            small = cv2.resize(bgr_frame, (pip_w, pip_h))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self.camera_surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        except Exception:
            self.camera_surface = None

    def spawn_target_if_needed(self) -> None:
        """Spawn targets dynamically based on current game difficulty."""
        now = time.time()
        # Adjust difficulty based on score and time
        elapsed = now - self.start_time
        self.level = 1 + int(self.score // 1000) + int(elapsed // 30)
        self.spawn_interval = max(0.45, 1.4 - (self.level * 0.08))

        max_active = min(7, 3 + int(self.level // 2))
        if len(self.targets) < max_active and (now - self.last_spawn_time >= self.spawn_interval):
            self.targets.append(Target(self.width, self.height, self.level))
            self.last_spawn_time = now

    def shoot_at(self, x: float, y: float) -> bool:
        """
        Execute a shot at (x, y). Checks target collisions and updates game state.
        """
        self.shots_fired += 1
        self.flash_timer = 0.12  # Trigger muzzle flash
        self.sound.play_shoot()

        # Check collision with targets (check from top to bottom)
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

            # Points calculation with combo multiplier
            multiplier = 1.0 + (self.combo - 1) * 0.25
            points_awarded = int(hit_target.points * multiplier)
            self.score += points_awarded

            # Trigger sound and effects
            self.sound.play_hit()
            for _ in range(18):
                self.particles.append(Particle(hit_target.x, hit_target.y, hit_target.color))

            # Floating text
            label = f"+{points_awarded}"
            if self.combo > 1:
                label += f" ({self.combo}x Combo!)"
            self.floating_texts.append(
                FloatingText(hit_target.x, hit_target.y, label, COLOR_ACCENT)
            )

            self.targets.remove(hit_target)
            return True
        else:
            # Missed shot resets combo
            if self.combo > 2:
                self.floating_texts.append(
                    FloatingText(x, y, "Combo Broken", (240, 100, 100))
                )
            self.combo = 0
            return False

    def handle_events(self) -> None:
        """Handle standard Pygame window and keyboard events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_m:
                    # Toggle Control Mode
                    self.control_mode = "MOUSE" if self.control_mode == "HAND" else "HAND"
                    print(f"[Mode] Switched control mode to: {self.control_mode}")
                elif event.key == pygame.K_d:
                    # Toggle Debug Mode
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_r:
                    # Restart
                    self.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.control_mode == "MOUSE":
                    mx, my = pygame.mouse.get_pos()
                    if self.state == "PLAYING":
                        self.shoot_at(mx, my)
                    elif self.state == "GAME_OVER":
                        self.reset_game()

    def update(self, dt: float, control_state: Optional[Dict[str, Any]] = None) -> None:
        """
        Advance game physics and state for this frame.
        """
        # Read control inputs
        if self.control_mode == "MOUSE":
            mx, my = pygame.mouse.get_pos()
            self.aim_x = float(mx)
            self.aim_y = float(my)
            self.is_gun_ready = True
            self.last_gesture = "MOUSE"
            self.last_confidence = 1.0
        elif control_state is not None:
            self.aim_x = control_state.get("aim_x", self.aim_x)
            self.aim_y = control_state.get("aim_y", self.aim_y)
            self.is_gun_ready = control_state.get("gun_ready", False)
            self.last_gesture = control_state.get("gesture", "NO_GUN")
            self.last_confidence = control_state.get("confidence", 0.0)

            # Fire shot if triggered
            if control_state.get("shoot", False):
                if self.state == "PLAYING":
                    self.shoot_at(self.aim_x, self.aim_y)
                elif self.state == "GAME_OVER":
                    self.reset_game()

        # Update Muzzle Flash
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.state != "PLAYING":
            return

        # Spawning
        self.spawn_target_if_needed()

        # Update Targets
        for target in list(self.targets):
            alive = target.update(dt)
            if not alive:
                # Target escaped off screen -> Lose life
                self.targets.remove(target)
                self.lives -= 1
                self.combo = 0
                self.sound.play_hurt()
                self.floating_texts.append(
                    FloatingText(self.width / 2, self.height / 2, "TARGET ESCAPED! -1 LIFE", (255, 60, 60))
                )
                if self.lives <= 0:
                    self.state = "GAME_OVER"

        # Update Particles
        self.particles = [p for p in self.particles if p.update(dt)]

        # Update Floating Texts
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

    def draw_crosshair(self, surface: pygame.Surface) -> None:
        """Render dynamic animated aiming reticle."""
        cx = int(self.aim_x)
        cy = int(self.aim_y)

        # Crosshair color based on state
        if self.flash_timer > 0:
            reticle_color = COLOR_CROSSHAIR_FIRING
        elif self.is_gun_ready:
            reticle_color = COLOR_CROSSHAIR_READY
        else:
            reticle_color = COLOR_CROSSHAIR_NOT_READY

        # Muzzle flash expanding halo
        if self.flash_timer > 0:
            flash_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 100, 50, 120), (60, 60), 55)
            pygame.draw.circle(flash_surf, (255, 255, 200, 200), (60, 60), 30)
            surface.blit(flash_surf, (cx - 60, cy - 60))

        # Outer segmented ring
        radius = 24
        pygame.draw.circle(surface, reticle_color, (cx, cy), radius, 2)
        # Inner dot
        pygame.draw.circle(surface, reticle_color, (cx, cy), 3)

        # Crosshair tick marks
        tick_len = 10
        gap = 8
        pygame.draw.line(surface, reticle_color, (cx, cy - radius - tick_len), (cx, cy - gap), 2)
        pygame.draw.line(surface, reticle_color, (cx, cy + gap), (cx, cy + radius + tick_len), 2)
        pygame.draw.line(surface, reticle_color, (cx - radius - tick_len, cy), (cx - gap, cy), 2)
        pygame.draw.line(surface, reticle_color, (cx + gap, cy), (cx + radius + tick_len, cy), 2)

        # Small status label below crosshair in debug mode
        if self.debug_mode:
            lbl = f"({cx}, {cy})"
            txt = self.font_mono.render(lbl, True, reticle_color)
            surface.blit(txt, (cx + 15, cy + 15))

    def draw_hud(self, surface: pygame.Surface) -> None:
        """Render top score bar, health indicators, and game stats."""
        # Top banner background
        top_bar = pygame.Surface((self.width, 55), pygame.SRCALPHA)
        top_bar.fill((10, 14, 20, 210))
        surface.blit(top_bar, (0, 0))
        pygame.draw.line(surface, COLOR_GRID, (0, 55), (self.width, 55), 2)

        # Score Display
        score_txt = self.font_mid.render(f"SCORE: {self.score:,}", True, COLOR_TEXT)
        surface.blit(score_txt, (20, 14))

        # Combo Display
        if self.combo > 1:
            combo_txt = self.font_mid.render(f"COMBO {self.combo}x", True, COLOR_ACCENT)
            surface.blit(combo_txt, (220, 14))

        # Level Display
        level_txt = self.font_small.render(f"LEVEL {self.level}", True, (180, 190, 210))
        surface.blit(level_txt, (380, 20))

        # Accuracy
        acc_pct = (self.shots_hit / max(1, self.shots_fired)) * 100.0
        acc_txt = self.font_small.render(f"ACCURACY: {acc_pct:.0f}%", True, (180, 190, 210))
        surface.blit(acc_txt, (470, 20))

        # Lives Bar (Hearts / pips)
        lives_x = self.width - 220
        lives_lbl = self.font_small.render("LIVES:", True, COLOR_TEXT)
        surface.blit(lives_lbl, (lives_x, 20))

        for i in range(self.max_lives):
            pip_x = lives_x + 55 + i * 22
            pip_y = 18
            pip_color = COLOR_HEALTH_GOOD if i < self.lives else (60, 60, 70)
            pygame.draw.circle(surface, pip_color, (pip_x, pip_y + 8), 7)

        # Bottom Bar: Control Mode & Status
        bot_bar = pygame.Surface((self.width, 36), pygame.SRCALPHA)
        bot_bar.fill((10, 14, 20, 210))
        surface.blit(bot_bar, (0, self.height - 36))

        mode_color = COLOR_ACCENT if self.control_mode == "HAND" else (255, 200, 60)
        mode_txt = self.font_small.render(
            f"MODE: {self.control_mode} (Press [M] to toggle) | [R] Restart | [ESC] Quit",
            True,
            mode_color,
        )
        surface.blit(mode_txt, (20, self.height - 26))

        # Gesture status in Hand mode
        if self.control_mode == "HAND":
            gest_color = (
                COLOR_CROSSHAIR_READY if self.is_gun_ready else COLOR_CROSSHAIR_NOT_READY
            )
            gest_txt = self.font_small.render(
                f"GESTURE: {self.last_gesture} ({self.last_confidence * 100:.0f}%)",
                True,
                gest_color,
            )
            surface.blit(gest_txt, (self.width - 250, self.height - 26))

        # Webcam Mini Picture-in-Picture (Bottom-right corner)
        if self.control_mode == "HAND" and self.camera_surface:
            pip_x = self.width - 190
            pip_y = self.height - 180
            # Border frame
            pygame.draw.rect(surface, (40, 50, 70), (pip_x - 3, pip_y - 3, 186, 141), 2)
            surface.blit(self.camera_surface, (pip_x, pip_y))
            tag = self.font_mono.render("CAM FEED", True, (0, 255, 200))
            surface.blit(tag, (pip_x + 6, pip_y + 6))

        # Debug Mode overlay (FPS, Entity counts)
        if self.debug_mode:
            fps_val = self.clock.get_fps()
            debug_txt = self.font_mono.render(
                f"DEBUG | FPS: {fps_val:.1f} | Targets: {len(self.targets)} | Particles: {len(self.particles)}",
                True,
                (255, 255, 0),
            )
            surface.blit(debug_txt, (20, 65))

    def draw_game_over(self, surface: pygame.Surface) -> None:
        """Render Game Over overlay dialog."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 220))
        surface.blit(overlay, (0, 0))

        center_x = self.width // 2
        center_y = self.height // 2

        # Title
        title_surf = self.font_large.render("GAME OVER", True, (255, 70, 70))
        surface.blit(title_surf, title_surf.get_rect(center=(center_x, center_y - 100)))

        # Final Score
        score_surf = self.font_mid.render(f"Final Score: {self.score:,}", True, COLOR_TEXT)
        surface.blit(score_surf, score_surf.get_rect(center=(center_x, center_y - 40)))

        # Stats
        acc_pct = (self.shots_hit / max(1, self.shots_fired)) * 100.0
        stats_str = f"Max Combo: {self.max_combo}x  |  Accuracy: {acc_pct:.1f}%  |  Level Reached: {self.level}"
        stats_surf = self.font_small.render(stats_str, True, (180, 190, 210))
        surface.blit(stats_surf, stats_surf.get_rect(center=(center_x, center_y + 10)))

        # Instructions
        prompt_surf = self.font_mid.render(
            "Pull Trigger (Gesture) or Click / Press [R] to Restart", True, COLOR_ACCENT
        )
        surface.blit(prompt_surf, prompt_surf.get_rect(center=(center_x, center_y + 70)))

    def render(self) -> None:
        """Draw everything to the game display."""
        self.screen.fill(COLOR_BG)

        # Background subtle grid lines
        grid_step = 60
        for gx in range(0, self.width, grid_step):
            pygame.draw.line(self.screen, COLOR_GRID, (gx, 0), (gx, self.height), 1)
        for gy in range(0, self.height, grid_step):
            pygame.draw.line(self.screen, COLOR_GRID, (0, gy), (self.width, gy), 1)

        # Draw Targets
        for target in self.targets:
            target.draw(self.screen)

        # Draw Particles
        for particle in self.particles:
            particle.draw(self.screen)

        # Draw Floating Texts
        for ft in self.floating_texts:
            ft.draw(self.screen, self.font_mid)

        # Draw Crosshair
        self.draw_crosshair(self.screen)

        # Draw HUD
        self.draw_hud(self.screen)

        # Game Over Screen
        if self.state == "GAME_OVER":
            self.draw_game_over(self.screen)

        pygame.display.flip()

    def run_standalone(self) -> None:
        """Run game independently in MOUSE mode for instant testing."""
        print("\nStarting Hand Gun Game in Standalone Mouse Mode...")
        print("Use mouse to aim, left-click to shoot, [M] to toggle mode, [D] for debug.")
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
