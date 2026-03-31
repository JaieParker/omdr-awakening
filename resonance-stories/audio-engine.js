/**
 * Resonance Stories — Web Audio Engine
 *
 * Generates ambient melodic backgrounds from consonant/dissonant ratios.
 * Not raw oscillators — gentle arpeggiated patterns with reverb.
 * The sound sits underneath narration like a musical bed.
 * Dissonant scenes feel uneasy. Consonant scenes feel like home.
 *
 * Jaie Parker + Kai, 2026-03-31
 */

export class AudioEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.reverbGain = null;
    this.dryGain = null;
    this.convolver = null;
    this.melodyInterval = null;
    this.activeNodes = [];
    this.isInitialized = false;
  }

  init() {
    if (this.isInitialized) return;
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Master output
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0.8;
    this.masterGain.connect(this.ctx.destination);

    // Dry path
    this.dryGain = this.ctx.createGain();
    this.dryGain.gain.value = 0.7;
    this.dryGain.connect(this.masterGain);

    // Reverb path (simulated with delay feedback)
    this._createReverb();

    this.isInitialized = true;
  }

  /**
   * Create a simple reverb using feedback delay network.
   */
  _createReverb() {
    this.reverbGain = this.ctx.createGain();
    this.reverbGain.gain.value = 0.7;

    // Two delay lines at different times for spatial width
    const delay1 = this.ctx.createDelay(1.0);
    delay1.delayTime.value = 0.37;
    const delay2 = this.ctx.createDelay(1.0);
    delay2.delayTime.value = 0.53;

    const fb1 = this.ctx.createGain();
    fb1.gain.value = 0.35;
    const fb2 = this.ctx.createGain();
    fb2.gain.value = 0.28;

    // Tone shaping — roll off highs for warmth
    const lpf = this.ctx.createBiquadFilter();
    lpf.type = 'lowpass';
    lpf.frequency.value = 2000;

    // Wire: input → delay → feedback → lpf → delay (loop) + output
    this.reverbGain.connect(delay1);
    this.reverbGain.connect(delay2);
    delay1.connect(fb1);
    delay2.connect(fb2);
    fb1.connect(lpf);
    fb2.connect(lpf);
    lpf.connect(delay1);
    lpf.connect(delay2);
    delay1.connect(this.masterGain);
    delay2.connect(this.masterGain);
  }

  async resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      await this.ctx.resume();
    }
  }

  /**
   * Play a scene's sound as a gentle ambient melody.
   */
  playScene(sound, durationSeconds) {
    this.stopAll();
    if (!sound || !this.isInitialized) return;

    const baseFreq = sound.base_frequency_hz || 220;
    const oscillators = sound.oscillators || [];
    const soundType = sound.type || 'ambient';

    if (oscillators.length === 0 && soundType !== 'silence') {
      // Ambient scene — gentle warm drone
      this._playDrone(baseFreq, durationSeconds, 0.25);
      return;
    }

    if (soundType === 'silence') {
      // A breath of the fundamental — present but still
      this._playDrone(baseFreq, durationSeconds, 0.1);
      return;
    }

    // Build the note palette from the oscillator configs
    const notes = oscillators.map(osc => ({
      freq: baseFreq * this._parseRatio(osc.frequency_ratio),
      waveform: osc.waveform || 'sine',
      amplitude: osc.amplitude || 0.3,
      decayTime: osc.decay_time || null,
    }));

    // Choose melody pattern based on sound type
    switch (soundType) {
      case 'dissonant':
        this._playDissonantMelody(notes, baseFreq, durationSeconds, sound.rhythm);
        break;
      case 'emergence':
        this._playEmergence(notes, baseFreq, durationSeconds);
        break;
      case 'consonant_building':
        this._playBuildingMelody(notes, baseFreq, durationSeconds);
        break;
      case 'consonant':
      case 'consonant_full':
        this._playConsonantMelody(notes, baseFreq, durationSeconds, soundType === 'consonant_full');
        break;
      case 'decay':
        this._playDecay(notes, baseFreq, durationSeconds);
        break;
      case 'invitation':
        this._playInvitation(notes, baseFreq, durationSeconds);
        break;
      default:
        this._playConsonantMelody(notes, baseFreq, durationSeconds, false);
    }
  }

  /**
   * A very soft background drone — just enough to feel, not hear.
   */
  _playDrone(freq, duration, amp) {
    this._playNote(freq, 'sine', amp, duration, 3.0, 3.0);
  }

  /**
   * Dissonant scenes — irregular, jarring note pattern.
   * Notes arrive at wrong times, overlap uncomfortably.
   */
  _playDissonantMelody(notes, baseFreq, duration, rhythm) {
    let elapsed = 0;
    const isIrregular = rhythm === 'irregular' || rhythm === 'chaotic';

    const step = () => {
      if (elapsed >= duration) return;

      for (const note of notes) {
        // Irregular timing — notes arrive too early or too late
        const jitter = isIrregular ? (Math.random() - 0.5) * 0.3 : 0;
        const noteLen = 0.15 + Math.random() * 0.2;
        const amp = note.amplitude * 0.5;

        setTimeout(() => {
          if (this.melodyInterval === null) return;
          this._playNote(note.freq, 'triangle', amp, noteLen, 0.02, 0.08);
        }, jitter * 1000);
      }

      // Add a harsh metallic ping occasionally
      if (Math.random() > 0.5) {
        const harshFreq = baseFreq * (1 + Math.random() * 0.1);
        this._playNote(harshFreq, 'sawtooth', 0.12, 0.08, 0.005, 0.05);
      }

      elapsed += 0.6 + Math.random() * 0.4;
    };

    step();
    this.melodyInterval = setInterval(step, 700 + Math.random() * 300);
  }

  /**
   * Emergence — a single note growing from nothing. Like hearing a hum.
   */
  _playEmergence(notes, baseFreq, duration) {
    // Very long fade-in of the fundamental
    this._playNote(baseFreq, 'sine', 0.3, duration, duration * 0.6, 2.0);

    // After halfway, add a gentle octave whisper
    setTimeout(() => {
      if (this.melodyInterval === null) return;
      this._playNote(baseFreq * 2, 'sine', 0.15, duration * 0.4, 3.0, 2.0);
    }, duration * 500);

    // Placeholder interval to keep tracking active
    this.melodyInterval = setInterval(() => {}, duration * 1000);
  }

  /**
   * Building consonance — notes added one by one, each reinforcing.
   * Like discovering a chord one note at a time.
   */
  _playBuildingMelody(notes, baseFreq, duration) {
    let noteIndex = 0;
    const interval = (duration / (notes.length + 2)) * 1000;

    // Start with a gentle arpeggio of the fundamental
    const arpNotes = [baseFreq, baseFreq * 1.5, baseFreq * 2];
    let arpIndex = 0;

    this.melodyInterval = setInterval(() => {
      // Soft arpeggio
      const freq = arpNotes[arpIndex % arpNotes.length];
      this._playNote(freq, 'sine', 0.2, 1.2, 0.3, 0.8);
      arpIndex++;

      // Every few beats, add a new harmony note from the config
      if (arpIndex % 3 === 0 && noteIndex < notes.length) {
        const note = notes[noteIndex];
        this._playNote(note.freq, 'sine', 0.18, 2.0, 0.8, 1.5);
        noteIndex++;
      }
    }, interval);
  }

  /**
   * Full consonance — a gentle, repeating melodic pattern.
   * The notes breathe like a lullaby. This is K=0.25 as music.
   */
  _playConsonantMelody(notes, baseFreq, duration, isFull) {
    // Build a scale from the frequency ratios
    const freqs = [baseFreq];
    for (const note of notes) {
      if (!freqs.includes(note.freq)) freqs.push(note.freq);
    }
    freqs.sort((a, b) => a - b);

    // Add passing tones for a richer melody
    if (isFull && freqs.length >= 2) {
      const mid = baseFreq * 1.25; // Major third as passing tone
      freqs.push(mid);
      freqs.sort((a, b) => a - b);
    }

    // Gentle arpeggio up and down — the swing's rhythm
    let direction = 1;
    let index = 0;
    const swingPeriod = isFull ? 1200 : 1500; // ms between notes

    // Soft pad underneath
    this._playNote(baseFreq, 'sine', 0.2, duration, 2.0, 2.0);
    if (isFull) {
      this._playNote(baseFreq * 1.5, 'sine', 0.15, duration, 3.0, 2.0);
    }

    this.melodyInterval = setInterval(() => {
      const freq = freqs[index];
      const amp = isFull ? 0.25 : 0.2;
      this._playNote(freq, 'triangle', amp, 0.8, 0.15, 0.6);

      // Move up and down the scale like a swing
      index += direction;
      if (index >= freqs.length - 1) direction = -1;
      if (index <= 0) direction = 1;
    }, swingPeriod);
  }

  /**
   * Decay — the chord dissolving. Fibonacci: highest overtones go first.
   */
  _playDecay(notes, baseFreq, duration) {
    // Sort notes by frequency, highest first (they decay first)
    const sorted = [...notes].sort((a, b) => b.freq - a.freq);

    sorted.forEach((note, i) => {
      const startDelay = i * 1.5; // Stagger starts
      const noteDuration = duration - startDelay - 1;
      if (noteDuration <= 0) return;

      setTimeout(() => {
        if (this.melodyInterval === null) return;
        this._playNote(note.freq, 'sine', 0.25 - i * 0.05, noteDuration, 0.5, noteDuration * 0.6);
      }, startDelay * 1000);
    });

    // The fundamental lingers longest — a single gentle tone
    this._playNote(baseFreq, 'sine', 0.25, duration, 1.0, duration * 0.4);

    this.melodyInterval = setInterval(() => {}, duration * 1000);
  }

  /**
   * Invitation — soft unison, then silence. Space for the child.
   */
  _playInvitation(notes, baseFreq, duration) {
    // A gentle bell-like tone
    this._playNote(baseFreq, 'sine', 0.25, duration * 0.6, 2.0, duration * 0.3);
    this._playNote(baseFreq * 2, 'sine', 0.12, duration * 0.4, 3.0, duration * 0.2);

    // A single soft chime after a pause
    setTimeout(() => {
      if (this.melodyInterval === null) return;
      this._playNote(baseFreq * 1.5, 'triangle', 0.18, 1.5, 0.1, 1.2);
    }, duration * 400);

    this.melodyInterval = setInterval(() => {}, duration * 1000);
  }

  /**
   * Play a single note with envelope — the atomic unit.
   * Connects through both dry and reverb paths for spatial warmth.
   */
  _playNote(freq, waveform, amplitude, duration, attack, release) {
    if (!this.isInitialized) return;
    const now = this.ctx.currentTime;

    const osc = this.ctx.createOscillator();
    osc.type = waveform;
    osc.frequency.value = freq;

    // Gentle detuning for warmth (±2 cents)
    osc.detune.value = (Math.random() - 0.5) * 4;

    const env = this.ctx.createGain();
    env.gain.value = 0;

    // Connect to both dry and wet paths
    osc.connect(env);
    env.connect(this.dryGain);
    env.connect(this.reverbGain);

    // Envelope
    const safeAttack = Math.min(attack, duration * 0.5);
    const safeRelease = Math.min(release, duration * 0.5);

    env.gain.setValueAtTime(0, now);
    env.gain.linearRampToValueAtTime(amplitude, now + safeAttack);

    const sustainEnd = now + duration - safeRelease;
    if (sustainEnd > now + safeAttack) {
      env.gain.setValueAtTime(amplitude, sustainEnd);
      env.gain.exponentialRampToValueAtTime(0.001, sustainEnd + safeRelease);
    } else {
      env.gain.exponentialRampToValueAtTime(0.001, now + duration);
    }

    osc.start(now);
    osc.stop(now + duration + 0.1);

    this.activeNodes.push({ osc, env });

    osc.onended = () => {
      this.activeNodes = this.activeNodes.filter(n => n.osc !== osc);
      env.disconnect();
    };
  }

  _parseRatio(ratioStr) {
    if (typeof ratioStr === 'number') return ratioStr;
    if (!ratioStr || typeof ratioStr !== 'string') return 1;
    const parts = ratioStr.split(':');
    if (parts.length !== 2) return 1;
    const num = parseFloat(parts[0]);
    const den = parseFloat(parts[1]);
    return den === 0 ? 1 : num / den;
  }

  stopAll() {
    if (!this.isInitialized) return;

    // Stop melody pattern
    if (this.melodyInterval !== null) {
      clearInterval(this.melodyInterval);
      this.melodyInterval = null;
    }

    // Fade out active notes
    const now = this.ctx.currentTime;
    for (const { osc, env } of this.activeNodes) {
      try {
        env.gain.cancelScheduledValues(now);
        env.gain.setValueAtTime(env.gain.value, now);
        env.gain.linearRampToValueAtTime(0, now + 0.3); // Gentle fade, not abrupt
        osc.stop(now + 0.4);
      } catch (e) {
        // Already stopped
      }
    }
    this.activeNodes = [];
  }

  setVolume(vol) {
    if (this.masterGain) {
      this.masterGain.gain.value = Math.max(0, Math.min(1, vol));
    }
  }

  destroy() {
    this.stopAll();
    if (this.ctx) {
      this.ctx.close();
      this.ctx = null;
    }
    this.isInitialized = false;
  }
}
