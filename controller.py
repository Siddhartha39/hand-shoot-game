"""
Controller Module.

Translates hand tracking landmarks and gesture predictions into clean game control inputs.
Handles aim smoothing, coordinate mapping, and trigger debouncing/cooldown.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import numpy as np

from gesture_model import GESTURE_GUN_READY, GESTURE_SHOOT, GestureClassifier
from hand_tracker import get_thumb_trigger_metric

# Configurable Controller Parameters
SMOOTHING_FACTOR: float = 0.35  # Alpha for Exponential Moving Average (0 < alpha <= 1)
TRIGGER_COOLDOWN_SEC: float = 0.25  # Debounce delay between successive shots (250 ms)
CONFIDENCE_THRESHOLD: float = 0.65  # Minimum ML model confidence
ACTIVE_MARGIN_X: float = 0.10  # Margin to allow comfortable edge-to-edge aiming
ACTIVE_MARGIN_Y: float = 0.10


class GunController:
    """
    Manages aiming smoothing, trigger debouncing, and converts
    vision/ML detections into a unified game control state.
    """

    def __init__(
        self,
        screen_width: int = 1000,
        screen_height: int = 700,
        smoothing_factor: float = SMOOTHING_FACTOR,
        trigger_cooldown_sec: float = TRIGGER_COOLDOWN_SEC,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        """
        Initialize the gun controller.

        Args:
            screen_width: Game window width in pixels.
            screen_height: Game window height in pixels.
            smoothing_factor: Exponential moving average factor.
            trigger_cooldown_sec: Cooldown in seconds between shots.
            confidence_threshold: Minimum classifier probability.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.smoothing_factor = max(0.01, min(1.0, smoothing_factor))
        self.trigger_cooldown_sec = trigger_cooldown_sec
        self.confidence_threshold = confidence_threshold

        # Smoothed aim position in screen pixels
        self.aim_x: float = screen_width / 2.0
        self.aim_y: float = screen_height / 2.0
        self.has_aim_history: bool = False

        # State tracking
        self.last_shot_time: float = 0.0
        self.is_gun_ready: bool = False
        self.current_gesture: str = "NO_GUN"
        self.current_confidence: float = 0.0

    def update(
        self,
        raw_landmarks: Optional[np.ndarray],
        index_tip_norm: Optional[Tuple[float, float]],
        gesture_classifier: Optional[GestureClassifier] = None,
    ) -> Dict[str, Any]:
        """
        Process current frame's tracking data and compute control state.

        Args:
            raw_landmarks: MediaPipe landmarks array (21, 3) or None.
            index_tip_norm: (x, y) normalized coordinates of index fingertip (0.0 to 1.0).
            gesture_classifier: Loaded GestureClassifier instance.

        Returns:
            Dictionary with control state:
            {
                "gun_ready": bool,
                "aim_x": float,
                "aim_y": float,
                "shoot": bool,
                "gesture": str,
                "confidence": float
            }
        """
        now = time.time()
        should_shoot = False

        # Reset states if no hand detected
        if raw_landmarks is None or index_tip_norm is None:
            self.is_gun_ready = False
            self.current_gesture = "NO_GUN"
            self.current_confidence = 0.0
            return {
                "gun_ready": False,
                "aim_x": self.aim_x,
                "aim_y": self.aim_y,
                "shoot": False,
                "gesture": "NO_GUN",
                "confidence": 0.0,
            }

        # Predict gesture
        if gesture_classifier and gesture_classifier.is_loaded():
            predicted_gesture, confidence = gesture_classifier.predict(raw_landmarks)
            self.current_gesture = predicted_gesture
            self.current_confidence = confidence
        else:
            # Fallback heuristic if model is not loaded: check index finger extended
            self.current_gesture = GESTURE_GUN_READY
            self.current_confidence = 1.0

        is_valid_confidence = self.current_confidence >= self.confidence_threshold
        is_ready = is_valid_confidence and (
            self.current_gesture in (GESTURE_GUN_READY, GESTURE_SHOOT)
        )
        self.is_gun_ready = is_ready

        # Update smoothed aiming crosshair when gun is active or tracking
        raw_x_norm, raw_y_norm = index_tip_norm

        # Map normalized camera coordinate (with margin inset) to screen coordinate
        # Clamp between active margins so reaching corners is easy
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
            # Exponential Moving Average (EMA) smoothing
            self.aim_x = (
                self.smoothing_factor * target_x
                + (1.0 - self.smoothing_factor) * self.aim_x
            )
            self.aim_y = (
                self.smoothing_factor * target_y
                + (1.0 - self.smoothing_factor) * self.aim_y
            )

        # Dynamic trigger detection
        thumb_metric = get_thumb_trigger_metric(raw_landmarks)
        classifier_shoot = is_valid_confidence and (self.current_gesture == GESTURE_SHOOT)
        physical_trigger = self.is_gun_ready and (thumb_metric < 0.52)
        cooldown_ready = (now - self.last_shot_time >= self.trigger_cooldown_sec)

        if (classifier_shoot or physical_trigger) and cooldown_ready:
            should_shoot = True
            self.last_shot_time = now
            self.current_gesture = GESTURE_SHOOT

        return {
            "gun_ready": self.is_gun_ready,
            "aim_x": self.aim_x,
            "aim_y": self.aim_y,
            "shoot": should_shoot,
            "gesture": self.current_gesture,
            "confidence": self.current_confidence,
            "thumb_metric": thumb_metric,
        }

    def reset_cooldown(self) -> None:
        """Reset shot cooldown timer."""
        self.last_shot_time = 0.0
