// Runs every hand-built case of ground-truth/cases.json against the tool. Each case runs twice.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluate } from './checks.mjs';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const cases = JSON.parse(fs.readFileSync(path.join(root, 'ground-truth/cases.json'), 'utf8'));
const only = process.argv[2];
const results = [];
for (const c of cases) {
  if (only && !c.id.startsWith(only)) continue;
  const text = fs.readFileSync(path.join(root, c.dataset), 'utf8');
  const first = await evaluate(text, c.expect, c.view);
  const second = await evaluate(text, c.expect, c.view);
  const stable = JSON.stringify(first) === JSON.stringify(second);
  const failed = first.filter(x => !x.pass);
  results.push({ id: c.id, feature: c.feature, version: c.version, dataset: c.dataset, kind: c.kind, basis: c.basis,
    status: failed.length === 0 && stable ? 'PASS' : 'FAIL', stable, checks: first });
  const mark = failed.length === 0 ? 'PASS' : 'FAIL';
  console.log(`${mark} ${c.id} [${c.kind}] ${c.feature}`);
  for (const f of failed) console.log(`      ${f.check}\n        expected: ${JSON.stringify(f.expected)}\n        actual:   ${JSON.stringify(f.actual)?.slice(0, 600)}`);
}
fs.mkdirSync(path.join(root, 'reports/partial'), { recursive: true });
if (!only) fs.writeFileSync(path.join(root, 'reports/partial/cases.json'), JSON.stringify(results, null, 1));
const fails = results.filter(r => r.status === 'FAIL');
console.log(`\n${results.length} cases: ${results.length - fails.length} PASS, ${fails.length} FAIL (${fails.filter(f => f.kind === 'prd').length} against the PRD/design, ${fails.filter(f => f.kind === 'fix').length} against FIX / business truth)`);
