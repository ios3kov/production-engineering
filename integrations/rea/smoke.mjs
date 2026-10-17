// Real published-CLI qualification on synthetic inputs only. Run inside the
// workflow's network-disabled, read-only container, not on user applications.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const runtime = '/runtime';
const out = '/out';
const cli = path.join(runtime, 'node_modules/rea-agents/scripts/rea.mjs');
const metadata = JSON.parse(fs.readFileSync(path.join(runtime, 'node_modules/rea-agents/package.json')));
assert.equal(metadata.name, 'rea-agents');
assert.equal(metadata.version, '6.5.0');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const report = {schema_version: 1, package: {name: metadata.name, version: metadata.version,
  entry_sha256: sha(fs.readFileSync(cli)),
  dependency_lock_sha256: sha(fs.readFileSync(path.join(runtime, 'package-lock.json')))},
  host: {node: process.version, platform: process.platform, arch: process.arch},
  scope: 'Synthetic ZIP and JavaScript, real published REA CLI; not AE/iPhone qualification',
  product_readiness: 'NOT_ASSESSED', cases: []};

function call(id, args, expectedOperation) {
  const result = spawnSync(process.execPath, [cli, ...args, '--json'], {
    cwd: '/tmp', env: {PATH: process.env.PATH, HOME: '/tmp/rea-home', TMPDIR: '/tmp',
      NO_COLOR: '1'},
    timeout: 150000, maxBuffer: 16 * 1024 * 1024,
  });
  const stdout = result.stdout ?? Buffer.alloc(0);
  const stderr = result.stderr ?? Buffer.alloc(0);
  fs.writeFileSync(path.join(out, id + '.stdout.json'), stdout, {flag:'wx'});
  fs.writeFileSync(path.join(out, id + '.stderr.txt'), stderr, {flag:'wx'});
  const record = {id, argv: args, exit_code: result.status, signal: result.signal,
    stdout_sha256: sha(stdout), stderr_sha256: sha(stderr), status: 'FAIL'};
  report.cases.push(record);
  if (result.error) record.error = result.error.message;
  assert.equal(result.error, undefined, id + ': subprocess error');
  assert.equal(result.status, 0, id + ': exit status; inspect retained stderr');
  const data = JSON.parse(stdout.toString('utf8'));
  assert.equal(data.operation, expectedOperation, id + ': unexpected result schema/operation');
  assert.match(data.evidence_id, /^ev_/);
  assert.ok(data.normalized_result && typeof data.normalized_result === 'object');
  assert.ok(Array.isArray(data.limitations), 'limitations must remain present');
  record.evidence_id = data.evidence_id;
  record.subject = data.subject;
  record.limitations = data.limitations;
  record.status = 'PASS';
  return data;
}

try {
  fs.mkdirSync('/tmp/rea-home', {recursive:true});
  const inv = call('zip-inventory', ['inspect-artifact', '/inputs/sample.zip'], 'inspect_artifact');
  assert.equal(inv.subject.digest.sha256, sha(fs.readFileSync('/inputs/sample.zip')));
  assert.ok(JSON.stringify(inv.normalized_result).includes('main.js'), 'fixture member absent');
  const js = call('javascript-analysis', ['analyze-javascript-application', '/inputs/app'], 'analyze_javascript_application');
  assert.ok(JSON.stringify(js.normalized_result).includes('main.js'), 'entry module absent');
  assert.ok(JSON.stringify(js.normalized_result).includes('math.js'), 'imported module absent');
  // Full parent evidence, not a lossy summary, is used by the upstream view tool.
  const request = '/tmp/view-request.json';
  fs.writeFileSync(request, JSON.stringify({source:{kind:'inline',evidence:js},view:{kind:'summary'}}));
  call('retained-summary', ['inspect-analysis-view', request], 'inspect_analysis_view');
  assert.equal(fs.existsSync('/out/target-executed'), false, 'Target JavaScript was executed');
  report.status = 'PASS';
} catch (error) {
  report.status = 'FAIL';
  report.error = String(error);
  process.exitCode = 1;
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2), {flag:'wx'});
  console.log(JSON.stringify(report, null, 2));
}
