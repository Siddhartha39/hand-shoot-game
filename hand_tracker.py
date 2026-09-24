"""
Hand Tracker Module.

Provides robust hand landmark detection and landmark normalization
using MediaPipe Hands.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

# Cache matplotlib configs locally if needed
_local_mpl = Path(__file__).resolve().parent / ".mplconfig"
_local_mpl.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_local_mpl))

import mediapipe as mp

# MediaPipe landmark constants
WRIST_IDX = 0
THUMB_TIP_IDX = 4
INDEX_MCP_IDX = 5
INDEX_TIP_IDX = 8
MIDDLE_MCP_IDX = 9
MIDDLE_TIP_IDX = 12
RING_TIP_IDX = 16
PINKY_TIP_IDX = 20

NUM_LANDMARKS = 21
NUM_FEATURES = 63  # 21 landmarks * 3 (x, y, z)


def get_feature_names() -> List[str]:
    """Return ordered feature column names: x0, y0, z0, ..., x20, y20, z20."""
    names: List[str] = []
    for i in range(NUM_LANDMARKS):
        names.extend([f"x{i}", f"y{i}", f"z{i}"])
    return names


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """
    Normalize 21 hand landmarks relative to the wrist (landmark 0).
    
    Normalization steps:
    1. Translate coordinates so wrist is at origin (0, 0, 0).
    2. Compute Euclidean distance from wrist (landmark 0) to middle finger MCP
       (landmark 9), which represents the stable palm bone structure.
    3. Scale coordinates by 1.0 / distance, making the scale invariant to
       hand size and distance from the camera.
    
    Args:
        landmarks: Shape (21, 3) representing (x, y, z) coordinates.
        
    Returns:
        Flattened 1D numpy array of shape (63,) with normalized coordinates.
    """
    if landmarks.shape != (NUM_LANDMARKS, 3):
        raise ValueError(f"Expected landmarks array of shape (21, 3), got {landmarks.shape}")

    # 1. Wrist as origin
    wrist = landmarks[WRIST_IDX].copy()
    centered = landmarks - wrist

    # 2. Scale factor based on distance between wrist and middle MCP (landmark 9)
    palm_ref = centered[MIDDLE_MCP_IDX]
    scale_dist = float(np.linalg.norm(palm_ref))

    # Guard against division by zero or degenerate small values
    if scale_dist < 1e-5:
        # Fallback to index MCP if middle MCP is somehow degenerate
        fallback_ref = centered[INDEX_MCP_IDX]
        scale_dist = float(np.linalg.norm(fallback_ref))
        if scale_dist < 1e-5:
            scale_dist = 1.0

    normalized = centered / scale_dist
    return normalized.flatten().astype(np.float32)


def classify_gesture_heuristically(landmarks: np.ndarray) -> Tuple[str, float]:
    """
    Biomechanical rule-based gesture classification.
    Extremely robust to hand orientation, camera distance, and left/right hand.

    Returns:
        (gesture_name, confidence)
    """
    if landmarks.shape != (NUM_LANDMARKS, 3):
        return "NO_GUN", 0.0

    wrist = landmarks[WRIST_IDX]
    mid_mcp = landmarks[MIDDLE_MCP_IDX]
    palm_scale = float(np.linalg.norm(mid_mcp - wrist))
    if palm_scale < 1e-4:
        palm_scale = 1.0

    # 1. Index extension check
    idx_tip_dist = np.linalg.norm(landmarks[INDEX_TIP_IDX] - wrist)
    idx_pip_dist = np.linalg.norm(landmarks[6] - wrist)
    idx_mcp_dist = np.linalg.norm(landmarks[INDEX_MCP_IDX] - wrist)
    idx_extended = (idx_tip_dist > idx_pip_dist * 1.08) and (
        (idx_tip_dist - idx_mcp_dist) / palm_scale > 0.45
    )

    # 2. Middle, Ring, Pinky folded check
    mid_tip_dist = np.linalg.norm(landmarks[MIDDLE_TIP_IDX] - wrist)
    mid_pip_dist = np.linalg.norm(landmarks[10] - wrist)
    mid_mcp_to_tip = (
        np.linalg.norm(landmarks[MIDDLE_TIP_IDX] - landmarks[MIDDLE_MCP_IDX]) / palm_scale
    )
    mid_folded = (mid_tip_dist < mid_pip_dist * 1.22) or (mid_mcp_to_tip < 0.95)

    ring_tip_dist = np.linalg.norm(landmarks[RING_TIP_IDX] - wrist)
    ring_pip_dist = np.linalg.norm(landmarks[14] - wrist)
    ring_mcp_to_tip = (
        np.linalg.norm(landmarks[RING_TIP_IDX] - landmarks[13]) / palm_scale
    )
    ring_folded = (ring_tip_dist < ring_pip_dist * 1.22) or (ring_mcp_to_tip < 0.95)

    pinky_tip_dist = np.linalg.norm(landmarks[PINKY_TIP_IDX] - wrist)
    pinky_pip_dist = np.linalg.norm(landmarks[18] - wrist)
    pinky_mcp_to_tip = (
        np.linalg.norm(landmarks[PINKY_TIP_IDX] - landmarks[17]) / palm_scale
    )
    pinky_folded = (pinky_tip_dist < pinky_pip_dist * 1.22) or (pinky_mcp_to_tip < 0.95)

    folded_count = int(mid_folded) + int(ring_folded) + int(pinky_folded)
    is_gun_shape = idx_extended and (folded_count >= 1)

    if not is_gun_shape:
        return "NO_GUN", 0.90

    # 3. Gun shape is active: Determine GUN_READY vs SHOOT via thumb position
    thumb_tip = landmarks[THUMB_TIP_IDX]
    thumb_to_index_mcp = float(
        np.linalg.norm(thumb_tip - landmarks[INDEX_MCP_IDX]) / palm_scale
    )
    thumb_to_mid_mcp = float(
        np.linalg.norm(thumb_tip - landmarks[MIDDLE_MCP_IDX]) / palm_scale
    )

    if thumb_to_index_mcp < 0.58 or thumb_to_mid_mcp < 0.65:
        return "SHOOT", 0.88
    else:
        return "GUN_READY", 0.92


def get_thumb_trigger_metric(landmarks: np.ndarray) -> float:
    """
    Compute normalized thumb trigger distance metric.
    Checks distance to both index MCP and middle MCP.
    """
    wrist = landmarks[WRIST_IDX]
    mid_mcp = landmarks[MIDDLE_MCP_IDX]
    palm_scale = float(np.linalg.norm(mid_mcp - wrist))
    if palm_scale < 1e-4:
        palm_scale = 1.0
    thumb_tip = landmarks[THUMB_TIP_IDX]
    d_index = float(np.linalg.norm(thumb_tip - landmarks[INDEX_MCP_IDX]) / palm_scale)
    d_mid = float(np.linalg.norm(thumb_tip - landmarks[MIDDLE_MCP_IDX]) / palm_scale)
    return min(d_index, d_mid)


def is_pointing_down(landmarks: np.ndarray) -> bool:
    """
    Detect whether the hand is pointing downwards (Reload Gesture: Point Down).
    In camera/image coordinates, Y increases downwards.
    Index fingertip Y must be significantly greater than MCP and wrist Y.
    """
    if landmarks.shape != (NUM_LANDMARKS, 3):
        return False
    wrist = landmarks[WRIST_IDX]
    mid_mcp = landmarks[MIDDLE_MCP_IDX]
    palm_scale = float(np.linalg.norm(mid_mcp - wrist))
    if palm_scale < 1e-4:
        palm_scale = 1.0

    index_tip = landmarks[INDEX_TIP_IDX]
    index_pip = landmarks[6]
    index_mcp = landmarks[INDEX_MCP_IDX]

    # Fingertip must be lower (greater Y) than PIP, MCP, and wrist
    tip_lower_than_mcp = (index_tip[1] - index_mcp[1]) / palm_scale > 0.35
    tip_lower_than_pip = (index_tip[1] - index_pip[1]) > 0.02
    tip_lower_than_wrist = (index_tip[1] - wrist[1]) / palm_scale > 0.25

    dy = index_tip[1] - index_mcp[1]
    dx = abs(index_tip[0] - index_mcp[0])

    return bool(tip_lower_than_mcp and tip_lower_than_pip and tip_lower_than_wrist and (dy > dx * 0.8))


def check_two_hand_tap(landmarks1: np.ndarray, landmarks2: np.ndarray) -> bool:
    """
    Detect whether two hands are tapping / touching each other (Reload Gesture: Palm Tap).
    Checks distance between either hand's fingertips and the other hand's palm center/wrist.
    """
    if landmarks1.shape != (NUM_LANDMARKS, 3) or landmarks2.shape != (NUM_LANDMARKS, 3):
        return False

    palm1 = landmarks1[MIDDLE_MCP_IDX]
    palm2 = landmarks2[MIDDLE_MCP_IDX]
    wrist1 = landmarks1[WRIST_IDX]
    wrist2 = landmarks2[WRIST_IDX]

    scale1 = float(np.linalg.norm(palm1 - wrist1))
    scale2 = float(np.linalg.norm(palm2 - wrist2))
    if scale1 < 0.04 or scale2 < 0.04:
        return False
    avg_scale = (scale1 + scale2) / 2.0

    # Hand 1 tip to Hand 2 palm/wrist
    tip1 = landmarks1[INDEX_TIP_IDX]
    d1 = float(np.linalg.norm(tip1 - palm2))
    dw1 = float(np.linalg.norm(tip1 - wrist2))

    # Hand 2 tip to Hand 1 palm/wrist
    tip2 = landmarks2[INDEX_TIP_IDX]
    d2 = float(np.linalg.norm(tip2 - palm1))
    dw2 = float(np.linalg.norm(tip2 - wrist1))

    # Palm to palm distance
    d_palms = float(np.linalg.norm(palm1 - palm2))

    threshold = 0.90 * avg_scale
    return bool(d1 < threshold or dw1 < threshold or d2 < threshold or dw2 < threshold or d_palms < 1.0 * avg_scale)


class HandTracker:
    """
    MediaPipe-based hand tracker supporting simultaneous multi-hand interaction (dual-wielding).
    """

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.50,
        min_tracking_confidence: float = 0.50,
    ) -> None:
        """Initialize the hand tracking detector."""
        self.max_num_hands = max_num_hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process_frame_multi(
        self, frame_bgr: np.ndarray, flip_horizontal: bool = True
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Process a BGR video frame to detect up to 2 hands simultaneously.

        Returns:
            processed_frame: BGR frame with landmarks drawn for all detected hands.
            hands_data: List of dicts for each detected hand.
        """
        if flip_horizontal:
            frame = cv2.flip(frame_bgr, 1)
        else:
            frame = frame_bgr.copy()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        hands_data: List[Dict[str, Any]] = []
        h, w, _ = frame.shape

        if results.multi_hand_landmarks:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                coords = [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]
                raw_landmarks = np.array(coords, dtype=np.float32)

                index_tip = hand_landmarks.landmark[INDEX_TIP_IDX]
                thumb_tip = hand_landmarks.landmark[THUMB_TIP_IDX]
                wrist = hand_landmarks.landmark[WRIST_IDX]

                handedness_label = f"Hand {i + 1}"
                if results.multi_handedness and i < len(results.multi_handedness):
                    orig_label = results.multi_handedness[i].classification[0].label
                    if flip_horizontal:
                        handedness_label = "Left" if orig_label == "Right" else "Right"
                    else:
                        handedness_label = orig_label

                hands_data.append({
                    "landmarks": raw_landmarks,
                    "index_tip_norm": (float(index_tip.x), float(index_tip.y)),
                    "thumb_tip_norm": (float(thumb_tip.x), float(thumb_tip.y)),
                    "wrist_norm": (float(wrist.x), float(wrist.y)),
                    "handedness": handedness_label,
                    "hand_idx": i,
                })

                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )

                aim_color = (0, 255, 255) if i == 0 else (255, 0, 255)
                thumb_color = (0, 165, 255) if i == 0 else (255, 120, 0)

                aim_px = (int(index_tip.x * w), int(index_tip.y * h))
                thumb_px = (int(thumb_tip.x * w), int(thumb_tip.y * h))

                cv2.circle(frame, aim_px, 8, aim_color, -1)
                cv2.circle(frame, thumb_px, 6, thumb_color, -1)
                cv2.putText(
                    frame,
                    f"P{i + 1}",
                    (aim_px[0] + 10, aim_px[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    aim_color,
                    2,
                )

        return frame, hands_data

    def process_frame(
        self, frame_bgr: np.ndarray, flip_horizontal: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Tuple[float, float]]]:
        """Backward-compatible single-hand process_frame."""
        frame, hands_data = self.process_frame_multi(frame_bgr, flip_horizontal=flip_horizontal)
        if hands_data:
            primary = hands_data[0]
            return frame, primary["landmarks"], primary["index_tip_norm"]
        return frame, None, None

    def close(self) -> None:
        """Release MediaPipe resources."""
        if hasattr(self, "hands") and self.hands:
            self.hands.close()
