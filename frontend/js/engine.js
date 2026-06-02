/**
 * AVG 渲染引擎：立绘回退链、场景、表情、分页
 */
(function (global) {
  function createEngine(template) {
    const portraits = template.portraits || {};
    const sceneBackgrounds = template.sceneBackgrounds || {};
    const expressionKeywords = global.AvgTemplates.EXPRESSION_KEYWORDS;

    let currentCharName = null;
    let currentCharId = null;
    let currentExpression = 'default';

    function detectCharacter(text) {
      for (const name of Object.keys(portraits)) {
        if (text.includes(name)) return name;
      }
      return null;
    }

    function detectExpression(text) {
      if (global.AvgMood) {
        const beat = global.AvgMood.parsePageBeat(text, portraits);
        if (beat) return beat.expression;
      }

      const explicit = text.match(/\[EXPR:\s*(\w+)\]/i);
      if (explicit) {
        const e = explicit[1].toLowerCase();
        if (global.AvgMood?.normalizeExpression(e)) return e;
      }

      if (global.AvgMood) {
        const mood = global.AvgMood.detectMood(text);
        if (mood) return global.AvgMood.moodToExpression(mood);
      }

      for (const [keyword, exp] of Object.entries(expressionKeywords)) {
        if (text.includes(keyword)) return exp;
      }
      return null;
    }

    function detectScene(text) {
      const match = text.match(/\[SCENE:\s*(\w+)\]/);
      return match ? match[1] : null;
    }

    function portraitPaths(charId, expression) {
      const base = 'assets/portraits/' + charId + '/';
      const expressions = [expression];
      if (expression !== 'smile') expressions.push('smile');
      if (expression !== 'default') expressions.push('default');
      return expressions.map((expr) => base + expr + '.png');
    }

    function updateSprite(spriteImage, textNameEl, charName, expression) {
      const charId = portraits[charName];
      if (!charId) {
        spriteImage.classList.remove('visible', 'slide-in-left');
        spriteImage.src = '';
        currentCharName = null;
        currentCharId = null;
        textNameEl.classList.remove('visible');
        return;
      }

      if (expression) currentExpression = expression;
      const paths = portraitPaths(charId, currentExpression);
      const isNewChar = charName !== currentCharName;

      let pathIndex = 0;

      function tryNext() {
        if (pathIndex >= paths.length) {
          spriteImage.classList.remove('visible', 'slide-in-left');
          spriteImage.src = '';
          return;
        }
        spriteImage.src = paths[pathIndex++];
      }

      spriteImage.onload = () => {
        spriteImage.onerror = null;
      };
      spriteImage.onerror = tryNext;
      tryNext();

      spriteImage.classList.add('visible');
      if (isNewChar) {
        spriteImage.classList.remove('slide-in-left');
        void spriteImage.offsetWidth;
        spriteImage.classList.add('slide-in-left');
      }

      currentCharName = charName;
      currentCharId = charId;
      textNameEl.textContent = charName;
      textNameEl.classList.add('visible');
    }

    function updateBg(bgImage, sceneId) {
      const path = sceneBackgrounds[sceneId] || sceneBackgrounds.default;
      if (!path) return;
      if (bgImage.src.indexOf(path) === -1) bgImage.src = path;
    }

    function applyCharacterFromText(spriteImage, textNameEl, text) {
      if (global.AvgMood) {
        const beat = global.AvgMood.parsePageBeat(text, portraits);
        if (!beat || !beat.hasDialogue) {
          spriteImage.classList.remove('visible', 'slide-in-left');
          textNameEl.classList.remove('visible');
          return null;
        }
        updateSprite(
          spriteImage,
          textNameEl,
          beat.charName,
          beat.expression,
        );
        return beat;
      }

      const charName = detectCharacter(text);
      if (!charName) {
        textNameEl.classList.remove('visible');
        return null;
      }
      const expr = detectExpression(text) || 'default';
      updateSprite(spriteImage, textNameEl, charName, expr);
      return { charName, expression: expr };
    }

    function getState() {
      return {
        currentCharName,
        currentCharId,
        currentExpression,
      };
    }

    function setState(state) {
      if (!state) return;
      currentCharName = state.currentCharName ?? null;
      currentCharId = state.currentCharId ?? null;
      currentExpression = state.currentExpression || 'default';
    }

    return {
      detectCharacter,
      detectExpression,
      detectScene,
      updateSprite,
      updateBg,
      applyCharacterFromText,
      getState,
      setState,
      get portraits() {
        return portraits;
      },
    };
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function isSkippedLine(trimmed) {
    return (
      /^[\dA-Za-z][.\)】）:]/.test(trimmed) ||
      /^❤/.test(trimmed) ||
      /^\[GALGAME STATE\]/.test(trimmed) ||
      /^Scene:/.test(trimmed) ||
      /^🏁/.test(trimmed) ||
      /^Progress:/.test(trimmed) ||
      /^Recent:/.test(trimmed) ||
      /^---/.test(trimmed)
    );
  }

  function extractOptions(text) {
    const options = [];
    for (const line of text.split('\n')) {
      const t = line.trim();
      if (/^[\dA-Za-z][.\)】）:]/.test(t) && !/^---/.test(t)) options.push(t);
    }
    return options;
  }

  function extractNarrativeUnits(text) {
    const units = [];
    const pendingMeta = [];

    function pushUnit(unit) {
      if (pendingMeta.length) {
        unit.raw = pendingMeta.concat(unit.raw).join('\n');
        pendingMeta.length = 0;
      }
      units.push(unit);
    }

    for (const line of text.split('\n')) {
      const raw = line.trim();
      if (!raw || isSkippedLine(raw)) continue;
      if (/^\[SCENE:\s*\w+\]$/i.test(raw)) {
        pendingMeta.push(raw);
        continue;
      }

      if (raw.startsWith('###')) {
        pushUnit({ type: 'title', raw, text: raw.replace(/^###\s*/, '') });
      } else if (raw.startsWith('>')) {
        pushUnit({ type: 'quote', raw, text: raw.replace(/^>\s*/, '') });
      } else if (/「[^」]+」/.test(raw) && raw.indexOf('「') > 0) {
        pushUnit({
          type: 'dialogue',
          raw,
          text: global.AvgMood?.formatPageLineForDisplay(raw) ?? raw,
        });
      } else {
        pushUnit({
          type: 'para',
          raw,
          text: global.AvgMood?.formatPageLineForDisplay(raw) ?? raw,
        });
      }
    }
    return units;
  }

  function renderPageText(container, text) {
    container.innerHTML = '';
    for (const unit of extractNarrativeUnits(text)) {
      if (unit.type === 'title') {
        const span = document.createElement('span');
        span.className = 'scene-title';
        span.textContent = unit.text;
        container.appendChild(span);
      } else if (unit.type === 'quote') {
        const p = document.createElement('p');
        p.textContent = unit.text;
        p.style.cssText =
          'color:rgba(200,180,255,.6);font-style:italic;padding-left:10px;border-left:2px solid rgba(200,180,255,.2);margin:4px 0;';
        container.appendChild(p);
      } else {
        const p = document.createElement('p');
        p.textContent = unit.text;
        container.appendChild(p);
      }
    }
  }

  function renderUnits(container, units) {
    container.innerHTML = '';
    for (const unit of units) {
      if (unit.type === 'title') {
        const span = document.createElement('span');
        span.className = 'scene-title';
        span.textContent = unit.text;
        container.appendChild(span);
      } else if (unit.type === 'quote') {
        const p = document.createElement('p');
        p.textContent = unit.text;
        p.style.cssText =
          'color:rgba(200,180,255,.6);font-style:italic;padding-left:10px;border-left:2px solid rgba(200,180,255,.2);margin:4px 0;';
        container.appendChild(p);
      } else {
        const p = document.createElement('p');
        p.textContent = unit.text;
        container.appendChild(p);
      }
    }
  }

  function getMeasureBox(textBody) {
    let el = document.getElementById('avgTextMeasure');
    if (!el) {
      el = document.createElement('div');
      el.id = 'avgTextMeasure';
      el.className = 'text-body text-measure';
      el.setAttribute('aria-hidden', 'true');
      textBody.parentElement.insertBefore(el, textBody);
    }
    el.style.width = textBody.clientWidth + 'px';
    return el;
  }

  function paginateUnits(units, textBodyEl) {
    const fallbackLines = 4;
    if (!textBodyEl || !units.length) {
      const pages = [];
      let current = [];
      for (const unit of units) {
        if (unit.type === 'dialogue') {
          if (current.length) pages.push(current);
          current = [];
          pages.push([unit]);
        } else {
          current.push(unit);
          if (current.length >= fallbackLines) {
            pages.push(current);
            current = [];
          }
        }
      }
      if (current.length) pages.push(current);
      return pages.length ? pages : [[]];
    }

    const measure = getMeasureBox(textBodyEl);
    const maxH = textBodyEl.clientHeight;
    if (!maxH || maxH < 8) {
      const pages = [];
      for (let i = 0; i < units.length; i += fallbackLines) {
        pages.push(units.slice(i, i + fallbackLines));
      }
      return pages.length ? pages : [[]];
    }

    const pages = [];
    let current = [];
    for (const unit of units) {
      if (unit.type === 'dialogue') {
        if (current.length) {
          pages.push(current);
          current = [];
        }
        pages.push([unit]);
        continue;
      }

      const trial = current.concat(unit);
      renderUnits(measure, trial);
      if (measure.scrollHeight > maxH && current.length > 0) {
        pages.push(current);
        current = [unit];
      } else {
        current = trial;
      }
    }
    if (current.length) pages.push(current);
    return pages.length ? pages : [[]];
  }

  function unitsToPageText(units) {
    return units.map((u) => u.raw).join('\n');
  }

  function splitIntoPages(text, textBodyEl) {
    const units = extractNarrativeUnits(text);
    const options = extractOptions(text);
    if (!units.length) return { pages: [], options };

    const pageGroups = paginateUnits(units, textBodyEl);
    const pages = pageGroups.map(unitsToPageText).filter((p) => p.trim());
    return { pages, options };
  }

  global.AvgEngine = { createEngine, escapeHtml, splitIntoPages, renderPageText };
})(window);
