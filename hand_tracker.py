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
    is_gun_shape = idx_extended and (folded_count >= 2)

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

    if thumb_to_index_mcp < 0.52 or thumb_to_mid_mcp < 0.62:
        return "SHOOT", 0.88
    else:
        return "GUN_READY", 0.92


def get_thumb_trigger_metric(landmarks: np.ndarray) -> float:
    """
    Compute normalized thumb-to-index distance metric.
    High value (~0.7 to 1.2) = Thumb cocked up (GUN_READY).
    Low value (<0.52) = Thumb pulled down (SHOOT).
    """
    wrist = landmarks[WRIST_IDX]
    mid_mcp = landmarks[MIDDLE_MCP_IDX]
    palm_scale = float(np.linalg.norm(mid_mcp - wrist))
    if palm_scale < 1e-4:
        palm_scale = 1.0
    thumb_tip = landmarks[THUMB_TIP_IDX]
    return float(np.linalg.norm(thumb_tip - landmarks[INDEX_MCP_IDX]) / palm_scale)


class HandTracker:
    """
    MediaPipe-based hand tracker optimized for single-hand interaction.
    """

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
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

    def process_frame(
        self, frame_bgr: np.ndarray, flip_horizontal: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Tuple[float, float]]]:
        """
        Process a BGR video frame to detect hands.

        Args:
            frame_bgr: OpenCV BGR image frame.
            flip_horizontal: Whether to flip frame horizontally for selfie/mirror mode.

        Returns:
            processed_frame: BGR frame with landmarks drawn.
            raw_landmarks: Numpy array of shape (21, 3) or None if no hand detected.
            index_tip_norm: (x, y) normalized coordinates of index tip (0.0 to 1.0), or None.
        """
        if flip_horizontal:
            frame = cv2.flip(frame_bgr, 1)
        else:
            frame = frame_bgr.copy()

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        raw_landmarks: Optional[np.ndarray] = None
        index_tip_norm: Optional[Tuple[float, float]] = None

        if results.multi_hand_landmarks:
            # Select the primary hand (first detected hand)
            primary_hand = results.multi_hand_landmarks[0]

            # Extract coordinates into numpy array
            coords = []
            for lm in primary_hand.landmark:
                coords.append([lm.x, lm.y, lm.z])
            raw_landmarks = np.array(coords, dtype=np.float32)

            # Extract normalized index fingertip (landmark 8)
            index_tip = primary_hand.landmark[INDEX_TIP_IDX]
            index_tip_norm = (float(index_tip.x), float(index_tip.y))

            # Draw landmarks on frame
            self.mp_drawing.draw_landmarks(
                frame,
                primary_hand,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style(),
            )

            # Highlight index fingertip (aiming reticle origin) and thumb tip
            h, w, _ = frame.shape
            aim_px = (int(index_tip.x * w), int(index_tip.y * h))
            thumb_px = (int(primary_hand.landmark[THUMB_TIP_IDX].x * w),
                        int(primary_hand.landmark[THUMB_TIP_IDX].y * h))

            cv2.circle(frame, aim_px, 8, (0, 255, 255), -1)  # Yellow circle for aim tip
            cv2.circle(frame, thumb_px, 6, (0, 165, 255), -1)  # Orange circle for thumb tip

        return frame, raw_landmarks, index_tip_norm

    def close(self) -> None:
        """Release MediaPipe resources."""
        if hasattr(self, "hands") and self.hands:
            self.hands.close()
