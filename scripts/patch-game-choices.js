const fs = require('fs');
const path = require('path');
const p = path.join(__dirname, '..', 'frontend', 'game.html');
let h = fs.readFileSync(p, 'utf8');
const d = 'div';

const newBlock = [
  '    <', d, ' class="text-window">',
  '\n      <', d, ' class="choices-in-window choices-overlay" id="choicesOverlay"></', d, '>',
  '\n      <', d, ' class="text-bg"></', d, '>',
  '\n      <', d, ' class="text-inner">',
].join('');

const oldBlock = [
  '    <', d, ' class="text-window">',
  '\n      <', d, ' class="text-bg"></', d, '>',
  '\n      <', d, ' class="text-inner">',
].join('');

if (h.includes('id="choicesOverlay"')) {
  console.log('choices already patched');
} else {
  h = h.replace(oldBlock, newBlock);
  if (!h.includes('id="choicesOverlay"')) {
    console.error('failed to insert choicesOverlay');
    process.exit(1);
  }
}

h = h.replace(
  /\n  <!-- 选项覆盖 -->\n  <div class="choices-overlay" id="choicesOverlay"><\/div>\n/g,
  '\n'
);

const scripts = [
  '<script src="js/template-registry.js"></script>',
  '<script src="js/mood.js"></script>',
  '<script src="js/engine.js"></script>',
  '<script src="js/api.js"></script>',
  '<script src="js/stream.js"></script>',
  '<script src="js/tts.js"></script>',
  '<script src="js/save.js"></script>',
  '<script src="js/bootstrap.js"></script>',
].join('\n');

h = h.replace(
  /<script src="js\/template-registry.js"><\/script>[\s\S]*?<script src="js\/bootstrap.js"><\/script>/,
  scripts
);

fs.writeFileSync(p, h);
console.log('done, has choices-in-window:', h.includes('choices-in-window'));
