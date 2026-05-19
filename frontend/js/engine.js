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
      const explicit = text.match(/\[EXPR:\s*(\w+)\]/i);
      if (explicit) return explicit[1].toLowerCase();

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
      const exts = ['svg', 'png'];
      const expressions = [expression];
      if (expression !== 'default') expressions.push('default');

      const paths = [];
      for (const expr of expressions) {
        for (const ext of exts) {
          paths.push(base + expr + '.' + ext);
        }
      }
      return paths;
    }

    function updateSprite(spriteImage, textNameEl, charName, expression) {
      const charId = portraits[charName];
      if (!charId) {
        spriteImage.classList.remove('visible', 'slide-in-left', 'slide-in-right');
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
          spriteImage.classList.remove('visible', 'slide-in-left', 'slide-in-right');
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
        spriteImage.classList.remove('slide-in-left', 'slide-in-right');
        void spriteImage.offsetWidth;
        spriteImage.classList.add(Math.random() > 0.5 ? 'slide-in-left' : 'slide-in-right');
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
      const charName = detectCharacter(text);
      if (!charName) return null;
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

  function splitIntoPages(text) {
    const paragraphBlocks = [];
    const lines = text.split('\n');

    let currentBlock = '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        if (currentBlock) {
          paragraphBlocks.push(currentBlock.trim());
          currentBlock = '';
        }
        continue;
      }
      if (
        /^[\dA-Za-z][.\)】）:]/.test(trimmed) ||
        /^❤/.test(trimmed) ||
        /^\[GALGAME STATE\]/.test(trimmed) ||
        /^Scene:/.test(trimmed) ||
        /^🏁/.test(trimmed) ||
        /^Progress:/.test(trimmed) ||
        /^Recent:/.test(trimmed) ||
        /^---/.test(trimmed)
      ) {
        if (currentBlock) {
          paragraphBlocks.push(currentBlock.trim());
          currentBlock = '';
        }
        continue;
      }
      currentBlock += trimmed + '\n';
    }
    if (currentBlock) paragraphBlocks.push(currentBlock.trim());

    const options = [];
    for (const line of lines) {
      const t = line.trim();
      if (/^[\dA-Za-z][.\)】）:]/.test(t) && !/^---/.test(t)) options.push(t);
    }

    const merged = [];
    let buffer = '';
    for (const block of paragraphBlocks) {
      if (!buffer) {
        buffer = block;
        continue;
      }
      if (buffer.length + block.length < 300 || block.length < 80) {
        buffer += '\n\n' + block;
      } else {
        merged.push(buffer);
        buffer = block;
      }
    }
    if (buffer) merged.push(buffer);

    return { pages: merged, options };
  }

  global.AvgEngine = { createEngine, escapeHtml, splitIntoPages };
})(window);
