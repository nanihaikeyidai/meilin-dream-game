const fs = require('fs');
const p = 'd:/HermesWorkspace/girlgame-skill/frontend/index.html';
let h = fs.readFileSync(p, 'utf8');
h = h.replaceAll('<motion ', '<div ');
h = h.replaceAll('</motion>', '</div>');
fs.writeFileSync(p, h);
console.log('done');
