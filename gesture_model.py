"""
Gesture Classifier Model Module.

Loads and evaluates the trained Random Forest gesture recognition model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np

from hand_tracker import classify_gesture_heuristically, normalize_landmarks

# Canonical gesture labels
GESTURE_NO_GUN = "NO_GUN"
GESTURE_GUN_READY = "GUN_READY"
GESTURE_SHOOT = "SHOOT"

ALL_GESTURES = [GESTURE_NO_GUN, GESTURE_GUN_READY, GESTURE_SHOOT]
CONFIDENCE_THRESHOLD: float = 0.65

# Mapping between numeric codes and labels
LABEL_TO_INT: Dict[str, int] = {
    GESTURE_NO_GUN: 0,
    GESTURE_GUN_READY: 1,
    GESTURE_SHOOT: 2,
}
INT_TO_LABEL: Dict[int, str] = {v: k for k, v in LABEL_TO_INT.items()}


class GestureClassifier:
    """
    Wrapper around the trained Scikit-Learn Random Forest model.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        min_confidence: float = 0.65,
    ) -> None:
        """
        Initialize the gesture classifier.

        Args:
            model_path: Path to the serialized model file (.pkl).
            min_confidence: Minimum probability to accept a prediction.
        """
        self.min_confidence = min_confidence
        self.model = None
        self.model_path = Path(model_path) if model_path else None
        self.classes_: Optional[List[Union[str, int]]] = None

        if self.model_path and self.model_path.exists():
            self.load_model(self.model_path)

    def load_model(self, path: Union[str, Path]) -> None:
        """
        Load a trained model from disk.

        Args:
            path: Path to joblib file.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at: {path}")

        loaded = joblib.load(path)
        # Check if saved as a dict with metadata or raw estimator
        if isinstance(loaded, dict) and "model" in loaded:
            self.model = loaded["model"]
            self.classes_ = loaded.get("classes", list(self.model.classes_))
        else:
            self.model = loaded
            self.classes_ = list(self.model.classes_)

        self.model_path = path

    def is_loaded(self) -> bool:
        """Return True if model is loaded and ready."""
        return self.model is not None

    def predict(
        self, features_or_landmarks: np.ndarray
    ) -> Tuple[str, float]:
        """
        Predict hand gesture from normalized features or raw landmarks.

        Args:
            features_or_landmarks:
                Either 1D array of 63 normalized features,
                or (21, 3) raw landmarks array.

        Returns:
            predicted_gesture: One of 'NO_GUN', 'GUN_READY', 'SHOOT'.
            confidence: Probability between 0.0 and 1.0.
        """
        if self.model is None:
            raise RuntimeError("Model is not loaded. Train a model or load a valid .pkl file.")

        raw_lm = features_or_landmarks if features_or_landmarks.shape == (21, 3) else None
        if raw_lm is not None:
            features = normalize_landmarks(raw_lm)
            heur_label, heur_conf = classify_gesture_heuristically(raw_lm)
        else:
            features = features_or_landmarks
            heur_label, heur_conf = None, 0.0

        if features.ndim == 1:
            features = features.reshape(1, -1)

        probabilities = self.model.predict_proba(features)[0]
        max_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[max_idx])
        raw_pred = self.model.classes_[max_idx]

        # Convert numeric prediction to label if needed
        if isinstance(raw_pred, (int, np.integer)):
            predicted_label = INT_TO_LABEL.get(int(raw_pred), GESTURE_NO_GUN)
        else:
            predicted_label = str(raw_pred)

        # Hybrid fusion: If raw landmarks are present and model is uncertain
        # or model returned NO_GUN while physical finger configuration is clearly a gun
        if raw_lm is not None and heur_label is not None:
            if heur_label in (GESTURE_GUN_READY, GESTURE_SHOOT):
                if predicted_label == GESTURE_NO_GUN or confidence < self.min_confidence:
                    # Physical finger geometry takes precedence when clear gun shape is formed
                    return heur_label, max(confidence, heur_conf)
                elif predicted_label in (GESTURE_GUN_READY, GESTURE_SHOOT):
                    # Both agree on gun shape! Fine-tune trigger state with heuristic
                    final_label = heur_label if heur_label == GESTURE_SHOOT else predicted_label
                    return final_label, max(confidence, 0.85)

        # Apply confidence threshold
        if confidence < self.min_confidence:
            return GESTURE_NO_GUN, confidence

        return predicted_label, confidence
