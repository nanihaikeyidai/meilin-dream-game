/**
 * TTS：经 /proxy/tts 转发，失败时静默降级
 */
(function (global) {
  function createTts(template, portraits) {
    const apiBaseUrl = '/proxy';
    const enabled = !!template.ttsEnabled;
    let player = null;
    let indicator = null;
    let preloaded = null;

    function bindDom(ttsPlayer, ttsIndicator) {
      player = ttsPlayer;
      indicator = ttsIndicator;
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
      for (const [name, charId] of Object.entries(portraits)) {
        if (!pageText.includes(name)) continue;
        const match = pageText.match(/「([^」]*)」/);
        if (!match || !match[1].trim()) return null;
        const moodMatch = pageText.match(/\[MOOD:\s*(\w+)\]/i);
        return {
          charId,
          charName: name,
          dialogue: match[1].trim(),
          mood: moodMatch ? moodMatch[1].toLowerCase() : 'neutral',
        };
      }
      return null;
    }

    function fetchAndPlay(dialogue, turnCount, pageIdx) {
      if (!enabled) return;
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
      if (!enabled) return;
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
          audio.dataset.voiceKey = dialogue.charId + '_' + turnCount + '_' + pageIdx;
          audio.oncanplaythrough = () => {
            preloaded = audio;
          };
        })
        .catch(() => {});
    }

    return { bindDom, play, preloadNext, stop, enabled };
  }

  global.AvgTts = { createTts };
})(window);
