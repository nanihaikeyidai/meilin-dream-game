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

    function bindDom(ttsPlayer, ttsIndicator) {
      player = ttsPlayer;
      indicator = ttsIndicator;
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

    function stop() {
      if (player) {
        player.pause();
        player.currentTime = 0;
      }
      showIndicator(false);
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

    function fetchAndPlay(dialogue, turnCount, pageIdx) {
      if (!enabled) return;
      if (serverReady === false) return;

      showIndicator(true);

      fetch(apiBaseUrl + '/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          charId: dialogue.charId,
          text: dialogue.dialogue,
          mood: dialogue.mood,
          turnCount,
          pageIdx,
        }),
      })
        .then((response) => {
          if (!response.ok) throw new Error('TTS ' + response.status);
          return response.blob();
        })
        .then((blob) => {
          if (!blob || blob.size < 100) throw new Error('empty audio');
          if (!player) return;
          player.src = URL.createObjectURL(blob);
          return player.play();
        })
        .catch((err) => {
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

      const voiceKey = dialogue.charId + '_' + turnCount + '_' + pageIdx;
      if (preloaded && preloaded.dataset.voiceKey === voiceKey) {
        player.src = preloaded.src;
        player.play().catch(() => fetchAndPlay(dialogue, turnCount, pageIdx));
        preloaded = null;
        showIndicator(true);
        return;
      }

      fetchAndPlay(dialogue, turnCount, pageIdx);
    }

    function preloadNext(turnCount, pageIdx, pageText) {
      if (!enabled || serverReady === false) return;
      const dialogue = extractDialogue(pageText);
      if (!dialogue) return;

      fetch(apiBaseUrl + '/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          charId: dialogue.charId,
          text: dialogue.dialogue,
          mood: dialogue.mood,
          turnCount,
          pageIdx,
        }),
      })
        .then((r) => (r.ok ? r.blob() : null))
        .then((blob) => {
          if (!blob || blob.size < 100) return;
          const audio = new Audio();
          audio.src = URL.createObjectURL(blob);
          audio.dataset.voiceKey =
            dialogue.charId + '_' + turnCount + '_' + pageIdx;
          audio.oncanplaythrough = () => {
            preloaded = audio;
          };
        })
        .catch(() => {});
    }

    return { bindDom, play, preloadNext, stop, checkStatus, enabled };
  }

  global.AvgTts = { createTts };
})(window);
