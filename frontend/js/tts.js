/**
 * TTS：经 /proxy/tts 转发，MOOD 驱动 VoxCPM2 Voice Design
 */
(function (global) {
  function createTts(template, portraits) {
    const apiBaseUrl = '/proxy';
    const enabled = !!template.ttsEnabled;
    let player = null;
    let indicator = null;
    let preloaded = null;
    let serverReady = null;
    let activeVoiceKey = null;
    let playAbort = null;
    let preloadAbort = null;
    let playGeneration = 0;
    let paintToken = 0;

    function bindDom(ttsPlayer, ttsIndicator) {
      player = ttsPlayer;
      indicator = ttsIndicator;
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
      if (!enabled) {
        serverReady = false;
        return false;
      }
      try {
        const r = await fetch(apiBaseUrl + '/tts/status', { method: 'GET' });
        serverReady = r.ok;
        if (indicator && !serverReady) {
          indicator.title = '语音服务未连接';
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

    function showIndicator(active) {
      if (!indicator) return;
      indicator.classList.toggle('active', !!active);
    }

    function makeVoiceKey(charId, turnCount, pageIdx) {
      return charId + '_' + turnCount + '_' + pageIdx;
    }

    function abortPlayRequest() {
      if (playAbort) playAbort.abort();
      playAbort = null;
    }

    function abortPreloadRequest() {
      if (preloadAbort) preloadAbort.abort();
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
      if (!enabled || serverReady === false) return;
      if (gen !== playGeneration || activeVoiceKey !== voiceKey) return;

      abortPlayRequest();
      playAbort = new AbortController();
      const signal = playAbort.signal;

      requestTtsAudio(dialogue, turnCount, pageIdx, signal)
        .then((blob) => {
          if (gen !== playGeneration || activeVoiceKey !== voiceKey) return;
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
      if (!enabled || !player) return;

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

        fetchAndPlay(dialogue, turnCount, pageIdx, voiceKey, gen);
      });
    }

    function preloadNext(turnCount, pageIdx, pageText) {
      if (!enabled || serverReady === false) return;
      const dialogue = extractDialogue(pageText);
      if (!dialogue) return;

      const voiceKey = makeVoiceKey(dialogue.charId, turnCount, pageIdx);
      if (preloaded && preloaded.dataset.voiceKey === voiceKey) return;

      abortPreloadRequest();
      preloadAbort = new AbortController();
      const signal = preloadAbort.signal;

      requestTtsAudio(dialogue, turnCount, pageIdx, signal)
        .then((blob) => {
          if (signal.aborted) return;
          if (!blob || blob.size < 100) return;

          preloaded = new Audio();
          preloaded.src = URL.createObjectURL(blob);
          preloaded.dataset.voiceKey = voiceKey;
        })
        .catch(() => {});
    }

    return { bindDom, play, preloadNext, stop, checkStatus, enabled };
  }

  global.AvgTts = { createTts };
})(window);
