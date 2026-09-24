/**
 * Web Game & MediaPipe Gesture Engine for Hand Gun Shooter.
 * Features:
 * 1. Two-Hand Dual Wielding (independent crosshairs, aiming, and firing simultaneously).
 * 2. Reload Gestures (pointing hand down & two-hand palm tapping).
 * 3. 3 Customizable Sound Packs (Laser, Revolver, Silencer) via Web Audio API.
 * 4. Multi-hit Shielded Boss Battles & Counter-Projectiles.
 * 5. Collectible Power-Ups (Freeze Time, Rapid Fire, Health Repair).
 */

// Web Audio API Synthesizer with 3 Sound Packs
class SoundSynth {
  constructor() {
    this.ctx = null;
    this.currentPack = "LASER";
    this.packs = ["LASER", "REVOLVER", "SILENCER"];
    this.packIndex = 0;
    this.initAudio();
  }

  initAudio() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  resume() {
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  cycleSoundPack() {
    this.packIndex = (this.packIndex + 1) % this.packs.length;
    this.currentPack = this.packs[this.packIndex];
    this.playShoot();
    return this.currentPack;
  }

  // 1. SHOOT SOUND
  playShoot() {
    if (!this.ctx) return;
    this.resume();
    const now = this.ctx.currentTime;

    if (this.currentPack === "LASER") {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(950, now);
      osc.frequency.exponentialRampToValueAtTime(180, now + 0.12);
      gain.gain.setValueAtTime(0.28, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.12);
    } else if (this.currentPack === "REVOLVER") {
      const bufferSize = Math.floor(this.ctx.sampleRate * 0.18);
      const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.25));
      }
      const noise = this.ctx.createBufferSource();
      noise.buffer = buffer;
      const noiseGain = this.ctx.createGain();
      noiseGain.gain.setValueAtTime(0.35, now);
      noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
      noise.connect(noiseGain);
      noiseGain.connect(this.ctx.destination);
      noise.start(now);

      const boom = this.ctx.createOscillator();
      const boomGain = this.ctx.createGain();
      boom.type = "sine";
      boom.frequency.setValueAtTime(140, now);
      boom.frequency.exponentialRampToValueAtTime(45, now + 0.18);
      boomGain.gain.setValueAtTime(0.4, now);
      boomGain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
      boom.connect(boomGain);
      boomGain.connect(this.ctx.destination);
      boom.start(now);
      boom.stop(now + 0.18);
    } else {
      // SILENCER
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(340, now);
      osc.frequency.exponentialRampToValueAtTime(90, now + 0.08);
      gain.gain.setValueAtTime(0.22, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.08);
    }
  }

  // 2. HIT SOUND
  playHit() {
    if (!this.ctx) return;
    this.resume();
    const now = this.ctx.currentTime;

    if (this.currentPack === "LASER") {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(420, now);
      osc.frequency.exponentialRampToValueAtTime(90, now + 0.15);
      gain.gain.setValueAtTime(0.35, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.15);
    } else if (this.currentPack === "REVOLVER") {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(920, now);
      osc.frequency.exponentialRampToValueAtTime(300, now + 0.16);
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.16);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.16);
    } else {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.exponentialRampToValueAtTime(60, now + 0.10);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.10);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.10);
    }
  }

  // 3. RELOAD SOUND
  playReload() {
    if (!this.ctx) return;
    this.resume();
    const now = this.ctx.currentTime;

    if (this.currentPack === "LASER") {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(260, now);
      osc.frequency.exponentialRampToValueAtTime(840, now + 0.22);
      gain.gain.setValueAtTime(0.02, now);
      gain.gain.linearRampToValueAtTime(0.25, now + 0.15);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.22);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (this.currentPack === "REVOLVER") {
      for (let i = 0; i < 3; i++) {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const t = now + i * 0.07;
        osc.frequency.setValueAtTime(600 + i * 150, t);
        gain.gain.setValueAtTime(0.25, t);
        gain.gain.exponentialRampToValueAtTime(0.01, t + 0.04);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(t);
        osc.stop(t + 0.04);
      }
    } else {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(550, now);
      osc.frequency.exponentialRampToValueAtTime(200, now + 0.12);
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.12);
    }
  }

  // 4. EMPTY CLICK SOUND
  playEmpty() {
    if (!this.ctx) return;
    this.resume();
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = this.currentPack === "LASER" ? "square" : "sine";
    osc.frequency.setValueAtTime(160, now);
    gain.gain.setValueAtTime(0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.05);
  }

  // 5. BOSS DEFLECTION & EXPLOSION
  playBossHit() {
    if (!this.ctx) return;
    this.resume();
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(520, now);
    osc.frequency.exponentialRampToValueAtTime(140, now + 0.18);
    gain.gain.setValueAtTime(0.35, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.18);
  }

  playBossDestroy() {
    if (!this.ctx) return;
    this.resume();
    const now = this.ctx.currentTime;
    const boom = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    boom.type = "sine";
    boom.frequency.setValueAtTime(95, now);
    boom.frequency.exponentialRampToValueAtTime(30, now + 0.55);
    gain.gain.setValueAtTime(0.6, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.55);
    boom.connect(gain);
    gain.connect(this.ctx.destination);
    boom.start(now);
    boom.stop(now + 0.55);
  }

  // 6. POWER-UP ASCENDING CHIME
  playPowerUp() {
    if (!this.ctx) return;
    this.resume();
    const notes = [440, 554, 659, 880];
    const now = this.ctx.currentTime;
    notes.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const t = now + idx * 0.07;
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0.22, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + 0.12);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(t);
      osc.stop(t + 0.12);
    });
  }

  // 7. HURT
  playHurt() {
    if (!this.ctx) return;
    this.resume();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const now = this.ctx.currentTime;
    osc.type = "square";
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.linearRampToValueAtTime(75, now + 0.25);
    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.25);
  }
}

