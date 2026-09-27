# 🎯 Hand Gun Gesture Shooter

> 🚀 **Live Browser Game**: [hand-shoot-game-six.vercel.app](https://hand-shoot-game-six.vercel.app/)  
> 💻 **GitHub Repository**: [github.com/Siddhartha39/hand-shoot-game](https://github.com/Siddhartha39/hand-shoot-game)

An interactive, real-time computer-vision shooting game where your hand becomes the controller. Point your index finger like a gun to aim your virtual crosshair, and pull down your thumb like a trigger to fire shots at moving targets!

Available both as a **Zero-Install Web Application** (deployed live on Vercel) and as a **Desktop Python Application** (OpenCV + MediaPipe + Pygame).

![Game Preview](screenshots/gameplay_preview.png)

---

## 🌟 Features & Highlights

- **Live Browser Game on Vercel**: Powered by HTML5 Canvas, MediaPipe Hands Web SDK, and Web Audio API synthesizer. Play instantly in Chrome, Edge, or Safari with zero installation.
- **Desktop Python Application**: Standalone Pygame 2D arcade shooter with OpenCV webcam processing and Scikit-learn ML inference.
- **Hybrid Gesture Recognition Engine**:
  - **Machine Learning**: 300-tree Random Forest classifier trained on 6,000 rotation-augmented samples across both left and right hands (99.8% test accuracy).
  - **Biomechanical Rule Validation**: Real-time geometric joint verification (index extension, finger curl, and relative thumb trigger metric) ensuring zero false negatives regardless of camera angle or distance.
- **Dual-Path Instant Trigger**:
  - Fires via ML gesture classification OR instantaneous physical thumb pull-down metric ($\text{metric} < 0.52$).
  - Built-in 250ms debouncing cooldown prevents unintended machine-gun spamming.
- **Jitter-Free Aiming**:
  - Exponential Moving Average (EMA, $\alpha = 0.35$) eliminates webcam landmark noise for pinpoint crosshair stability.
  - Active margin calibration allows comfortable reach into all four corners of the screen.
- **2D Arcade Shooting Gallery**:
  - 3 dynamic target tiers: Normal (100 pts), Fast (250 pts), and Bonus Bullseyes (500 pts) with sinusoidal wobble physics.
  - Combo multiplier system, floating damage text, particle explosion bursts, and health/lives system.
- **Dual Control Modes**:
  - `HAND MODE`: Webcam hand gesture aiming and thumb trigger shooting.
  - `MOUSE MODE`: Standard mouse aiming and left-click shooting (press `M` to toggle anytime).

---

## 🏗️ Architecture & Pipeline

```text
       Webcam Stream (640x480)
                 ↓
      cv2.flip / Mirror Transform
                 ↓
     MediaPipe Hand Landmark Detection
                 ↓
        21 3D Joint Coordinates
                 ↓
┌──────────────────────────────────────────────┐
│  Normalization (Translation & Scale Invariance)│
│  1. Center wrist (landmark 0) at origin      │
│  2. Scale by middle MCP (landmark 9) dist    │
│  3. Flatten to 63 numerical features         │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│         Hybrid Gesture Classification        │
│  - Random Forest Classifier (6,000 samples)  │
│  - Biomechanical Finger State Validation     │
│  - Left-hand & Right-hand support            │
└──────────────────────┬───────────────────────┘
                       ↓
        [ NO_GUN / GUN_READY / SHOOT ]
                       ↓
┌──────────────────────────────────────────────┐
│             Gun Controller Layer             │
│  - Index Fingertip (Landmark 8) → Aim coords │
│  - Exponential Moving Average (EMA) smoothing│
│  - Trigger debouncing (250ms cooldown)       │
│  - Instant thumb pull-down detection         │
└──────────────────────┬───────────────────────┘
                       ↓
           Pygame / Web Canvas Engine
        (Target physics, combos, HUD)
```

---

## 📁 Project Structure

```text
hand_gun_game/
│
├── README.md               # Complete documentation and setup guide
├── requirements.txt         # Python project dependencies
├── .gitignore              # Git ignore rules (caches, venv)
├── vercel.json             # Vercel static deployment configuration
│
├── index.html              # Web Edition entrypoint (Vercel-ready)
├── web_game.js             # Browser game engine & MediaPipe Web tracker
│
├── hand_tracker.py         # MediaPipe wrapper, normalization & heuristic validation
├── gesture_model.py        # Hybrid ML classifier wrapper with confidence fusion
├── controller.py           # Aim smoothing & dual-path trigger debouncing
├── game.py                 # Self-contained Pygame shooting gallery
├── collect_data.py         # Live webcam dataset collection tool
├── train_model.py          # Random Forest training & evaluation script
├── test_gesture.py         # Real-time gesture testing HUD with trigger feedback
├── main.py                 # Main integrated Python desktop application
├── generate_starter_data.py# 6,000-sample left/right hand dataset generator
│
├── models/
│   └── gun_gesture_model.pkl # Trained Random Forest model (99.8% test accuracy)
│
├── data/
│   └── dataset.csv         # 6,000 normalized landmark samples
│
└── screenshots/
    └── gameplay_preview.png# Game preview screenshot
```

---

## 🌐 Web Edition (Live on Vercel)

The web edition requires **no installation** and runs directly in any modern browser:

- **Live URL**: [hand-shoot-game-six.vercel.app](https://hand-shoot-game-six.vercel.app/)
- **Run Locally**:
  ```bash
  python3 -m http.server 8000
  ```
  Open `http://localhost:8000` in Chrome, Edge, or Safari.

---

## 💻 Python Desktop Installation & Setup

### Requirements
- **Python**: 3.11 or 3.12 (Recommended: Python 3.12)
- **Webcam**: Built-in or external USB camera

### 1. Set Up Virtual Environment

#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows:
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🎮 How to Run (Desktop Python)

A pre-trained model ([`models/gun_gesture_model.pkl`](models/gun_gesture_model.pkl)) and a 6,000-sample dataset ([`data/dataset.csv`](data/dataset.csv)) are already bundled. You can jump directly to **Step 4** to play immediately:

### Step 1: Collect Custom Hand Data (Optional)
Record your own hand gestures via webcam:
```bash
python collect_data.py
```
- `0`: Select `NO_GUN` (open hand, fist, neutral)
- `1`: Select `GUN_READY` (index extended, thumb pointing up)
- `2`: Select `SHOOT` (gun shape with thumb pulled down)
- `SPACE`: Toggle continuous frame recording
- `Q`: Save to `data/dataset.csv` and quit

### Step 2: Train the ML Model
Train the Random Forest classifier:
```bash
python train_model.py
```
- Stratified train/test evaluation (99.8% accuracy).
- Saves model to `models/gun_gesture_model.pkl`.

### Step 3: Test Gesture Recognition Live
Verify live detection and trigger responsiveness before launching the game:
```bash
python test_gesture.py
```
- Real-time HUD displaying detected gesture, confidence bar, and FPS.
- Visual trigger feedback: **`TRIGGER: READY`** (green) vs **`TRIGGER: BANG! FIRED!`** (red flash).
- Press `Q` to exit.

### Step 4: Launch the Game!
Start the integrated gesture shooting game:
```bash
python main.py
```

To play with a mouse (no webcam needed):
```bash
python main.py --mouse
```

---

## 🕹️ In-Game Controls

| Key / Action | Function |
|---|---|
| **Point Index Finger** | Move virtual crosshair (in `HAND MODE`) |
| **Pull Down Thumb** | Fire shot (Trigger in `HAND MODE`) |
| **Mouse Move + Left Click** | Aim & shoot (in `MOUSE MODE`) |
| **`M`** | Toggle between `HAND MODE` and `MOUSE MODE` |
| **`D`** | Toggle Debug Overlay (FPS, entity counts, reticle coords) |
| **`R`** | Restart round / play again |
| **`Q` / `ESC`** | Quit application |

---

## 📐 Machine Learning & Computer Vision Details

### 1. 21 3D Hand Landmarks
MediaPipe extracts 21 keypoints per hand in normalized camera space ($x, y, z$):
- **Landmark 0**: Wrist (origin)
- **Landmarks 1–4**: Thumb (Landmark 4 = Tip)
- **Landmarks 5–8**: Index Finger (Landmark 8 = Tip, used for aiming)
- **Landmarks 9–12**: Middle Finger
- **Landmarks 13–16**: Ring Finger
- **Landmarks 17–20**: Pinky Finger

### 2. Normalization Math
For translation and scale invariance:
1. **Translation**: Center coordinates at the wrist:
   $$\vec{P}'_i = \vec{P}_i - \vec{P}_0$$
2. **Scale**: Divide by the anatomical palm base reference length $d = \|\vec{P}'_9 - \vec{P}'_0\|$:
   $$\vec{P}''_{i} = \frac{\vec{P}'_i}{d}$$
3. **Features**: Flattened into a 63-dimensional vector ($x_0, y_0, z_0, \dots, x_{20}, y_{20}, z_{20}$).

### 3. Hybrid Classification & Trigger Logic
1. **Random Forest Classifier**: 300 estimators trained on 6,000 augmented samples for left- and right-handed play across diverse 3D angles.
2. **Biomechanical Geometry Checks**:
   - **Index Extended**: $\text{dist}(\text{wrist}, \text{index\_tip}) > 1.08 \times \text{dist}(\text{wrist}, \text{index\_pip})$.
   - **Fingers Folded**: Middle, ring, and pinky tips curled toward the palm.
   - **Thumb Trigger Metric**:
     $$\text{Metric} = \frac{\|\text{thumb\_tip} - \text{index\_mcp}\|}{\|\text{middle\_mcp} - \text{wrist}\|}$$
     - $\ge 0.52$: Cocked Hammer $\rightarrow$ `GUN_READY`
     - $< 0.52$: Trigger Pulled $\rightarrow$ `SHOOT` (250ms debounced cooldown)

### 4. Exponential Moving Average (EMA) Aiming
$$\text{Aim}_t = \alpha \cdot \text{Target}_t + (1 - \alpha) \cdot \text{Aim}_{t-1}$$
where $\alpha = 0.35$. Active margin clamping ensures reach into extreme screen corners without stretching your arm out of camera view.

---

## 🔧 Troubleshooting

- **Webcam not detected / black screen:**
  - Verify browser/OS camera permissions.
  - If using multiple webcams in Python: `python main.py --camera 1`.
  - Press `M` to instantly switch to Mouse Mode.
- **Crosshair sensitivity:**
  - Adjust smoothing via CLI: `python main.py --smoothing 0.5` (higher = faster, lower = smoother).
- **Trigger sensitivity:**
  - Adjust confidence threshold: `python main.py --threshold 0.60`.

---

## 🔮 Roadmap & Planned Features

- [ ] **Global Online Leaderboard**: Persist high scores across web players using Vercel KV / Redis.
- [ ] **Sound Pack Selector**: In-game audio toggle for Laser, Revolver, and Silencer sound profiles.
- [ ] **Dual-Wielding Mode**: Track two hands simultaneously for twin crosshairs.
- [ ] **Reload Mechanics**: Optional tactical reload gesture (tilt hand down or tap palm).
