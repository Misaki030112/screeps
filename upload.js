// Usage: node upload.js [branch]  -- runs checks first, uploads dist/ (flat modules).
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
execSync('node ' + path.join(__dirname, 'scripts', 'check.js'), { stdio: 'inherit' });
const token = fs.readFileSync(path.join(__dirname, '.env'), 'utf8').match(/SCREEPS_TOKEN=(\S+)/)[1];
const branch = process.argv[2] || 'default';
const DIST = path.join(__dirname, 'dist'), modules = {};
for (const f of fs.readdirSync(DIST)) modules[f.slice(0, -3)] = fs.readFileSync(path.join(DIST, f), 'utf8');
fetch('https://screeps.com/api/user/code', { method: 'POST', headers: { 'X-Token': token, 'Content-Type': 'application/json; charset=utf-8' }, body: JSON.stringify({ branch, modules }) })
  .then(r => r.json()).then(j => { console.log('upload', branch, j); if (!j.ok) process.exit(1); });