// Regular Target Class
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
      this.y = 130 + Math.random() * (screenH - 250);
      this.vx = baseSpeed * (1.0 + Math.random() * 0.8);
      this.vy = (Math.random() - 0.5) * 2;
    } else if (side === "RIGHT") {
      this.x = screenW + this.radius;
      this.y = 130 + Math.random() * (screenH - 250);
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

  update(dt, speedFactor = 1.0) {
    const effDt = dt * speedFactor;
    this.x += this.vx * (effDt * 60);
    this.y += this.vy * (effDt * 60);
    const t = (performance.now() - this.createdAt) / 1000.0;
    this.y += Math.sin(t * this.wobbleFreq) * (this.wobbleAmp * effDt * 60);

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

    ctx.beginPath();
    ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 0.65, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 0.35, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
  }
}

// Boss Counter-Projectile
class BossProjectile {
  constructor(x, y, speed = 2.5) {
    this.x = x;
    this.y = y;
    this.speed = speed;
    this.radius = 14;
    this.createdAt = performance.now();
  }
  update(dt, speedFactor = 1.0) {
    const effDt = dt * speedFactor;
    this.y += this.speed * (effDt * 60);
    const t = (performance.now() - this.createdAt) / 1000.0;
    this.x += Math.sin(t * 5.0) * 1.2 * (effDt * 60);
    return this.y < 730;
  }
  isHit(px, py) {
    return Math.hypot(this.x - px, this.y - py) <= this.radius + 6;
  }
  draw(ctx) {
    const cx = Math.floor(this.x);
    const cy = Math.floor(this.y);
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius + 4, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 80, 20, 0.4)";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = "#ff6432";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 0.45, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffc8";
    ctx.fill();
    ctx.restore();
  }
}

// Armored Shielded Boss Drone
class BossEnemy {
  constructor(screenW, screenH, level) {
    this.screenW = screenW;
    this.screenH = screenH;
    this.width = 140;
    this.height = 70;
    this.x = screenW / 2;
    this.targetY = 150;
    this.y = -80;
    this.level = level;

    this.maxShield = 6 + (level - 1) * 2;
    this.shield = this.maxShield;
    this.maxHull = 12 + (level - 1) * 3;
    this.hull = this.maxHull;

    this.lastAttackTime = performance.now();
    this.attackInterval = Math.max(1800, 3200 - level * 250);
    this.projectiles = [];

    this.hitFlash = 0;
    this.shieldFlash = 0;
    this.createdAt = performance.now();
    this.shieldAngle = 0;
  }

  update(dt, speedFactor = 1.0) {
    const effDt = dt * speedFactor;
    if (this.y < this.targetY) {
      this.y += 120 * effDt;
      if (this.y > this.targetY) this.y = this.targetY;
    }

    const t = (performance.now() - this.createdAt) / 1000.0;
    this.x = this.screenW / 2 + Math.sin(t * 0.9) * (this.screenW * 0.35);
    this.y = this.targetY + Math.cos(t * 1.8) * 15;
    this.shieldAngle += 1.5 * (effDt * 60);

    if (this.hitFlash > 0) this.hitFlash = Math.max(0, this.hitFlash - dt);
    if (this.shieldFlash > 0) this.shieldFlash = Math.max(0, this.shieldFlash - dt);

    const now = performance.now();
    const effInterval = this.attackInterval / Math.max(0.25, speedFactor);
    if (this.y >= this.targetY && now - this.lastAttackTime >= effInterval) {
      this.lastAttackTime = now;
      this.projectiles.push(new BossProjectile(this.x, this.y + 35, 2.5 + this.level * 0.2));
    }

    this.projectiles = this.projectiles.filter((p) => p.update(dt, speedFactor));
    return this.hull > 0;
  }

  isHit(px, py) {
    return Math.hypot(this.x - px, this.y - py) <= Math.max(this.width, this.height) * 0.55;
  }

  takeHit() {
    if (this.shield > 0) {
      this.shield--;
      this.shieldFlash = 0.15;
      return { shieldDamaged: true, destroyed: false };
    } else {
      this.hull--;
      this.hitFlash = 0.15;
      return { shieldDamaged: false, destroyed: this.hull <= 0 };
    }
  }

  draw(ctx) {
    const cx = Math.floor(this.x);
    const cy = Math.floor(this.y);

    if (this.shield > 0) {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(cx, cy, (this.width + 50) / 2, (this.height + 40) / 2, 0, 0, Math.PI * 2);
      ctx.strokeStyle = this.shieldFlash > 0 ? "#ffffff" : "rgba(0, 195, 255, 0.75)";
      ctx.lineWidth = 3;
      ctx.stroke();

      for (let ang = 0; ang < 360; ang += 60) {
        const rad = ((ang + this.shieldAngle) * Math.PI) / 180;
        const tx = cx + (Math.cos(rad) * (this.width + 50)) / 2;
        const ty = cy + (Math.sin(rad) * (this.height + 40)) / 2;
        ctx.beginPath();
        ctx.arc(tx, ty, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#00ffd5";
        ctx.fill();
      }
      ctx.restore();
    }

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx - 70, cy);
    ctx.lineTo(cx - 30, cy - 25);
    ctx.lineTo(cx + 30, cy - 25);
    ctx.lineTo(cx + 70, cy);
    ctx.lineTo(cx + 40, cy + 25);
    ctx.lineTo(cx - 40, cy + 25);
    ctx.closePath();
    ctx.fillStyle = this.hitFlash > 0 ? "#ffffff" : "#2d374b";
    ctx.fill();
    ctx.strokeStyle = this.shield === 0 ? "#ff4646" : "#00dcd2";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx, cy, 15, 0, Math.PI * 2);
    ctx.fillStyle = this.shield === 0 ? "#ff3c3c" : "#00f0dc";
    ctx.fill();

