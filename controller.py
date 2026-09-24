"""
Controller Module.

Translates hand tracking landmarks and gesture predictions into clean game control inputs.
Handles multi-hand tracking, dual-wielding, aim smoothing, trigger debouncing,
ammo management, and reload gestures (hand pointing down & two-hand palm tap).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from gesture_model import GESTURE_GUN_READY, GESTURE_SHOOT, GestureClassifier
from hand_tracker import check_two_hand_tap, get_thumb_trigger_metric, is_pointing_down

# Configurable Controller Parameters
SMOOTHING_FACTOR: float = 0.35  # Alpha for Exponential Moving Average (0 < alpha <= 1)
TRIGGER_COOLDOWN_SEC: float = 0.25  # Debounce delay between successive shots (250 ms)
RAPID_FIRE_COOLDOWN_SEC: float = 0.09  # Debounce delay when Rapid Fire power-up is active
CONFIDENCE_THRESHOLD: float = 0.65  # Minimum ML model confidence
ACTIVE_MARGIN_X: float = 0.10  # Margin to allow comfortable edge-to-edge aiming
ACTIVE_MARGIN_Y: float = 0.10
MAX_AMMO_PER_GUN: int = 8
RELOAD_DURATION_SEC: float = 0.60


class SingleGunState:
    """Manages state for an individual gun (Primary or Secondary)."""

    def __init__(
        self,
        gun_id: int,
        label: str,
        color: Tuple[int, int, int],
        screen_width: int = 1000,
        screen_height: int = 700,
        smoothing_factor: float = SMOOTHING_FACTOR,
        trigger_cooldown_sec: float = TRIGGER_COOLDOWN_SEC,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        self.gun_id = gun_id
        self.label = label
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.smoothing_factor = smoothing_factor
        self.trigger_cooldown_sec = trigger_cooldown_sec
        self.confidence_threshold = confidence_threshold

        # Aim coordinates
        self.aim_x: float = screen_width / 2.0 + (gun_id * 80 - 40)
        self.aim_y: float = screen_height / 2.0
        self.has_aim_history: bool = False

        # Ammo and reload
        self.max_ammo: int = MAX_AMMO_PER_GUN
        self.ammo: int = MAX_AMMO_PER_GUN
        self.is_reloading: bool = False
        self.reload_start_time: float = 0.0
        self.reload_duration_sec: float = RELOAD_DURATION_SEC
        self.last_reload_trigger_time: float = 0.0

        # Shooting state
        self.last_shot_time: float = 0.0
        self.is_gun_ready: bool = False
        self.current_gesture: str = "NO_GUN"
        self.current_confidence: float = 0.0
        self.thumb_metric: float = 1.0
        self.flash_timer: float = 0.0
        self.active: bool = False

    def trigger_reload(self) -> bool:
        """Start reloading if not already full and not currently reloading."""
        now = time.time()
        if self.is_reloading or (now - self.last_reload_trigger_time < 0.4):
            return False
        if self.ammo < self.max_ammo:
            self.is_reloading = True
            self.reload_start_time = now
            self.last_reload_trigger_time = now
            return True
        return False

    def update_reload(self, now: float) -> bool:
        """Advance reload timer. Returns True on the exact frame reload finishes."""
        if not self.is_reloading:
            return False
        if now - self.reload_start_time >= self.reload_duration_sec:
            self.ammo = self.max_ammo
            self.is_reloading = False
            return True
        return False

    def update_aim(self, raw_x_norm: float, raw_y_norm: float) -> None:
        """Apply active margin clamping and EMA smoothing to target coordinates."""
        norm_x_clamped = np.clip(
            (raw_x_norm - ACTIVE_MARGIN_X) / (1.0 - 2 * ACTIVE_MARGIN_X), 0.0, 1.0
        )
        norm_y_clamped = np.clip(
            (raw_y_norm - ACTIVE_MARGIN_Y) / (1.0 - 2 * ACTIVE_MARGIN_Y), 0.0, 1.0
        )

        target_x = float(norm_x_clamped * self.screen_width)
        target_y = float(norm_y_clamped * self.screen_height)

        if not self.has_aim_history:
            self.aim_x = target_x
            self.aim_y = target_y
            self.has_aim_history = True
        else:
            self.aim_x = (
                self.smoothing_factor * target_x
                + (1.0 - self.smoothing_factor) * self.aim_x
            )
            self.aim_y = (
                self.smoothing_factor * target_y
                + (1.0 - self.smoothing_factor) * self.aim_y
            )


class GunController:
    """
    Manages dual-wielding hand guns, aim smoothing, trigger debouncing,
    ammo tracking, and reload gestures.
    """

    def __init__(
        self,
        screen_width: int = 1000,
        screen_height: int = 700,
        smoothing_factor: float = SMOOTHING_FACTOR,
        trigger_cooldown_sec: float = TRIGGER_COOLDOWN_SEC,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.smoothing_factor = max(0.01, min(1.0, smoothing_factor))
        self.trigger_cooldown_sec = trigger_cooldown_sec
        self.confidence_threshold = confidence_threshold

        # Gun 0 (Primary / Cyan) and Gun 1 (Secondary / Orange)
        self.guns: List[SingleGunState] = [
            SingleGunState(
                gun_id=0,
                label="RIGHT GUN",
                color=(0, 240, 220),
                screen_width=screen_width,
                screen_height=screen_height,
                smoothing_factor=self.smoothing_factor,
                trigger_cooldown_sec=self.trigger_cooldown_sec,
                confidence_threshold=self.confidence_threshold,
            ),
            SingleGunState(
                gun_id=1,
                label="LEFT GUN",
                color=(255, 140, 30),
                screen_width=screen_width,
                screen_height=screen_height,
                smoothing_factor=self.smoothing_factor,
                trigger_cooldown_sec=self.trigger_cooldown_sec,
                confidence_threshold=self.confidence_threshold,
            ),
        ]

    def reload_all(self) -> bool:
        """Trigger reload on all guns."""
        reloaded = False
        for gun in self.guns:
            if gun.trigger_reload():
                reloaded = True
        return reloaded

    def update_multi(
        self,
        hands_data: List[Dict[str, Any]],
        gesture_classifier: Optional[GestureClassifier] = None,
        rapid_fire: bool = False,
    ) -> Dict[str, Any]:
        """
        Process current frame's tracking data for up to 2 hands simultaneously.
        """
        now = time.time()
        current_cooldown = (
            RAPID_FIRE_COOLDOWN_SEC if rapid_fire else self.trigger_cooldown_sec
        )

        # 1. Check for two-hand palm tap reload if at least 2 hands are detected
        palm_tap_detected = False
        if len(hands_data) >= 2:
            lm1 = hands_data[0]["landmarks"]
            lm2 = hands_data[1]["landmarks"]
            if check_two_hand_tap(lm1, lm2):
                palm_tap_detected = True
                self.reload_all()

        # 2. Stable Hand-to-Gun Spatial Association
        # To prevent index flipping jitter when both hands are on screen:
        # Sort hands from left to right on screen
        sorted_hands: List[Optional[Dict[str, Any]]] = [None, None]
        if len(hands_data) >= 2:
            hA, hB = hands_data[0], hands_data[1]
            if hA["index_tip_norm"][0] < hB["index_tip_norm"][0]:
                sorted_hands[1] = hA  # Left side of screen -> Left Gun (Gun 1)
                sorted_hands[0] = hB  # Right side of screen -> Right Gun (Gun 0)
            else:
                sorted_hands[1] = hB
                sorted_hands[0] = hA
        elif len(hands_data) == 1:
            h = hands_data[0]
            # Match by proximity or default to Gun 0
            if self.guns[1].active and not self.guns[0].active:
                sorted_hands[1] = h
            elif h["index_tip_norm"][0] < 0.40 and self.guns[1].has_aim_history:
                sorted_hands[1] = h
            else:
                sorted_hands[0] = h

        guns_state: List[Dict[str, Any]] = []
        any_reloaded_this_frame = False
        any_reload_started = palm_tap_detected

        for gun_idx in range(len(self.guns)):
            gun = self.guns[gun_idx]
            hand = sorted_hands[gun_idx]

            # Advance reload completion
            if gun.update_reload(now):
                any_reloaded_this_frame = True

            should_shoot = False
            empty_click = False

            if hand is not None:
                gun.active = True
                raw_landmarks = hand["landmarks"]
                index_tip_norm = hand["index_tip_norm"]

                # Check pointing down reload gesture for this hand
                if is_pointing_down(raw_landmarks):
                    if gun.trigger_reload():
                        any_reload_started = True

                # Predict gesture
                if gesture_classifier and gesture_classifier.is_loaded():
                    pred_gesture, conf = gesture_classifier.predict(raw_landmarks)
                    gun.current_gesture = pred_gesture
                    gun.current_confidence = conf
                else:
                    gun.current_gesture = GESTURE_GUN_READY
                    gun.current_confidence = 1.0

                is_valid = gun.current_confidence >= gun.confidence_threshold
                gun.is_gun_ready = is_valid and (
                    gun.current_gesture in (GESTURE_GUN_READY, GESTURE_SHOOT)
                )

                # Update smoothed aim position
                gun.update_aim(index_tip_norm[0], index_tip_norm[1])

                # Trigger detection
                gun.thumb_metric = get_thumb_trigger_metric(raw_landmarks)
                is_shooting_gesture = (
                    is_valid and gun.current_gesture == GESTURE_SHOOT
                ) or (gun.is_gun_ready and gun.thumb_metric < 0.52)

                cooldown_ready = (now - gun.last_shot_time >= current_cooldown)

                if is_shooting_gesture and cooldown_ready and not gun.is_reloading:
                    if gun.ammo > 0 or rapid_fire:
                        should_shoot = True
                        if not rapid_fire:
                            gun.ammo -= 1
                        gun.last_shot_time = now
                        gun.current_gesture = GESTURE_SHOOT
                    else:
                        empty_click = True
                        gun.last_shot_time = now
            else:
                gun.active = False
                gun.is_gun_ready = False
                gun.current_gesture = "NO_GUN"
                gun.current_confidence = 0.0

            reload_progress = 0.0
            if gun.is_reloading:
                elapsed = now - gun.reload_start_time
                reload_progress = min(1.0, elapsed / gun.reload_duration_sec)

            guns_state.append({
                "gun_id": gun.gun_id,
                "label": gun.label,
                "color": gun.color,
                "aim_x": gun.aim_x,
                "aim_y": gun.aim_y,
                "gun_ready": gun.is_gun_ready,
                "shoot": should_shoot,
                "empty_click": empty_click,
                "ammo": gun.ammo,
                "max_ammo": gun.max_ammo,
                "is_reloading": gun.is_reloading,
                "reload_progress": reload_progress,
                "gesture": gun.current_gesture,
                "confidence": gun.current_confidence,
                "thumb_metric": gun.thumb_metric,
                "active": gun.active,
            })

        primary = guns_state[0] if guns_state[0]["active"] else (guns_state[1] if guns_state[1]["active"] else guns_state[0])
        return {
            "guns": guns_state,
            "num_hands": len(hands_data),
            "reload_started": any_reload_started,
            "reloaded_complete": any_reloaded_this_frame,
            "aim_x": primary["aim_x"],
            "aim_y": primary["aim_y"],
            "gun_ready": primary["gun_ready"],
            "shoot": primary["shoot"],
            "empty_click": primary["empty_click"],
            "ammo": primary["ammo"],
            "max_ammo": primary["max_ammo"],
            "is_reloading": primary["is_reloading"],
            "gesture": primary["gesture"],
            "confidence": primary["confidence"],
        }

    def update(
        self,
        raw_landmarks: Optional[np.ndarray],
        index_tip_norm: Optional[Tuple[float, float]],
        gesture_classifier: Optional[GestureClassifier] = None,
        rapid_fire: bool = False,
    ) -> Dict[str, Any]:
        """Backward-compatible single-hand update method."""
        if raw_landmarks is not None and index_tip_norm is not None:
            hands_data = [{
                "landmarks": raw_landmarks,
                "index_tip_norm": index_tip_norm,
                "handedness": "Primary",
                "hand_idx": 0,
            }]
        else:
            hands_data = []

        return self.update_multi(
            hands_data=hands_data,
            gesture_classifier=gesture_classifier,
            rapid_fire=rapid_fire,
        )

    def reset_cooldown(self) -> None:
        """Reset shot cooldown timer for all guns."""
        for gun in self.guns:
            gun.last_shot_time = 0.0
