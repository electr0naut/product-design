// Logic-module benchmarks under Node. One child process per measurement, so that peak memory is per dataset.
//   FIX_LENS_DIR=<product> node --expose-gc benchmarks/bench_node.mjs --perf <dir from generators/build.py --perf> \
//        [--lifted <copy of the product with the limit raised>] --out reports/partial/bench-node.json
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, x, i, all) => (x.startsWith('--') ? [...acc, [x.slice(2), all[i + 1]]] : acc), []));
const SOH = '\x01';
const enc = new TextEncoder();
function msg(fields, begin = 'FIX.4.4') {
  const body = fields.map(([t, v]) => `${t}=${v}${SOH}`).join('');
  const head = `8=${begin}${SOH}9=${enc.encode(body).length}${SOH}`;
  let sum = 0;
  for (const b of enc.encode(head + body)) sum += b;
  return `${head}${body}10=${String(sum % 256).padStart(3, '0')}${SOH}`;
}
const HEAD = [[35, 'D'], [49, 'A'], [56, 'B'], [34, 1], [52, '20261127-09:00:00.000']];
const hostile = {
  'one message with a 1,000,000-character value': () => msg([...HEAD, [58, 'L'.repeat(1_000_000)]]),
  'one message with 100,000 fields': () => msg([...HEAD, ...Array.from({ length: 100_000 }, (_, i) => [5000 + (i % 900), 'v'])]),
  'pipe form, 1,000,000 literal pipes in a value': () => `8=FIX.4.4|9=5|35=0|58=${'|'.repeat(1_000_000)}`,
  'caret form, 1,000,000 carets in a value': () => `8=FIX.4.4^A9=5^A35=0^A58=${'^'.repeat(1_000_000)}`,
  'angle form, 250,000 near-miss "<SOH" in a value': () => `8=FIX.4.4<SOH>9=5<SOH>35=0<SOH>58=${'<SOH'.repeat(250_000)}`,
  '"8=FIX" 200,000 times with no delimiter': () => '8=FIX'.repeat(200_000),
  '"8=FIX|" 170,000 times (over the message limit)': () => '8=FIX|'.repeat(170_000),
  '"18=FIX" 170,000 times (never a start)': () => '18=FIX'.repeat(170_000),
  'pipe form, 300,000 empty-looking fields "|1=|"': () => `8=FIX.4.4|9=5|35=0${'|1='.repeat(300_000)}|10=000|`,
  '1,000 messages chained by OrigClOrdID (one order)': () => Array.from({ length: 1000 }, (_, i) => msg([[35, 'G'], [49, 'A'], [56, 'B'], [34, i + 1], [11, `C${i + 1}`], [41, `C${i}`], [55, 'ACME'], [54, 1], [38, 100]])).join('\n'),
  '1 MiB of newlines and "=" signs': () => '=\n'.repeat(524_288),
};