    const bw = 120;
    const bh = 6;
    const bx = cx - bw / 2;
    const by = cy - 45;

    if (this.maxShield > 0) {
      ctx.fillStyle = "#1e2832";
      ctx.fillRect(bx, by - 9, bw, bh);
      ctx.fillStyle = "#00c3ff";
      ctx.fillRect(bx, by - 9, Math.max(0, bw * (this.shield / this.maxShield)), bh);
    }

    ctx.fillStyle = "#1e2832";
    ctx.fillRect(bx, by, bw, bh);
    ctx.fillStyle = "#ff4b4b";
    ctx.fillRect(bx, by, Math.max(0, bw * (this.hull / this.maxHull)), bh);

    ctx.restore();

    for (const p of this.projectiles) p.draw(ctx);
  }
}

// Power-Up Item
class PowerUpItem {
  constructor(x, y, type = null) {
    this.x = x;
    this.y = y;
    this.radius = 20;
    this.type = type || ["FREEZE", "RAPID_FIRE", "HEALTH"][Math.floor(Math.random() * 3)];
    this.createdAt = performance.now();
    this.vy = 1.0 + Math.random() * 0.6;
    this.vx = (Math.random() - 0.5) * 1.0;

    if (this.type === "FREEZE") {
      this.color = "#50dcff";
      this.icon = "FREEZE";
    } else if (this.type === "RAPID_FIRE") {
      this.color = "#ffd228";
      this.icon = "RAPID";
    } else {
      this.color = "#32dc64";
      this.icon = "+LIFE";
    }
  }

  update(dt) {
    this.y += this.vy * (dt * 60);
    this.x += this.vx * (dt * 60);
    const t = (performance.now() - this.createdAt) / 1000.0;
    this.x += Math.sin(t * 3.0) * 0.8;
    return this.y < 730;
  }

  isHit(px, py) {
    return Math.hypot(this.x - px, this.y - py) <= this.radius + 4;
  }

  draw(ctx) {
    const cx = Math.floor(this.x);
    const cy = Math.floor(this.y);
    const t = (performance.now() - this.createdAt) / 1000.0;
    const pulse = Math.sin(t * 8.0) * 3;

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius + pulse, 0, Math.PI * 2);
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
    ctx.fill();

    ctx.font = "bold 11px -apple-system, sans-serif";
    ctx.fillStyle = this.color;
    ctx.textAlign = "center";
    ctx.fillText(this.icon, cx, cy + 4);
    ctx.restore();
  }
}

