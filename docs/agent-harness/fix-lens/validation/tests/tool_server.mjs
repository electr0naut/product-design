// A line server around the tool, for the Python property and differential tests.
// One JSON request per line on stdin: { id, text, render? }  ->  one JSON answer per line on stdout.
import readline from 'node:readline';
import { analyse, renderText, orderGroups } from './harness.mjs';
import { tradesOf, statsOf, gapsOf, eventsOf } from './checks.mjs';

const rl = readline.createInterface({ input: process.stdin });
for await (const line of rl) {
  if (!line.trim()) continue;
  const { id, text, render } = JSON.parse(line);
  const t0 = performance.now();
  let out;
  try {
    const a = analyse(text);
    out = { id, ok: a.ok, threw: null,
      errors: a.errors.map(e => ({ number: e.number, rule: e.rule, position: e.position })),
      messages: a.messages.map(m => ({ number: m.number, fields: m.fields.map(f => [f.tag, f.value]) })) };
    if (render) {
      const r = await renderText(a);
      Object.assign(out, { stats: statsOf(r), trades: tradesOf(r), events: eventsOf(a), gaps: gapsOf(a), groups: orderGroups(a.decoded).map(g => g.numbers) });
    }
  } catch (error) {
    out = { id, threw: String(error?.stack ?? error) };
  }
  out.ms = performance.now() - t0;
  process.stdout.write(JSON.stringify(out) + '\n');
}
