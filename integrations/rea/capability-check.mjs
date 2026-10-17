// All inputs below are owned fixtures. No third-party target is executed.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const runtime=path.resolve(process.env.REA_RUNTIME);
const out=path.resolve(process.env.REA_OUTPUT);
const work=fs.realpathSync(fs.mkdtempSync('/tmp/rea-capabilities-'));
const cli=path.join(runtime,'scripts/rea.mjs');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const report={schema_version:1,source_commit:'20643d4a47b0562aa794f0a15903630c62912c80',host:{platform:process.platform,arch:process.arch,node:process.version},status:'FAIL',cases:[],product_readiness:'NOT_ASSESSED'};
const env={...process.env,HOME:path.join(work,'home'),TMPDIR:work,NO_COLOR:'1',REA_LOG_LEVEL:'silent'};fs.mkdirSync(env.HOME);
function command(id,exe,args){
 const r=spawnSync(exe,args,{cwd:work,env,timeout:360000,maxBuffer:32*1024*1024});
 fs.writeFileSync(path.join(out,id+'.stdout'),r.stdout??Buffer.alloc(0));
 fs.writeFileSync(path.join(out,id+'.stderr'),r.stderr??Buffer.alloc(0));
 const item={id,exit_code:r.status,signal:r.signal,status:'FAIL',stdout_sha256:sha(r.stdout??''),stderr_sha256:sha(r.stderr??'')};report.cases.push(item);
 assert.ifError(r.error);assert.equal(r.status,0,id+': retained stderr contains details');item.status='PASS';return r.stdout;
}
const rea=(id,args)=>{const data=JSON.parse(command(id,process.execPath,[cli,...args,'--json']));assert.match(data.evidence_id,/^ev_[0-9a-f]{64}$/);return data;};
const check=(id,fn)=>{const item={id,status:'FAIL'};report.cases.push(item);fn();item.status='PASS';};
const request=(name,data)=>{const p=path.join(work,name+'.json');fs.writeFileSync(p,JSON.stringify(data));return p;};
try{
 const app=path.join(work,'app');fs.mkdirSync(app);
 fs.writeFileSync(path.join(app,'package.json'),JSON.stringify({name:'owned-fixture',version:'1.0.0',type:'module',main:'main.js'}));
 fs.writeFileSync(path.join(app,'main.js'),'import {sum} from "./math.js"; export function calculate(a,b){return sum(a,b);}\nthrow new Error("Target must not execute");\n');
 fs.writeFileSync(path.join(app,'math.js'),'export function sum(a,b){return a+b;}\n');
 const zip=path.join(work,'fixture.zip');
 command('create-owned-zip','python3',['-c','import pathlib,sys,zipfile; p=pathlib.Path(sys.argv[1]); z=zipfile.ZipFile(sys.argv[2],"w"); [z.write(f,f.name) for f in sorted(p.iterdir())]; z.close()',app,zip]);
 const inv=rea('package-inventory',['inspect-artifact',zip]);
 check('inventory-source-digest',()=>{assert.equal(inv.subject.digest.sha256,sha(fs.readFileSync(zip)));for(const name of ['main.js','math.js','package.json'])assert.ok(JSON.stringify(inv.normalized_result).includes(name));});
 const left=rea('js-module-analysis',['analyze-javascript-application',app]);
 const trace=rea('feature-trace',['trace-application-feature',request('trace',{application:left,seed:{kind:'module',value:'main.js',match:'contains'},direction:'both'})]);
 check('feature-cross-module-relations',()=>{assert.ok(trace.normalized_result.summary.matched_seeds>0);assert.ok(trace.normalized_result.summary.traced_edges>0);assert.ok(JSON.stringify(trace.normalized_result.graph).includes('math.js'));});
 fs.writeFileSync(path.join(app,'added.js'),'export function subtract(a,b){return a-b;}\n');
 const right=rea('js-second-version',['analyze-javascript-application',app]);
 const compared=rea('version-comparison',['compare-application-versions',request('compare',{left,right})]);
 check('version-change-and-identities',()=>{assert.notEqual(left.subject.digest.sha256,right.subject.digest.sha256);assert.ok(compared.normalized_result.summary.added>0);assert.equal(compared.normalized_result.left.evidence_id,left.evidence_id);assert.equal(compared.normalized_result.right.evidence_id,right.evidence_id);});
 const view=rea('focused-view',['inspect-analysis-view',request('view',{source:{kind:'inline',evidence:right},view:{kind:'summary'}})]);
 check('view-preserves-parent',()=>assert.equal(view.subject.digest.sha256,right.subject.digest.sha256));
 // Source-owned C fixture is compiled but never launched.
 const c=path.join(work,'sample.c'),binary=path.join(work,'sample');
 fs.writeFileSync(c,'__attribute__((noinline)) int owned_sum(int a,int b){return a+b;}\nint main(void){return owned_sum(2,3);}\n');
 command('compile-native-fixture','cc',['-O0','-g',c,'-o',binary]);
 const native=rea('ghidra-overview',['analyze',binary,'--provider','ghidra']);
 check('native-provider-and-digest',()=>{assert.equal(native.subject.digest.sha256,sha(fs.readFileSync(binary)));assert.ok(JSON.stringify(native.provider).toLowerCase().includes('ghidra'));});
 const func=rea('ghidra-function',['function',binary,'owned_sum','--provider','ghidra']);
 check('native-function-found',()=>assert.ok(JSON.stringify(func.normalized_result).includes('owned_sum')));
 if(process.platform==='darwin'){
   const bundle=path.join(work,'Owned.app');fs.mkdirSync(path.join(bundle,'Contents','MacOS'),{recursive:true});
   fs.copyFileSync(binary,path.join(bundle,'Contents','MacOS','Owned'));
   fs.writeFileSync(path.join(bundle,'Contents','Info.plist'),'<?xml version="1.0"?><plist version="1.0"><dict><key>CFBundleExecutable</key><string>Owned</string><key>CFBundleIdentifier</key><string>test.owned.fixture</string></dict></plist>');
   const dmg=path.join(work,'Owned.dmg');
   command('create-owned-dmg','hdiutil',['create','-srcfolder',bundle,'-format','UDZO','-volname','OwnedFixture',dmg]);
   const disk=rea('macos-dmg-inventory',['inspect-artifact',dmg]);
   check('dmg-source-digest',()=>assert.equal(disk.subject.digest.sha256,sha(fs.readFileSync(dmg))));
   const dependency=rea('macos-dylib-resolution',['trace-dylib-resolution',bundle]);
   check('dylib-evidence-retained',()=>assert.ok(dependency.normalized_result && Array.isArray(dependency.limitations)));
 }
 report.status='PASS';
}catch(error){report.error=String(error);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,'capability-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));}
