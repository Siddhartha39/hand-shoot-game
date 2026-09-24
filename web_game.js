/**
 * Web Game & MediaPipe Gesture Engine for Hand Gun Shooter.
 * Enables zero-setup web browser execution & Vercel deployment.
 */

// Web Audio API Synthesizer
class SoundSynth {
  constructor() {
    this.ctx = null;
    this.initAudio();
  }

  initAudio() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  playLaser() {
    if (!this.ctx) return;
    if (this.ctx.state === "suspended") this.ctx.resume();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const now = this.ctx.currentTime;

    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(150, now + 0.12);

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.12);
  }

  playPop() {
    if (!this.ctx) return;
    if (this.ctx.state === "suspended") this.ctx.resume();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const now = this.ctx.currentTime;

    osc.type = "triangle";
    osc.frequency.setValueAtTime(320, now);
    osc.frequency.exponentialRampToValueAtTime(70, now + 0.18);

    gain.gain.setValueAtTime(0.4, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.18);
  }

  playHurt() {
    if (!this.ctx) return;
    if (this.ctx.state === "suspended") this.ctx.resume();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const now = this.ctx.currentTime;

    osc.type = "square";
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.linearRampToValueAtTime(80, now + 0.25);

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.25);
  }
}

// Target Class
class Target {
  constructor(screenW, screenH, level) {
    this.screenW = screenW;
    this.screenH = screenH;

    const r = Math.random();
    if (r < 0.65) {
      this.type = "NORMAL";
      this.radius = 28 + Math.random() * 8;
      this.points = 100;
      this.color = "#f04646";
      this.speedMult = 1.0;
    } else if (r < 0.88) {
      this.type = "FAST";
      this.radius = 20 + Math.random() * 6;
      this.points = 250;
      this.color = "#ffb428";
      this.speedMult = 1.6;
    } else {
      this.type = "BONUS";
      this.radius = 16 + Math.random() * 6;
      this.points = 500;
      this.color = "#b450ff";
      this.speedMult = 2.0;
    }

    const side = ["LEFT", "RIGHT", "BOTTOM"][Math.floor(Math.random() * 3)];
    const baseSpeed = (1.5 + 0.2 * level) * this.speedMult;

    if (side === "LEFT") {
      this.x = -this.radius;
      this.y = 120 + Math.random() * (screenH - 240);
      this.vx = baseSpeed * (1.0 + Math.random() * 0.8);
      this.vy = (Math.random() - 0.5) * 2;
    } else if (side === "RIGHT") {
      this.x = screenW + this.radius;
      this.y = 120 + Math.random() * (screenH - 240);
      this.vx = -baseSpeed * (1.0 + Math.random() * 0.8);
      this.vy = (Math.random() - 0.5) * 2;
    } else {
      this.x = 100 + Math.random() * (screenW - 200);
      this.y = screenH + this.radius;
      this.vx = (Math.random() - 0.5) * 2.4;
      this.vy = -baseSpeed * (1.2 + Math.random() * 0.8);
    }

    this.wobbleFreq = 2.0 + Math.random() * 2.0;
    this.wobbleAmp = 1.5 + Math.random() * 1.5;
    this.createdAt = performance.now();
  }

  update(dt) {
    this.x += this.vx * (dt * 60);
    this.y += this.vy * (dt * 60);
    const t = (performance.now() - this.createdAt) / 1000.0;
    this.y += Math.sin(t * this.wobbleFreq) * (this.wobbleAmp * dt * 60);

    const margin = this.radius * 2 + 50;
    return (
      this.x >= -margin &&
      this.x <= this.screenW + margin &&
      this.y >= -margin &&
      this.y <= this.screenH + margin
    );
  }

  isHit(px, py) {
    return Math.hypot(this.x - px, this.y - py) <= this.radius;
  }

  draw(ctx) {
    const cx = Math.floor(this.x);
    const cy = Math.floor(this.y);

    // Outer circle
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    // Middle white ring
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 0.65, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    // Center bullseye
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 0.35, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
  }
}

// Particle & Floating Text
class Particle {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.color = color;
    const angle = Math.random() * Math.PI * 2;
    const speed = 2 + Math.random() * 6;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
    this.lifetime = 0.35 + Math.random() * 0.25;
    this.age = 0;
    this.radius = 2 + Math.random() * 3;
  }
  update(dt) {
    this.age += dt;
    this.x += this.vx * (dt * 60);
    this.y += this.vy * (dt * 60);
    this.vy += 0.15 * (dt * 60);
    return this.age < this.lifetime;
  }
  draw(ctx) {
    const alpha = Math.max(0, 1 - this.age / this.lifetime);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.restore();
  }
}

