// Synthetic inputs only. This is an integration regression, not app acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';

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
  scope: 'Owned binding, feature/semantic trace, version and view fixtures; real corrected CLI',
  product_readiness: 'NOT_ASSESSED',
  host: { platform: process.platform, arch: process.arch, node: process.version },
  cases: [],
};
function call(runtime, id, args, expectedOperation) {
  const cli = path.join(runtime, 'scripts/rea.mjs');
  const result = spawnSync(process.execPath, [cli, ...args, '--json'], {
    cwd: root,
    env: { PATH: process.env.PATH, HOME: path.join(root, 'home'), TMPDIR: process.env.TMPDIR || '/tmp', NO_COLOR: '1', REA_LOG_LEVEL: 'silent' },
    timeout: 180000, maxBuffer: 24 * 1024 * 1024,
  });
  const stdout = result.stdout || Buffer.alloc(0), stderr = result.stderr || Buffer.alloc(0);
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
  record.evidence_id = evidence.evidence_id; record.subject = evidence.subject;
  return { evidence, record };
}
function request(id, command, payload, operation) {
  const file = path.join(inputs, id + '.json');
  fs.writeFileSync(file, JSON.stringify(payload), {flag:'wx'});
  return call(candidate, id, [command, file], operation);
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
const expected = {'17':['parse'],'18':['declared','extra','named','parse'],'19':['parse'],
  '20':[],'21':['parse'],'22':['real'],'23':['parse'],'24':['parse'],'25':[''],'26':['default']};
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
  assert.deepEqual(oldExports['17'], ['parse']);
  assert.notDeepEqual(oldExports['19'], ['parse'], 'Baseline defect not reproduced');
  before.record.status = 'PASS'; before.record.meaning = 'Known defect reproduced, NOT baseline approval'; before.record.exports = oldExports;
  const fixed = call(candidate, 'corrected-bindings', ['analyze-javascript-application', fixture], 'analyze_javascript_application');
  assert.deepEqual(exportsByKey(fixed.evidence), expected);
  fixed.record.status = 'PASS'; fixed.record.exports = exportsByKey(fixed.evidence);
  const summary = request('corrected-summary','inspect-analysis-view',
    {source:{kind:'inline',evidence:fixed.evidence},view:{kind:'summary'}},'inspect_analysis_view');
  assert.equal(summary.evidence.subject.digest.sha256, fixed.evidence.subject.digest.sha256);
  assert.ok(JSON.stringify(summary.evidence.normalized_result).includes(fixed.evidence.evidence_id));
  summary.record.status = 'PASS';

  const module = fixed.evidence.normalized_result.graph.nodes.find(n => n.kind==='javascript-module' && n.observations.some(o=>o.properties.module_key==='19'));
  assert.ok(module, 'Independent expected module 19 absent');
  const trace = request('feature-trace','trace-application-feature',
    {application:fixed.evidence,seed:{kind:'node-id',value:module.node_id,match:'exact',case_sensitive:true},direction:'both'},'trace_application_feature');
  assert.equal(trace.evidence.normalized_result.source_evidence_id,fixed.evidence.evidence_id);
  assert.deepEqual(trace.evidence.normalized_result.seed_matches.map(x=>x.node_id),[module.node_id]);
  assert.ok(trace.evidence.normalized_result.graph.nodes.some(n=>n.node_id===module.node_id));
  trace.record.status='PASS';
  const absent=request('feature-no-match','trace-application-feature',
    {application:fixed.evidence,seed:{kind:'node-id',value:'jag_node_'+'0'.repeat(64),match:'exact'},direction:'both'},'trace_application_feature');
  assert.equal(absent.evidence.normalized_result.summary.matched_seeds,0);
  assert.equal(absent.evidence.normalized_result.coverage.status,'no-match');absent.record.status='PASS';

  const semanticGraph=fixed.evidence.normalized_result.semantic_graph;
  assert.ok(semanticGraph.nodes.length>0 && semanticGraph.relations.length>0);
  const seed=semanticGraph.nodes.find(n=>n.kind==='binding') || semanticGraph.nodes[0];
  const semantics=request('semantic-trace','trace-javascript-semantics',
    {application:fixed.evidence,query:{seed:{kind:'semantic-node',node_id:seed.node_id},direction:'backward-provenance'}},'trace_javascript_semantics');
  assert.equal(semantics.evidence.normalized_result.source_evidence_id,fixed.evidence.evidence_id);
  assert.deepEqual(semantics.evidence.normalized_result.seed_node_ids,[seed.node_id]);
  assert.ok(semantics.evidence.normalized_result.nodes.some(n=>n.node_id===seed.node_id));semantics.record.status='PASS';

  const newer=path.join(inputs,'newer');fs.mkdirSync(newer);
  const nextSource=source.replace('19(e) { e.exports = {parse: value => value}; }','19(e) { e.exports = {parse: value => value, addedApi: 123}; }');
  assert.notEqual(nextSource,source);fs.writeFileSync(path.join(newer,'bundle.js'),nextSource);
  const next=call(candidate,'new-version',['analyze-javascript-application',newer],'analyze_javascript_application');
  assert.deepEqual(exportsByKey(next.evidence)['19'],['addedApi','parse']);next.record.status='PASS';
  const compare=request('version-comparison','compare-application-versions',
    {left:fixed.evidence,right:next.evidence},'compare_application_versions');
  const comparison=compare.evidence.normalized_result;
  assert.equal(comparison.left.evidence_id,fixed.evidence.evidence_id);assert.equal(comparison.right.evidence_id,next.evidence.evidence_id);
  assert.notEqual(comparison.left.root_artifact_sha256,comparison.right.root_artifact_sha256);
  assert.ok(comparison.items.some(item=>item.left_node_id===module.node_id && ['changed','removed'].includes(item.status)),'Known changed module not detected');
  compare.record.status='PASS';compare.record.summary=comparison.summary;
  assert.equal(fs.existsSync(sentinel),false,'Target JavaScript was executed');

  // Content identity for the exact installed runtime; this does not attest the producer.
  const roots=['package.json','package-lock.json','scripts','dist','bridge','native','third_party','licenses','LICENSE','THIRD_PARTY_NOTICES.md','node_modules'];
  const entries=[];
  function walk(relative){
    const full=path.join(candidate,relative);if(!fs.existsSync(full))return;
    const s=fs.lstatSync(full);
    if(s.isSymbolicLink()){
      const target=fs.readlinkSync(full);const resolved=fs.realpathSync(full);
      assert.ok(resolved===candidate || resolved.startsWith(candidate+path.sep),'Runtime link escapes prefix');
      entries.push({path:relative,link:target});
    }else if(s.isDirectory()){
      for(const name of fs.readdirSync(full).sort())walk(relative+'/'+name);
    }else{assert.ok(s.isFile(),'Non-regular runtime entry');entries.push({path:relative,sha256:digest(fs.readFileSync(full)),bytes:s.size});}
  }
  roots.forEach(walk);
  entries.sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0);
  const manifest={schema_version:1,runtime_id:'rea-6.5.0-patch3552.1',release_commit:'3b79af28e80785afce9f5998d8f03289402a1847',patch_commit:'20643d4a47b0562aa794f0a15903630c62912c80',patch_blob:'cf3f9aca413a00ebf5a5b8e4a5c94999776506ce',entries};
  const bytes=Buffer.from(JSON.stringify(manifest));
  fs.writeFileSync(path.join(out,'runtime-manifest.json'),bytes,{flag:'wx'});
  report.runtime_manifest_sha256=digest(bytes);report.runtime_entries=entries.length;
  report.status='PASS';
} catch(error){report.status='FAIL';report.error=String(error.stack||error);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,'binding-report.json'),JSON.stringify(report,null,2),{flag:'wx'});console.log(JSON.stringify(report,null,2));}
