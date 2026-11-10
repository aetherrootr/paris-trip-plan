(()=>{'use strict';
function fits(date,start,end,kind){return !date||kind==='permanent'||kind==='uncertain'||(!start||date>=start)&&(!end||date<=end);}
if(typeof module!=='undefined'&&module.exports){module.exports={fits};return;}
const root=document.getElementById('day-exhibitions');if(!root)return;
const input=document.getElementById('exhibition-date'),reset=document.getElementById('exhibition-reset'),status=document.getElementById('exhibition-filter-status');
function refresh(){const date=input.value;if(date&&(!input.validity.valid||date<'2027-02-01'||date>'2027-03-31')){status.textContent='请选择2027年2月1日至3月31日之间的日期。';return;}let count=0;
for(const group of root.querySelectorAll('.exhibition-venue')){let visible=0;for(const card of group.querySelectorAll('.exhibition-item')){const match=fits(date,card.dataset.exhibitionStart,card.dataset.exhibitionEnd,card.dataset.exhibitionKind);card.hidden=!match;if(match){visible++;count++;}card.querySelector('.exhibition-date-state').textContent=card.dataset.exhibitionKind==='uncertain'?'日期待核':card.dataset.exhibitionKind==='programme'?'活动日另核':card.dataset.exhibitionKind==='permanent'?'常设':date?'展期匹配':'已公布展期';}group.querySelector('.exhibition-empty').hidden=visible!==0;if(date)group.open=true;}
status.textContent=date?`${date}：${count}项展期匹配、常设或待核项目；仍需核对当天闭馆、活动场次与票务。`:'未选日期：显示与2027年2—3月相关的已公布展览及待核项目。';}
function openHash(){let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}if(!id.startsWith('exhibitions-'))return;const target=document.getElementById(id);if(target&&target.matches('.exhibition-venue')){target.open=true;target.scrollIntoView({block:'start'});}}
input.addEventListener('change',refresh);reset.addEventListener('click',()=>{input.value='';refresh();});window.addEventListener('hashchange',openHash);
for(const a of document.querySelectorAll('a[href^="#exhibitions-"]'))a.addEventListener('click',()=>{const target=document.getElementById(a.hash.slice(1));if(target)target.open=true;});
refresh();openHash();
})();
