/**
 * TTS：经 /proxy/tts 转发，MOOD 驱动 VoxCPM2 Voice Design
 */
(function (global) {
  const TTS_ENABLED_KEY = 'avg_tts_enabled';

  function createTts(template, portraits) {
    const apiBaseUrl = '/proxy';
    const templateId = template?.id || 'changan-moon';
    const templateEnabled = !!template.ttsEnabled;
    let userEnabled = global.localStorage?.getItem(TTS_ENABLED_KEY) !== '0';
    let player = null;
    let indicator = null;
    let preloaded = null;
    let serverReady = null;
    let activeVoiceKey = null;
    let playAbort = null;
    let preloadAbort = null;
    let playGeneration = 0;
    let paintToken = 0;
    let requestQueue = Promise.resolve();

    function bindDom(ttsPlayer, ttsIndicator) {
      player = ttsPlayer;
      indicator = ttsIndicator;
    }

    function isEnabled() {
      return templateEnabled && userEnabled;
    }

    /** 等对话框文字完成绘制后再执行（避免先出声后出字） */
    function afterTextPaint(fn) {
      const token = paintToken;
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (token !== paintToken) return;
          fn();
        });
      });
    }

    async function checkStatus() {
      if (!isEnabled()) {
        serverReady = false;
        if (indicator) {
          indicator.title = templateEnabled ? '语音已关闭' : '当前剧本未启用语音';
          indicator.dataset.offline = '1';
        }
        return false;
      }
      try {
        const r = await fetch(apiBaseUrl + '/tts/status', { method: 'GET' });
        let status = null;
        try {
          status = await r.json();
        } catch (_) {
          /* non-JSON status responses are treated by HTTP status only */
        }
        serverReady = r.ok && status?.model_loaded !== false;
        if (indicator && !serverReady) {
          indicator.title = status?.model_error
            ? '语音模型不可用：' + status.model_error
            : '语音服务未连接';
          indicator.dataset.offline = '1';
        } else if (indicator) {
          indicator.removeAttribute('title');
          delete indicator.dataset.offline;
        }
      } catch {
        serverReady = false;
        if (indicator) {
          indicator.title = '语音服务未连接';
          indicator.dataset.offline = '1';
        }
      }
      return serverReady;
    }

    async function setEnabled(next) {
      userEnabled = !!next;
      global.localStorage?.setItem(TTS_ENABLED_KEY, userEnabled ? '1' : '0');
      if (!userEnabled) {
        stop();
        if (indicator) {
          indicator.title = '语音已关闭';
          indicator.dataset.offline = '1';
        }
        serverReady = false;
        return false;
      }
      return checkStatus();
    }

    function showIndicator(active) {
      if (!indicator) return;
      indicator.classList.toggle('active', !!active);
    }

    function makeVoiceKey(charId, turnCount, pageIdx) {
      return charId + '_' + turnCount + '_' + pageIdx;
    }

    function abortPlayRequest() {
      playAbort = null;
    }

    function abortPreloadRequest() {
      preloadAbort = null;
    }

    function stopPlayback() {
      if (player) {
        player.pause();
        player.currentTime = 0;
        player.removeAttribute('src');
        try {
          player.load();
        } catch (_) {
          /* ignore */
        }
      }
      showIndicator(false);
    }

    function stop() {
      abortPlayRequest();
      playGeneration += 1;
      paintToken += 1;
      activeVoiceKey = null;
      stopPlayback();
    }

    function extractDialogue(pageText) {
      if (!global.AvgMood) return null;
      const beat = global.AvgMood.parsePageBeat(pageText, portraits);
      if (!beat || !beat.hasDialogue) return null;
      return {
        charId: beat.charId,
        charName: beat.charName,
        dialogue: beat.dialogue,
        mood: beat.mood,
        expression: beat.expression,
      };
    }

    function requestTtsAudio(dialogue, turnCount, pageIdx, signal) {
      return fetch(apiBaseUrl + '/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal,
        body: JSON.stringify({
          templateId,
          charId: dialogue.charId,
          text: dialogue.dialogue,
          mood: dialogue.mood,
          turnCount,
          pageIdx,
        }),
      }).then((response) => {
        if (!response.ok) throw new Error('TTS ' + response.status);
        return response.blob();
      });
    }

    function enqueueTtsAudio(dialogue, turnCount, pageIdx, signal, shouldRun) {
      const run = () => {
        if (shouldRun && !shouldRun()) return null;
        return requestTtsAudio(dialogue, turnCount, pageIdx, signal);
      };
      requestQueue = requestQueue.catch(() => {}).then(run);
      return requestQueue;
    }

    function startPlayback(src, voiceKey) {
      if (!player || activeVoiceKey !== voiceKey) return;
      player.src = src;
      showIndicator(true);
      return player.play().catch((err) => {
        if (err?.name !== 'AbortError') console.warn('[TTS]', err.message || err);
        showIndicator(false);
      });
    }

    function fetchAndPlay(dialogue, turnCount, pageIdx, voiceKey, gen) {
      if (!isEnabled()) return;
      if (gen !== playGeneration || activeVoiceKey !== voiceKey) return;

      abortPlayRequest();
      playAbort = new AbortController();
      const signal = playAbort.signal;

      enqueueTtsAudio(
        dialogue,
        turnCount,
        pageIdx,
        signal,
        () => gen === playGeneration && activeVoiceKey === voiceKey
      )
        .then((blob) => {
          if (gen !== playGeneration || activeVoiceKey !== voiceKey) return;
          if (!blob) return;
          if (!blob || blob.size < 100) throw new Error('empty audio');
          return startPlayback(URL.createObjectURL(blob), voiceKey);
        })
        .catch((err) => {
          if (err?.name === 'AbortError') return;
          if (gen !== playGeneration || activeVoiceKey !== voiceKey) return;
          console.warn('[TTS]', err.message || err);
          showIndicator(false);
        });
    }

    function play(turnCount, pageIdx, pageText) {
      if (!isEnabled() || !player) return;

      const dialogue = extractDialogue(pageText);
      if (!dialogue) {
        stop();
        return;
      }

      const voiceKey = makeVoiceKey(dialogue.charId, turnCount, pageIdx);

      abortPlayRequest();
      playGeneration += 1;
      paintToken += 1;
      stopPlayback();

      activeVoiceKey = voiceKey;
      const gen = playGeneration;
      const paintAt = paintToken;

      // 等文字渲染到屏幕后再开始播放/下载
      afterTextPaint(() => {
        if (paintAt !== paintToken || gen !== playGeneration || activeVoiceKey !== voiceKey) {
          return;
        }

        if (preloaded && preloaded.dataset.voiceKey === voiceKey) {
          const src = preloaded.src;
          preloaded = null;
          startPlayback(src, voiceKey);
          return;
        }

        const playWhenReady = () => fetchAndPlay(dialogue, turnCount, pageIdx, voiceKey, gen);
        if (serverReady === true) {
          playWhenReady();
        } else {
          checkStatus().then((ready) => {
            if (ready) playWhenReady();
          });
        }
      });
    }

    function preloadNext(turnCount, pageIdx, pageText) {
      // VoxCPM2 is GPU-heavy; speculative preload can create stale queued work
      // and poison CUDA state after repeated navigation. Keep playback on-demand.
    }

    return {
      bindDom,
      play,
      preloadNext,
      stop,
      checkStatus,
      setEnabled,
      isEnabled,
      get enabled() {
        return isEnabled();
      },
      get templateEnabled() {
        return templateEnabled;
      },
    };
  }

  global.AvgTts = { createTts };
})(window);
