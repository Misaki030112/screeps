// Flattens src/**.js into dist/<a.b.c>.js and rewrites require paths to flat names.
const fs = require('fs'), path = require('path');
const SRC = path.join(__dirname, '..', 'src'), DIST = path.join(__dirname, '..', 'dist');
fs.rmSync(DIST, { recursive: true, force: true }); fs.mkdirSync(DIST);
const flat = rel => rel.replace(/\.js$/, '').split(path.sep).join('.');
function walk(d) { return fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith('.js') ? [path.join(d, e.name)] : []); }
for (const file of walk(SRC)) {
  const code = fs.readFileSync(file, 'utf8').replace(/require\((['"])(\.{1,2}\/[^'"]+)\1\)/g, (m, q, p) => {
    const target = path.resolve(path.dirname(file), p);
    const rel = path.relative(SRC, target.endsWith('.js') ? target : target + '.js');
    if (!fs.existsSync(path.join(SRC, rel))) throw new Error(`${file}: cannot resolve ${p}`);
    return `require('${flat(rel)}')`;
  });
  fs.writeFileSync(path.join(DIST, flat(path.relative(SRC, file)) + '.js'), code);
}
console.log('built', fs.readdirSync(DIST).join(', '));
