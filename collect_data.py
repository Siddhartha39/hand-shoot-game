"""
Data Collection Script.

Captures normalized hand landmark data from webcam video feed
and saves it to data/dataset.csv for ML model training.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
import pandas as pd

from hand_tracker import (
    NUM_FEATURES,
    HandTracker,
    get_feature_names,
    normalize_landmarks,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
DATASET_PATH = DATA_DIR / "dataset.csv"

# Target classes
CLASSES = {
    0: "NO_GUN",
    1: "GUN_READY",
    2: "SHOOT",
}

TARGET_SAMPLES_PER_CLASS = 1000


def load_existing_counts(filepath: Path) -> Dict[str, int]:
    """Return count of samples per class already in the dataset file."""
    counts = {cls_name: 0 for cls_name in CLASSES.values()}
    if not filepath.exists():
        return counts

    try:
        df = pd.read_csv(filepath)
        if "label" in df.columns:
            for cls_name in counts:
                counts[cls_name] = int((df["label"] == cls_name).sum())
    except Exception as e:
        print(f"[Warning] Could not parse existing dataset: {e}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Hand Gun gesture training data.")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index (default: 0)")
    parser.add_argument("--target", type=int, default=TARGET_SAMPLES_PER_CLASS,
                        help="Target sample count per class (default: 1000)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    counts = load_existing_counts(DATASET_PATH)

    print("\n" + "=" * 65)
    print("      HAND GUN GESTURE DATA COLLECTOR")
    print("=" * 65)
    print("Controls:")
    print("  [0] : Select / Record 'NO_GUN'     (open hand, fist, neutral)")
    print("  [1] : Select / Record 'GUN_READY'  (index extended, thumb up)")
    print("  [2] : Select / Record 'SHOOT'      (gun shape with thumb pulled/down)")
    print("  [SPACE] : Toggle continuous recording for active class")
    print("  [C] : Clear current recorded buffer before saving")
    print("  [Q] or [ESC] : Save and Quit")
    print("-" * 65)
    print(f"Current counts: NO_GUN={counts['NO_GUN']}, GUN_READY={counts['GUN_READY']}, SHOOT={counts['SHOOT']}")
    print(f"Dataset destination: {DATASET_PATH}")
    print("=" * 65 + "\n")

    # Initialize Hand Tracker
    tracker = HandTracker(max_num_hands=1, min_detection_confidence=0.7)

    # Initialize Camera
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Could not open webcam at index {args.camera}.")
        print("Please check your camera connection or camera permissions.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    active_class_id: int = 1  # Default to GUN_READY
    is_recording: bool = False
    new_samples: List[List[float]] = []
    new_labels: List[str] = []

    last_record_time = 0.0
    record_interval = 0.04  # ~25 samples per second max during continuous recording

    prev_frame_time = time.time()
    fps = 30.0

    try:
        while True:
            success, frame = cap.read()
            if not success or frame is None:
                print("[Warning] Failed to grab frame from webcam.")
                time.sleep(0.05)
                continue

            current_time = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, current_time - prev_frame_time))
            prev_frame_time = current_time

            # Hand tracking
            annotated_frame, raw_landmarks, index_tip = tracker.process_frame(frame, flip_horizontal=True)
            hand_detected = raw_landmarks is not None

            # Recording logic
            active_class_name = CLASSES[active_class_id]
            if is_recording and hand_detected:
                if current_time - last_record_time >= record_interval:
                    norm_features = normalize_landmarks(raw_landmarks)
                    new_samples.append(norm_features.tolist())
                    new_labels.append(active_class_name)
                    counts[active_class_name] += 1
                    last_record_time = current_time

            # Drawing HUD
            h, w, _ = annotated_frame.shape
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 140), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.75, annotated_frame, 0.25, 0, annotated_frame)

            # Title & FPS
            cv2.putText(
                annotated_frame,
                f"Hand Gun Data Collector | FPS: {fps:.1f}",
                (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            # Active Mode
            rec_status = "[REC]" if is_recording else "[PAUSED]"
            rec_color = (0, 0, 255) if is_recording else (180, 180, 180)
            cv2.putText(
                annotated_frame,
                f"Active Class: {active_class_name} {rec_status}",
                (15, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                rec_color,
                2,
            )

            # Hand Detection Status
            detect_text = "Hand Detected" if hand_detected else "NO HAND DETECTED"
            detect_color = (0, 255, 0) if hand_detected else (0, 0, 255)
            cv2.putText(
                annotated_frame,
                detect_text,
                (w - 220, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                detect_color,
                2,
            )

            # Class Progress Counters
            y_offset = 85
            for cid, cname in CLASSES.items():
                cnt = counts[cname]
                pct = min(1.0, cnt / args.target) * 100.0
                highlight = (0, 255, 255) if cid == active_class_id else (200, 200, 200)
                txt = f"[{cid}] {cname}: {cnt}/{args.target} ({pct:.0f}%)"
                cv2.putText(
                    annotated_frame,
                    txt,
                    (15 + cid * 205, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    highlight,
                    1,
                )

            # Instructions bottom bar
            cv2.putText(
                annotated_frame,
                "Keys: [0,1,2] Select Class | [SPACE] Toggle Rec | [Q] Save & Quit",
                (15, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            cv2.imshow("Hand Gun Gesture Data Collection", annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):  # Q or ESC
                break
            elif key == ord("0"):
                active_class_id = 0
                print(f"[Select] Switched active class to {CLASSES[0]}")
            elif key == ord("1"):
                active_class_id = 1
                print(f"[Select] Switched active class to {CLASSES[1]}")
            elif key == ord("2"):
                active_class_id = 2
                print(f"[Select] Switched active class to {CLASSES[2]}")
            elif key == ord(" "):  # Spacebar toggles continuous recording
                is_recording = not is_recording
                state = "RECORDING" if is_recording else "PAUSED"
                print(f"[Record] {state} for class {CLASSES[active_class_id]}")

    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()

    # Save data to CSV
    if new_samples:
        print(f"\n[Saving] Appending {len(new_samples)} new samples to {DATASET_PATH}...")
        columns = get_feature_names() + ["label"]
        df_new = pd.DataFrame(new_samples, columns=get_feature_names())
        df_new["label"] = new_labels

        if DATASET_PATH.exists():
            df_existing = pd.read_csv(DATASET_PATH)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.to_csv(DATASET_PATH, index=False)
        print(f"[SUCCESS] Dataset saved! Total dataset size: {len(df_combined)} samples.")
        print(df_combined["label"].value_counts().to_string())
    else:
        print("\n[Info] No new samples were recorded.")


if __name__ == "__main__":
    main()
