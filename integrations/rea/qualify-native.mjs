// Execute only against the source-owned fixtures created by the named workflow.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const root=process.env.REA_QUALIFICATION_ROOT;
const runtime=process.env.REA_CANDIDATE_ROOT;
const lane=process.env.REA_QUALIFICATION_LANE;
assert.ok(root && path.isAbsolute(root) && runtime && ['ghidra','macos'].includes(lane));
const out=path.join(root,'output');
fs.mkdirSync(out,{recursive:true});
fs.mkdirSync(path.join(root,'home'),{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={schema_version:1,lane,scope:'Owned native/package fixtures only',product_readiness:'NOT_ASSESSED',host:{platform:process.platform,arch:process.arch,node:process.version},cases:[]};
const cli=path.join(runtime,'scripts/rea.mjs');
function call(id,args){
 const env={PATH:process.env.PATH,HOME:path.join(root,'home'),TMPDIR:process.env.TMPDIR||'/tmp',NO_COLOR:'1',REA_LOG_LEVEL:'silent'};
 if(lane==='ghidra'){env.GHIDRA_INSTALL_DIR=process.env.GHIDRA_INSTALL_DIR;env.JAVA_HOME=process.env.JAVA_HOME;}
 const r=spawnSync(process.execPath,[cli,...args,'--json'],{cwd:root,env,timeout:240000,maxBuffer:32*1024*1024});
 const stdout=r.stdout||Buffer.alloc(0),stderr=r.stderr||Buffer.alloc(0);
 fs.writeFileSync(path.join(out,id+'.stdout.json'),stdout,{flag:'wx'});
 fs.writeFileSync(path.join(out,id+'.stderr.txt'),stderr,{flag:'wx'});
 const record={id,args,exit_code:r.status,signal:r.signal,stdout_sha256:sha(stdout),stderr_sha256:sha(stderr),status:'FAIL'};report.cases.push(record);
 assert.equal(r.error,undefined,id+': subprocess error');assert.equal(r.status,0,id+': inspect retained stderr');
 const data=JSON.parse(stdout);assert.match(data.evidence_id,/^ev_[a-f0-9]{64}$/);assert.ok(Array.isArray(data.limitations));
 record.evidence_id=data.evidence_id;record.subject=data.subject;record.limitations=data.limitations;
 return {data,record};
}
function objects(value){const result=[];const stack=[value];while(stack.length){const x=stack.pop();if(x && typeof x==='object'){result.push(x);stack.push(...Object.values(x));}}return result;}
try{
 report.package=JSON.parse(fs.readFileSync(path.join(runtime,'package.json'))).version;
 assert.equal(report.package,'6.5.0');
 report.entry_sha256=sha(fs.readFileSync(cli));
 if(lane==='ghidra'){
   const binary=path.join(root,'inputs','fixture');const binaryHash=sha(fs.readFileSync(binary));
   const f=call('ghidra-function',['function',binary,'rea_sum','--provider','ghidra']);
   assert.equal(f.data.subject.digest.sha256,binaryHash);
   assert.equal(f.data.operation,'analyze_function');
   const result=f.data.normalized_result;
   assert.equal(result.procedure.name,'rea_sum');assert.ok(typeof result.pseudocode==='string' && result.pseudocode.includes('+'),'Addition missing from real pseudocode');
   assert.ok(result.assembly.length>0);assert.ok(result.callers.length>0,'Expected main caller absent');
   f.record.status='PASS';
   const decompiled=call('ghidra-decompile',['decompile',binary,result.procedure.address,'--provider','ghidra']);
   assert.equal(decompiled.data.subject.digest.sha256,binaryHash);
   assert.ok(JSON.stringify(decompiled.data.normalized_result).includes('+'),'No addition in decompiled result');decompiled.record.status='PASS';
   const refs=call('ghidra-xrefs',['xrefs',binary,result.procedure.address,'--provider','ghidra']);
   assert.equal(refs.data.subject.digest.sha256,binaryHash);
   assert.ok(objects(refs.data.normalized_result).some(x=>Array.isArray(x) && x.length>0),'No incoming reference facts');refs.record.status='PASS';
 }else{
   const bundle=path.join(root,'inputs','Sample.app');
   const inventory=call('macos-bundle',['inspect-artifact',bundle]);
   assert.ok(objects(inventory.data.normalized_result).some(x=>x.logical_path==='Contents/Frameworks/libfixture.dylib'),'Library missing in inventory');inventory.record.status='PASS';
   const loads=call('macos-dylib',['trace-dylib-resolution',bundle]);
   const loadText=JSON.stringify(loads.data.normalized_result);
   assert.ok(loadText.includes('libfixture.dylib') && loadText.includes('resolved'),'Own dylib resolution absent');loads.record.status='PASS';
   const disk=path.join(root,'inputs','sample.dmg');const dmg=call('macos-dmg',['inspect-artifact',disk]);
   assert.equal(dmg.data.subject.digest.sha256,sha(fs.readFileSync(disk)));
   assert.ok(objects(dmg.data.normalized_result).some(x=>typeof x.logical_path==='string' && x.logical_path.endsWith('/Contents/MacOS/Sample')),'Mounted DMG child executable missing');dmg.record.status='PASS';
 }
 report.status='PASS';
}catch(e){report.status='FAIL';report.error=String(e.stack||e);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,lane+'-report.json'),JSON.stringify(report,null,2),{flag:'wx'});console.log(JSON.stringify(report,null,2));}
