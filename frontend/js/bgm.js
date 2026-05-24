/**
 * BGM：开始菜单单曲循环；剧本内单曲循环或双曲交替。
 */
(function (global) {
  const DEFAULT_VOLUME = 0.32;
  const MENU_BGM_TRACK = 'assets/music/menu/bgm.mp3';

  function safePlay(player) {
    const p = player.play();
    if (p && typeof p.catch === 'function') {
      p.catch((err) => {
        if (err?.name !== 'NotAllowedError') {
          console.warn('[BGM]', err.message || err);
        }
      });
    }
  }

  /** 开始界面 / 标题菜单 BGM（Sweet Route Echo） */
  function createMenuBgm() {
    let player = null;
    let bound = false;

    function bindDom(audioEl) {
      if (!audioEl || bound) return;
      player = audioEl;
      player.volume = DEFAULT_VOLUME;
      player.preload = 'auto';
      player.loop = true;
      bound = true;
    }

    function start() {
      if (!player) return;
      player.src = MENU_BGM_TRACK;
      safePlay(player);
    }

    function stop() {
      if (!player) return;
      player.pause();
      try {
        player.currentTime = 0;
      } catch (_) {
        /* ignore */
      }
      player.removeAttribute('src');
      player.load();
    }

    return { bindDom, start, stop };
  }

  function createBgm(template) {
    const tracks = Array.isArray(template?.bgmTracks)
      ? template.bgmTracks.filter(Boolean)
      : [];
    let player = null;
    let trackIndex = 0;
    let bound = false;

    function bindDom(audioEl) {
      if (!audioEl || bound) return;
      player = audioEl;
      player.volume = DEFAULT_VOLUME;
      player.preload = 'auto';
      player.addEventListener('ended', onEnded);
      bound = true;
    }

    function onEnded() {
      if (!player || tracks.length <= 1) return;
      trackIndex = (trackIndex + 1) % tracks.length;
      playIndex(trackIndex);
    }

    function playIndex(index) {
      if (!player || !tracks.length) return;
      trackIndex = index % tracks.length;
      const single = tracks.length === 1;
      player.loop = single;
      player.src = tracks[trackIndex];
      safePlay(player);
    }

    function start() {
      if (!player || !tracks.length) return;
      trackIndex = 0;
      playIndex(0);
    }

    function stop() {
      if (!player) return;
      player.pause();
      try {
        player.currentTime = 0;
      } catch (_) {
        /* ignore */
      }
      player.removeAttribute('src');
      player.load();
    }

    function hasTracks() {
      return tracks.length > 0;
    }

    return { bindDom, start, stop, hasTracks };
  }

  global.AvgBgm = {
    MENU_BGM_TRACK,
    createBgm,
    createMenuBgm,
    DEFAULT_VOLUME,
  };
})(window);
