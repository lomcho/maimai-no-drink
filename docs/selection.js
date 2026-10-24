'use strict';
const money=v=>'¥'+(v/100).toFixed(2);
function matchingQuotes(data,target,strict,allowExtra){
 if(!target.length)return [];
 const seen=new Set();
 return data.rows.filter(r=>r.fees_complete&&target.every(k=>(r.foods[k]||0)>=1)&&(!strict||!r.foods['903050'])&&(allowExtra||Object.entries(r.foods).every(([k,n])=>k==='903050'||(target.includes(k)&&n===1)))).sort((a,b)=>a.payable_fen-b.payable_fen).filter(r=>{const key=JSON.stringify(Object.entries(r.foods).sort());if(seen.has(key))return false;seen.add(key);return true;});
}
function valueQuotes(data,target,base,cap){
 return matchingQuotes(data,target,true,true).filter(r=>Object.entries(r.foods).some(([k,n])=>k!=='903050'&&n>(target.includes(k)?1:0))&&(!base||r.payable_fen-base.payable_fen<=cap)).slice(0,2);
}
function extraFoods(r,target){return Object.entries(r.foods).filter(([k,n])=>k!=='903050'&&n-(target.includes(k)?1:0)>0).map(([k,n])=>`${DATA.catalog[k]} × ${n-(target.includes(k)?1:0)}`);}
const $=id=>document.getElementById(id);
function selected(){return [...document.querySelectorAll('[data-food]:checked')].map(b=>b.dataset.food==='burger'?$('burgerKind').value:b.dataset.food).sort();}
function render(){
 const target=selected(),strict=$('strict').checked,allowExtra=$('extra').checked,cap=Number($('extraBudget').value);
 $('valueCards').innerHTML='';$('valueHint').textContent='';$('valueSection').hidden=!allowExtra;$('extraBudget').disabled=!allowExtra;
 $('burgerKind').disabled=!document.querySelector('[data-food="burger"]').checked;
 $('copyStatus').textContent='';$('copy').disabled=!target.length;$('copyRequest').disabled=!target.length;
 const prompt='使用 $maimai-no-drink。我想吃'+target.map(k=>DATA.catalog[k]+'1份').join('、')+'。'+(strict?'完全不要饮料。':'家里有饮料，但更便宜的含饮料套餐也可以比较。')+(allowExtra?`请另列不含饮料、包含全部目标食品的加量备选，最多加${cap/100}元，明确整单差价和多出的食物。`:'只要所选食物和份量，不接受额外小食。')+'请查询本次麦乐送菜单及可用优惠，比较含配送和打包费的实际付款，不下单。';
 $('requestText').value=target.length?prompt:'';
 if(!target.length){$('summary').textContent='先选至少一种想吃的';$('counts').textContent='尚未选择';$('cards').innerHTML='';$('explanation').textContent='汉堡、对翅、鸡块、薯条都可以自由组合。';$('copyText').value='';return;}
 const all=DATA.rows.filter(r=>r.target.join(',')===target.join(','));
 const quotes=matchingQuotes(DATA,target,strict,false),base=all.find(r=>r.baseline);
 if(!quotes.length||!base){$('summary').textContent='这个组合还没有完整核价';$('counts').textContent='待询价';$('cards').innerHTML='';$('explanation').textContent='不估算优惠；复制下方需求进行真实询价。';$('copyText').value=prompt;return;}
 const best=quotes[0],saved=base.payable_fen-best.payable_fen;
 const upgrades=allowExtra?valueQuotes(DATA,target,best,cap):[];
 $('summary').textContent=saved>0?`按需买实付 ${money(best.payable_fen)}，比按需单点少 ${money(saved)}`:`按需买实付 ${money(best.payable_fen)}，与单点基准同价`;
 const noDrink=quotes.filter(r=>!r.foods['903050']).length;
 $('counts').textContent=`指定份量 ${quotes.length} 种 · 无饮料 ${noDrink} 种 · 加量备选 ${upgrades.length} 种`;
 const lines=[];
 $('cards').innerHTML=quotes.map((r,i)=>{
  const extras=extraFoods(r,target),delta=base.payable_fen-r.payable_fen;
  const description=Object.entries(r.foods).map(([k,n])=>`${DATA.catalog[k]} × ${n}`).join('、');
  const diff=r.baseline?'按需单点基准':delta>0?`比按需单点少 ${money(delta)}`:delta<0?`比按需单点多 ${money(-delta)}`:'与按需单点同价';
  lines.push(`${r.name}：${money(r.payable_fen)}，${diff}；${description}（餐品${money(r.food_fen)}＋配送${money(r.delivery_fen)}＋打包${money(r.packing_fen)}）`);
  return `<article class="card ${i===0?'best':''}"><small>${i===0?'指定份量中实付最低':'其他已核价方案'} · ${r.foods['903050']?'含饮料':'无饮料'}</small><h3>${r.name}</h3><div class="price">${money(r.payable_fen)}</div><p>${description}</p><div class="bill">餐品 ${money(r.food_fen)} ＋ 配送 ${money(r.delivery_fen)} ＋ 打包 ${money(r.packing_fen)}</div><div class="extra">${diff}<br>${extras.length?'额外小食：'+extras.join('、'):'没有额外小食'}${r.foods['903050']?'；另带中杯可乐':''}</div></article>`;
 }).join('');
 $('valueCards').innerHTML=upgrades.map(r=>{
  const delta=r.payable_fen-best.payable_fen,extras=extraFoods(r,target);
  const diff=delta>0?`多付 ${money(delta)}`:delta<0?`反而少付 ${money(-delta)}`:'同价多得';
  const description=Object.entries(r.foods).map(([k,n])=>`${DATA.catalog[k]} × ${n}`).join('、');
  lines.push(`加量备选：${r.name}，整单${money(r.payable_fen)}，比按需买${diff}；多得${extras.join('、')}；实际包含${description}；无饮料`);
  return `<article class="card"><small>保留全部所选食品 · 无饮料</small><h3>${diff}</h3><div class="price">${money(r.payable_fen)}</div><p>${r.name}</p><div class="extra"><b>多得：${extras.join('、')}</b></div><p>${description}</p><div class="bill">餐品 ${money(r.food_fen)} ＋ 配送 ${money(r.delivery_fen)} ＋ 打包 ${money(r.packing_fen)}</div></article>`;
 }).join('');
 $('valueHint').textContent=upgrades.length?`相对按需买，最多多付${cap/100}元。加价是额外支出，多出的食物是否需要由你决定。`:`已核价样例中没有加价${cap/100}元以内的无饮料加量方案，可调整上限或保持按需买。`;
 $('explanation').textContent=`按需单点基准 ${money(base.payable_fen)}。仅统计本例已核价候选，不代表全菜单选择总数。差价来自整单试算，不是把饮料价格直接扣掉。`;
 $('copyText').value=`【历史报价体验 · 非当前报价】\n需求：${target.map(k=>DATA.catalog[k]+'1份').join('＋')}\n${strict?'完全不要饮料':'允许附带饮料'}；${allowExtra?'另看无饮料加量备选，最多多付'+cap/100+'元':'不接受多带小食'}\n${lines.join('\n')}\n核价时间：${DATA.queried_at}。${DATA.scope}。本次无可用券。仅比较本例候选，购买前重新核价。`;
}
document.querySelectorAll('[data-food],#burgerKind,#strict,#extra,#extraBudget').forEach(el=>el.addEventListener('change',render));
document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>{const set=b.dataset.preset.split(',');document.querySelectorAll('[data-food]').forEach(c=>c.checked=set.includes(c.dataset.food));render();}));
async function copyField(id){const el=$(id);try{await navigator.clipboard.writeText(el.value);$('copyStatus').textContent='已复制，报价日期或询价要求已保留。';}catch{el.focus();el.select();$('copyStatus').textContent='已选中文字，请手动复制。';}}
$('copy').addEventListener('click',()=>copyField('copyText'));
$('copyRequest').addEventListener('click',()=>copyField('requestText'));
render();
