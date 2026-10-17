// Synthetic inputs only. This is an integration regression, not app acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const root = process.env.REA_QUALIFICATION_ROOT;
assert.ok(root && path.isAbsolute(root), 'Explicit qualification root required');
const candidate = process.env.REA_CANDIDATE_ROOT;
const baseline = process.env.REA_BASELINE_ROOT;
assert.ok(candidate && baseline, 'Both exact runtimes are required');
const out = path.join(root, 'output');
const inputs = path.join(root, 'inputs');
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(inputs, { recursive: true });
const digest = data => createHash('sha256').update(data).digest('hex');
const report = {
  schema_version: 1,
  scope: 'Owned export-binding fixtures, real baseline and corrected CLI',
  product_readiness: 'NOT_ASSESSED',
  host: { platform: process.platform, arch: process.arch, node: process.version },
  cases: [],
};
function call(runtime, id, args, expectedOperation) {
  const cli = path.join(runtime, 'scripts/rea.mjs');
  const result = spawnSync(process.execPath, [cli, ...args, '--json'], {
    cwd: root,
    env: { PATH: process.env.PATH, HOME: path.join(root, 'home'), TMPDIR: process.env.TMPDIR || '/tmp', NO_COLOR: '1', REA_LOG_LEVEL: 'silent' },
    timeout: 180000,
    maxBuffer: 24 * 1024 * 1024,
  });
  const stdout = result.stdout || Buffer.alloc(0);
  const stderr = result.stderr || Buffer.alloc(0);
  fs.writeFileSync(path.join(out, id + '.stdout.json'), stdout, { flag: 'wx' });
  fs.writeFileSync(path.join(out, id + '.stderr.txt'), stderr, { flag: 'wx' });
  const record = { id, argv: args, exit_code: result.status, signal: result.signal,
    stdout_sha256: digest(stdout), stderr_sha256: digest(stderr), status: 'FAIL' };
  report.cases.push(record);
  assert.equal(result.error, undefined, id + ': execution error');
  assert.equal(result.status, 0, id + ': CLI failed; inspect retained stderr');
  const evidence = JSON.parse(stdout);
  assert.equal(evidence.operation, expectedOperation, id + ': unexpected operation');
  assert.match(evidence.evidence_id, /^ev_[a-f0-9]{64}$/);
  assert.ok(Array.isArray(evidence.limitations));
  record.evidence_id = evidence.evidence_id;
  record.subject = evidence.subject;
  // The caller must run the semantic assertions before marking this case PASS.
  return { evidence, record };
}
function exportsByKey(evidence) {
  const result = {};
  for (const node of evidence.normalized_result.graph.nodes) {
    if (node.kind !== 'javascript-module') continue;
    for (const observation of node.observations) {
      const p = observation.properties;
      if (typeof p?.module_key !== 'string') continue;
      assert.ok(!Object.hasOwn(result, p.module_key), 'Duplicate module key');
      result[p.module_key] = p.exports;
    }
  }
  return result;
}
const expected = {
  '17': ['parse'],
  '18': ['declared', 'extra', 'named', 'parse'],
  '19': ['parse'],
  '20': [],
  '21': ['parse'],
  '22': ['real'],
  '23': ['parse'],
  '24': ['parse'],
  '25': [''],
  '26': ['default'],
};
try {
  fs.mkdirSync(path.join(root, 'home'), { recursive: true });
  const fixture = path.join(inputs, 'bindings');
  fs.mkdirSync(fixture, { recursive: true });
  const sentinel = path.join(out, 'target-executed');
  const source = `
import { writeFileSync } from 'node:fs';
writeFileSync(${JSON.stringify(sentinel)}, 'unexpected execution');
throw new Error('This input is static-analysis data and must not execute');
globalThis.webpackChunkApp.push([[1], {
  17(module, exports) { module.exports = {parse: value => value}; },
  18(e = {}, t = {}, r) {
    e.exports = {parse: value => value}; e.exports.extra = 1;
    Object.defineProperty(e.exports, 'named', {value: 1});
    r.d(t, {declared: () => 1});
    function shadow(e = {}, t = {}) { e.exports.fake = 1; t.fake = 1; }
    { const module = {exports:{}}; module.exports.fake = 1; }
  },
  19(e) { e.exports = {parse: value => value}; },
  20(exports) { exports.parse = 1; },
  21(exports) { exports.exports.parse = 1; },
  22(e, t) { { const e = {exports:{}}; e.exports.fake = 1; } e.exports.real = 1; },
  23(e, t = {}) { t.parse = 1; },
  24(module = {}, exports = {}) { module.exports = {parse: value => value}; },
  25(e, t) { e['exports'][''] = 1; },
  26(e, t) { e.exports = value => value; }
}]);
`;
  fs.writeFileSync(path.join(fixture, 'bundle.js'), source);
  report.fixture_sha256 = digest(Buffer.from(source));
  const before = call(baseline, 'baseline-bindings', ['analyze-javascript-application', fixture], 'analyze_javascript_application');
  const oldExports = exportsByKey(before.evidence);
  assert.deepEqual(oldExports['17'], ['parse'], 'Baseline control must work');
  assert.notDeepEqual(oldExports['19'], ['parse'], 'Expected baseline bug was not reproduced');
  before.record.status = 'PASS';
  before.record.meaning = 'Known defect reproduced, NOT approval of baseline';
  before.record.exports = oldExports;
  const fixed = call(candidate, 'corrected-bindings', ['analyze-javascript-application', fixture], 'analyze_javascript_application');
  assert.deepEqual(exportsByKey(fixed.evidence), expected);
  assert.equal(fs.existsSync(sentinel), false, 'Input JavaScript was executed');
  fixed.record.status = 'PASS';
  fixed.record.exports = exportsByKey(fixed.evidence);
  const request = path.join(inputs, 'view-request.json');
  fs.writeFileSync(request, JSON.stringify({source:{kind:'inline',evidence:fixed.evidence},view:{kind:'summary'}}));
  const summary = call(candidate, 'corrected-summary', ['inspect-analysis-view', request], 'inspect_analysis_view');
  assert.equal(summary.evidence.subject.digest.sha256, fixed.evidence.subject.digest.sha256);
  assert.ok(JSON.stringify(summary.evidence.normalized_result).includes(fixed.evidence.evidence_id), 'Parent identity missing from summary');
  summary.record.status = 'PASS';
  // Record the actual built schemas for the remaining independently reviewed probes.
  const { toolContract } = await import(pathToFileURL(path.join(candidate, 'dist/contracts/toolContracts.js')));
  const { z } = await import(pathToFileURL(path.join(candidate, 'node_modules/zod/index.js')));
  const contracts = {};
  for (const name of ['trace_application_feature','trace_javascript_semantics','compare_application_versions','compare_artifacts','compare_functions','trace_dylib_resolution']) {
    const c = toolContract(name);
    contracts[name] = { examples:c.examples, input:z.toJSONSchema(c.inputSchema, {unrepresentable:'any'}) };
  }
  fs.writeFileSync(path.join(out, 'built-contracts.json'), JSON.stringify(contracts, null, 2), {flag:'wx'});
  console.log('BUILT_CONTRACTS=' + JSON.stringify(contracts));
  report.status = 'PASS';
} catch (error) {
  report.status = 'FAIL';
  report.error = String(error.stack || error);
  process.exitCode = 1;
} finally {
  fs.writeFileSync(path.join(out, 'binding-report.json'), JSON.stringify(report, null, 2), {flag:'wx'});
  console.log(JSON.stringify(report, null, 2));
}
