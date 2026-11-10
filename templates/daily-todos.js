(()=>{'use strict';
const items=[...document.querySelectorAll('[data-todo-key]')],status=document.getElementById('todo-save-status'),progress=document.getElementById('todo-progress');
let unavailable=false;
function update(){if(progress)progress.textContent=items.filter(input=>input.checked).length+' / '+items.length+' 已完成';}
function warn(){if(status)status.textContent='当前浏览器无法保存勾选状态；刷新页面后会恢复为日程文件中的进度。';}
for(const input of items){
 try{const saved=JSON.parse(localStorage.getItem(input.dataset.todoKey)||'null');if(saved&&saved.signature===input.dataset.todoSignature&&typeof saved.checked==='boolean')input.checked=saved.checked;}catch(error){unavailable=true;}
 input.addEventListener('change',()=>{update();try{localStorage.setItem(input.dataset.todoKey,JSON.stringify({signature:input.dataset.todoSignature,checked:input.checked}));}catch(error){warn();}});
}
if(unavailable)warn();update();
})();
