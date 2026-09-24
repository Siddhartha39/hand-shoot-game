"""
Starter Dataset Generator.

Generates an extensive, rotation-invariant baseline dataset with realistic
MediaPipe landmark geometry covering both left and right hands, all aiming angles,
and natural biomechanical variations for NO_GUN, GUN_READY, and SHOOT gestures.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from hand_tracker import (
    NUM_LANDMARKS,
    get_feature_names,
    normalize_landmarks,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
DATASET_PATH = DATA_DIR / "dataset.csv"


def create_base_skeleton(gesture_type: str, is_left_hand: bool = False) -> np.ndarray:
    """Generate a 21x3 landmark array representing hand geometry."""
    coords = np.zeros((NUM_LANDMARKS, 3), dtype=np.float32)

    # 0: Wrist
    coords[0] = [0.0, 0.0, 0.0]

    # Hand horizontal direction factor: +1 for right hand, -1 for left hand
    h = -1.0 if is_left_hand else 1.0

    # Thumb: 1, 2, 3, 4
    if gesture_type == "GUN_READY":
        # Thumb extended outward/upward (cocked hammer)
        coords[1] = [-0.35 * h, -0.22, 0.02]
        coords[2] = [-0.60 * h, -0.45, 0.04]
        coords[3] = [-0.78 * h, -0.72, 0.05]
        coords[4] = [-0.92 * h, -1.00, 0.06]
    elif gesture_type == "SHOOT":
        # Thumb pulled / curled down (trigger action)
        coords[1] = [-0.35 * h, -0.22, 0.02]
        coords[2] = [-0.48 * h, -0.38, 0.08]
        coords[3] = [-0.40 * h, -0.52, 0.16]
        coords[4] = [-0.30 * h, -0.56, 0.20]
    else:  # NO_GUN
        coords[1] = [-0.30 * h, -0.25, 0.0]
        coords[2] = [-0.45 * h, -0.48, 0.0]
        coords[3] = [-0.55 * h, -0.70, 0.0]
        coords[4] = [-0.60 * h, -0.92, 0.0]

    # Index finger: 5, 6, 7, 8
    coords[5] = [-0.25 * h, -0.90, 0.0]
    coords[6] = [-0.26 * h, -1.25, 0.0]
    coords[7] = [-0.27 * h, -1.58, 0.0]
    coords[8] = [-0.28 * h, -1.92, 0.0]

    # Middle finger: 9, 10, 11, 12
    coords[9] = [0.0, -1.00, 0.0]  # Reference palm bone
    if gesture_type in ("GUN_READY", "SHOOT"):
        # Folded tightly into palm
        coords[10] = [0.02 * h, -1.15, 0.20]
        coords[11] = [0.03 * h, -0.88, 0.35]
        coords[12] = [0.04 * h, -0.62, 0.30]
    else:
        coords[10] = [0.0, -1.35, 0.0]
        coords[11] = [0.0, -1.68, 0.0]
        coords[12] = [0.0, -2.00, 0.0]

    # Ring finger: 13, 14, 15, 16
    coords[13] = [0.24 * h, -0.92, 0.0]
    if gesture_type in ("GUN_READY", "SHOOT"):
        coords[14] = [0.22 * h, -1.12, 0.20]
        coords[15] = [0.20 * h, -0.86, 0.35]
        coords[16] = [0.18 * h, -0.60, 0.30]
    else:
        coords[14] = [0.24 * h, -1.28, 0.0]
        coords[15] = [0.24 * h, -1.58, 0.0]
        coords[16] = [0.24 * h, -1.88, 0.0]

    # Pinky finger: 17, 18, 19, 20
    coords[17] = [0.46 * h, -0.80, 0.0]
    if gesture_type in ("GUN_READY", "SHOOT"):
        coords[18] = [0.42 * h, -1.00, 0.18]
        coords[19] = [0.38 * h, -0.76, 0.32]
        coords[20] = [0.34 * h, -0.52, 0.28]
    else:
        coords[18] = [0.46 * h, -1.12, 0.0]
        coords[19] = [0.46 * h, -1.38, 0.0]
        coords[20] = [0.46 * h, -1.65, 0.0]

    return coords


def generate_no_gun_variations(num_samples: int) -> np.ndarray:
    """Generate diverse NO_GUN hand poses (open hand, fist, relaxed, peace sign, thumbs up)."""
    samples = []
    for i in range(num_samples):
        is_left = (i % 2 == 1)
        mode = (i // 2) % 5
        base = create_base_skeleton("NO_GUN", is_left_hand=is_left)

        h = -1.0 if is_left else 1.0

        if mode == 0:
            # Full open hand (all fingers extended)
            pass
        elif mode == 1:
            # Full fist (all fingers folded)
            for mcp_idx, tip_idx in [(5, 8), (9, 12), (13, 16), (17, 20)]:
                base[mcp_idx + 1] = base[mcp_idx] + [0, -0.2, 0.2]
                base[mcp_idx + 2] = base[mcp_idx] + [0, 0.0, 0.35]
                base[tip_idx] = base[mcp_idx] + [0, 0.2, 0.25]
            base[4] = [-0.3 * h, -0.5, 0.2]
        elif mode == 2:
            # Peace sign (index & middle up, ring & pinky folded)
            base[14:17] = np.array([[0.2 * h, -0.8, 0.2], [0.2 * h, -0.6, 0.3], [0.2 * h, -0.5, 0.25]])
            base[18:21] = np.array([[0.4 * h, -0.7, 0.2], [0.4 * h, -0.5, 0.3], [0.4 * h, -0.4, 0.25]])
            base[4] = [-0.3 * h, -0.5, 0.2]
        elif mode == 3:
            # Thumbs up (thumb extended up, all 4 fingers curled)
            for mcp_idx, tip_idx in [(5, 8), (9, 12), (13, 16), (17, 20)]:
                base[mcp_idx + 1] = base[mcp_idx] + [0, -0.2, 0.2]
                base[mcp_idx + 2] = base[mcp_idx] + [0, 0.0, 0.35]
                base[tip_idx] = base[mcp_idx] + [0, 0.2, 0.25]
            base[1:5] = np.array([[-0.2 * h, -0.3, 0.0], [-0.3 * h, -0.6, 0.0], [-0.35 * h, -0.9, 0.0], [-0.4 * h, -1.2, 0.0]])
        elif mode == 4:
            # Pointing without thumb extended (index extended, thumb tucked into palm)
            base[1:5] = np.array([[-0.15 * h, -0.25, 0.1], [-0.2 * h, -0.45, 0.15], [-0.15 * h, -0.55, 0.18], [-0.1 * h, -0.6, 0.2]])
            for mcp_idx, tip_idx in [(9, 12), (13, 16), (17, 20)]:
                base[mcp_idx + 1] = base[mcp_idx] + [0, -0.2, 0.2]
                base[mcp_idx + 2] = base[mcp_idx] + [0, 0.0, 0.35]
                base[tip_idx] = base[mcp_idx] + [0, 0.2, 0.25]

        # 3D Rotation covering full hemisphere
        angle_z = np.random.uniform(-0.8, 0.8)
        angle_y = np.random.uniform(-0.6, 0.6)
        angle_x = np.random.uniform(-0.6, 0.6)
        Rz = np.array([[np.cos(angle_z), -np.sin(angle_z), 0], [np.sin(angle_z), np.cos(angle_z), 0], [0, 0, 1]])
        Ry = np.array([[np.cos(angle_y), 0, np.sin(angle_y)], [0, 1, 0], [-np.sin(angle_y), 0, np.cos(angle_y)]])
        Rx = np.array([[1, 0, 0], [0, np.cos(angle_x), -np.sin(angle_x)], [0, np.sin(angle_x), np.cos(angle_x)]])
        R = Rz @ Ry @ Rx

        scale = np.random.uniform(0.7, 1.4)
        noise = np.random.normal(0, 0.03, base.shape).astype(np.float32)
        trans = np.random.uniform(-0.4, 0.4, 3)

        sample = (base @ R.T) * scale + trans + noise
        samples.append(normalize_landmarks(sample))

    return np.array(samples, dtype=np.float32)


def generate_gun_samples(gesture_type: str, num_samples: int) -> np.ndarray:
    """Generate realistic variations of GUN_READY and SHOOT for both hands."""
    samples = []

    for i in range(num_samples):
        is_left = (i % 2 == 1)
        base = create_base_skeleton(gesture_type, is_left_hand=is_left)

        coords = base.copy()
        # Biomechanical joint jitters
        coords += np.random.normal(0, 0.025, coords.shape).astype(np.float32)

        # 3D Rotation covering aiming tilts and rotations
        angle_z = np.random.uniform(-0.7, 0.7)  # Hand tilt
        angle_y = np.random.uniform(-0.5, 0.5)  # Palm rotation
        angle_x = np.random.uniform(-0.5, 0.5)  # Pitch up/down
        Rz = np.array([[np.cos(angle_z), -np.sin(angle_z), 0], [np.sin(angle_z), np.cos(angle_z), 0], [0, 0, 1]])
        Ry = np.array([[np.cos(angle_y), 0, np.sin(angle_y)], [0, 1, 0], [-np.sin(angle_y), 0, np.cos(angle_y)]])
        Rx = np.array([[1, 0, 0], [0, np.cos(angle_x), -np.sin(angle_x)], [0, np.sin(angle_x), np.cos(angle_x)]])
        R = Rz @ Ry @ Rx

        scale = np.random.uniform(0.65, 1.5)
        trans = np.random.uniform(-0.4, 0.4, 3)

        sample = (coords @ R.T) * scale + trans
        samples.append(normalize_landmarks(sample))

    return np.array(samples, dtype=np.float32)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    num_per_class = 2000
    print(f"Generating {num_per_class} rotation-invariant baseline samples per class (Left + Right hands)...")

    X_no_gun = generate_no_gun_variations(num_per_class)
    X_gun_ready = generate_gun_samples("GUN_READY", num_per_class)
    X_shoot = generate_gun_samples("SHOOT", num_per_class)

    X_all = np.vstack([X_no_gun, X_gun_ready, X_shoot])
    y_all = (
        ["NO_GUN"] * num_per_class
        + ["GUN_READY"] * num_per_class
        + ["SHOOT"] * num_per_class
    )

    columns = get_feature_names()
    df = pd.DataFrame(X_all, columns=columns)
    df["label"] = y_all

    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df.to_csv(DATASET_PATH, index=False)
    print(f"[SUCCESS] Generated robust dataset with {len(df)} samples at {DATASET_PATH}")
    print(df["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
