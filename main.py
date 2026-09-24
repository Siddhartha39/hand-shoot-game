"""
Main Application Entry Point.

Coordinates webcam capture, MediaPipe hand tracking, ML gesture recognition,
aim smoothing, and the Pygame shooting game loop.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

from controller import GunController
from game import GunShooterGame, WINDOW_HEIGHT, WINDOW_WIDTH
from gesture_model import GestureClassifier
from hand_tracker import HandTracker

# Default Paths
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "gun_gesture_model.pkl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand Gun Gesture Shooter Main Application")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index (default: 0)")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Trained model path")
    parser.add_argument("--mouse", action="store_true", help="Force mouse-only control mode")
    parser.add_argument("--debug", action="store_true", help="Enable FPS and coordinate debug HUD")
    parser.add_argument("--threshold", type=float, default=0.65, help="Gesture confidence threshold")
    parser.add_argument("--smoothing", type=float, default=0.35, help="Aim smoothing factor (0.01 - 1.0)")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("Game Controls & Features:")
    print("  - Dual Wielding:  Use 1 or 2 hands for independent aiming & shooting!")
    print("  - Hand Gun Ready: Point index finger to aim crosshair")
    print("  - Thumb Trigger:  Curl/pull thumb down to fire shot")
    print("  - Reload Gesture: Point hand DOWN or TAP PALMS together (or [SPACE])")
    print("  - [S] Key:        Cycle Sound Packs (LASER, REVOLVER, SILENCER)")
    print("  - [M] Key:        Toggle between HAND MODE and MOUSE MODE")
    print("  - [D] Key:        Toggle DEBUG overlay (FPS & counts)")
    print("  - [R] Key:        Restart current round")
    print("  - [Q] / [ESC]:    Quit application")
    print("  - Special:        Defeat shielded BOSSES & collect POWER-UPS (Freeze/Rapid/Life)")
    print("=" * 65 + "\n")

    initial_mode = "MOUSE" if args.mouse else "HAND"

    # 1. Initialize Pygame Game
    try:
        game = GunShooterGame(
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            control_mode=initial_mode,
            debug_mode=args.debug,
        )
    except Exception as e:
        print(f"[FATAL] Pygame initialization failed: {e}")
        sys.exit(1)

    # 2. Check and Load Gesture Model
    classifier: GestureClassifier | None = None
    if not args.mouse:
        if not args.model.exists():
            print(f"[WARNING] Gesture model not found at: {args.model}")
            print("Tip: You can generate or train a model with 'python train_model.py'.")
            print("Falling back to MOUSE MODE for gameplay.\n")
            game.control_mode = "MOUSE"
        else:
            try:
                classifier = GestureClassifier(args.model, min_confidence=args.threshold)
                print(f"[OK] Loaded gesture model from {args.model}")
            except Exception as e:
                print(f"[WARNING] Could not load model: {e}. Falling back to MOUSE MODE.")
                game.control_mode = "MOUSE"

    # 3. Initialize Webcam & Tracker if in HAND mode
    cap: cv2.VideoCapture | None = None
    tracker: HandTracker | None = None
    controller = GunController(
        screen_width=WINDOW_WIDTH,
        screen_height=WINDOW_HEIGHT,
        smoothing_factor=args.smoothing,
        confidence_threshold=args.threshold,
    )

    if game.control_mode == "HAND":
        try:
            tracker = HandTracker(max_num_hands=2, min_detection_confidence=0.50)
            cap = cv2.VideoCapture(args.camera)
            if not cap.isOpened():
                print(f"[WARNING] Camera at index {args.camera} unavailable.")
                print("Switching control mode to MOUSE MODE.\n")
                game.control_mode = "MOUSE"
                cap = None
            else:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                # Optimize camera buffer
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print(f"[OK] Camera {args.camera} initialized successfully.")
        except Exception as e:
            print(f"[WARNING] MediaPipe or Camera initialization failed: {e}")
            print("Defaulting to MOUSE MODE.\n")
            game.control_mode = "MOUSE"
            cap = None

    print(f"\n[Ready] Game started in {game.control_mode} MODE. Have fun!\n")

    # Main Application Loop
    last_frame_time = time.time()

    try:
        while game.running:
            dt = game.clock.tick(60) / 1000.0
            game.handle_events()

            control_state = None

            if game.control_mode == "HAND" and cap is not None and tracker is not None:
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Run multi-hand tracking (supports both hands simultaneously)
                    annotated_frame, hands_data = tracker.process_frame_multi(
                        frame, flip_horizontal=True
                    )
                    # Pass frame to mini camera HUD PiP
                    game.set_camera_frame(annotated_frame)

                    # Update gun controller with both hands & power-up state
                    control_state = controller.update_multi(
                        hands_data=hands_data,
                        gesture_classifier=classifier,
                        rapid_fire=(game.rapid_fire_timer > 0),
                    )
                else:
                    game.set_camera_frame(None)
            else:
                game.set_camera_frame(None)

            # Update and render game
            game.update(dt, control_state=control_state)
            game.render()

    except KeyboardInterrupt:
        print("\n[Exiting] Game closed by user.")
    finally:
        if cap is not None:
            cap.release()
        if tracker is not None:
            tracker.close()
        cv2.destroyAllWindows()
        import pygame
        pygame.quit()
        print("[Done] Resources cleaned up. Goodbye!")


if __name__ == "__main__":
    main()


# Vercel Serverless Function compatibility entrypoint
def handler(request=None, *args, **kwargs):
    """Fallback handler if invoked on Vercel Python runtime."""
    index_file = BASE_DIR / "index.html"
    content = index_file.read_text(encoding="utf-8") if index_file.exists() else "Hand Gun Game"
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html; charset=utf-8"},
        "body": content,
    }


app = handler

