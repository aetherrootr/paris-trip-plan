(()=>{'use strict';
 const nav=document.querySelector('[data-site-nav]');if(!nav)return;
 const button=nav.querySelector('[data-nav-toggle]'),links=nav.querySelector('[data-nav-links]');
 if(!button||!links)return;
 const mobile=window.matchMedia('(max-width:760px)');
 function expand(open){
  links.hidden=!open;
  button.setAttribute('aria-expanded',String(open));
  button.textContent=open?'收起行程导航':'展开行程导航';
 }
 function layout(){button.hidden=!mobile.matches;expand(!mobile.matches);}
 button.addEventListener('click',()=>expand(button.getAttribute('aria-expanded')!=='true'));
 links.addEventListener('click',event=>{if(mobile.matches&&event.target.closest('a'))expand(false);});
 mobile.addEventListener('change',layout);
 layout();
})();