// Particle & Floating Text
class Particle {
  constructor(x, y, color, speedMult = 1.0) {
    this.x = x;
    this.y = y;
    this.color = color;
    const angle = Math.random() * Math.PI * 2;
    const speed = (2 + Math.random() * 6) * speedMult;
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
  constructor(x, y, text, color, size = 20) {
    this.x = x;
    this.y = y;
    this.text = text;
    this.color = color;
    this.size = size;
    this.lifetime = 0.85;
    this.age = 0;
  }
  update(dt) {
    this.age += dt;
    this.y -= 38 * dt;
    return this.age < this.lifetime;
  }
  draw(ctx) {
    const alpha = Math.max(0, 1 - this.age / this.lifetime);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = this.color;
    ctx.font = `bold ${this.size}px -apple-system, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(this.text, this.x, this.y);
    ctx.restore();
  }
}

// Single Gun Model (Supports simultaneous dual wielding)
class WebGunState {
  constructor(id, label, color, x) {
    this.id = id;
    this.label = label;
    this.color = color;
    this.aimX = x;
    this.aimY = 350;
    this.isGunReady = false;
    this.flashTimer = 0;
    this.ammo = 8;
    this.maxAmmo = 8;
    this.isReloading = false;
    this.reloadStartTime = 0;
    this.reloadDuration = 600; // ms
    this.lastShotTime = 0;
    this.active = false;
    this.gesture = "NO_GUN";
    this.thumbMetric = 1.0;
  }

  triggerReload() {
    const now = performance.now();
    if (!this.isReloading && this.ammo < this.maxAmmo) {
      this.isReloading = true;
      this.reloadStartTime = now;
      return true;
    }
    return false;
  }

  updateReload(now) {
    if (!this.isReloading) return false;
    if (now - this.reloadStartTime >= this.reloadDuration) {
      this.ammo = this.maxAmmo;
      this.isReloading = false;
      return true;
    }
    return false;
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

    this.controlMode = "HAND";
    this.state = "PLAYING";

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
    this.nextBossScore = 2500;

    this.freezeTimer = 0;
    this.rapidFireTimer = 0;
    this.screenShake = 0;

    this.targets = [];
    this.particles = [];
    this.floatingTexts = [];
    this.powerups = [];
    this.boss = null;

    // Gun 0 (Primary / Right hand on screen / Cyan)
    // Gun 1 (Secondary / Left hand on screen / Orange)
    this.guns = [
      new WebGunState(0, "RIGHT GUN", "#00f0dc", 550),
      new WebGunState(1, "LEFT GUN", "#ff8c1e", 450),
    ];
    this.guns[0].active = true;

    this.setupListeners();
    this.lastFrameTime = performance.now();
    requestAnimationFrame((t) => this.gameLoop(t));
  }

  setupListeners() {
    const sBadge = document.getElementById("hud-sound-badge");
    if (sBadge) {
      sBadge.onclick = () => {
        const pack = this.sound.cycleSoundPack();
        sBadge.textContent = `SOUND: ${pack} [S]`;
        this.floatingTexts.push(new FloatingText(this.width / 2, 90, `SOUND: ${pack}`, "#00ffd5"));
      };
    }

    window.addEventListener("keydown", (e) => {
      if (e.key === "m" || e.key === "M") {
        this.controlMode = this.controlMode === "HAND" ? "MOUSE" : "HAND";
        document.getElementById("hud-mode-badge").textContent = `${this.controlMode} MODE`;
      } else if (e.key === "s" || e.key === "S") {
        const pack = this.sound.cycleSoundPack();
        if (sBadge) sBadge.textContent = `SOUND: ${pack} [S]`;
        this.floatingTexts.push(new FloatingText(this.width / 2, 90, `SOUND: ${pack}`, "#00ffd5"));
      } else if (e.key === " " || e.code === "Space") {
        this.reloadAll();
      } else if (e.key === "r" || e.key === "R") {
        this.resetGame();
      }
    });

    this.canvas.addEventListener("mousemove", (e) => {
      if (this.controlMode === "MOUSE") {
        const rect = this.canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left) * (this.width / rect.width);
        const my = (e.clientY - rect.top) * (this.height / rect.height);
        this.guns[0].aimX = mx + 28;
        this.guns[0].aimY = my;
        this.guns[0].isGunReady = true;
        this.guns[0].active = true;

        this.guns[1].aimX = mx - 28;
        this.guns[1].aimY = my;
        this.guns[1].isGunReady = true;
        this.guns[1].active = true;
      }
    });

    this.canvas.addEventListener("contextmenu", (e) => e.preventDefault());

    this.canvas.addEventListener("mousedown", (e) => {
      if (this.controlMode === "MOUSE") {
        if (this.state === "PLAYING") {
          const gunIdx = e.button === 0 ? 0 : 1;
          const g = this.guns[gunIdx];
          if (g.ammo > 0 || this.rapidFireTimer > 0) {
            if (this.rapidFireTimer <= 0) g.ammo--;
            this.shootAt(g.aimX, g.aimY, gunIdx);
          } else {
            this.sound.playEmpty();
            this.floatingTexts.push(new FloatingText(g.aimX, g.aimY, "CLICK! RELOAD", "#ff5050"));
          }
        } else if (this.state === "GAME_OVER") {
          this.resetGame();
        }
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

  reloadAll() {
    let reloadedAny = false;
    for (const g of this.guns) {
      if (g.triggerReload()) reloadedAny = true;
    }
    if (reloadedAny) {
      this.sound.playReload();
      this.floatingTexts.push(new FloatingText(this.width / 2, this.height - 120, "+RELOADED!", "#00ffd5"));
    }
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
    this.nextBossScore = 2500;
    this.freezeTimer = 0;
    this.rapidFireTimer = 0;
    this.screenShake = 0;
    this.targets = [];
    this.particles = [];
    this.floatingTexts = [];
    this.powerups = [];
    this.boss = null;
    for (const g of this.guns) {
      g.ammo = g.maxAmmo;
      g.isReloading = false;
      g.flashTimer = 0;
    }
    this.state = "PLAYING";
  }

  shootAt(x, y, gunId = 0) {
    this.shotsFired++;
    if (this.guns[gunId]) this.guns[gunId].flashTimer = 0.12;
    this.sound.playShoot();

    // 1. Power-Ups Hit
    for (let i = this.powerups.length - 1; i >= 0; i--) {
      if (this.powerups[i].isHit(x, y)) {
        const p = this.powerups.splice(i, 1)[0];
        this.sound.playPowerUp();
        this.activatePowerUp(p.type, p.x, p.y);
        return true;
      }
    }

    // 2. Boss Projectiles Hit
    if (this.boss) {
      for (let i = this.boss.projectiles.length - 1; i >= 0; i--) {
        const proj = this.boss.projectiles[i];
        if (proj.isHit(x, y)) {
          this.boss.projectiles.splice(i, 1);
          this.sound.playHit();
          this.score += 50;
          for (let k = 0; k < 8; k++) {
            this.particles.push(new Particle(proj.x, proj.y, "#ff7832"));
          }
          this.floatingTexts.push(new FloatingText(proj.x, proj.y, "+50 INTERCEPT", "#00ffd5"));
          return true;
        }
      }
    }

    // 3. Boss Hit
    if (this.boss && this.boss.isHit(x, y)) {
      this.shotsHit++;
      const { shieldDamaged, destroyed } = this.boss.takeHit();

      if (shieldDamaged) {
        this.sound.playBossHit();
        for (let k = 0; k < 12; k++) this.particles.push(new Particle(x, y, "#00c3ff"));
        this.floatingTexts.push(new FloatingText(x, y, "SHIELD HIT!", "#00c3ff"));
      } else {
        this.sound.playHit();
        for (let k = 0; k < 14; k++) this.particles.push(new Particle(x, y, "#ff4b4b"));
        this.floatingTexts.push(new FloatingText(x, y, "HULL DAMAGED!", "#ff4b4b"));
      }

      if (destroyed) {
        this.sound.playBossDestroy();
        this.screenShake = 0.4;
        const bossPts = 3000;
        this.score += bossPts;
        this.nextBossScore = this.score + 3500;

        for (let k = 0; k < 45; k++) {
          const col = ["#ff4b4b", "#00c3ff", "#00ffd5", "#ffffc8"][Math.floor(Math.random() * 4)];
          this.particles.push(new Particle(this.boss.x, this.boss.y, col, 1.8));
        }
        this.floatingTexts.push(new FloatingText(this.boss.x, this.boss.y - 20, `+${bossPts} BOSS DESTROYED!`, "#ffd700", 28));
        this.powerups.push(new PowerUpItem(this.boss.x, this.boss.y));
        this.boss = null;
      }
      return true;
    }

    // 4. Regular Targets Hit
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

      this.sound.playHit();
      for (let i = 0; i < 18; i++) {
        this.particles.push(new Particle(hitTarget.x, hitTarget.y, hitTarget.color));
      }

      let label = `+${pts}`;
      if (this.combo > 1) label += ` (${this.combo}x Combo!)`;
      this.floatingTexts.push(new FloatingText(hitTarget.x, hitTarget.y, label, "#00ffd5"));
      return true;
    } else {
      if (this.rapidFireTimer <= 0) {
        if (this.combo > 2) {
          this.floatingTexts.push(new FloatingText(x, y, "Combo Broken", "#ff4646"));
        }
        this.combo = 0;
      }
      return false;
    }
  }

  activatePowerUp(type, x, y) {
    for (let i = 0; i < 22; i++) this.particles.push(new Particle(x, y, "#ffffff"));

    if (type === "FREEZE") {
      this.freezeTimer = 6.0;
      this.floatingTexts.push(new FloatingText(x, y, "⏳ TIME FROZEN! (6s)", "#50dcff"));
    } else if (type === "RAPID_FIRE") {
      this.rapidFireTimer = 7.0;
      for (const g of this.guns) g.ammo = g.maxAmmo;
      this.floatingTexts.push(new FloatingText(x, y, "⚡ RAPID FIRE ACTIVATED!", "#ffd228"));
    } else if (type === "HEALTH") {
      if (this.lives < this.maxLives) {
        this.lives++;
        this.floatingTexts.push(new FloatingText(x, y, "+1 LIFE RESTORED!", "#32dc64"));
      } else {
        this.score += 500;
        this.floatingTexts.push(new FloatingText(x, y, "+500 BONUS POINTS!", "#00ffd5"));
      }
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
      maxNumHands: 2, // Enable two-hand simultaneous tracking
      modelComplexity: 0, // Lite model for smooth 60fps web tracking without dropping second hand
      minDetectionConfidence: 0.50,
      minTrackingConfidence: 0.50,
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
    const pw = this.pipCanvas.width;
    const ph = this.pipCanvas.height;
    this.pipCtx.save();
    this.pipCtx.clearRect(0, 0, pw, ph);
    this.pipCtx.translate(pw, 0);
    this.pipCtx.scale(-1, 1);
    this.pipCtx.drawImage(results.image, 0, 0, pw, ph);

    const hands = results.multiHandLandmarks || [];

    // Update PiP status indicator
    const pipLabel = document.getElementById("pip-label");
    if (pipLabel) {
      if (hands.length >= 2) {
        pipLabel.textContent = "DUAL HANDS (2/2)";
        pipLabel.style.color = "#00ffd5";
      } else if (hands.length === 1) {
        pipLabel.textContent = "1 HAND (1/2)";
        pipLabel.style.color = "#ffd228";
      } else {
        pipLabel.textContent = "SEARCHING HANDS";
        pipLabel.style.color = "#ff6464";
      }
    }

    // Check two-hand palm tap reload
    if (hands.length >= 2) {
      const h1 = hands[0];
      const h2 = hands[1];
      const dist = (p1, p2) => Math.hypot(p1.x - p2.x, p1.y - p2.y, (p1.z || 0) - (p2.z || 0));
      const palm1 = h1[9];
      const palm2 = h2[9];
      const wrist1 = h1[0];
      const wrist2 = h2[0];
      const scale1 = Math.max(0.04, dist(palm1, wrist1));
      const scale2 = Math.max(0.04, dist(palm2, wrist2));
      const avgScale = (scale1 + scale2) / 2;

      const d1 = dist(h1[8], palm2);
      const d2 = dist(h2[8], palm1);
      const dPalms = dist(palm1, palm2);

      if (d1 < 0.9 * avgScale || d2 < 0.9 * avgScale || dPalms < 1.0 * avgScale) {
        this.reloadAll();
      }
    }

    // Rock-Solid Spatial Hand-to-Gun Assignment using Palm Center
    // Palm Center Mirrored X = 1.0 - (lm[0].x + lm[9].x) / 2.0
    // Gun 1 (LEFT GUN, Orange) takes hand on the left of screen
    // Gun 0 (RIGHT GUN, Cyan) takes hand on the right of screen
    let rightHandLm = null;
    let leftHandLm = null;

    if (hands.length >= 2) {
      const hA = hands[0];
      const hB = hands[1];
      const xA = 1.0 - (hA[0].x + hA[9].x) / 2.0;
      const xB = 1.0 - (hB[0].x + hB[9].x) / 2.0;
      if (xA < xB) {
        leftHandLm = hA;
        rightHandLm = hB;
      } else {
        leftHandLm = hB;
        rightHandLm = hA;
      }
    } else if (hands.length === 1) {
      const h = hands[0];
      const x = 1.0 - (h[0].x + h[9].x) / 2.0;
      if (x < 0.45) {
        leftHandLm = h;
      } else if (x > 0.55) {
        rightHandLm = h;
      } else {
        // Near center: preserve whichever gun was active, or default to Right Gun
        if (this.guns[1].active && !this.guns[0].active) {
          leftHandLm = h;
        } else {
          rightHandLm = h;
        }
      }
    }

    // Process Gun 0 (Right Gun, Cyan)
    if (rightHandLm) {
      this.guns[0].active = true;
      this.drawLandmarksOnPip(rightHandLm, this.guns[0].color, pw, ph);
      this.processGunGesture(this.guns[0], rightHandLm);
    } else {
      if (this.controlMode === "HAND") {
        this.guns[0].active = false;
        this.guns[0].isGunReady = false;
      }
    }

    // Process Gun 1 (Left Gun, Orange)
    if (leftHandLm) {
      this.guns[1].active = true;
      this.drawLandmarksOnPip(leftHandLm, this.guns[1].color, pw, ph);
      this.processGunGesture(this.guns[1], leftHandLm);
    } else {
      if (this.controlMode === "HAND") {
        this.guns[1].active = false;
        this.guns[1].isGunReady = false;
      }
    }

    this.pipCtx.restore();
  }

  drawLandmarksOnPip(lm, color, pw, ph) {
    const connections = [
      [0, 1], [1, 2], [2, 3], [3, 4],
      [0, 5], [5, 6], [6, 7], [7, 8],
      [5, 9], [9, 10], [10, 11], [11, 12],
      [9, 13], [13, 14], [14, 15], [15, 16],
      [13, 17], [17, 18], [18, 19], [19, 20],
      [0, 17]
    ];

    this.pipCtx.save();
    this.pipCtx.strokeStyle = color;
    this.pipCtx.lineWidth = 1.5;
    for (const [i, j] of connections) {
      this.pipCtx.beginPath();
      this.pipCtx.moveTo(lm[i].x * pw, lm[i].y * ph);
      this.pipCtx.lineTo(lm[j].x * pw, lm[j].y * ph);
      this.pipCtx.stroke();
    }

    this.pipCtx.fillStyle = color;
    for (const p of lm) {
      this.pipCtx.beginPath();
      this.pipCtx.arc(p.x * pw, p.y * ph, 2.5, 0, Math.PI * 2);
      this.pipCtx.fill();
    }
    this.pipCtx.restore();
  }

  processGunGesture(gun, lm) {
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

    const dist = (p1, p2) => Math.hypot(p1.x - p2.x, p1.y - p2.y, (p1.z || 0) - (p2.z || 0));
    const palmScale = Math.max(0.001, dist(midMcp, wrist));

    // Reload Gesture: Point hand DOWN
    const tipLowerThanMcp = (indexTip.y - indexMcp.y) / palmScale > 0.35;
    const tipLowerThanWrist = (indexTip.y - wrist.y) / palmScale > 0.25;
    const dy = indexTip.y - indexMcp.y;
    const dx = Math.abs(indexTip.x - indexMcp.x);
    if (tipLowerThanMcp && tipLowerThanWrist && dy > dx * 0.8) {
      if (gun.triggerReload()) {
        this.sound.playReload();
        this.floatingTexts.push(new FloatingText(gun.aimX, gun.aimY - 20, "+RELOADED!", "#00ffd5"));
      }
    }

    // Gun Ready Check: index extended, at least 1 finger folded
    const idxTipDist = dist(indexTip, wrist);
    const idxPipDist = dist(indexPip, wrist);
    const idxExtended = (idxTipDist > idxPipDist * 1.03) && (idxTipDist > dist(indexMcp, wrist));

    const midFolded = dist(midTip, wrist) < dist(indexTip, wrist) * 0.95 || dist(midTip, midMcp) / palmScale < 1.10;
    const ringFolded = dist(ringTip, wrist) < dist(indexTip, wrist) * 0.95 || dist(ringTip, lm[13]) / palmScale < 1.10;
    const pinkyFolded = dist(pinkyTip, wrist) < dist(indexTip, wrist) * 0.95 || dist(pinkyTip, lm[17]) / palmScale < 1.10;

    const isGun = idxExtended && ((midFolded ? 1 : 0) + (ringFolded ? 1 : 0) + (pinkyFolded ? 1 : 0) >= 1);
    gun.isGunReady = isGun;

    // Mirrored Aim Coords
    const normX = 1.0 - indexTip.x;
    const normY = indexTip.y;
    const margin = 0.08;
    const clampedX = Math.min(1.0, Math.max(0.0, (normX - margin) / (1.0 - 2 * margin)));
    const clampedY = Math.min(1.0, Math.max(0.0, (normY - margin) / (1.0 - 2 * margin)));

    const targetX = clampedX * this.width;
    const targetY = clampedY * this.height;

    gun.aimX = 0.40 * targetX + 0.60 * gun.aimX;
    gun.aimY = 0.40 * targetY + 0.60 * gun.aimY;

    // Trigger Pull Detection (Support both thumb-to-index and thumb-to-middle curl)
    const dThumbIndex = dist(thumbTip, indexMcp) / palmScale;
    const dThumbMid = dist(thumbTip, midMcp) / palmScale;
    gun.thumbMetric = Math.min(dThumbIndex, dThumbMid);

    const now = performance.now();
    const cooldown = this.rapidFireTimer > 0 ? 90 : 220;

    if (isGun) {
      if (gun.thumbMetric < 0.60) {
        gun.gesture = "SHOOT";
        if (now - gun.lastShotTime >= cooldown && !gun.isReloading) {
          if (gun.ammo > 0 || this.rapidFireTimer > 0) {
            if (this.rapidFireTimer <= 0) gun.ammo--;
            if (this.state === "PLAYING") this.shootAt(gun.aimX, gun.aimY, gun.id);
            else if (this.state === "GAME_OVER") this.resetGame();
          } else {
            this.sound.playEmpty();
            this.floatingTexts.push(new FloatingText(gun.aimX, gun.aimY, "CLICK! RELOAD", "#ff5050"));
          }
          gun.lastShotTime = now;
        }
      } else {
        gun.gesture = "GUN_READY";
      }
    } else {
      gun.gesture = "NO_GUN";
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
    const now = performance.now();

    let speedFactor = 1.0;
    if (this.freezeTimer > 0) {
      this.freezeTimer = Math.max(0, this.freezeTimer - dt);
      speedFactor = 0.25;
    }
    if (this.rapidFireTimer > 0) {
      this.rapidFireTimer = Math.max(0, this.rapidFireTimer - dt);
    }
    if (this.screenShake > 0) {
      this.screenShake = Math.max(0, this.screenShake - dt);
    }

    for (const g of this.guns) {
      if (g.updateReload(now)) {
        this.floatingTexts.push(new FloatingText(g.aimX, g.aimY - 20, "+RELOADED!", "#00ffd5"));
      }
      if (g.flashTimer > 0) g.flashTimer = Math.max(0, g.flashTimer - dt);
    }

    if (this.state !== "PLAYING") return;

    const elapsed = (now - this.startTime) / 1000.0;
    this.level = 1 + Math.floor(this.score / 1000) + Math.floor(elapsed / 30);

    // Boss Spawn Check
    if (!this.boss && this.score >= this.nextBossScore) {
      this.boss = new BossEnemy(this.width, this.height, this.level);
      this.floatingTexts.push(new FloatingText(this.width / 2, 220, "⚠️ WARNING: BOSS INCOMING! ⚠️", "#ff3c3c", 30));
    }

    // Regular Targets
    const maxTargets = this.boss ? 4 : Math.min(7, 3 + Math.floor(this.level / 2));
    this.spawnInterval = Math.max(0.50, 1.4 - this.level * 0.07);

    if (this.targets.length < maxTargets && now - this.lastSpawnTime >= this.spawnInterval * 1000) {
      this.targets.push(new Target(this.width, this.height, this.level));
      this.lastSpawnTime = now;

      if (this.powerups.length < 2 && Math.random() < 0.15) {
        this.powerups.push(new PowerUpItem(100 + Math.random() * (this.width - 200), -25));
      }
    }

    // Update Targets
    for (let i = this.targets.length - 1; i >= 0; i--) {
      const alive = this.targets[i].update(dt, speedFactor);
      if (!alive) {
        this.targets.splice(i, 1);
        this.lives--;
        this.combo = 0;
        this.sound.playHurt();
        this.screenShake = 0.2;
        this.floatingTexts.push(new FloatingText(this.width / 2, this.height / 2, "TARGET ESCAPED! -1 LIFE", "#f04646"));
        if (this.lives <= 0) this.state = "GAME_OVER";
      }
    }

    // Update Boss
    if (this.boss) {
      const alive = this.boss.update(dt, speedFactor);
      if (alive) {
        for (let i = this.boss.projectiles.length - 1; i >= 0; i--) {
          const proj = this.boss.projectiles[i];
          if (proj.y >= this.height - 10) {
            this.boss.projectiles.splice(i, 1);
            this.lives--;
            this.sound.playHurt();
            this.screenShake = 0.25;
            this.floatingTexts.push(new FloatingText(this.width / 2, this.height / 2, "BOSS ATTACK HIT! -1 LIFE", "#ff4646"));
            if (this.lives <= 0) this.state = "GAME_OVER";
          }
        }
      }
    }

    this.powerups = this.powerups.filter((p) => p.update(dt));
    this.particles = this.particles.filter((p) => p.update(dt));
    this.floatingTexts = this.floatingTexts.filter((ft) => ft.update(dt));
  }

  render() {
    this.ctx.save();

    if (this.screenShake > 0) {
      const intensity = Math.floor(this.screenShake * 12);
      const ox = (Math.random() - 0.5) * intensity * 2;
      const oy = (Math.random() - 0.5) * intensity * 2;
      this.ctx.translate(ox, oy);
    }

    this.ctx.fillStyle = "#10141c";
    this.ctx.fillRect(0, 0, this.width, this.height);

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

    if (this.freezeTimer > 0) {
      this.ctx.fillStyle = "rgba(0, 180, 255, 0.1)";
      this.ctx.fillRect(0, 0, this.width, this.height);
    }

    for (const t of this.targets) t.draw(this.ctx);
    if (this.boss) this.boss.draw(this.ctx);
    for (const p of this.powerups) p.draw(this.ctx);
    for (const p of this.particles) p.draw(this.ctx);
    for (const ft of this.floatingTexts) ft.draw(this.ctx);

    // Draw both independent crosshairs
    this.drawCrosshairs();

    this.drawHUD();

    if (this.state === "GAME_OVER") {
      this.drawGameOver();
    }

    this.ctx.restore();
  }

  drawCrosshairs() {
    for (const g of this.guns) {
      if (!g.active && this.controlMode === "HAND") continue;

      const cx = Math.floor(g.aimX);
      const cy = Math.floor(g.aimY);

      let color = g.color;
      if (g.flashTimer > 0) color = "#ff3c3c";
      else if (this.rapidFireTimer > 0) color = "#ffd228";
      else if (!g.isGunReady) color = "#828796";

      if (g.flashTimer > 0) {
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, 45, 0, Math.PI * 2);
        this.ctx.fillStyle = "rgba(255, 100, 50, 0.45)";
        this.ctx.fill();
      }

      this.ctx.beginPath();
      this.ctx.arc(cx, cy, 24, 0, Math.PI * 2);
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 2;
      this.ctx.stroke();

      this.ctx.beginPath();
      this.ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      this.ctx.fillStyle = color;
      this.ctx.fill();

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

      const maxAmmo = g.maxAmmo;
      const curAmmo = g.ammo;
      const ammoR = 38;

      if (g.isReloading) {
        const elapsed = performance.now() - g.reloadStartTime;
        const progress = Math.min(1.0, elapsed / g.reloadDuration);
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, ammoR, 0, progress * Math.PI * 2);
        this.ctx.strokeStyle = "#00ffd5";
        this.ctx.lineWidth = 3;
        this.ctx.stroke();

        this.ctx.font = "bold 11px -apple-system, sans-serif";
        this.ctx.fillStyle = "#00ffd5";
        this.ctx.textAlign = "center";
        this.ctx.fillText("RELOADING", cx, cy + 48);
      } else {
        for (let i = 0; i < maxAmmo; i++) {
          const ang = (i / maxAmmo) * Math.PI * 2 - Math.PI / 2;
          const px = cx + Math.cos(ang) * ammoR;
          const py = cy + Math.sin(ang) * ammoR;
          this.ctx.beginPath();
          this.ctx.arc(px, py, 3, 0, Math.PI * 2);
          this.ctx.fillStyle = i < curAmmo ? color : "#464b55";
          this.ctx.fill();
        }

        if (curAmmo === 0) {
          const blink = Math.floor(performance.now() / 250) % 2 === 0;
          if (blink) {
            this.ctx.font = "bold 11px -apple-system, sans-serif";
            this.ctx.fillStyle = "#ff4646";
            this.ctx.textAlign = "center";
            this.ctx.fillText("POINT DOWN TO RELOAD", cx, cy + 48);
          }
        }
      }

      this.ctx.font = "bold 11px monospace";
      this.ctx.fillStyle = color;
      this.ctx.textAlign = "center";
      this.ctx.fillText(g.label, cx, cy - 40);
    }
  }

  drawHUD() {
    this.ctx.fillStyle = "rgba(10, 14, 20, 0.88)";
    this.ctx.fillRect(0, 0, this.width, 58);
    this.ctx.strokeStyle = "#1c2432";
    this.ctx.beginPath();
    this.ctx.moveTo(0, 58);
    this.ctx.lineTo(this.width, 58);
    this.ctx.stroke();

    this.ctx.font = "bold 20px -apple-system, sans-serif";
    this.ctx.fillStyle = "#f0f4fa";
    this.ctx.textAlign = "left";
    this.ctx.fillText(`SCORE: ${this.score.toLocaleString()}`, 18, 36);

    if (this.combo > 1) {
      this.ctx.fillStyle = "#00ffd5";
      this.ctx.fillText(`COMBO ${this.combo}x`, 210, 36);
    }

    this.ctx.font = "14px -apple-system, sans-serif";
    this.ctx.fillStyle = "#8b949e";
    this.ctx.fillText(`LEVEL ${this.level}`, 350, 36);

    this.ctx.fillStyle = "#ffd750";
    this.ctx.fillText(`SOUND: ${this.sound.currentPack}`, 430, 36);

    this.ctx.fillStyle = "#f0f4fa";
    this.ctx.fillText("LIVES:", this.width - 200, 36);
    for (let i = 0; i < this.maxLives; i++) {
      this.ctx.beginPath();
      this.ctx.arc(this.width - 135 + i * 22, 31, 7, 0, Math.PI * 2);
      this.ctx.fillStyle = i < this.lives ? "#32dc64" : "#3c3c46";
      this.ctx.fill();
    }

    let badgeY = 82;
    if (this.freezeTimer > 0) {
      this.ctx.fillStyle = "#50dcff";
      this.ctx.font = "bold 13px -apple-system, sans-serif";
      this.ctx.fillText(`⏳ FREEZE: ${this.freezeTimer.toFixed(1)}s`, 18, badgeY);
      badgeY += 20;
    }
    if (this.rapidFireTimer > 0) {
      this.ctx.fillStyle = "#ffd228";
      this.ctx.font = "bold 13px -apple-system, sans-serif";
      this.ctx.fillText(`⚡ RAPID FIRE: ${this.rapidFireTimer.toFixed(1)}s`, 18, badgeY);
    }

    this.ctx.fillStyle = "rgba(10, 14, 20, 0.88)";
    this.ctx.fillRect(0, this.height - 35, this.width, 35);

    this.ctx.font = "13px -apple-system, sans-serif";
    this.ctx.fillStyle = this.controlMode === "HAND" ? "#00ffd5" : "#ffc83c";
    this.ctx.textAlign = "left";
    this.ctx.fillText(
      `MODE: ${this.controlMode} ([M] Toggle) | [SPACE] Reload | [S] Sound Pack | [R] Restart`,
      18,
      this.height - 13
    );

    if (this.controlMode === "HAND") {
      this.ctx.fillStyle = "#8b949e";
      this.ctx.textAlign = "right";
      const activeCount = this.guns.filter((g) => g.active).length;
      this.ctx.fillText(
        `DUAL-WIELD HANDS: ${activeCount} ACTIVE`,
        this.width - 20,
        this.height - 13
      );
    }
  }

  drawGameOver() {
    this.ctx.fillStyle = "rgba(10, 12, 18, 0.92)";
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
    this.ctx.fillText("Pull Thumb Trigger / Click / Press [R] to Play Again", cx, cy + 75);
  }
}

window.onload = () => {
  window.game = new WebShooterGame();
};
