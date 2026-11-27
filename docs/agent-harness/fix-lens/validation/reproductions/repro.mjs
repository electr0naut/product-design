// Reproduces one defect (or all): prints, for each of its fixtures, what a correct reading is and what FIX Lens shows.
//   FIX_LENS_DIR=<product> node reproductions/repro.mjs FL-01        (no argument: every defect)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluate } from '../tests/checks.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const index = JSON.parse(fs.readFileSync(path.join(here, 'index.json'), 'utf8'));
const want = process.argv[2];
let failures = 0;
for (const d of index) {
  if (want && d.defect !== want) continue;
  console.log(`\n=== ${d.defect} (${d.severity}) ${d.title}`);
  for (const c of d.fixtures) {
    const text = fs.readFileSync(path.join(here, c.file), 'utf8');
    const checks = (await evaluate(text, c.expect, c.view)).filter(x => !x.pass);
    failures += checks.length ? 1 : 0;
    console.log(`  ${c.file}  (${c.test}: ${c.feature})`);
    console.log(`    input:    ${text.replaceAll('\x01', '|').split('\n').filter(Boolean).map(l => (l.length > 150 ? l.slice(0, 150) + ' …' : l)).join('\n              ')}`);
    if (!checks.length) console.log('    NOT REPRODUCED: the tool gave the expected result');
    for (const k of checks) console.log(`    ${k.check}\n      expected: ${JSON.stringify(k.expected)}\n      actual:   ${JSON.stringify(k.actual)}`);
  }
}
console.log(`\n${failures} fixture(s) reproduce a defect`);