if (args.child) {
  const product = args.child;
  const mod = name => import(pathToFileURL(path.join(product, 'src', name)).href);
  const t0 = performance.now();
  const { analyse } = await mod('analyse.js');
  const importMs = performance.now() - t0;
  const { checkLimits } = await mod('limits.js');
  const { splitMessages, checkMessage } = await mod('framing.js');
  const { decode } = await mod('decode.js');
  const { timeline } = await mod('timeline.js');
  const { orderGroups } = await mod('orders.js');
  const { tradeSummary } = await mod('summary.js');
  const { applyFilters, filterOptions } = await mod('filters.js');
  const text = args.hostile ? hostile[args.hostile]() : fs.readFileSync(args.file, 'utf8');
  const runs = Number(args.runs ?? 15);
  const time = fn => { const s = performance.now(); const r = fn(); return [performance.now() - s, r]; };
  const many = fn => { const xs = []; for (let i = 0; i < runs; i++) xs.push(time(fn)[0]); xs.sort((a, b) => a - b); return { min: xs[0], median: xs[Math.floor(xs.length / 2)], max: xs.at(-1) }; };
  const [firstMs, result] = time(() => analyse(text));
  const out = { importMs, firstMs, ok: result.ok, bytes: enc.encode(text).length, messages: result.ok ? result.messages.length + result.errors.length : result.limit.messages,
    valid: result.messages.length, malformed: result.errors.length, warning: result.limit?.warning ?? null, partialOutput: !result.ok && (result.decoded.length + result.timeline.length + result.errors.length) > 0 };
  out.analyse = many(() => analyse(text));
  if (result.ok && !args.hostile) {
    const candidates = splitMessages(text);
    const valid = candidates.filter(c => !checkMessage(c, text));
    out.modules = {
      checkLimits: many(() => checkLimits(text)), splitMessages: many(() => splitMessages(text)),
      checkMessage: many(() => candidates.forEach(c => checkMessage(c, text))), decode: many(() => valid.map(m => decode(m, text))),
      timeline: many(() => timeline(valid)), orderGroups: many(() => orderGroups(result.decoded)),
      tradeSummary: many(() => tradeSummary(result.decoded, undefined)), filterOptions: many(() => filterOptions(result.decoded)),
    };
    const options = filterOptions(result.decoded);
    if (options.account.length) out.modules.applyFiltersAccount = many(() => applyFilters(result.decoded, { account: options.account[0] }));
    if (options.senderCompId.length) out.modules.applyFiltersSender = many(() => applyFilters(result.decoded, { senderCompId: options.senderCompId[0] }));
    out.orders = orderGroups(result.decoded).length;
    out.directions = new Set(result.timeline.map(e => `${e.sender}>${e.target}`)).size;
  }
  globalThis.gc?.();
  out.heapRetainedMb = process.memoryUsage().heapUsed / 1048576;      // with the analysis result still referenced
  out.keep = result.messages.length;                                   // keeps `result` alive until here
  out.maxRssMb = process.resourceUsage().maxRSS / 1024;
  process.stdout.write(JSON.stringify(out));
} else {
  const self = fileURLToPath(import.meta.url);
  const product = process.env.FIX_LENS_DIR;
  const rows = [];
  const child = (prod, extra) => {
    const r = spawnSync(process.execPath, ['--expose-gc', self, '--child', prod, ...extra], { encoding: 'utf8', timeout: 600_000, maxBuffer: 1 << 26 });
    if (r.status !== 0) return { failed: true, signal: r.signal, stderr: r.stderr?.slice(-400) };
    return JSON.parse(r.stdout);
  };
  const baseline = child(product, ['--file', path.join(args.perf, 'mix-100.log'), '--runs', '1']);   // process baseline for memory
  const run = (suite, label, prod, extra, limit) => {
    const repeats = [1, 2, 3].map(() => child(prod, extra));           // three fresh processes, to tell noise from signal
    const m = repeats[1];
    const row = { suite, dataset: label, product: limit, ...m, processRepeatsAnalyseMedianMs: repeats.map(x => x.analyse?.median ?? null) };
    rows.push(row);
    const per = m.failed ? '' : ` | ${(m.messages / (m.analyse.median / 1000)).toFixed(0)} msg/s, ${(m.bytes / 1048576 / (m.analyse.median / 1000)).toFixed(1)} MB/s, maxRSS ${m.maxRssMb.toFixed(0)} MB`;
    console.log(`${suite} | ${label} | ${limit} | ${m.failed ? `FAILED ${m.signal ?? ''} ${m.stderr ?? ''}` : `ok=${m.ok} messages=${m.messages} first=${m.firstMs.toFixed(1)}ms median=${m.analyse.median.toFixed(2)}ms`}${per}`);
    return row;
  };
  for (const n of [100, 250, 500, 999, 1000]) run('inside the limits', `mix-${n}`, product, ['--file', path.join(args.perf, `mix-${n}.log`)], 'v1.2');
  for (const n of [1001, 10000]) run('over the limit', `mix-${n}`, product, ['--file', path.join(args.perf, `mix-${n}.log`)], 'v1.2');
  for (const f of fs.readdirSync(args.perf).filter(f => /^(extra|sessions|malformed|bytes)-/.test(f)).sort()) run('variants', f.replace('.log', ''), product, ['--file', path.join(args.perf, f)], 'v1.2');
  for (const name of Object.keys(hostile)) run('hostile input', name, product, ['--hostile', name, '--runs', '5'], 'v1.2');
  if (args.lifted) {
    for (const n of [1000, 2500, 5000, 10000]) run('limit lifted to 10,000 (information)', `mix-${n}`, args.lifted, ['--file', path.join(args.perf, `mix-${n}.log`)], 'copy, limit lifted');
    run('limit lifted to 10,000 (information)', '10,000 messages chained by OrigClOrdID', args.lifted, ['--file', path.join(args.perf, 'chain-10000.log'), '--runs', '5'], 'copy, limit lifted');
  }
  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  fs.writeFileSync(args.out, JSON.stringify({ node: process.version, baselineMaxRssMb: baseline.maxRssMb, rows }, null, 1));
}
