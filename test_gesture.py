"""
Real-time Gesture Testing Script with Simultaneous Dual-Hand Support.

Loads models/gun_gesture_model.pkl and performs live webcam dual-hand gesture recognition
with visual HUD, dual independent crosshairs, trigger debouncing, and reload detection.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from controller import GunController
from gesture_model import (
    CONFIDENCE_THRESHOLD,
    GESTURE_GUN_READY,
    GESTURE_NO_GUN,
    GESTURE_SHOOT,
    GestureClassifier,
)
from hand_tracker import HandTracker

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "gun_gesture_model.pkl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Test trained Hand Gun gesture model on live webcam with dual hands.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Path to trained .pkl model")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--confidence", type=float, default=CONFIDENCE_THRESHOLD, help="Confidence threshold")
    parser.add_argument("--hands", type=int, default=2, help="Max hands to track (default: 2)")
    args = parser.parse_args()

    if not args.model.exists():
        print(f"[ERROR] Trained model file not found at: {args.model}")
        print("Please train a model first using 'python train_model.py'.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("      HAND GUN GESTURE REAL-TIME TESTER (DUAL HANDS)")
    print("=" * 65)
    print(f"Loading model from: {args.model}")
    print(f"Confidence threshold: {args.confidence:.2f}")
    print(f"Max hands: {args.hands}")
    print("Controls:")
    print("  - Raise 1 or 2 hands: Independent Left & Right Gun detection")
    print("  - Point index finger to aim crosshairs")
    print("  - Pull thumb down to fire trigger (independent for each hand)")
    print("  - Point hand DOWN or TAP PALMS to reload")
    print("  - [Q] or [ESC] : Quit tester")
    print("=" * 65 + "\n")

    classifier = GestureClassifier(args.model, min_confidence=args.confidence)
    tracker = HandTracker(max_num_hands=args.hands, min_detection_confidence=0.50, min_tracking_confidence=0.50)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Could not open webcam at index {args.camera}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    prev_time = time.time()
    fps = 30.0

    # Colors for gestures (BGR)
    COLOR_MAP = {
        GESTURE_NO_GUN: (120, 120, 120),  # Grey
        GESTURE_GUN_READY: (0, 220, 0),    # Bright Green
        GESTURE_SHOOT: (0, 0, 255),       # Bright Red
    }

    controller = GunController(
        screen_width=640,
        screen_height=480,
        confidence_threshold=args.confidence,
    )

    shot_flash = [0.0, 0.0]  # Gun 0 and Gun 1 flash timers

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            current_time = time.time()
            dt = max(1e-5, current_time - prev_time)
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
            prev_time = current_time

            # Multi-hand tracking
            annotated_frame, hands_data = tracker.process_frame_multi(frame, flip_horizontal=True)
            h, w, _ = annotated_frame.shape

            control_state = controller.update_multi(
                hands_data=hands_data,
                gesture_classifier=classifier,
            )

            guns_data = control_state.get("guns", [])

            # Update shot flash timers
            for idx in range(min(2, len(guns_data))):
                if guns_data[idx].get("shoot", False):
                    shot_flash[idx] = 0.30
                elif shot_flash[idx] > 0:
                    shot_flash[idx] = max(0.0, shot_flash[idx] - dt)

            # Top HUD Banner
            banner = annotated_frame.copy()
            cv2.rectangle(banner, (0, 0), (w, 115), (15, 18, 24), -1)
            cv2.addWeighted(banner, 0.85, annotated_frame, 0.15, 0, annotated_frame)

            # Top Header Bar
            num_detected = len(hands_data)
            detect_color = (0, 255, 200) if num_detected >= 2 else ((0, 210, 255) if num_detected == 1 else (100, 100, 255))
            cv2.putText(
                annotated_frame,
                f"Dual-Hand Test | FPS: {fps:.1f}",
                (15, 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 220, 220),
                1,
            )
            cv2.putText(
                annotated_frame,
                f"HANDS DETECTED: {num_detected} / {args.hands}",
                (w - 240, 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                detect_color,
                2,
            )

            # Render Left Gun HUD (Gun 1, Left of screen) & Right Gun HUD (Gun 0, Right of screen)
            # Layout: Left column for Gun 1, Right column for Gun 0
            gun_panels = [
                (1, 15, (30, 140, 255)),       # Gun 1: Left Gun (Orange in BGR)
                (0, w // 2 + 10, (220, 240, 0)), # Gun 0: Right Gun (Cyan in BGR)
            ]

            for g_id, col_x, default_bgr in gun_panels:
                g_data = guns_data[g_id] if g_id < len(guns_data) else None
                label = "LEFT GUN" if g_id == 1 else "RIGHT GUN"

                if g_data and g_data["active"]:
                    gesture = g_data["gesture"]
                    conf = g_data["confidence"]
                    ready = g_data["gun_ready"]
                    thumb_metric = g_data.get("thumb_metric", 1.0)
                    ammo = g_data.get("ammo", 8)
                    is_reloading = g_data.get("is_reloading", False)
                    g_color = COLOR_MAP.get(gesture, default_bgr)

                    status_str = f"{label}: {gesture} ({conf * 100:.0f}%)"
                    cv2.putText(annotated_frame, status_str, (col_x, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.58, g_color, 2)

                    if is_reloading:
                        trig_str = "STATUS: RELOADING..."
                        trig_col = (0, 255, 220)
                    elif shot_flash[g_id] > 0:
                        trig_str = "TRIGGER: BANG! FIRED!"
                        trig_col = (0, 0, 255)
                    elif ready:
                        trig_str = f"TRIGGER: READY (Thumb: {thumb_metric:.2f})"
                        trig_col = (0, 255, 0)
                    else:
                        trig_str = f"TRIGGER: IDLE (Ammo: {ammo}/8)"
                        trig_col = (140, 140, 140)

                    cv2.putText(annotated_frame, trig_str, (col_x, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.48, trig_col, 1)

                    # Confidence bar
                    bar_w = 120
                    cv2.rectangle(annotated_frame, (col_x, 82), (col_x + bar_w, 90), (50, 50, 50), -1)
                    fill_w = int(bar_w * max(0.0, min(1.0, conf)))
                    cv2.rectangle(annotated_frame, (col_x, 82), (col_x + fill_w, 90), g_color, -1)

                    # Ammo dots
                    for a_i in range(8):
                        dot_col = default_bgr if a_i < ammo else (50, 50, 50)
                        cv2.circle(annotated_frame, (col_x + 135 + a_i * 11, 86), 4, dot_col, -1)

                else:
                    cv2.putText(
                        annotated_frame,
                        f"{label}: NO HAND",
                        (col_x, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.58,
                        (100, 100, 100),
                        1,
                    )
                    cv2.putText(
                        annotated_frame,
                        "Raise hand to aim",
                        (col_x, 72),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.48,
                        (80, 80, 80),
                        1,
                    )

            # Draw Crosshairs for active guns on the camera feed
            for g_id in [1, 0]:
                if g_id < len(guns_data) and guns_data[g_id]["active"]:
                    g_data = guns_data[g_id]
                    cx = int(g_data["aim_x"])
                    cy = int(g_data["aim_y"])
                    color = (30, 140, 255) if g_id == 1 else (220, 240, 0)  # Orange vs Cyan

                    if shot_flash[g_id] > 0:
                        color = (0, 0, 255)
                        cv2.circle(annotated_frame, (cx, cy), 38, (0, 80, 255), 3)
                        cv2.putText(annotated_frame, "BANG!", (cx + 15, cy - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    elif not g_data["gun_ready"]:
                        color = (130, 130, 140)

                    # Reticle circle
                    cv2.circle(annotated_frame, (cx, cy), 22, color, 2)
                    cv2.circle(annotated_frame, (cx, cy), 3, color, -1)

                    # Crosshair lines
                    gap, tick = 6, 10
                    cv2.line(annotated_frame, (cx, cy - 22 - tick), (cx, cy - gap), color, 2)
                    cv2.line(annotated_frame, (cx, cy + gap), (cx, cy + 22 + tick), color, 2)
                    cv2.line(annotated_frame, (cx - 22 - tick, cy), (cx - gap, cy), color, 2)
                    cv2.line(annotated_frame, (cx + gap, cy), (cx + 22 + tick, cy), color, 2)

                    # Label
                    g_label = "L-GUN" if g_id == 1 else "R-GUN"
                    cv2.putText(annotated_frame, g_label, (cx - 22, cy - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

            # Global Reload Notification
            if control_state.get("reload_started", False):
                cv2.putText(
                    annotated_frame,
                    "RELOAD GESTURE DETECTED!",
                    (w // 2 - 140, h - 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 220),
                    2,
                )

            # Footer
            cv2.putText(
                annotated_frame,
                "Press [Q] or [ESC] to Exit | Dual-Wield Active",
                (15, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (180, 180, 180),
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
