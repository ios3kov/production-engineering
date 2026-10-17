// Qualification of a pinned REA source build. Only generated test inputs.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync, spawn} from 'node:child_process';
import {createInterface} from 'node:readline';

const root = path.resolve(process.env.REA_RUNTIME ?? '/runtime');
const out = path.resolve(process.env.REA_OUTPUT ?? '/out');
const work = fs.mkdtempSync('/tmp/rea-repair-');
const cli = path.join(root, 'scripts/rea.mjs');
const commit = '20643d4a47b0562aa794f0a15903630c62912c80';
const sha = value => createHash('sha256').update(value).digest('hex');
const report = {schema_version:1, source_commit:commit, host:{platform:process.platform,arch:process.arch,node:process.version},
  qualification_scope:'Generated fixtures; not application or device acceptance', status:'FAIL', cases:[]};
fs.mkdirSync(out,{recursive:true});
const environment = {...process.env,HOME:path.join(work,'home'),TMPDIR:work,REA_LOG_LEVEL:'silent',NO_COLOR:'1'};
fs.mkdirSync(environment.HOME);
const record = (id, fn) => {
  const item={id,status:'FAIL'};report.cases.push(item);
  const result=fn(); item.status='PASS';return result;
};
function call(id,args){
  const r=spawnSync(process.execPath,[cli,...args,'--json'],{cwd:work,env:environment,timeout:150000,maxBuffer:32*1024*1024});
  fs.writeFileSync(path.join(out,id+'.stdout.json'),r.stdout??Buffer.alloc(0));
  fs.writeFileSync(path.join(out,id+'.stderr.txt'),r.stderr??Buffer.alloc(0));
  const item={id,argv:args,exit_code:r.status,signal:r.signal,status:'FAIL',stdout_sha256:sha(r.stdout??''),stderr_sha256:sha(r.stderr??'')};
  report.cases.push(item);
  assert.ifError(r.error);assert.equal(r.status,0,id+': inspect retained stderr');
  const data=JSON.parse(r.stdout);assert.match(data.evidence_id,/^ev_[0-9a-f]{64}$/);
  assert.ok(data.normalized_result && typeof data.normalized_result==='object');
  item.status='PASS';item.evidence_id=data.evidence_id;item.subject=data.subject;return data;
}
function factoryExports(evidence){
  return Object.fromEntries(evidence.normalized_result.graph.nodes.filter(n=>n.kind==='javascript-module')
    .flatMap(n=>n.observations.filter(o=>o.properties.module_key!==undefined).map(o=>[o.properties.module_key,o.properties.exports])));
}
let server;
try{
  const source=fs.readFileSync(path.join(root,'src/domain/javascript/javascriptAstFingerprint.ts'));
  report.producer_sha256=sha(source);
  report.lock_sha256=sha(fs.readFileSync(path.join(root,'package-lock.json')));
  const app=path.join(work,'app');fs.mkdirSync(app);
  fs.writeFileSync(path.join(app,'bundle.js'),`
    throw new Error('Target must never execute');
    globalThis.webpackChunkOwned.push([[1], {
      17(module, exports) { module.exports = { parse: value => value }; },
      18(e, t) { e.exports = { parse: value => value }; },
      19(e = {}, t = {}, r) {
        e.exports = { parse: value => value }; e.exports.extra = 1;
        Object.defineProperty(e.exports,'named',{value:1});r.d(t,{declared:()=>1});
        function shadow(e = {}, t = {}) { e.exports.fake=1; t.fake=1; }
        { const e = {exports:{}};e.exports.fake=1; }
      },
      20(e) { e.exports = {parse: value => value}; },
      21(exports) { exports.parse=1; },
      22(exports) { exports.exports.parse=1; },
      23(e,t) { function shadow(module) { module.exports.fake=1; } },
      24(e,t) { e['exports']['']=1; }
    }]);
  `);
  const expected={'17':['parse'],'18':['parse'],'19':['declared','extra','named','parse'],'20':['parse'],'21':[],'22':['parse'],'23':[],'24':['']};
  const js=call('javascript-export-regression',['analyze-javascript-application',app]);
  record('renamed-defaulted-shadowed-positional-exports',()=>assert.deepEqual(factoryExports(js),expected));
  const request=path.join(work,'view.json');
  fs.writeFileSync(request,JSON.stringify({source:{kind:'inline',evidence:js},view:{kind:'summary'}}));
  const view=call('retained-summary',['inspect-analysis-view',request]);
  record('summary-parent-identity',()=>assert.equal(view.subject.digest.sha256,js.subject.digest.sha256));
  // Real stdio MCP; a configuration file alone does not establish a connection.
  server=spawn(process.execPath,[cli,'mcp'],{cwd:work,env:environment,stdio:['pipe','pipe','pipe']});
  const pending=new Map();let seq=0;let stderr='';
  server.stderr.on('data',chunk=>{if(stderr.length<65536)stderr+=chunk;});
  const lines=createInterface({input:server.stdout});
  lines.on('line',line=>{try{const message=JSON.parse(line);const p=pending.get(message.id);if(p){pending.delete(message.id);clearTimeout(p.timer);message.error?p.reject(Error(JSON.stringify(message.error))):p.resolve(message.result);}}catch(error){for(const p of pending.values())p.reject(error);}});
  server.on('error',error=>{for(const p of pending.values())p.reject(error);});
  server.on('exit',code=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('MCP exited '+code));}pending.clear();});
  const rpc=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error('MCP timeout: '+method));},150000);pending.set(id,{resolve,reject,timer});server.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');});
  const init=await rpc('initialize',{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'owned-rea-qualification',version:'1.0.0'}});
  assert.ok(init.serverInfo);server.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n');
  const catalog=await rpc('tools/list');
  fs.writeFileSync(path.join(out,'mcp-catalog.json'),JSON.stringify(catalog,null,2));
  assert.ok(catalog.tools.some(t=>t.name==='analyze_javascript_application'));
  const reply=await rpc('tools/call',{name:'analyze_javascript_application',arguments:{input_path:app}});
  fs.writeFileSync(path.join(out,'mcp-analysis.json'),JSON.stringify(reply,null,2));
  assert.notEqual(reply.isError,true);
  const evidence=reply.structuredContent;
  record('mcp-export-regression',()=>assert.deepEqual(factoryExports(evidence),expected));
  record('cli-mcp-evidence-identity',()=>assert.equal(evidence.evidence_id,js.evidence_id));
  await rpc('ping');report.status='PASS';
  fs.writeFileSync(path.join(out,'mcp.stderr.txt'),stderr);
}catch(error){report.error=String(error);process.exitCode=1;}
finally{
  if(server){server.stdin.end();const timer=setTimeout(()=>server.kill('SIGTERM'),3000);timer.unref();}
  fs.writeFileSync(path.join(out,'repair-report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
}
