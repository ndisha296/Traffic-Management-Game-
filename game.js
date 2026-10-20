/**
 * Vehicle Masters: Precision Driver & Dynamic A* Traffic Navigator
 * Pure Vanilla JavaScript & HTML5 Canvas 60FPS Game Engine
 */

(function () {
  'use strict';

  // --- Constants & Config ---
  const CANVAS_WIDTH = 1260;
  const CANVAS_HEIGHT = 860;
  const GRID_COLS = 4;
  const GRID_ROWS = 4;
  const CELL_WIDTH = 190;
  const CELL_HEIGHT = 190;
  const GRID_OFFSET_X = 155;
  const GRID_OFFSET_Y = 145;
  const ROAD_WIDTH = 38;
  const LANE_OFFSET = 9;

  // Colors
  const COLOR_GRASS_BASE = '#5CB23C';
  const COLOR_GRASS_STRIPE = '#54A536';
  const COLOR_ROAD = '#334155';
  const COLOR_ROAD_BORDER = '#F1F5F9';
  const COLOR_SIDEWALK = '#E8EEF5';
  const COLOR_SIDEWALK_CURB = '#B0BEC5';
  const COLOR_RED_LIGHT = '#EF4444';
  const COLOR_YELLOW_LIGHT = '#F59E0B';
  const COLOR_GREEN_LIGHT = '#10B981';
  const COLOR_PLAYER = '#FACC15';
  const COLOR_PLAYER_DARK = '#CA8A04';
  const COLOR_CAR_BLUE = '#3B82F6';
  const COLOR_EMERGENCY = '#EC4899';
  const COLOR_PARK_GREEN = '#22C55E';
  const COLOR_CYAN_GLOW = '#06B6D4';

  const BUILDING_PALETTES = [
    { base: '#F87171', roof: '#EF4444', edge: '#DC2626' },
    { base: '#60A5FA', roof: '#3B82F6', edge: '#2563EB' },
    { base: '#FBBF24', roof: '#F59E0B', edge: '#D97706' },
    { base: '#34D399', roof: '#10B981', edge: '#059669' },
    { base: '#C084FC', roof: '#A855F7', edge: '#9333EA' },
    { base: '#E2E8F0', roof: '#CBD5E1', edge: '#94A3B8' }
  ];

  // --- Web Audio Procedural Synthesizer ---
  class SoundEngine {
    constructor() {
      this.ctx = null;
      this.muted = false;
      this.engineOsc = null;
      this.engineGain = null;
    }

    init() {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
          this._initEngineHum();
        }
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    _initEngineHum() {
      try {
        this.engineOsc = this.ctx.createOscillator();
        this.engineGain = this.ctx.createGain();
        this.engineOsc.type = 'sawtooth';
        this.engineOsc.frequency.setValueAtTime(45, this.ctx.currentTime);
        this.engineGain.gain.setValueAtTime(0.0, this.ctx.currentTime);

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(220, this.ctx.currentTime);

        this.engineOsc.connect(filter);
        filter.connect(this.engineGain);
        this.engineGain.connect(this.ctx.destination);
        this.engineOsc.start();
      } catch (e) {
        console.warn('Audio init warning', e);
      }
    }

    updateEngine(speed, isGas) {
      if (!this.ctx || this.muted || !this.engineOsc) return;
      const baseFreq = 48 + Math.min(Math.abs(speed) * 0.8, 120) + (isGas ? 25 : 0);
      const targetGain = Math.min(0.04 + Math.abs(speed) * 0.0006 + (isGas ? 0.04 : 0), 0.12);
      this.engineOsc.frequency.setTargetAtTime(baseFreq, this.ctx.currentTime, 0.08);
      this.engineGain.gain.setTargetAtTime(targetGain, this.ctx.currentTime, 0.08);
    }

    playHorn() {
      if (!this.ctx || this.muted) return;
      const now = this.ctx.currentTime;
      [440, 554].forEach(freq => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(freq, now);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.36);
      });
    }

    playBlinker() {
      if (!this.ctx || this.muted) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(950, now);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.045);
    }

    playSiren() {
      if (!this.ctx || this.muted) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(650, now);
      osc.frequency.linearRampToValueAtTime(950, now + 0.3);
      osc.frequency.linearRampToValueAtTime(650, now + 0.6);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.62);
    }

    playFanfare() {
      if (!this.ctx || this.muted) return;
      const now = this.ctx.currentTime;
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C E G C
      notes.forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.1);
        gain.gain.setValueAtTime(0, now + idx * 0.1);
        gain.gain.linearRampToValueAtTime(0.15, now + idx * 0.1 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.1 + 0.38);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now + idx * 0.1);
        osc.stop(now + idx * 0.1 + 0.4);
      });
    }

    playBuzzer() {
      if (!this.ctx || this.muted) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'square';
      osc.frequency.setValueAtTime(140, now);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.26);
    }

    toggleMute() {
      this.muted = !this.muted;
      if (this.engineGain) {
        this.engineGain.gain.setValueAtTime(this.muted ? 0 : 0.04, this.ctx ? this.ctx.currentTime : 0);
      }
      return this.muted;
    }
  }

  // --- Graph & City Network ---
  class CityNode {
    constructor(id, x, y, isPerimeter = false, gridPos = null) {
      this.id = id;
      this.x = x;
      this.y = y;
      this.isPerimeter = isPerimeter;
      this.gridPos = gridPos; // [row, col]
      this.outgoing = [];
      this.incoming = [];
    }
  }

  class RoadEdge {
    constructor(fromNode, toNode) {
      this.from = fromNode;
      this.to = toNode;
      const dx = toNode.x - fromNode.x;
      const dy = toNode.y - fromNode.y;
      this.length = Math.hypot(dx, dy);
      this.direction = { x: dx / (this.length || 1), y: dy / (this.length || 1) };
      this.angle = Math.atan2(dy, dx);

      const nx = -this.direction.y;
      const ny = this.direction.x;
      this.start = { x: fromNode.x + nx * LANE_OFFSET, y: fromNode.y + ny * LANE_OFFSET };
      this.end = { x: toNode.x + nx * LANE_OFFSET, y: toNode.y + ny * LANE_OFFSET };

      this.vehicles = [];
      this.queueDensity = 0;
      this.baseCost = this.length;
    }

    updateDensity() {
      this.queueDensity = this.vehicles.filter(v => v.speed < 15).length;
    }

    getDynamicCost(kPenalty = 6.0, isEmergency = false) {
      const k = kPenalty * (isEmergency ? 1.6 : 1.0);
      return this.baseCost + k * this.queueDensity * 25.0;
    }
  }

  // --- Priority Queue for Dynamic A* ---
  class MinHeap {
    constructor() {
      this.heap = [];
    }
    push(item) {
      this.heap.push(item);
      this._bubbleUp(this.heap.length - 1);
    }
    pop() {
      if (this.heap.length === 0) return null;
      const top = this.heap[0];
      const bottom = this.heap.pop();
      if (this.heap.length > 0) {
        this.heap[0] = bottom;
        this._sinkDown(0);
      }
      return top;
    }
    isEmpty() {
      return this.heap.length === 0;
    }
    _bubbleUp(idx) {
      const element = this.heap[idx];
      while (idx > 0) {
        const parentIdx = (idx - 1) >> 1;
        const parent = this.heap[parentIdx];
        if (element.f >= parent.f) break;
        this.heap[idx] = parent;
        this.heap[parentIdx] = element;
        idx = parentIdx;
      }
    }
    _sinkDown(idx) {
      const length = this.heap.length;
      const element = this.heap[idx];
      while (true) {
        let leftIdx = (idx << 1) + 1;
        let rightIdx = leftIdx + 1;
        let swap = null;

        if (leftIdx < length && this.heap[leftIdx].f < element.f) {
          swap = leftIdx;
        }
        if (rightIdx < length) {
          if ((swap === null && this.heap[rightIdx].f < element.f) ||
              (swap !== null && this.heap[rightIdx].f < this.heap[swap].f)) {
            swap = rightIdx;
          }
        }
        if (swap === null) break;
        this.heap[idx] = this.heap[swap];
        this.heap[swap] = element;
        idx = swap;
      }
    }
  }

  // --- Dynamic Traffic Light Controller ---
  class TrafficLight {
    constructor(node) {
      this.node = node;
      this.state = 'EW_GREEN'; // 'EW_GREEN', 'EW_YELLOW', 'ALL_RED_1', 'NS_GREEN', 'NS_YELLOW', 'ALL_RED_2'
      this.timer = 0;
      this.greenDuration = 7.0;
      this.yellowDuration = 2.0;
      this.allRedDuration = 0.6;
      this.automated = true;
      this.emergencyOverride = false;
    }

    update(dt, nearbyEmergency) {
      if (nearbyEmergency) {
        this.emergencyOverride = true;
        // Priority green for emergency approach
        if (Math.abs(nearbyEmergency.direction.x) > Math.abs(nearbyEmergency.direction.y)) {
          this.state = 'EW_GREEN';
        } else {
          this.state = 'NS_GREEN';
        }
        this.timer = 0;
        return;
      }
      this.emergencyOverride = false;

      if (!this.automated) return;

      this.timer += dt;
      switch (this.state) {
        case 'EW_GREEN':
          if (this.timer >= this.greenDuration) {
            this.state = 'EW_YELLOW';
            this.timer = 0;
          }
          break;
        case 'EW_YELLOW':
          if (this.timer >= this.yellowDuration) {
            this.state = 'ALL_RED_1';
            this.timer = 0;
          }
          break;
        case 'ALL_RED_1':
          if (this.timer >= this.allRedDuration) {
            this.state = 'NS_GREEN';
            this.timer = 0;
          }
          break;
        case 'NS_GREEN':
          if (this.timer >= this.greenDuration) {
            this.state = 'NS_YELLOW';
            this.timer = 0;
          }
          break;
        case 'NS_YELLOW':
          if (this.timer >= this.yellowDuration) {
            this.state = 'ALL_RED_2';
            this.timer = 0;
          }
          break;
        case 'ALL_RED_2':
          if (this.timer >= this.allRedDuration) {
            this.state = 'EW_GREEN';
            this.timer = 0;
          }
          break;
      }
    }

    canPass(edge) {
      const isEW = Math.abs(edge.direction.x) > Math.abs(edge.direction.y);
      if (isEW) {
        return this.state === 'EW_GREEN';
      } else {
        return this.state === 'NS_GREEN';
      }
    }
  }

  // --- AI Commuter Vehicle ---
  class Vehicle {
    constructor(id, path, isEmergency = false) {
      this.id = id;
      this.path = path; // Array of CityNode
      this.pathIndex = 0;
      this.isEmergency = isEmergency;
      this.length = 22;
      this.width = 11;

      this.currentEdge = this._findEdge(path[0], path[1]);
      this.x = this.currentEdge ? this.currentEdge.start.x : path[0].x;
      this.y = this.currentEdge ? this.currentEdge.start.y : path[0].y;
      this.speed = 0;
      this.maxSpeed = isEmergency ? 115 : 65 + Math.random() * 20;
      this.acceleration = 120;
      this.deceleration = 260;
      this.heading = this.currentEdge ? this.currentEdge.angle : 0;
      this.direction = this.currentEdge ? this.currentEdge.direction : { x: 1, y: 0 };
      this.distanceOnEdge = 0;
      this.finished = false;
      this.waitTime = 0;

      // Color
      const carColors = ['#3B82F6', '#60A5FA', '#34D399', '#F43F5E', '#A855F7', '#F97316'];
      this.color = isEmergency ? COLOR_EMERGENCY : carColors[id % carColors.length];
    }

    _findEdge(fromNode, toNode) {
      if (!fromNode || !toNode) return null;
      return fromNode.outgoing.find(e => e.to === toNode) || null;
    }

    update(dt, city, trafficLights) {
      if (this.finished || !this.currentEdge) return;

      const targetNode = this.currentEdge.to;
      const distToNode = this.currentEdge.length - this.distanceOnEdge;
      let shouldStop = false;

      // 1. Check traffic light
      if (distToNode < 45 && distToNode > 5 && !targetNode.isPerimeter) {
        const light = trafficLights[targetNode.id];
        if (light && !this.isEmergency && !light.canPass(this.currentEdge)) {
          shouldStop = true;
        }
      }

      // 2. Check vehicle ahead in lane
      for (const other of this.currentEdge.vehicles) {
        if (other !== this && other.distanceOnEdge > this.distanceOnEdge) {
          const gap = other.distanceOnEdge - this.distanceOnEdge;
          if (gap < 32) {
            shouldStop = true;
            break;
          }
        }
      }

      // Physics integration
      if (shouldStop) {
        this.speed = Math.max(0, this.speed - this.deceleration * dt);
        if (this.speed < 5) this.waitTime += dt;
      } else {
        this.speed = Math.min(this.maxSpeed, this.speed + this.acceleration * dt);
      }

      this.distanceOnEdge += this.speed * dt;
      const progress = Math.min(1.0, this.distanceOnEdge / this.currentEdge.length);
      this.x = this.currentEdge.start.x + (this.currentEdge.end.x - this.currentEdge.start.x) * progress;
      this.y = this.currentEdge.start.y + (this.currentEdge.end.y - this.currentEdge.start.y) * progress;
      this.heading = this.currentEdge.angle;

      // Advance to next edge
      if (this.distanceOnEdge >= this.currentEdge.length - 2) {
        this.pathIndex++;
        if (this.pathIndex < this.path.length - 1) {
          const nextFrom = this.path[this.pathIndex];
          const nextTo = this.path[this.pathIndex + 1];
          const nextEdge = this._findEdge(nextFrom, nextTo);
          if (nextEdge) {
            // Remove from old edge, add to new
            const idx = this.currentEdge.vehicles.indexOf(this);
            if (idx !== -1) this.currentEdge.vehicles.splice(idx, 1);
            this.currentEdge = nextEdge;
            this.currentEdge.vehicles.push(this);
            this.distanceOnEdge = 0;
          } else {
            this.finished = true;
          }
        } else {
          this.finished = true;
          const idx = this.currentEdge.vehicles.indexOf(this);
          if (idx !== -1) this.currentEdge.vehicles.splice(idx, 1);
        }
      }
    }

    draw(ctx, camX, camY) {
      ctx.save();
      ctx.translate(this.x - camX, this.y - camY);
      ctx.rotate(this.heading);

      // Vehicle shadow
      ctx.fillStyle = 'rgba(15, 23, 42, 0.4)';
      ctx.fillRect(-this.length / 2 + 2, -this.width / 2 + 3, this.length, this.width);

      // Body
      ctx.fillStyle = this.color;
      ctx.beginPath();
      ctx.roundRect(-this.length / 2, -this.width / 2, this.length, this.width, 3);
      ctx.fill();

      // Windshield & roof
      ctx.fillStyle = '#0F172A';
      ctx.fillRect(-this.length * 0.15, -this.width * 0.4, this.length * 0.4, this.width * 0.8);

      // Headlights
      ctx.fillStyle = '#FEF08A';
      ctx.fillRect(this.length / 2 - 2, -this.width / 2 + 1, 2, 3);
      ctx.fillRect(this.length / 2 - 2, this.width / 2 - 4, 2, 3);

      // Tail lights
      ctx.fillStyle = '#EF4444';
      ctx.fillRect(-this.length / 2, -this.width / 2 + 1, 2, 3);
      ctx.fillRect(-this.length / 2, this.width / 2 - 4, 2, 3);

      // Emergency roof strobe
      if (this.isEmergency) {
        const strobe = Math.floor(Date.now() / 150) % 2 === 0;
        ctx.fillStyle = strobe ? '#38BDF8' : '#EC4899';
        ctx.beginPath();
        ctx.arc(0, 0, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    }
  }

  // --- Particle FX (Confetti & Dust) ---
  class Particle {
    constructor(x, y, color) {
      this.x = x;
      this.y = y;
      this.color = color;
      const angle = Math.random() * Math.PI * 2;
      const speed = 40 + Math.random() * 120;
      this.vx = Math.cos(angle) * speed;
      this.vy = Math.sin(angle) * speed;
      this.life = 1.0;
      this.decay = 0.9 + Math.random() * 1.5;
      this.size = 3 + Math.random() * 3;
    }
    update(dt) {
      this.x += this.vx * dt;
      this.y += this.vy * dt;
      this.life -= this.decay * dt;
    }
    draw(ctx, camX, camY) {
      if (this.life <= 0) return;
      ctx.save();
      ctx.globalAlpha = Math.max(0, this.life);
      ctx.fillStyle = this.color;
      ctx.fillRect(this.x - camX - this.size / 2, this.y - camY - this.size / 2, this.size, this.size);
      ctx.restore();
    }
  }

  // --- Player Car & Physics ---
  class PlayerCar {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      this.speed = 0;
      this.heading = 0; // Radians
      this.steeringAngle = 0; // Steering wheel degrees (-55 to +55)
      this.gear = 'P'; // 'P', 'R', 'N', 'D'
      this.length = 26;
      this.width = 14;

      // Stats
      this.score = 1000;
      this.violations = 0;
      this.collisionCooldown = 0;
      this.blinker = null; // 'L', 'R', 'HAZARD', null
      this.blinkerTimer = 0;
      this.blinkerState = false;

      // Notification toast
      this.notification = null;
      this.notificationTimer = 0;
      this.notificationColor = '#22C55E';
    }

    notify(text, color = '#22C55E', duration = 3.0) {
      this.notification = text;
      this.notificationColor = color;
      this.notificationTimer = duration;
    }

    update(dt, input, sound) {
      if (this.collisionCooldown > 0) this.collisionCooldown -= dt;
      if (this.notificationTimer > 0) {
        this.notificationTimer -= dt;
        if (this.notificationTimer <= 0) this.notification = null;
      }

      // Blinker flash
      if (this.blinker) {
        this.blinkerTimer += dt;
        if (this.blinkerTimer >= 0.38) {
          this.blinkerTimer = 0;
          this.blinkerState = !this.blinkerState;
          if (this.blinkerState && sound) sound.playBlinker();
        }
      } else {
        this.blinkerState = false;
      }

      // Input steering
      const steerSpeed = 160.0;
      if (input.left) {
        this.steeringAngle = Math.max(-55, this.steeringAngle - steerSpeed * dt);
      } else if (input.right) {
        this.steeringAngle = Math.min(55, this.steeringAngle + steerSpeed * dt);
      } else if (!input.mouseSteering) {
        // Return to center spring
        if (this.steeringAngle > 0) {
          this.steeringAngle = Math.max(0, this.steeringAngle - 180 * dt);
        } else if (this.steeringAngle < 0) {
          this.steeringAngle = Math.min(0, this.steeringAngle + 180 * dt);
        }
      }

      // Acceleration / Brake / Transmission
      const maxForwardSpeed = 145.0;
      const maxReverseSpeed = 65.0;
      const accel = 240.0;
      const brakePower = 420.0;
      const rollingResistance = 50.0;

      if (input.gas) {
        if (this.gear === 'P') this.gear = 'D'; // Auto engage Drive
        if (this.gear === 'D') {
          this.speed = Math.min(maxForwardSpeed, this.speed + accel * dt);
        } else if (this.gear === 'R') {
          this.speed = Math.max(-maxReverseSpeed, this.speed - accel * dt);
        }
      } else if (input.brake) {
        if (this.gear === 'D') {
          if (this.speed > 0) {
            this.speed = Math.max(0, this.speed - brakePower * dt);
          } else {
            // Auto switch to Reverse when stopped and holding brake/down
            this.gear = 'R';
            this.speed = Math.max(-maxReverseSpeed, this.speed - accel * 0.7 * dt);
          }
        } else if (this.gear === 'R') {
          if (this.speed < 0) {
            this.speed = Math.min(0, this.speed + brakePower * dt);
          } else {
            this.gear = 'D';
          }
        } else if (this.gear === 'P' || this.gear === 'N') {
          this.speed = 0;
        }
      } else {
        // Coasting deceleration
        if (this.speed > 0) {
          this.speed = Math.max(0, this.speed - rollingResistance * dt);
        } else if (this.speed < 0) {
          this.speed = Math.min(0, this.speed + rollingResistance * dt);
        }
      }

      if (this.gear === 'P') {
        this.speed = 0;
      }

      // Turning kinematics (Bicycle model)
      if (Math.abs(this.speed) > 1.0) {
        const steerRad = (this.steeringAngle * Math.PI) / 180.0;
        const angularVelocity = (this.speed / 24.0) * Math.sin(steerRad);
        this.heading += angularVelocity * dt;
      }

      // Position update
      this.x += Math.cos(this.heading) * this.speed * dt;
      this.y += Math.sin(this.heading) * this.speed * dt;

      // Bound within canvas bounds
      this.x = Math.max(30, Math.min(CANVAS_WIDTH - 30, this.x));
      this.y = Math.max(30, Math.min(CANVAS_HEIGHT - 30, this.y));

      // Audio engine pitch
      if (sound) {
        sound.updateEngine(this.speed, input.gas);
      }
    }

    draw(ctx, camX, camY) {
      ctx.save();
      ctx.translate(this.x - camX, this.y - camY);
      ctx.rotate(this.heading);

      // Drop shadow
      ctx.fillStyle = 'rgba(15, 23, 42, 0.45)';
      ctx.beginPath();
      ctx.roundRect(-this.length / 2 + 3, -this.width / 2 + 4, this.length, this.width, 4);
      ctx.fill();

      // Front wheels (angled by steering)
      const steerRad = (this.steeringAngle * Math.PI) / 180.0;
      [-this.width / 2 - 1, this.width / 2 + 1].forEach(wy => {
        ctx.save();
        ctx.translate(this.length * 0.32, wy);
        ctx.rotate(steerRad);
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(-4, -1.5, 8, 3);
        ctx.restore();
      });

      // Rear wheels
      [-this.width / 2 - 1, this.width / 2 + 1].forEach(wy => {
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(-this.length * 0.35 - 4, wy - 1.5, 8, 3);
      });

      // Car body (Sport Coupe Yellow)
      ctx.fillStyle = COLOR_PLAYER;
      ctx.beginPath();
      ctx.roundRect(-this.length / 2, -this.width / 2, this.length, this.width, 4);
      ctx.fill();
      ctx.strokeStyle = COLOR_PLAYER_DARK;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Hood racing stripe / accents
      ctx.fillStyle = '#FEF08A';
      ctx.fillRect(-this.length * 0.2, -this.width * 0.15, this.length * 0.6, this.width * 0.3);

      // Windshield & roof
      ctx.fillStyle = '#0F172A';
      ctx.beginPath();
      ctx.roundRect(-this.length * 0.22, -this.width * 0.38, this.length * 0.44, this.width * 0.76, 2);
      ctx.fill();

      // Driver avatar (visible through glass)
      ctx.fillStyle = '#F87171';
      ctx.beginPath();
      ctx.arc(-this.length * 0.05, 0, 3, 0, Math.PI * 2);
      ctx.fill();

      // Headlights
      ctx.fillStyle = '#FEF08A';
      ctx.fillRect(this.length / 2 - 1.5, -this.width / 2 + 1.5, 2, 3);
      ctx.fillRect(this.length / 2 - 1.5, this.width / 2 - 4.5, 2, 3);

      // Tail lights
      ctx.fillStyle = this.speed < 0 ? '#FFFFFF' : '#EF4444';
      ctx.fillRect(-this.length / 2 - 0.5, -this.width / 2 + 1.5, 2, 3);
      ctx.fillRect(-this.length / 2 - 0.5, this.width / 2 - 4.5, 2, 3);

      // Active Blinkers
      if (this.blinkerState) {
        ctx.fillStyle = '#F59E0B';
        if (this.blinker === 'L' || this.blinker === 'HAZARD') {
          ctx.beginPath();
          ctx.arc(this.length / 2, -this.width / 2, 3, 0, Math.PI * 2);
          ctx.arc(-this.length / 2, -this.width / 2, 3, 0, Math.PI * 2);
          ctx.fill();
        }
        if (this.blinker === 'R' || this.blinker === 'HAZARD') {
          ctx.beginPath();
          ctx.arc(this.length / 2, this.width / 2, 3, 0, Math.PI * 2);
          ctx.arc(-this.length / 2, this.width / 2, 3, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      ctx.restore();
    }
  }

  // --- Main Simulation State ---
  class SimulationGame {
    constructor() {
      this.canvas = document.getElementById('gameCanvas');
      this.ctx = this.canvas.getContext('2d');
      this.sound = new SoundEngine();

      this.cameraMode = 'COCKPIT'; // 'COCKPIT', 'FOLLOW', 'OVERVIEW'
      this.camX = 0;
      this.camY = 0;

      // Telemetry
      this.kPenalty = 6.0;
      this.aiLights = true;
      this.showHeatmap = false;
      this.congestion = 0;
      this.avgWait = 0;
      this.efficiency = 96;

      // Inputs
      this.input = {
        gas: false,
        brake: false,
        left: false,
        right: false,
        mouseSteering: false
      };

      // Mouse drag for cockpit controls
      this.dragSteering = false;
      this.dragShifter = false;
      this.steerCenter = { x: 135, y: 730, radius: 70 };

      // World objects
      this.nodes = {};
      this.intersections = {};
      this.edges = [];
      this.perimeterNodes = [];
      this.buildings = [];
      this.trees = [];
      this.streetlights = [];
      this.trafficLights = {};
      this.vehicles = [];
      this.particles = [];

      this.player = new PlayerCar(GRID_OFFSET_X, GRID_OFFSET_Y + 40);
      this.targetBay = null;
      this.playerRoute = [];

      this.lastTime = performance.now();
      this.spawnTimer = 0;

      this._initGraph();
      this._initBuildings();
      this._initTrees();
      this._pickNewTargetBay();
      this._recalculatePlayerRoute();
      this._bindUI();
      this._bindKeyboard();
      this._bindMouseTouch();

      // Start loop
      requestAnimationFrame(this.loop.bind(this));
    }

    _initGraph() {
      let nodeId = 0;
      // 1. Intersections
      for (let r = 0; r < GRID_ROWS; r++) {
        for (let c = 0; c < GRID_COLS; c++) {
          const x = GRID_OFFSET_X + c * CELL_WIDTH;
          const y = GRID_OFFSET_Y + r * CELL_HEIGHT;
          const node = new CityNode(nodeId, x, y, false, [r, c]);
          this.nodes[nodeId] = node;
          this.intersections[`${r},${c}`] = node;
          this.trafficLights[nodeId] = new TrafficLight(node);
          nodeId++;
        }
      }

      // 2. Perimeter Entry/Exit nodes
      const perimDist = 85;
      for (let c = 0; c < GRID_COLS; c++) {
        const x = GRID_OFFSET_X + c * CELL_WIDTH;
        const topNode = new CityNode(nodeId++, x, GRID_OFFSET_Y - perimDist, true);
        const botNode = new CityNode(nodeId++, x, GRID_OFFSET_Y + (GRID_ROWS - 1) * CELL_HEIGHT + perimDist, true);
        this.nodes[topNode.id] = topNode;
        this.nodes[botNode.id] = botNode;
        this.perimeterNodes.push(topNode, botNode);
      }
      for (let r = 0; r < GRID_ROWS; r++) {
        const y = GRID_OFFSET_Y + r * CELL_HEIGHT;
        const leftNode = new CityNode(nodeId++, GRID_OFFSET_X - perimDist, y, true);
        const rightNode = new CityNode(nodeId++, GRID_OFFSET_X + (GRID_COLS - 1) * CELL_WIDTH + perimDist, y, true);
        this.nodes[leftNode.id] = leftNode;
        this.nodes[rightNode.id] = rightNode;
        this.perimeterNodes.push(leftNode, rightNode);
      }

      // 3. Connect internal grid
      for (let r = 0; r < GRID_ROWS; r++) {
        for (let c = 0; c < GRID_COLS; c++) {
          const curr = this.intersections[`${r},${c}`];
          if (c < GRID_COLS - 1) {
            const right = this.intersections[`${r},${c + 1}`];
            this._createBiEdges(curr, right);
          }
          if (r < GRID_ROWS - 1) {
            const down = this.intersections[`${r + 1},${c}`];
            this._createBiEdges(curr, down);
          }
        }
      }

      // 4. Connect perimeter
      for (let c = 0; c < GRID_COLS; c++) {
        const topP = this.perimeterNodes.find(n => Math.abs(n.x - (GRID_OFFSET_X + c * CELL_WIDTH)) < 5 && n.y < GRID_OFFSET_Y);
        const topI = this.intersections[`0,${c}`];
        if (topP && topI) this._createBiEdges(topP, topI);

        const botP = this.perimeterNodes.find(n => Math.abs(n.x - (GRID_OFFSET_X + c * CELL_WIDTH)) < 5 && n.y > GRID_OFFSET_Y + 100);
        const botI = this.intersections[`${GRID_ROWS - 1},${c}`];
        if (botP && botI) this._createBiEdges(botI, botP);
      }
      for (let r = 0; r < GRID_ROWS; r++) {
        const leftP = this.perimeterNodes.find(n => Math.abs(n.y - (GRID_OFFSET_Y + r * CELL_HEIGHT)) < 5 && n.x < GRID_OFFSET_X);
        const leftI = this.intersections[`${r},0`];
        if (leftP && leftI) this._createBiEdges(leftP, leftI);

        const rightP = this.perimeterNodes.find(n => Math.abs(n.y - (GRID_OFFSET_Y + r * CELL_HEIGHT)) < 5 && n.x > GRID_OFFSET_X + 100);
        const rightI = this.intersections[`${r},${GRID_COLS - 1}`];
        if (rightP && rightI) this._createBiEdges(rightI, rightP);
      }
    }

    _createBiEdges(nodeA, nodeB) {
      const eAB = new RoadEdge(nodeA, nodeB);
      nodeA.outgoing.push(eAB);
      nodeB.incoming.push(eAB);
      this.edges.push(eAB);

      const eBA = new RoadEdge(nodeB, nodeA);
      nodeB.outgoing.push(eBA);
      nodeA.incoming.push(eBA);
      this.edges.push(eBA);
    }

    _initBuildings() {
      const inset = ROAD_WIDTH / 2 + 10;
      let pIdx = 0;
      for (let r = 0; r < GRID_ROWS - 1; r++) {
        for (let c = 0; c < GRID_COLS - 1; c++) {
          const tl = this.intersections[`${r},${c}`];
          const br = this.intersections[`${r + 1},${c + 1}`];
          const bx = tl.x + inset;
          const by = tl.y + inset;
          const bw = br.x - inset - bx;
          const bh = br.y - inset - by;
          const palette = BUILDING_PALETTES[pIdx % BUILDING_PALETTES.length];
          this.buildings.push({ x: bx, y: by, w: bw, h: bh, palette, helipad: (r + c) % 2 === 0 });
          pIdx++;
        }
      }
    }

    _initTrees() {
      for (const b of this.buildings) {
        // Place stylized trees at sidewalks
        this.trees.push({ x: b.x - 7, y: b.y + 16, r: 9 });
        this.trees.push({ x: b.x + b.w + 7, y: b.y + b.h - 16, r: 9 });
        this.trees.push({ x: b.x + 20, y: b.y - 7, r: 8 });
      }
    }

    _pickNewTargetBay() {
      // Pick a random internal road edge
      const candidates = this.edges.filter(e => !e.from.isPerimeter && !e.to.isPerimeter);
      const edge = candidates[Math.floor(Math.random() * candidates.length)] || this.edges[0];
      const t = 0.4 + Math.random() * 0.2;
      this.targetBay = {
        x: edge.start.x + (edge.end.x - edge.start.x) * t,
        y: edge.start.y + (edge.end.y - edge.start.y) * t,
        angle: edge.angle,
        edge: edge,
        node: edge.to,
        w: 38,
        h: 22
      };
      this.player.notify('NEW TARGET PARKING BAY LOCATED!', '#22C55E', 3.0);
    }

    _findDynamicAStar(startNode, goalNode, isEmergency = false) {
      if (!startNode || !goalNode || startNode === goalNode) return [startNode];
      const openSet = new MinHeap();
      const gScores = {};
      const cameFrom = {};

      gScores[startNode.id] = 0;
      openSet.push({ node: startNode, f: 0, path: [startNode] });

      while (!openSet.isEmpty()) {
        const currentItem = openSet.pop();
        const current = currentItem.node;
        const currentPath = currentItem.path;

        if (current === goalNode) {
          return currentPath;
        }

        for (const edge of current.outgoing) {
          const neighbor = edge.to;
          if (currentPath.length >= 2 && neighbor === currentPath[currentPath.length - 2] && current.outgoing.length > 1) {
            continue;
          }

          const edgeCost = edge.getDynamicCost(this.kPenalty, isEmergency);
          const tentativeG = gScores[current.id] + edgeCost;

          if (gScores[neighbor.id] === undefined || tentativeG < gScores[neighbor.id]) {
            gScores[neighbor.id] = tentativeG;
            const h = Math.hypot(neighbor.x - goalNode.x, neighbor.y - goalNode.y);
            const totalF = tentativeG + h;
            openSet.push({ node: neighbor, f: totalF, path: currentPath.concat([neighbor]) });
          }
        }
      }
      return [startNode, goalNode];
    }

    _recalculatePlayerRoute() {
      if (!this.targetBay) return;
      // Find closest node to player
      let closestNode = null;
      let minDist = Infinity;
      Object.values(this.nodes).forEach(n => {
        const d = Math.hypot(n.x - this.player.x, n.y - this.player.y);
        if (d < minDist) {
          minDist = d;
          closestNode = n;
        }
      });
      if (closestNode) {
        this.playerRoute = this._findDynamicAStar(closestNode, this.targetBay.node, false);
      }
    }

    spawnAICar(isEmergency = false) {
      if (this.perimeterNodes.length < 2) return;
      const start = this.perimeterNodes[Math.floor(Math.random() * this.perimeterNodes.length)];
      const farCandidates = this.perimeterNodes.filter(n => Math.hypot(n.x - start.x, n.y - start.y) > 300);
      const goal = farCandidates[Math.floor(Math.random() * farCandidates.length)] || start;

      const path = this._findDynamicAStar(start, goal, isEmergency);
      if (path && path.length >= 2) {
        const car = new Vehicle(this.vehicles.length + 1, path, isEmergency);
        if (car.currentEdge) {
          car.currentEdge.vehicles.push(car);
          this.vehicles.push(car);
          if (isEmergency && this.sound) this.sound.playSiren();
        }
      }
    }

    _bindUI() {
      const btnCamera = document.getElementById('btn-camera');
      const camLabel = document.getElementById('camera-label');
      btnCamera.addEventListener('click', () => {
        this.sound.init();
        if (this.cameraMode === 'COCKPIT') {
          this.cameraMode = 'FOLLOW';
          camLabel.textContent = 'Follow Cam';
        } else if (this.cameraMode === 'FOLLOW') {
          this.cameraMode = 'OVERVIEW';
          camLabel.textContent = 'City Overview';
        } else {
          this.cameraMode = 'COCKPIT';
          camLabel.textContent = 'Cockpit';
        }
      });

      const btnAudio = document.getElementById('btn-audio');
      const audioIcon = document.getElementById('audio-icon');
      btnAudio.addEventListener('click', () => {
        this.sound.init();
        const muted = this.sound.toggleMute();
        audioIcon.textContent = muted ? '🔇' : '🔊';
      });

      const drawer = document.getElementById('command-drawer');
      const btnDrawerToggle = document.getElementById('btn-drawer-toggle');
      const btnDrawerClose = document.getElementById('btn-drawer-close');
      const toggleDrawer = () => drawer.classList.toggle('open');
      btnDrawerToggle.addEventListener('click', toggleDrawer);
      btnDrawerClose.addEventListener('click', toggleDrawer);

      const modal = document.getElementById('help-modal');
      const btnHelp = document.getElementById('btn-help');
      const btnModalClose = document.getElementById('btn-modal-close');
      const btnModalGotIt = document.getElementById('btn-modal-got-it');
      btnHelp.addEventListener('click', () => modal.classList.add('open'));
      btnModalClose.addEventListener('click', () => modal.classList.remove('open'));
      btnModalGotIt.addEventListener('click', () => modal.classList.remove('open'));

      const kSlider = document.getElementById('k-slider');
      const kValDisplay = document.getElementById('k-val-display');
      kSlider.addEventListener('input', (e) => {
        this.kPenalty = parseFloat(e.target.value);
        kValDisplay.textContent = this.kPenalty.toFixed(1);
        this._recalculatePlayerRoute();
      });

      document.getElementById('btn-spawn-car').addEventListener('click', () => {
        this.sound.init();
        this.spawnAICar(false);
      });

      document.getElementById('btn-spawn-ambulance').addEventListener('click', () => {
        this.sound.init();
        this.spawnAICar(true);
        this.player.notify('EMERGENCY AMBULANCE DISPATCHED!', '#EC4899', 3.5);
      });

      const btnHeatmap = document.getElementById('btn-toggle-heatmap');
      btnHeatmap.addEventListener('click', () => {
        this.showHeatmap = !this.showHeatmap;
        btnHeatmap.innerHTML = `<span>🔥</span> Heatmap: ${this.showHeatmap ? 'ON' : 'OFF'}`;
        btnHeatmap.classList.toggle('active', this.showHeatmap);
      });

      const btnLights = document.getElementById('btn-toggle-lights');
      btnLights.addEventListener('click', () => {
        this.aiLights = !this.aiLights;
        Object.values(this.trafficLights).forEach(tl => tl.automated = this.aiLights);
        btnLights.innerHTML = `<span>🚦</span> AI Lights: ${this.aiLights ? 'ON' : 'OFF'}`;
        btnLights.classList.toggle('active', this.aiLights);
      });

      document.getElementById('btn-reroute').addEventListener('click', () => {
        this.sound.init();
        this._recalculatePlayerRoute();
        this.player.notify('GPS ROUTE RECALCULATED VIA DYNAMIC A*', '#06B6D4', 2.5);
      });

      document.getElementById('btn-reset-game').addEventListener('click', () => {
        this.player = new PlayerCar(GRID_OFFSET_X, GRID_OFFSET_Y + 40);
        this._pickNewTargetBay();
        this._recalculatePlayerRoute();
      });
    }

    _bindKeyboard() {
      window.addEventListener('keydown', (e) => {
        this.sound.init();
        switch (e.code) {
          case 'KeyW':
          case 'ArrowUp':
            this.input.gas = true;
            break;
          case 'KeyS':
          case 'ArrowDown':
            this.input.brake = true;
            break;
          case 'KeyA':
          case 'ArrowLeft':
            this.input.left = true;
            break;
          case 'KeyD':
          case 'ArrowRight':
            this.input.right = true;
            break;
          case 'KeyP':
            this.player.gear = this.player.gear === 'P' ? 'D' : 'P';
            break;
          case 'KeyH':
            this.sound.playHorn();
            break;
          case 'KeyV':
            document.getElementById('btn-camera').click();
            break;
          case 'KeyQ':
            document.getElementById('btn-reroute').click();
            break;
          case 'KeyZ':
            this.player.blinker = this.player.blinker === 'L' ? null : 'L';
            break;
          case 'KeyC':
            this.player.blinker = this.player.blinker === 'R' ? null : 'R';
            break;
          case 'KeyX':
            this.player.blinker = this.player.blinker === 'HAZARD' ? null : 'HAZARD';
            break;
          case 'Tab':
            e.preventDefault();
            document.getElementById('btn-drawer-toggle').click();
            break;
        }
      });

      window.addEventListener('keyup', (e) => {
        switch (e.code) {
          case 'KeyW':
          case 'ArrowUp':
            this.input.gas = false;
            break;
          case 'KeyS':
          case 'ArrowDown':
            this.input.brake = false;
            break;
          case 'KeyA':
          case 'ArrowLeft':
            this.input.left = false;
            break;
          case 'KeyD':
          case 'ArrowRight':
            this.input.right = false;
            break;
        }
      });
    }

    _bindMouseTouch() {
      const getCanvasPos = (evt) => {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
        const clientY = evt.touches ? evt.touches[0].clientY : evt.clientY;
        return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
      };

      const handleDown = (evt) => {
        this.sound.init();
        const pos = getCanvasPos(evt);

        // Check Steering Wheel
        const distToWheel = Math.hypot(pos.x - this.steerCenter.x, pos.y - this.steerCenter.y);
        if (distToWheel <= this.steerCenter.radius + 15) {
          if (distToWheel < 24) {
            // Center horn
            this.sound.playHorn();
          } else {
            this.dragSteering = true;
            this.input.mouseSteering = true;
          }
          return;
        }

        // Check Pedals
        // Brake pedal: (1065, 715, 74, 90)
        if (pos.x >= 1065 && pos.x <= 1139 && pos.y >= 715 && pos.y <= 805) {
          this.input.brake = true;
          return;
        }
        // Gas pedal: (1155, 680, 56, 125)
        if (pos.x >= 1155 && pos.x <= 1211 && pos.y >= 680 && pos.y <= 805) {
          this.input.gas = true;
          return;
        }

        // Check Shifter slots (1005, 665, 46, 165)
        if (pos.x >= 995 && pos.x <= 1055 && pos.y >= 665 && pos.y <= 830) {
          const slotH = 165 / 4;
          const slotIdx = Math.floor((pos.y - 665) / slotH);
          const gears = ['P', 'R', 'N', 'D'];
          if (gears[slotIdx]) {
            this.player.gear = gears[slotIdx];
            this.sound.playBlinker();
          }
          return;
        }

        // Check GPS Tablet click to reroute
        if (pos.x >= 470 && pos.x <= 790 && pos.y >= 660 && pos.y <= 840) {
          this._recalculatePlayerRoute();
          this.player.notify('GPS ROUTE RECALCULATED VIA DYNAMIC A*', '#06B6D4', 2.0);
          return;
        }
      };

      const handleMove = (evt) => {
        if (!this.dragSteering) return;
        const pos = getCanvasPos(evt);
        const dx = pos.x - this.steerCenter.x;
        const dy = pos.y - this.steerCenter.y;
        const angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;
        // Map angle to steer angle
        this.player.steeringAngle = Math.max(-55, Math.min(55, angleDeg - 90));
      };

      const handleUp = () => {
        this.dragSteering = false;
        this.input.mouseSteering = false;
        this.input.gas = false;
        this.input.brake = false;
      };

      this.canvas.addEventListener('mousedown', handleDown);
      window.addEventListener('mousemove', handleMove);
      window.addEventListener('mouseup', handleUp);

      this.canvas.addEventListener('touchstart', (e) => { e.preventDefault(); handleDown(e); }, { passive: false });
      window.addEventListener('touchmove', (e) => { handleMove(e); }, { passive: false });
      window.addEventListener('touchend', handleUp);
    }

    loop(timestamp) {
      const dt = Math.min(0.1, (timestamp - this.lastTime) / 1000);
      this.lastTime = timestamp;

      this.update(dt);
      this.draw();

      requestAnimationFrame(this.loop.bind(this));
    }

    update(dt) {
      // 1. Spawner
      this.spawnTimer += dt;
      if (this.spawnTimer >= 2.5 && this.vehicles.length < 18) {
        this.spawnTimer = 0;
        this.spawnAICar(Math.random() < 0.15);
      }

      // 2. Traffic signals
      const emergencyCar = this.vehicles.find(v => v.isEmergency);
      Object.values(this.trafficLights).forEach(tl => {
        let nearbyEmerg = null;
        if (emergencyCar && Math.hypot(emergencyCar.x - tl.node.x, emergencyCar.y - tl.node.y) < 220) {
          nearbyEmerg = emergencyCar;
        }
        tl.update(dt, nearbyEmerg);
      });

      // 3. Vehicles
      this.edges.forEach(e => e.vehicles = []);
      for (let i = this.vehicles.length - 1; i >= 0; i--) {
        const v = this.vehicles[i];
        v.update(dt, this, this.trafficLights);
        if (v.finished) {
          this.vehicles.splice(i, 1);
        } else if (v.currentEdge) {
          v.currentEdge.vehicles.push(v);
        }
      }
      this.edges.forEach(e => e.updateDensity());

      // 4. Player update
      this.player.update(dt, this.input, this.sound);

      // Check collisions with AI cars
      if (this.player.collisionCooldown <= 0) {
        for (const v of this.vehicles) {
          const dist = Math.hypot(v.x - this.player.x, v.y - this.player.y);
          if (dist < 18) {
            this.player.score = Math.max(0, this.player.score - 50);
            this.player.speed *= -0.5;
            this.player.collisionCooldown = 1.0;
            this.sound.playBuzzer();
            this.player.notify('COLLISION PENALTY: -50 PTS', '#EF4444', 2.0);
            // Spawn debris particles
            for (let p = 0; p < 12; p++) {
              this.particles.push(new Particle(this.player.x, this.player.y, '#FACC15'));
            }
            break;
          }
        }
      }

      // Check Target Parking Bay arrival
      if (this.targetBay) {
        const distToBay = Math.hypot(this.targetBay.x - this.player.x, this.targetBay.y - this.player.y);
        if (distToBay < 28 && Math.abs(this.player.speed) < 6.0 && this.player.gear === 'P') {
          // PERFECT PARK!
          this.sound.playFanfare();
          this.player.score += 500;
          this.player.notify('PERFECT PARK! ★★★ (+500 PTS)', '#22C55E', 4.0);
          // Confetti celebration
          for (let p = 0; p < 60; p++) {
            const colors = ['#22C55E', '#FACC15', '#38BDF8', '#EC4899', '#A855F7'];
            this.particles.push(new Particle(this.player.x, this.player.y, colors[p % colors.length]));
          }
          this._pickNewTargetBay();
          this._recalculatePlayerRoute();
        }
      }

      // 5. Particles
      for (let i = this.particles.length - 1; i >= 0; i--) {
        this.particles[i].update(dt);
        if (this.particles[i].life <= 0) this.particles.splice(i, 1);
      }

      // 6. Camera smooth tracking
      if (this.cameraMode === 'COCKPIT' || this.cameraMode === 'FOLLOW') {
        const lookahead = this.cameraMode === 'COCKPIT' ? 30 : 50;
        const targetCamX = this.player.x + Math.cos(this.player.heading) * lookahead - CANVAS_WIDTH / 2;
        const targetCamY = this.player.y + Math.sin(this.player.heading) * lookahead - CANVAS_HEIGHT / 2;
        this.camX += (targetCamX - this.camX) * 0.1;
        this.camY += (targetCamY - this.camY) * 0.1;
      } else {
        // City Overview
        this.camX += (0 - this.camX) * 0.1;
        this.camY += (0 - this.camY) * 0.1;
      }

      // 7. Update Telemetry displays
      const totalVehicles = this.vehicles.length;
      const slowVehicles = this.vehicles.filter(v => v.speed < 12).length;
      this.congestion = Math.round((slowVehicles / (totalVehicles || 1)) * 100);
      this.efficiency = Math.max(20, Math.min(100, 100 - Math.round(this.congestion * 0.8)));
      this.avgWait = (this.vehicles.reduce((acc, v) => acc + v.waitTime, 0) / (totalVehicles || 1)).toFixed(1);

      document.getElementById('hdr-speed').textContent = `${Math.round(Math.abs(this.player.speed) * 0.45)} MPH`;
      document.getElementById('hdr-gear').textContent = this.player.gear;
      document.getElementById('hdr-congestion').textContent = `${this.congestion}%`;
      document.getElementById('hdr-score').textContent = this.player.score.toLocaleString();

      document.getElementById('drawer-efficiency-val').textContent = `${this.efficiency}%`;
      document.getElementById('drawer-wait-val').textContent = `${this.avgWait}s`;
      document.getElementById('efficiency-progress-bar').style.width = `${this.efficiency}%`;
      document.getElementById('drawer-congestion-val').textContent = `${this.congestion}%`;
      document.getElementById('congestion-progress-bar').style.width = `${this.congestion}%`;
      document.getElementById('drawer-vehicle-count').textContent = totalVehicles;
      document.getElementById('drawer-bottlenecks').textContent = this.edges.filter(e => e.queueDensity > 2).length;
    }

    draw() {
      const ctx = this.ctx;
      const camX = this.camX;
      const camY = this.camY;

      ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

      // 1. Manicured lawn grass striping
      const stripeH = 38;
      for (let y = 0; y < CANVAS_HEIGHT + stripeH; y += stripeH) {
        ctx.fillStyle = (Math.floor(y / stripeH) % 2 === 0) ? COLOR_GRASS_BASE : COLOR_GRASS_STRIPE;
        ctx.fillRect(0, y, CANVAS_WIDTH, stripeH);
      }

      // 2. Sidewalk pavers and shadows around buildings
      for (const b of this.buildings) {
        // Sidewalk curb
        ctx.fillStyle = COLOR_SIDEWALK_CURB;
        ctx.beginPath();
        ctx.roundRect(b.x - 14 - camX, b.y - 14 - camY, b.w + 28, b.h + 28, 10);
        ctx.fill();

        // Sidewalk surface
        ctx.fillStyle = COLOR_SIDEWALK;
        ctx.beginPath();
        ctx.roundRect(b.x - 12 - camX, b.y - 12 - camY, b.w + 24, b.h + 24, 8);
        ctx.fill();

        // Ambient building drop shadow
        ctx.fillStyle = 'rgba(15, 23, 42, 0.35)';
        ctx.beginPath();
        ctx.roundRect(b.x + 6 - camX, b.y + 8 - camY, b.w, b.h, 8);
        ctx.fill();
      }

      // 3. Roads & Asphalt
      const drawnEdges = new Set();
      for (const edge of this.edges) {
        const pairKey = [edge.from.id, edge.to.id].sort().join('-');
        if (drawnEdges.has(pairKey)) continue;
        drawnEdges.add(pairKey);

        const x1 = edge.from.x - camX;
        const y1 = edge.from.y - camY;
        const x2 = edge.to.x - camX;
        const y2 = edge.to.y - camY;

        // White border
        ctx.strokeStyle = COLOR_ROAD_BORDER;
        ctx.lineWidth = ROAD_WIDTH + 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();

        // Dark slate asphalt
        ctx.strokeStyle = COLOR_ROAD;
        ctx.lineWidth = ROAD_WIDTH;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();

        // Dashed center divider line
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 8]);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 4. Intersections & Zebra crosswalks
      Object.values(this.intersections).forEach(node => {
        const nx = node.x - camX;
        const ny = node.y - camY;
        const halfR = ROAD_WIDTH / 2;

        ctx.fillStyle = '#2C384A';
        ctx.fillRect(nx - halfR - 2, ny - halfR - 2, ROAD_WIDTH + 4, ROAD_WIDTH + 4);

        // Zebra stripes on 4 sides
        ctx.fillStyle = '#FFFFFF';
        for (let i = -halfR + 3; i < halfR - 2; i += 7) {
          ctx.fillRect(nx + i, ny - halfR - 7, 4, 6); // North
          ctx.fillRect(nx + i, ny + halfR + 1, 4, 6); // South
          ctx.fillRect(nx - halfR - 7, ny + i, 6, 4); // West
          ctx.fillRect(nx + halfR + 1, ny + i, 6, 4); // East
        }
      });

      // 5. Congestion Heatmap Overlay (if toggled)
      if (this.showHeatmap) {
        for (const edge of this.edges) {
          if (edge.queueDensity > 0) {
            ctx.strokeStyle = edge.queueDensity >= 3 ? 'rgba(239, 68, 68, 0.55)' : 'rgba(245, 158, 11, 0.45)';
            ctx.lineWidth = ROAD_WIDTH - 4;
            ctx.beginPath();
            ctx.moveTo(edge.start.x - camX, edge.start.y - camY);
            ctx.lineTo(edge.end.x - camX, edge.end.y - camY);
            ctx.stroke();
          }
        }
      }

      // 6. Dynamic A* GPS Path Overlay (glowing cyan line)
      if (this.playerRoute && this.playerRoute.length > 1) {
        ctx.save();
        ctx.strokeStyle = COLOR_CYAN_GLOW;
        ctx.lineWidth = 4;
        ctx.shadowColor = COLOR_CYAN_GLOW;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.moveTo(this.player.x - camX, this.player.y - camY);
        for (const n of this.playerRoute) {
          ctx.lineTo(n.x - camX, n.y - camY);
        }
        if (this.targetBay) {
          ctx.lineTo(this.targetBay.x - camX, this.targetBay.y - camY);
        }
        ctx.stroke();
        ctx.restore();
      }

      // 7. Glowing Green Target Parking Bay
      if (this.targetBay) {
        ctx.save();
        ctx.translate(this.targetBay.x - camX, this.targetBay.y - camY);
        ctx.rotate(this.targetBay.angle);

        // Green translucent fill
        ctx.fillStyle = 'rgba(34, 197, 94, 0.28)';
        ctx.fillRect(-this.targetBay.w / 2, -this.targetBay.h / 2, this.targetBay.w, this.targetBay.h);

        // Animated dashed neon border
        const dashOffset = (Date.now() / 60) % 16;
        ctx.strokeStyle = COLOR_PARK_GREEN;
        ctx.lineWidth = 2.5;
        ctx.setLineDash([8, 8]);
        ctx.lineDashOffset = -dashOffset;
        ctx.strokeRect(-this.targetBay.w / 2, -this.targetBay.h / 2, this.targetBay.w, this.targetBay.h);
        ctx.setLineDash([]);

        // Painted tarmac stencil: "PARK HERE"
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '700 9px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('PARK HERE', 0, 0);

        // Floating pulsating beacon
        const pulse = 1.0 + Math.sin(Date.now() / 200) * 0.2;
        ctx.strokeStyle = '#FACC15';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, 16 * pulse, 0, Math.PI * 2);
        ctx.stroke();

        ctx.restore();
      }

      // 8. 3D Buildings & Rooftops
      for (const b of this.buildings) {
        const bx = b.x - camX;
        const by = b.y - camY;

        // Base facade
        ctx.fillStyle = b.palette.base;
        ctx.beginPath();
        ctx.roundRect(bx, by, b.w, b.h, 6);
        ctx.fill();

        // 3D Roof
        ctx.fillStyle = b.palette.roof;
        ctx.beginPath();
        ctx.roundRect(bx + 3, by - 3, b.w - 6, b.h - 6, 6);
        ctx.fill();
        ctx.strokeStyle = b.palette.edge;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Windows
        ctx.fillStyle = '#FEF08A';
        for (let wx = bx + 12; wx < bx + b.w - 14; wx += 22) {
          for (let wy = by + 10; wy < by + b.h - 14; wy += 24) {
            ctx.fillRect(wx, wy, 8, 12);
          }
        }

        // Rooftop Helipad
        if (b.helipad && b.w > 60 && b.h > 60) {
          ctx.strokeStyle = '#F1F5F9';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(bx + b.w / 2, by + b.h / 2 - 3, 16, 0, Math.PI * 2);
          ctx.stroke();
          ctx.fillStyle = '#F1F5F9';
          ctx.font = '800 16px Outfit, sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('H', bx + b.w / 2, by + b.h / 2 - 3);
        }
      }

      // 9. Street Trees
      for (const tree of this.trees) {
        const tx = tree.x - camX;
        const ty = tree.y - camY;

        // Drop shadow
        ctx.fillStyle = 'rgba(15, 23, 42, 0.35)';
        ctx.beginPath();
        ctx.arc(tx + 2, ty + 3, tree.r, 0, Math.PI * 2);
        ctx.fill();

        // Dark layered canopy
        ctx.fillStyle = '#2F855A';
        ctx.beginPath();
        ctx.arc(tx, ty, tree.r, 0, Math.PI * 2);
        ctx.fill();

        // Light top highlight
        ctx.fillStyle = '#48BB78';
        ctx.beginPath();
        ctx.arc(tx - 1.5, ty - 2, tree.r * 0.65, 0, Math.PI * 2);
        ctx.fill();
      }

      // 10. Traffic Light Signals
      Object.values(this.trafficLights).forEach(tl => {
        const lx = tl.node.x - camX;
        const ly = tl.node.y - camY;

        // 4-phase traffic light box
        const ewColor = tl.state === 'EW_GREEN' ? COLOR_GREEN_LIGHT : (tl.state === 'EW_YELLOW' ? COLOR_YELLOW_LIGHT : COLOR_RED_LIGHT);
        const nsColor = tl.state === 'NS_GREEN' ? COLOR_GREEN_LIGHT : (tl.state === 'NS_YELLOW' ? COLOR_YELLOW_LIGHT : COLOR_RED_LIGHT);

        // East-West light bulb
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(lx - 22, ly - 7, 8, 14);
        ctx.fillStyle = ewColor;
        ctx.shadowColor = ewColor;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(lx - 18, ly, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // North-South light bulb
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(lx - 7, ly - 22, 14, 8);
        ctx.fillStyle = nsColor;
        ctx.shadowColor = nsColor;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(lx, ly - 18, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // 11. AI Vehicles
      for (const v of this.vehicles) {
        v.draw(ctx, camX, camY);
      }

      // 12. Player Car
      this.player.draw(ctx, camX, camY);

      // 13. Particles
      for (const p of this.particles) {
        p.draw(ctx, camX, camY);
      }

      // 14. HUD Overlay & Cockpit
      this.drawCockpitHUD(ctx);
    }

    drawCockpitHUD(ctx) {
      // Notification Alert Banner
      if (this.player.notification) {
        ctx.save();
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.strokeStyle = this.player.notificationColor;
        ctx.lineWidth = 2;
        const toastW = 460;
        const toastH = 46;
        const toastX = (CANVAS_WIDTH - toastW) / 2;
        ctx.beginPath();
        ctx.roundRect(toastX, 75, toastW, toastH, 10);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = this.player.notificationColor;
        ctx.font = '700 15px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.player.notification, CANVAS_WIDTH / 2, 75 + toastH / 2);
        ctx.restore();
      }

      // --- Vehicle Masters Cockpit Controls ---
      // Bottom Cockpit Console Bezel
      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.fillRect(0, 640, CANVAS_WIDTH, 220);
      ctx.strokeStyle = 'rgba(71, 85, 105, 0.5)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, 640);
      ctx.lineTo(CANVAS_WIDTH, 640);
      ctx.stroke();

      // 1. Interactive Rotating Steering Wheel (Bottom-Left)
      const sw = this.steerCenter;
      ctx.save();
      ctx.translate(sw.x, sw.y);
      ctx.rotate((this.player.steeringAngle * Math.PI) / 180.0);

      // Outer rim
      ctx.strokeStyle = '#1E293B';
      ctx.lineWidth = 16;
      ctx.beginPath();
      ctx.arc(0, 0, sw.radius, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = '#FACC15';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(0, 0, sw.radius + 6, 0, Math.PI * 2);
      ctx.stroke();

      // 3 Spokes
      ctx.fillStyle = '#475569';
      [0, (Math.PI * 2) / 3, (Math.PI * 4) / 3].forEach(angle => {
        ctx.save();
        ctx.rotate(angle);
        ctx.fillRect(-sw.radius + 8, -6, sw.radius - 16, 12);
        ctx.restore();
      });

      // Center Hub (Clickable Horn)
      ctx.fillStyle = '#0F172A';
      ctx.beginPath();
      ctx.arc(0, 0, 24, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#38BDF8';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.font = '800 12px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('HORN', 0, 0);

      ctx.restore();

      // Steering Label
      ctx.fillStyle = '#94A3B8';
      ctx.font = '600 11px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`STEER: ${Math.round(this.player.steeringAngle)}°`, sw.x, sw.y + sw.radius + 24);

      // 2. Center Console: GPS Navigation Tablet (470, 660, 320, 180)
      ctx.save();
      const tabX = 470, tabY = 660, tabW = 320, tabH = 180;
      // Tablet frame
      ctx.fillStyle = '#0F172A';
      ctx.beginPath();
      ctx.roundRect(tabX, tabY, tabW, tabH, 12);
      ctx.fill();
      ctx.strokeStyle = '#38BDF8';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Tablet screen
      ctx.fillStyle = '#1E293B';
      ctx.beginPath();
      ctx.roundRect(tabX + 8, tabY + 8, tabW - 16, tabH - 16, 8);
      ctx.fill();

      // Tablet header
      ctx.fillStyle = '#38BDF8';
      ctx.font = '700 12px Outfit, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('⚡ DYNAMIC A* GPS TABLET', tabX + 16, tabY + 28);
      ctx.fillStyle = '#94A3B8';
      ctx.font = '500 10px JetBrains Mono, monospace';
      ctx.fillText('Click to Reroute', tabX + 215, tabY + 28);

      // Speedometer & Gear display inside tablet
      const mph = Math.round(Math.abs(this.player.speed) * 0.45);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '800 36px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(mph.toString(), tabX + tabW / 2, tabY + 88);

      ctx.fillStyle = '#94A3B8';
      ctx.font = '600 11px JetBrains Mono, monospace';
      ctx.fillText('MPH', tabX + tabW / 2, tabY + 112);

      // Speedometer curved progress arc
      const speedPct = Math.min(1.0, Math.abs(this.player.speed) / 145);
      ctx.strokeStyle = 'rgba(71, 85, 105, 0.4)';
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(tabX + tabW / 2, tabY + 85, 48, Math.PI * 0.8, Math.PI * 2.2);
      ctx.stroke();

      ctx.strokeStyle = mph > 45 ? '#EF4444' : (mph > 25 ? '#F59E0B' : '#06B6D4');
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(tabX + tabW / 2, tabY + 85, 48, Math.PI * 0.8, Math.PI * (0.8 + 1.4 * speedPct));
      ctx.stroke();

      // Blinker indicators on tablet
      ctx.fillStyle = (this.player.blinker === 'L' || this.player.blinker === 'HAZARD') && this.player.blinkerState ? '#F59E0B' : '#334155';
      ctx.beginPath();
      ctx.moveTo(tabX + 60, tabY + 85);
      ctx.lineTo(tabX + 75, tabY + 75);
      ctx.lineTo(tabX + 75, tabY + 95);
      ctx.fill();

      ctx.fillStyle = (this.player.blinker === 'R' || this.player.blinker === 'HAZARD') && this.player.blinkerState ? '#F59E0B' : '#334155';
      ctx.beginPath();
      ctx.moveTo(tabX + tabW - 60, tabY + 85);
      ctx.lineTo(tabX + tabW - 75, tabY + 75);
      ctx.lineTo(tabX + tabW - 75, tabY + 95);
      ctx.fill();

      // Mission distance status
      if (this.targetBay) {
        const d = Math.round(Math.hypot(this.targetBay.x - this.player.x, this.targetBay.y - this.player.y));
        ctx.fillStyle = '#4ADE80';
        ctx.font = '600 12px Outfit, sans-serif';
        ctx.fillText(`TARGET BAY: ${d}m AHEAD • GEAR: [${this.player.gear}]`, tabX + tabW / 2, tabY + 152);
      }

      ctx.restore();

      // 3. PRND Transmission Shifter (Bottom-Right: 1005, 665, 46, 165)
      const sx = 1005, sy = 665, swidth = 46, sheight = 165;
      ctx.fillStyle = '#0F172A';
      ctx.beginPath();
      ctx.roundRect(sx, sy, swidth, sheight, 8);
      ctx.fill();
      ctx.strokeStyle = '#475569';
      ctx.stroke();

      const gears = ['P', 'R', 'N', 'D'];
      const slotH = sheight / 4;
      gears.forEach((g, idx) => {
        const slotY = sy + idx * slotH;
        const isActive = this.player.gear === g;
        if (isActive) {
          ctx.fillStyle = g === 'P' ? '#EF4444' : (g === 'R' ? '#F59E0B' : '#22C55E');
          ctx.beginPath();
          ctx.roundRect(sx + 4, slotY + 4, swidth - 8, slotH - 8, 6);
          ctx.fill();
          ctx.fillStyle = '#FFFFFF';
        } else {
          ctx.fillStyle = '#94A3B8';
        }
        ctx.font = '800 16px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(g, sx + swidth / 2, slotY + slotH / 2);
      });

      // 4. Brake Pedal (1065, 715, 74, 90) & Gas Pedal (1155, 680, 56, 125)
      // Brake
      const bp = { x: 1065, y: 715, w: 74, h: 90 };
      const brakeDepressed = this.input.brake;
      ctx.fillStyle = brakeDepressed ? '#EF4444' : '#1E293B';
      ctx.beginPath();
      ctx.roundRect(bp.x, bp.y + (brakeDepressed ? 6 : 0), bp.w, bp.h, 8);
      ctx.fill();
      ctx.strokeStyle = brakeDepressed ? '#FCA5A5' : '#475569';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.font = '800 13px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('BRAKE', bp.x + bp.w / 2, bp.y + bp.h / 2 + (brakeDepressed ? 6 : 0));

      // Gas
      const gp = { x: 1155, y: 680, w: 56, h: 125 };
      const gasDepressed = this.input.gas;
      ctx.fillStyle = gasDepressed ? '#22C55E' : '#1E293B';
      ctx.beginPath();
      ctx.roundRect(gp.x, gp.y + (gasDepressed ? 8 : 0), gp.w, gp.h, 8);
      ctx.fill();
      ctx.strokeStyle = gasDepressed ? '#86EFAC' : '#475569';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.font = '800 13px Outfit, sans-serif';
      ctx.fillText('GAS', gp.x + gp.w / 2, gp.y + gp.h / 2 + (gasDepressed ? 8 : 0));
    }
  }

  // --- Initialize Simulation on Page Load ---
  window.addEventListener('DOMContentLoaded', () => {
    window.game = new SimulationGame();
  });
})();
