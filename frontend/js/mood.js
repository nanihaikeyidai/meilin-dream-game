/**
 * MOOD / EXPR：剧情页解析、立绘映射、TTS 情绪（对齐 VoxCPM2 Voice Design）
 * @see https://github.com/OpenBMB/VoxCPM — 括号内自然语言描述控制语气/情绪
 */
(function (global) {
  const MOOD_TO_EXPR = {
    neutral: 'default',
    warm: 'smile',
    happy: 'happy',
    sad: 'sad',
    angry: 'angry',
    cold: 'cold',
    surprised: 'surprised',
    blush: 'blush',
  };

  const VALID_MOODS = Object.keys(MOOD_TO_EXPR);
  const VALID_EXPRS = [
    'default', 'smile', 'happy', 'sad', 'angry', 'blush', 'cold', 'surprised',
  ];

  const MOOD_LABELS = {
    neutral: '平常',
    warm: '温和',
    happy: '开心',
    sad: '悲伤',
    angry: '生气',
    cold: '冷漠',
    surprised: '惊讶',
    blush: '害羞',
  };

  const KEYWORD_TO_MOOD = {
    微笑: 'warm',
    浅笑: 'warm',
    开心: 'happy',
    大笑: 'happy',
    愉快: 'happy',
    悲伤: 'sad',
    伤心: 'sad',
    哭: 'sad',
    哽咽: 'sad',
    生气: 'angry',
    愤怒: 'angry',
    怒: 'angry',
    冷漠: 'cold',
    冷淡: 'cold',
    冰冷: 'cold',
    惊讶: 'surprised',
    震惊: 'surprised',
    愣: 'surprised',
    脸红: 'blush',
    害羞: 'blush',
    羞涩: 'blush',
  };

  function normalizeMood(raw) {
    if (!raw) return 'neutral';
    const m = String(raw).toLowerCase();
    if (VALID_MOODS.includes(m)) return m;
    for (const [k, v] of Object.entries(KEYWORD_TO_MOOD)) {
      if (raw.includes(k)) return v;
    }
    return 'neutral';
  }

  function normalizeExpression(raw) {
    if (!raw) return null;
    const e = String(raw).toLowerCase();
    return VALID_EXPRS.includes(e) ? e : null;
  }

  function detectMood(text) {
    const match = text.match(/\[MOOD:\s*(\w+)\]/i);
    if (match) return normalizeMood(match[1]);
    for (const [keyword, mood] of Object.entries(KEYWORD_TO_MOOD)) {
      if (text.includes(keyword)) return mood;
    }
    return null;
  }

  function detectExpression(text) {
    const match = text.match(/\[EXPR:\s*(\w+)\]/i);
    if (match) return normalizeExpression(match[1]);
    return null;
  }

  function moodToExpression(mood) {
    return MOOD_TO_EXPR[mood] || 'default';
  }

  function getMoodLabel(mood) {
    return MOOD_LABELS[mood] || MOOD_LABELS.neutral;
  }

  /** 有台词但无 MOOD 标签时，从上下文关键词推断 */
  function inferMood(pageText) {
    const fromTag = detectMood(pageText);
    if (fromTag) return fromTag;
    if (!/「[^」]+」/.test(pageText)) return null;
    return 'neutral';
  }

  function stripEmotionTags(text) {
    return text
      .replace(/\[MOOD:\s*\w+\]/gi, '')
      .replace(/\[EXPR:\s*\w+\]/gi, '')
      .replace(/\[SCENE:\s*\w+\]/gi, '')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  /**
   * 解析一页剧情：角色、MOOD、EXPR、对白
   * @param {string} pageText
   * @param {Record<string,string>} portraits 角色名 → charId
   */
  function parsePageBeat(pageText, portraits) {
    if (!pageText || !portraits) return null;

    let charName = null;
    let charId = null;
    for (const name of Object.keys(portraits)) {
      if (pageText.includes(name)) {
        charName = name;
        charId = portraits[name];
        break;
      }
    }
    if (!charName) return null;

    const dialogueMatch = pageText.match(/「([^」]*)」/);
    const dialogue = dialogueMatch ? dialogueMatch[1].trim() : '';

    let mood = detectMood(pageText);
    if (!mood && dialogue) mood = inferMood(pageText) || 'neutral';
    if (!mood) mood = 'neutral';

    let expression = detectExpression(pageText);
    if (!expression) expression = moodToExpression(mood);

    return {
      charName,
      charId,
      mood,
      expression,
      moodLabel: getMoodLabel(mood),
      dialogue,
      hasDialogue: !!dialogue,
    };
  }

  /** 渲染用：去掉标签，保留角色名与对白 */
  function formatPageLineForDisplay(line) {
    const t = line.trim();
    if (!t) return '';
    return stripEmotionTags(t);
  }

  global.AvgMood = {
    MOOD_TO_EXPR,
    MOOD_LABELS,
    VALID_MOODS,
    VALID_EXPRS,
    normalizeMood,
    normalizeExpression,
    detectMood,
    detectExpression,
    moodToExpression,
    getMoodLabel,
    inferMood,
    stripEmotionTags,
    parsePageBeat,
    formatPageLineForDisplay,
  };
})(window);