class FloatingText {
  constructor(x, y, text, color) {
    this.x = x;
    this.y = y;
    this.text = text;
    this.color = color;
    this.lifetime = 0.8;
    this.age = 0;
  }
  update(dt) {
    this.age += dt;
    this.y -= 40 * dt;
    return this.age < this.lifetime;
  }
  draw(ctx) {
    const alpha = Math.max(0, 1 - this.age / this.lifetime);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = this.color;
    ctx.font = "bold 20px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(this.text, this.x, this.y);
    ctx.restore();
  }
}

// Main Game Controller
class WebShooterGame {
  constructor() {
    this.canvas = document.getElementById("game-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.pipCanvas = document.getElementById("pip-canvas");
    this.pipCtx = this.pipCanvas.getContext("2d");
    this.video = document.getElementById("webcam-video");

    this.width = 1000;
    this.height = 700;
    this.sound = new SoundSynth();

    // Mode
    this.controlMode = "HAND"; // "HAND" or "MOUSE"
    this.state = "PLAYING";

    // Scoring & Stats
    this.score = 0;
    this.lives = 5;
    this.maxLives = 5;
    this.shotsFired = 0;
    this.shotsHit = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.level = 1;
    this.startTime = performance.now();
    this.lastSpawnTime = 0;
    this.spawnInterval = 1.3;

    // Entities
    this.targets = [];
    this.particles = [];
    this.floatingTexts = [];

    // Aim & Trigger
    this.aimX = this.width / 2;
    this.aimY = this.height / 2;
    this.isGunReady = false;
    this.flashTimer = 0;
    this.lastShotTime = 0;
    this.triggerCooldown = 250; // ms
    this.thumbMetric = 1.0;
    this.gestureName = "NO_GUN";

    this.setupListeners();
    this.lastFrameTime = performance.now();
    requestAnimationFrame((t) => this.gameLoop(t));
  }

  setupListeners() {
    window.addEventListener("keydown", (e) => {
      if (e.key === "m" || e.key === "M") {
        this.controlMode = this.controlMode === "HAND" ? "MOUSE" : "HAND";
        document.getElementById("hud-mode-badge").textContent = `${this.controlMode} MODE`;
      } else if (e.key === "r" || e.key === "R") {
        this.resetGame();
      }
    });

    this.canvas.addEventListener("mousemove", (e) => {
      if (this.controlMode === "MOUSE") {
        const rect = this.canvas.getBoundingClientRect();
        this.aimX = (e.clientX - rect.left) * (this.width / rect.width);
        this.aimY = (e.clientY - rect.top) * (this.height / rect.height);
        this.isGunReady = true;
      }
    });

    this.canvas.addEventListener("mousedown", (e) => {
      if (this.controlMode === "MOUSE" && e.button === 0) {
        if (this.state === "PLAYING") this.shootAt(this.aimX, this.aimY);
        else if (this.state === "GAME_OVER") this.resetGame();
      }
    });

    document.getElementById("start-webcam-btn").onclick = () => {
      document.getElementById("start-modal").style.display = "none";
      this.sound.initAudio();
      this.initMediaPipe();
    };

    document.getElementById("start-mouse-btn").onclick = () => {
      document.getElementById("start-modal").style.display = "none";
      this.sound.initAudio();
      this.controlMode = "MOUSE";
      document.getElementById("hud-mode-badge").textContent = "MOUSE MODE";
      document.getElementById("pip-canvas").style.display = "none";
      document.getElementById("pip-label").style.display = "none";
    };
  }

  resetGame() {
    this.score = 0;
    this.lives = this.maxLives;
    this.shotsFired = 0;
    this.shotsHit = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.level = 1;
    this.startTime = performance.now();
    this.targets = [];
    this.particles = [];
    this.floatingTexts = [];
    this.state = "PLAYING";
  }

  shootAt(x, y) {
    this.shotsFired++;
    this.flashTimer = 0.12;
    this.sound.playLaser();

    let hitTarget = null;
    for (let i = this.targets.length - 1; i >= 0; i--) {
      if (this.targets[i].isHit(x, y)) {
        hitTarget = this.targets[i];
        this.targets.splice(i, 1);
        break;
      }
    }

    if (hitTarget) {
      this.shotsHit++;
      this.combo++;
      if (this.combo > this.maxCombo) this.maxCombo = this.combo;

      const mult = 1.0 + (this.combo - 1) * 0.25;
      const pts = Math.floor(hitTarget.points * mult);
      this.score += pts;

      this.sound.playPop();
      for (let i = 0; i < 18; i++) {
        this.particles.push(new Particle(hitTarget.x, hitTarget.y, hitTarget.color));
      }

      let label = `+${pts}`;
      if (this.combo > 1) label += ` (${this.combo}x Combo!)`;
      this.floatingTexts.push(new FloatingText(hitTarget.x, hitTarget.y, label, "#00ffd5"));
    } else {
      if (this.combo > 2) {
        this.floatingTexts.push(new FloatingText(x, y, "Combo Broken", "#ff4646"));
      }
      this.combo = 0;
    }
  }

  initMediaPipe() {
    if (typeof Hands === "undefined") {
      alert("MediaPipe Hands library loading. Please check internet connection.");
      return;
    }

    const hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
    });

    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 1,
      minDetectionConfidence: 0.65,
      minTrackingConfidence: 0.5,
    });

    hands.onResults((results) => this.onHandResults(results));

    const camera = new Camera(this.video, {
      onFrame: async () => {
        await hands.send({ image: this.video });
      },
      width: 640,
      height: 480,
    });

    camera.start().catch((err) => {
      console.warn("Camera failed:", err);
      alert("Webcam permission denied or camera not found. Switching to Mouse Mode.");
      this.controlMode = "MOUSE";
      document.getElementById("hud-mode-badge").textContent = "MOUSE MODE";
    });
  }

  onHandResults(results) {
    // Draw on mini PiP canvas
    const pw = this.pipCanvas.width;
    const ph = this.pipCanvas.height;
    this.pipCtx.save();
    this.pipCtx.clearRect(0, 0, pw, ph);
    // Mirror camera frame
    this.pipCtx.translate(pw, 0);
    this.pipCtx.scale(-1, 1);
    this.pipCtx.drawImage(results.image, 0, 0, pw, ph);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const lm = results.multiHandLandmarks[0];

      // Draw landmarks on PiP
      this.pipCtx.fillStyle = "#00ffd5";
      for (const p of lm) {
        this.pipCtx.beginPath();
        this.pipCtx.arc(p.x * pw, p.y * ph, 2.5, 0, Math.PI * 2);
        this.pipCtx.fill();
      }

      this.processGestureAndAim(lm);
    } else {
      this.isGunReady = false;
      this.gestureName = "NO_GUN";
    }
    this.pipCtx.restore();
  }

  processGestureAndAim(lm) {
    if (this.controlMode !== "HAND") return;

    const wrist = lm[0];
    const thumbTip = lm[4];
    const indexMcp = lm[5];
    const indexPip = lm[6];
    const indexTip = lm[8];
    const midMcp = lm[9];
    const midTip = lm[12];
    const ringTip = lm[16];
    const pinkyTip = lm[20];

    const dist = (p1, p2) => Math.hypot(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z);
    const palmScale = Math.max(0.001, dist(midMcp, wrist));

    // 1. Index extended check
    const idxTipDist = dist(indexTip, wrist);
    const idxPipDist = dist(indexPip, wrist);
    const idxExtended = idxTipDist > idxPipDist * 1.08 && (idxTipDist - dist(indexMcp, wrist)) / palmScale > 0.45;

    // 2. Middle, Ring, Pinky folded check
    const midFolded = dist(midTip, wrist) < dist(lm[10], wrist) * 1.25 || dist(midTip, midMcp) / palmScale < 0.95;
    const ringFolded = dist(ringTip, wrist) < dist(lm[14], wrist) * 1.25 || dist(ringTip, lm[13]) / palmScale < 0.95;
    const pinkyFolded = dist(pinkyTip, wrist) < dist(lm[18], wrist) * 1.25 || dist(pinkyTip, lm[17]) / palmScale < 0.95;

    const foldedCount = (midFolded ? 1 : 0) + (ringFolded ? 1 : 0) + (pinkyFolded ? 1 : 0);
    const isGun = idxExtended && foldedCount >= 2;

    this.isGunReady = isGun;

    // Aim position (Flipped horizontally for selfie mode)
    // Landmark x is 0..1 from left to right on raw camera, so mirrored x is (1.0 - indexTip.x)
    const normX = 1.0 - indexTip.x;
    const normY = indexTip.y;

    // Active margins for comfortable edge reach
    const margin = 0.10;
    const clampedX = Math.min(1.0, Math.max(0.0, (normX - margin) / (1.0 - 2 * margin)));
    const clampedY = Math.min(1.0, Math.max(0.0, (normY - margin) / (1.0 - 2 * margin)));

    const targetX = clampedX * this.width;
    const targetY = clampedY * this.height;

    // EMA Smoothing (alpha = 0.35)
    this.aimX = 0.35 * targetX + 0.65 * this.aimX;
    this.aimY = 0.35 * targetY + 0.65 * this.aimY;

    // Trigger Detection
    this.thumbMetric = dist(thumbTip, indexMcp) / palmScale;
    const now = performance.now();

    if (isGun) {
      if (this.thumbMetric < 0.52) {
        this.gestureName = "SHOOT";
        if (now - this.lastShotTime >= this.triggerCooldown) {
          if (this.state === "PLAYING") this.shootAt(this.aimX, this.aimY);
          else if (this.state === "GAME_OVER") this.resetGame();
          this.lastShotTime = now;
        }
      } else {
        this.gestureName = "GUN_READY";
      }
    } else {
      this.gestureName = "NO_GUN";
    }
  }

  gameLoop(timestamp) {
    const dt = Math.min(0.1, (timestamp - this.lastFrameTime) / 1000.0);
    this.lastFrameTime = timestamp;

    this.update(dt);
    this.render();

    requestAnimationFrame((t) => this.gameLoop(t));
  }

  update(dt) {
    if (this.flashTimer > 0) {
      this.flashTimer = Math.max(0, this.flashTimer - dt);
    }

    if (this.state !== "PLAYING") return;

    // Spawning
    const now = performance.now();
    const elapsed = (now - this.startTime) / 1000.0;
    this.level = 1 + Math.floor(this.score / 1000) + Math.floor(elapsed / 30);
    this.spawnInterval = Math.max(0.45, 1.4 - this.level * 0.08);

    const maxTargets = Math.min(7, 3 + Math.floor(this.level / 2));
    if (this.targets.length < maxTargets && now - this.lastSpawnTime >= this.spawnInterval * 1000) {
      this.targets.push(new Target(this.width, this.height, this.level));
      this.lastSpawnTime = now;
    }

    // Update Targets
    for (let i = this.targets.length - 1; i >= 0; i--) {
      const alive = this.targets[i].update(dt);
      if (!alive) {
        this.targets.splice(i, 1);
        this.lives--;
        this.combo = 0;
        this.sound.playHurt();
        this.floatingTexts.push(
          new FloatingText(this.width / 2, this.height / 2, "TARGET ESCAPED! -1 LIFE", "#f04646")
        );
        if (this.lives <= 0) {
          this.state = "GAME_OVER";
        }
      }
    }

    // Particles & Floating Text
    this.particles = this.particles.filter((p) => p.update(dt));
    this.floatingTexts = this.floatingTexts.filter((ft) => ft.update(dt));
  }

  render() {
    this.ctx.fillStyle = "#10141c";
    this.ctx.fillRect(0, 0, this.width, this.height);

    // Subtle Grid
    this.ctx.strokeStyle = "#1c2432";
    this.ctx.lineWidth = 1;
    for (let gx = 0; gx < this.width; gx += 60) {
      this.ctx.beginPath();
      this.ctx.moveTo(gx, 0);
      this.ctx.lineTo(gx, this.height);
      this.ctx.stroke();
    }
    for (let gy = 0; gy < this.height; gy += 60) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, gy);
      this.ctx.lineTo(this.width, gy);
      this.ctx.stroke();
    }

    // Draw Targets
    for (const t of this.targets) t.draw(this.ctx);

    // Draw Particles
    for (const p of this.particles) p.draw(this.ctx);

    // Draw Floating Text
    for (const ft of this.floatingTexts) ft.draw(this.ctx);

    // Draw Crosshair
    this.drawCrosshair();

    // Draw HUD
    this.drawHUD();

    // Game Over Overlay
    if (this.state === "GAME_OVER") {
      this.drawGameOver();
    }
  }

  drawCrosshair() {
    const cx = Math.floor(this.aimX);
    const cy = Math.floor(this.aimY);

    let color = "#9696a0";
    if (this.flashTimer > 0) color = "#ff3c3c";
    else if (this.isGunReady) color = "#32ff78";

    // Muzzle Flash
    if (this.flashTimer > 0) {
      this.ctx.beginPath();
      this.ctx.arc(cx, cy, 45, 0, Math.PI * 2);
      this.ctx.fillStyle = "rgba(255, 100, 50, 0.4)";
      this.ctx.fill();
    }

    // Reticle Ring
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, 24, 0, Math.PI * 2);
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    // Center Dot
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    this.ctx.fillStyle = color;
    this.ctx.fill();

    // Crosshair ticks
    this.ctx.beginPath();
    this.ctx.moveTo(cx, cy - 34);
    this.ctx.lineTo(cx, cy - 8);
    this.ctx.moveTo(cx, cy + 8);
    this.ctx.lineTo(cx, cy + 34);
    this.ctx.moveTo(cx - 34, cy);
    this.ctx.lineTo(cx - 8, cy);
    this.ctx.moveTo(cx + 8, cy);
    this.ctx.lineTo(cx + 34, cy);
    this.ctx.stroke();
  }

  drawHUD() {
    // Top Bar
    this.ctx.fillStyle = "rgba(10, 14, 20, 0.85)";
    this.ctx.fillRect(0, 0, this.width, 55);
    this.ctx.strokeStyle = "#1c2432";
    this.ctx.beginPath();
    this.ctx.moveTo(0, 55);
    this.ctx.lineTo(this.width, 55);
    this.ctx.stroke();

    this.ctx.font = "bold 20px -apple-system, sans-serif";
    this.ctx.fillStyle = "#f0f4fa";
    this.ctx.textAlign = "left";
    this.ctx.fillText(`SCORE: ${this.score.toLocaleString()}`, 20, 35);

    if (this.combo > 1) {
      this.ctx.fillStyle = "#00ffd5";
      this.ctx.fillText(`COMBO ${this.combo}x`, 220, 35);
    }

    this.ctx.font = "14px -apple-system, sans-serif";
    this.ctx.fillStyle = "#8b949e";
    this.ctx.fillText(`LEVEL ${this.level}`, 380, 35);

    const acc = Math.floor((this.shotsHit / Math.max(1, this.shotsFired)) * 100);
    this.ctx.fillText(`ACCURACY: ${acc}%`, 480, 35);

    // Lives
    this.ctx.fillStyle = "#f0f4fa";
    this.ctx.fillText("LIVES:", this.width - 200, 35);
    for (let i = 0; i < this.maxLives; i++) {
      this.ctx.beginPath();
      this.ctx.arc(this.width - 135 + i * 22, 30, 7, 0, Math.PI * 2);
      this.ctx.fillStyle = i < this.lives ? "#32dc64" : "#3c3c46";
      this.ctx.fill();
    }

    // Bottom Status Bar
    this.ctx.fillStyle = "rgba(10, 14, 20, 0.85)";
    this.ctx.fillRect(0, this.height - 35, this.width, 35);

    this.ctx.font = "13px -apple-system, sans-serif";
    this.ctx.fillStyle = this.controlMode === "HAND" ? "#00ffd5" : "#ffc83c";
    this.ctx.fillText(
      `MODE: ${this.controlMode} (Press [M] to toggle) | [R] Restart`,
      20,
      this.height - 13
    );

    if (this.controlMode === "HAND") {
      this.ctx.fillStyle = this.isGunReady ? "#32ff78" : "#9696a0";
      this.ctx.textAlign = "right";
      this.ctx.fillText(
        `GESTURE: ${this.gestureName} (Thumb: ${this.thumbMetric.toFixed(2)})`,
        this.width - 20,
        this.height - 13
      );
    }
  }

  drawGameOver() {
    this.ctx.fillStyle = "rgba(10, 12, 18, 0.9)";
    this.ctx.fillRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2;

    this.ctx.textAlign = "center";
    this.ctx.font = "bold 44px -apple-system, sans-serif";
    this.ctx.fillStyle = "#ff4646";
    this.ctx.fillText("GAME OVER", cx, cy - 80);

    this.ctx.font = "bold 26px -apple-system, sans-serif";
    this.ctx.fillStyle = "#f0f4fa";
    this.ctx.fillText(`Final Score: ${this.score.toLocaleString()}`, cx, cy - 25);

    const acc = Math.floor((this.shotsHit / Math.max(1, this.shotsFired)) * 100);
    this.ctx.font = "16px -apple-system, sans-serif";
    this.ctx.fillStyle = "#8b949e";
    this.ctx.fillText(
      `Max Combo: ${this.maxCombo}x  |  Accuracy: ${acc}%  |  Level Reached: ${this.level}`,
      cx,
      cy + 15
    );

    this.ctx.font = "bold 20px -apple-system, sans-serif";
    this.ctx.fillStyle = "#00ffd5";
    this.ctx.fillText(
      "Pull Trigger (Thumb Gesture) or Click / Press [R] to Restart",
      cx,
      cy + 75
    );
  }
}

// Start Game Instance
window.onload = () => {
  window.game = new WebShooterGame();
};
