const fs=require('fs'),vm=require('vm'),assert=require('assert');
const data=JSON.parse(fs.readFileSync('examples/multiselect-quotes.json','utf8'));
const source=fs.readFileSync('docs/selection.js','utf8').split('const $=')[0];
const ctx=vm.createContext({DATA:data});vm.runInContext(source,ctx);
const rank=(t,s,e)=>ctx.matchingQuotes(data,t,s,e);
const targets=[...new Set(data.rows.map(r=>r.target.join(',')))].map(s=>s.split(','));
assert.equal(targets.length,23);
for(const target of targets){
 const base=data.rows.find(r=>r.baseline&&r.target.join(',')===target.join(','));assert(base);
 for(const strict of [true,false])for(const extra of [true,false]){
  const rows=rank(target,strict,extra);assert(rows.length);
  for(const r of rows){assert.equal(r.payable_fen,r.food_fen+r.delivery_fen+r.packing_fen);assert(target.every(k=>r.foods[k]>=1));if(strict)assert(!r.foods['903050']);if(!extra)assert(Object.entries(r.foods).every(([k,n])=>k==='903050'||target.includes(k)&&n===1));}
  assert(rows[0].payable_fen<=base.payable_fen);
 }
}
assert.equal(rank(['901401','501205','901700'],true,true)[0].payable_fen,4780);
assert.equal(rank(['901401','501205','901700'],true,false)[0].payable_fen,5490);
assert.equal(rank(['901440','901700','901401'],false,false)[0].payable_fen,5380);
assert.equal(rank(['901440','901700','901401'],true,false)[0].payable_fen,6520);
assert.equal(rank([],true,true).length,0);assert.equal(rank(['unknown'],true,true).length,0);
console.log('PASS: 23 targets x 4 preference states, fee completeness, food coverage, strict drinks, extra portions, examples, empty/unknown');
