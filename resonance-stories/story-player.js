/**
 * Resonance Stories — Story Player
 *
 * State machine that progresses through scenes, triggers audio + visual cues.
 * The player IS the conductor — it holds the timing, the arc, the breath.
 *
 * Jaie Parker + Kai, 2026-03-31
 */

import { AudioEngine } from './audio-engine.js';

export class StoryPlayer {
  constructor(containerEl) {
    this.container = containerEl;
    this.audio = new AudioEngine();
    this.story = null;
    this.scenes = [];
    this.currentSceneIndex = -1;
    this.isPlaying = false;
    this.sceneTimer = null;
    this.narrationEl = null;       // current <audio> element
    this.preloadedAudio = null;    // next scene's pre-buffered audio
    this.preloadedIndex = -1;      // which scene index is pre-buffered
    this.onSceneChange = null;
    this.onStoryEnd = null;
  }

  /**
   * Load a story from its JSON data.
   */
  async loadStory(storyData) {
    this.stop();
    this.story = storyData;
    this.scenes = storyData.scenes || [];
    this.currentSceneIndex = -1;
    this._renderTitle();

    // Pre-buffer first scene's audio while showing title screen
    if (this.scenes.length > 0) {
      const audioEl = new Audio();
      audioEl.preload = 'auto';
      audioEl.src = this._audioUrl(this.scenes[0].id);
      audioEl.load();
      this.preloadedAudio = audioEl;
      this.preloadedIndex = 0;
    }
  }

  /**
   * Load story from a URL.
   */
  async loadFromUrl(url) {
    const resp = await fetch(url);
    const data = await resp.json();
    await this.loadStory(data);
  }

  /**
   * Start playback. Must be called from user gesture for AudioContext.
   */
  async play() {
    if (!this.story || this.scenes.length === 0) return;

    this.audio.init();
    await this.audio.resume();
    this.isPlaying = true;
    this._nextScene();
  }

  /**
   * Pause playback.
   */
  pause() {
    this.isPlaying = false;
    if (this.sceneTimer) {
      clearTimeout(this.sceneTimer);
      this.sceneTimer = null;
    }
    if (this._narrationTimer) { clearTimeout(this._narrationTimer); this._narrationTimer = null; }
    if (this.narrationEl) this.narrationEl.pause();
    this.audio.stopAll();
  }

  /**
   * Stop and reset to beginning.
   */
  stop() {
    this.pause();
    if (this._narrationTimer) { clearTimeout(this._narrationTimer); this._narrationTimer = null; }
    if (this.narrationEl) {
      this.narrationEl.pause();
      this.narrationEl = null;
    }
    this.currentSceneIndex = -1;
    this.audio.destroy();
  }

  /**
   * Skip to next scene.
   */
  next() {
    if (this.sceneTimer) {
      clearTimeout(this.sceneTimer);
      this.sceneTimer = null;
    }
    this._nextScene();
  }

  /**
   * Go to previous scene.
   */
  prev() {
    if (this.currentSceneIndex > 0) {
      this.currentSceneIndex -= 2; // -2 because _nextScene increments
      if (this.sceneTimer) {
        clearTimeout(this.sceneTimer);
        this.sceneTimer = null;
      }
      this._nextScene();
    }
  }

  /**
   * Advance to the next scene.
   */
  _nextScene() {
    this.currentSceneIndex++;

    if (this.currentSceneIndex >= this.scenes.length) {
      this.isPlaying = false;
      this.audio.stopAll();
      this._renderEnd();
      if (this.onStoryEnd) this.onStoryEnd();
      return;
    }

    const scene = this.scenes[this.currentSceneIndex];
    const duration = scene.duration_seconds || 15;

    // Render scene visuals
    this._renderScene(scene);

    // Sound design starts first — sets the mood
    this.audio.playScene(scene.sound, duration);

    // Narration enters after a breath (let the audio context warm up + mood establish)
    const narrationDelay = this.currentSceneIndex === 0 ? 2000 : 1200;
    this._narrationTimer = setTimeout(() => this._playNarration(scene), narrationDelay);

    // Animate progress bar continuously
    this._animateProgress(duration);

    // Notify listener
    if (this.onSceneChange) {
      this.onSceneChange(scene, this.currentSceneIndex, this.scenes.length);
    }

    // Auto-advance after scene duration
    if (this.isPlaying) {
      this.sceneTimer = setTimeout(() => {
        if (this.isPlaying) this._nextScene();
      }, duration * 1000);
    }
  }

  /**
   * Render the title screen.
   */
  _renderTitle() {
    if (!this.container || !this.story) return;
    this.container.innerHTML = `
      <div class="scene title-scene">
        <h1 class="story-title">${this._esc(this.story.title)}</h1>
        <p class="story-meta">A Resonance Story for ages ${this._esc(this.story.bracket)}</p>
        <button class="play-btn" id="playBtn">
          <span class="play-icon">&#9654;</span>
          <span>Listen</span>
        </button>
      </div>
    `;
    const btn = this.container.querySelector('#playBtn');
    if (btn) {
      btn.addEventListener('click', () => this.play(), { once: true });
    }
  }

