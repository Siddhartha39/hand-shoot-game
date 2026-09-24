"""
Real-time Gesture Testing Script.

Loads models/gun_gesture_model.pkl and performs live webcam gesture recognition
with visual HUD, landmark drawing, and confidence monitoring.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from gesture_model import (
    CONFIDENCE_THRESHOLD,
    GESTURE_GUN_READY,
    GESTURE_NO_GUN,
    GESTURE_SHOOT,
    GestureClassifier,
)
from controller import GunController
from hand_tracker import HandTracker, normalize_landmarks

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "gun_gesture_model.pkl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Test trained Hand Gun gesture model on live webcam.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Path to trained .pkl model")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--confidence", type=float, default=CONFIDENCE_THRESHOLD, help="Confidence threshold")
    args = parser.parse_args()

    if not args.model.exists():
        print(f"[ERROR] Trained model file not found at: {args.model}")
        print("Please train a model first using 'python train_model.py'.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("      HAND GUN GESTURE REAL-TIME TESTER")
    print("=" * 65)
    print(f"Loading model from: {args.model}")
    print(f"Confidence threshold: {args.confidence:.2f}")
    print("Controls:")
    print("  [Q] or [ESC] : Quit tester")
    print("=" * 65 + "\n")

    classifier = GestureClassifier(args.model, min_confidence=args.confidence)
    tracker = HandTracker(max_num_hands=1, min_detection_confidence=0.7)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Could not open webcam at index {args.camera}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prev_time = time.time()
    fps = 30.0

    # Colors for gestures (BGR)
    COLOR_MAP = {
        GESTURE_NO_GUN: (120, 120, 120),  # Grey
        GESTURE_GUN_READY: (0, 220, 0),    # Bright Green
        GESTURE_SHOOT: (0, 0, 255),       # Bright Red
    }

    controller = GunController(screen_width=640, screen_height=480, confidence_threshold=args.confidence)
    shot_flash_timer = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            current_time = time.time()
            dt = max(1e-5, current_time - prev_time)
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
            prev_time = current_time

            annotated_frame, raw_landmarks, index_tip = tracker.process_frame(frame, flip_horizontal=True)
            h, w, _ = annotated_frame.shape

            control_state = controller.update(
                raw_landmarks=raw_landmarks,
                index_tip_norm=index_tip,
                gesture_classifier=classifier,
            )

            gesture = control_state["gesture"]
            confidence = control_state["confidence"]
            gun_ready = control_state["gun_ready"]
            shot_fired = control_state["shoot"]
            thumb_metric = control_state.get("thumb_metric", 1.0)

            if shot_fired:
                shot_flash_timer = 0.35
            elif shot_flash_timer > 0:
                shot_flash_timer = max(0.0, shot_flash_timer - dt)

            # Top Banner
            banner = annotated_frame.copy()
            cv2.rectangle(banner, (0, 0), (w, 110), (20, 20, 20), -1)
            cv2.addWeighted(banner, 0.75, annotated_frame, 0.25, 0, annotated_frame)

            # Title & FPS
            cv2.putText(
                annotated_frame,
                f"Gesture Live Test | FPS: {fps:.1f}",
                (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (220, 220, 220),
                1,
            )

            # Predicted Gesture Display
            gesture_color = COLOR_MAP.get(gesture, (200, 200, 200))
            if raw_landmarks is None:
                status_text = "NO HAND DETECTED"
                status_color = (0, 0, 255)
            else:
                status_text = f"{gesture} ({confidence * 100:.1f}%)"
                status_color = gesture_color

            cv2.putText(
                annotated_frame,
                status_text,
                (15, 62),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                status_color,
                2,
            )

            # Trigger Status
            if shot_flash_timer > 0:
                trigger_text = "TRIGGER: BANG! FIRED!"
                trigger_color = (0, 0, 255)
            elif gun_ready:
                trigger_text = f"TRIGGER: READY (Thumb: {thumb_metric:.2f})"
                trigger_color = (0, 255, 0)
            else:
                trigger_text = "TRIGGER: IDLE"
                trigger_color = (130, 130, 130)

            cv2.putText(
                annotated_frame,
                trigger_text,
                (w - 320, 62),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                trigger_color,
                2,
            )

            # Confidence bar
            bar_x = 15
            bar_y = 80
            bar_w = 200
            bar_h = 10
            cv2.rectangle(annotated_frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
            fill_w = int(bar_w * max(0.0, min(1.0, confidence)))
            cv2.rectangle(annotated_frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), status_color, -1)

            # Aiming tip info
            if index_tip is not None:
                tip_px = (int(index_tip[0] * w), int(index_tip[1] * h))
                cv2.putText(
                    annotated_frame,
                    f"Aim: ({tip_px[0]}, {tip_px[1]})",
                    (w - 200, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1,
                )
                if shot_flash_timer > 0:
                    cv2.circle(annotated_frame, tip_px, 35, (0, 0, 255), 4)
                    cv2.putText(annotated_frame, "BANG!", (tip_px[0] + 15, tip_px[1] - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Instructions bottom bar
            cv2.putText(
                annotated_frame,
                "Press [Q] or [ESC] to Exit",
                (15, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )

            cv2.imshow("Hand Gun Gesture Live Test", annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