  /**
   * Render a scene.
   */
  _renderScene(scene) {
    if (!this.container) return;

    const soundType = scene.sound?.type || 'ambient';
    const moodClass = this._moodClass(soundType);
    const progress = ((this.currentSceneIndex + 1) / this.scenes.length) * 100;

    this.container.innerHTML = `
      <div class="scene ${moodClass}" data-scene-id="${this._esc(scene.id)}">
        <div class="scene-visual">
          <div class="resonance-viz ${moodClass}"></div>
        </div>
        <div class="scene-text">
          <p class="narration">${this._formatNarration(scene.narration)}</p>
        </div>
        <div class="scene-controls">
          <button class="ctrl-btn prev-btn" ${this.currentSceneIndex === 0 ? 'disabled' : ''}>&#9664;</button>
          <button class="ctrl-btn pause-btn">${this.isPlaying ? '&#10074;&#10074;' : '&#9654;'}</button>
          <button class="ctrl-btn next-btn">&#9654;&#9654;</button>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${progress}%"></div>
        </div>
        <p class="scene-hint">${this._esc(scene.visual_direction || '')}</p>
      </div>
    `;

    // Wire controls
    const prevBtn = this.container.querySelector('.prev-btn');
    const pauseBtn = this.container.querySelector('.pause-btn');
    const nextBtn = this.container.querySelector('.next-btn');

    if (prevBtn) prevBtn.addEventListener('click', () => this.prev());
    if (pauseBtn) pauseBtn.addEventListener('click', () => {
      if (this.isPlaying) {
        this.pause();
        pauseBtn.innerHTML = '&#9654;';
      } else {
        this.isPlaying = true;
        this.audio.init();
        this.audio.resume();
        this._nextScene();
      }
    });
    if (nextBtn) nextBtn.addEventListener('click', () => this.next());
  }

  /**
   * Render end screen.
   */
  _renderEnd() {
    if (!this.container) return;
    this.container.innerHTML = `
      <div class="scene end-scene">
        <h2>The End</h2>
        <p class="end-question">Can you hear it?</p>
        <button class="play-btn" id="replayBtn">
          <span>Listen Again</span>
        </button>
      </div>
    `;
    const btn = this.container.querySelector('#replayBtn');
    if (btn) {
      btn.addEventListener('click', () => {
        this.currentSceneIndex = -1;
        this.play();
      }, { once: true });
    }
  }

  /**
   * Play narration audio for a scene.
   * Uses pre-buffered audio if available, otherwise loads fresh.
   */
  _playNarration(scene) {
    if (this.narrationEl) {
      this.narrationEl.pause();
      this.narrationEl = null;
    }

    let audioEl;
    if (this.preloadedAudio && this.preloadedIndex === this.currentSceneIndex) {
      // Use pre-buffered audio — no loading delay
      audioEl = this.preloadedAudio;
      this.preloadedAudio = null;
      this.preloadedIndex = -1;
    } else {
      audioEl = new Audio(this._audioUrl(scene.id));
    }

    audioEl.volume = 0.9;
    audioEl.play().catch(() => {});
    this.narrationEl = audioEl;

    // Pre-buffer the NEXT scene's audio while this one plays
    this._preloadNext();
  }

  /**
   * Pre-buffer the next scene's narration audio.
   */
  _preloadNext() {
    const nextIndex = this.currentSceneIndex + 1;
    if (nextIndex >= this.scenes.length) return;

    const nextScene = this.scenes[nextIndex];
    const audioEl = new Audio();
    audioEl.preload = 'auto';
    audioEl.src = this._audioUrl(nextScene.id);
    // Force the browser to start downloading
    audioEl.load();

    this.preloadedAudio = audioEl;
    this.preloadedIndex = nextIndex;
  }

  /**
   * Get audio URL for a scene.
   */
  _audioUrl(sceneId) {
    const storyId = this.story?.id || 'unknown';
    return `stories/${storyId}/audio/${sceneId}.mp3`;
  }

  /**
   * Animate progress bar smoothly across the scene duration.
   */
  _animateProgress(duration) {
    if (this._progressRaf) cancelAnimationFrame(this._progressRaf);

    const fill = this.container?.querySelector('.progress-fill');
    if (!fill) return;

    const sceneStart = (this.currentSceneIndex / this.scenes.length) * 100;
    const sceneEnd = ((this.currentSceneIndex + 1) / this.scenes.length) * 100;
    const startTime = performance.now();
    const durationMs = duration * 1000;

    const animate = (now) => {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / durationMs, 1);
      fill.style.width = `${sceneStart + (sceneEnd - sceneStart) * t}%`;
      if (t < 1 && this.isPlaying) {
        this._progressRaf = requestAnimationFrame(animate);
      }
    };
    this._progressRaf = requestAnimationFrame(animate);
  }

  /**
   * Map sound type to CSS mood class for visual theming.
   */
  _moodClass(soundType) {
    const map = {
      ambient: 'mood-calm',
      dissonant: 'mood-tense',
      silence: 'mood-still',
      emergence: 'mood-discovery',
      consonant_building: 'mood-building',
      consonant: 'mood-harmony',
      consonant_full: 'mood-joy',
      decay: 'mood-wonder',
      invitation: 'mood-open'
    };
    return map[soundType] || 'mood-calm';
  }

  /**
   * Format narration text — add gentle pauses for ellipses and emphasis.
   */
  _formatNarration(text) {
    if (!text) return '';
    return this._esc(text)
      .replace(/\.\.\./g, '<span class="pause">...</span>')
      .replace(/HARD/g, '<em class="loud">HARD</em>')
      .replace(/SCREECH/g, '<em class="loud">SCREECH</em>')
      .replace(/GROAN/g, '<em class="loud">GROAN</em>')
      .replace(/HMMMMM!/g, '<em class="hum bright">HMMMMM!</em>')
      .replace(/Hmmmmm\./g, '<em class="hum">Hmmmmm.</em>')
      .replace(/Hmmmm\.\.\./g, '<em class="hum soft">Hmmmm...</em>');
  }

  /**
   * Escape HTML.
   */
  _esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
