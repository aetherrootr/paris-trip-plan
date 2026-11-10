(()=>{
 'use strict';
 const data=JSON.parse(document.getElementById('louvre-data').textContent),stages=data.stages;
 const $=id=>document.getElementById(id),canvas=$('louvre-canvas'),stack=$('louvre-stack');
 const svgs=[...document.querySelectorAll('.louvre-floor-svg')],planes=[...document.querySelectorAll('.louvre-plane')];
 const NS='http://www.w3.org/2000/svg',colors={denon:'#b93c45',sully:'#087c8a',richelieu:'#7651ad'};
 let current=0,floor=1,mode='2d',zoom3d=1,rotation=-16,pitch=48,lastPlaneHit=null,view=[0,0,949.16,477.53],drag=null;
 const geometry=new Map();
 const node=(tag,attrs,text)=>{const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;};
 // Measure official shapes in their SVG coordinate system, including their own transforms.
 for(const svg of svgs){
   const plane=svg.parentElement;plane.style.display='block';plane.style.visibility='hidden';
   const map=new Map();
   for(const el of svg.querySelectorAll('[data-room]')){
     const b=el.getBBox(),m=svg.getCTM().inverse().multiply(el.getCTM());
     const pt=new DOMPoint(b.x+b.width/2,b.y+b.height/2).matrixTransform(m);
     map.set(el.dataset.room,{el,x:pt.x,y:pt.y});
   }
   geometry.set(Number(svg.dataset.floor),map);plane.style.display='';plane.style.visibility='';
 }
 const aliases=r=>r==='227'?['2271','2272']:[r];
 function center(f,r){const pts=aliases(r).map(k=>geometry.get(f).get(k)).filter(Boolean);return pts.length?{x:pts.reduce((a,b)=>a+b.x,0)/pts.length,y:pts.reduce((a,b)=>a+b.y,0)/pts.length}:null;}
 function setView(v){view=v;svgs.find(s=>Number(s.dataset.floor)===floor).setAttribute('viewBox',v.join(' '));}
 function fit(all=false){
   if(mode==='3d'){zoom3d=1;transform3d();return;}
   if(all){setView([0,0,949.16,477.53]);return;}
   const pts=[...stages[current].rooms.map(r=>center(floor,r)).filter(Boolean),...(stages[current].waypoints||[])];
   if(!pts.length){setView([0,0,949.16,477.53]);return;}
   const xs=pts.map(p=>p.x),ys=pts.map(p=>p.y),w=Math.max(180,Math.max(...xs)-Math.min(...xs)+100),h=Math.max(150,Math.max(...ys)-Math.min(...ys)+100);
   setView([(Math.min(...xs)+Math.max(...xs)-w)/2,(Math.min(...ys)+Math.max(...ys)-h)/2,w,h]);
 }
 function draw(svg,selectedStages){
   svg.querySelectorAll('[data-route-room]').forEach(el=>{el.removeAttribute('data-route-room');el.style.removeProperty('--indoor-color');});
   svg.querySelectorAll('.indoor-overlay').forEach(el=>el.remove());
   const f=Number(svg.dataset.floor),map=geometry.get(f),overlay=node('g',{'class':'indoor-overlay'});
   for(const s of selectedStages){
     const color=colors[s.wing],g=node('g',{'style':'--indoor-color:'+color});let segment=[];const segments=[];
     s.rooms.forEach(r=>{const p=center(f,r);if(p)segment.push(p);else{if(segment.length)segments.push(segment);segment=[];}});if(segment.length)segments.push(segment);
     for(const points of segments)if(points.length>1)g.append(node('polyline',{'points':points.map(p=>p.x+','+p.y).join(' '),'class':'indoor-route-line'}));
     s.rooms.forEach((r,i)=>{
       for(const a of aliases(r)){const room=map.get(a);if(room){room.el.dataset.routeRoom='true';room.el.style.setProperty('--indoor-color',color);}}
       const p=center(f,r);if(!p)return;
       if((mode==='2d'||s.id===stages[current].id)&&(!s.label_rooms||s.label_rooms.includes(r))){
         const visits=s.rooms.map((room,index)=>room===r?index:-1).filter(index=>index>=0),occurrence=visits.indexOf(i);
         const markerX=p.x+(occurrence-(visits.length-1)/2)*14;
         if(visits.length>1)g.append(node('line',{x1:p.x,y1:p.y,x2:markerX,y2:p.y,'class':'indoor-repeat-leader'}));
         const dot=node('circle',{cx:markerX,cy:p.y,r:5.5,'class':'indoor-dot','data-step':i+1,'data-step-room':r});
         dot.append(node('title',{},'第'+(i+1)+'步：'+r+(visits.length>1?'（重复经过同一房间）':'')));g.append(dot);
         g.append(node('text',{x:markerX,y:p.y,'class':'indoor-order'},i+1));
         if(occurrence===0)g.append(node('text',{x:p.x,y:p.y-9,'class':'indoor-label'},r));
       }
     });
     for(const [i,w] of (s.waypoints||[]).entries()){
       const last=center(f,s.rooms.at(-1)),number=s.rooms.length+i+1;
       if(last){const transfer=node('line',{x1:last.x,y1:last.y,x2:w.x,y2:w.y,'class':'indoor-transfer-line'});transfer.append(node('title',{},'前往接待大厅方向；需换层，非同层已核实路径'));g.append(transfer);}
       const marker=node('g',{'class':'indoor-waypoint','data-waypoint-id':w.id,'role':'button','tabindex':'0','aria-label':'第'+number+'步：'+w.label+'，'+w.time,style:'--indoor-color:#237658'});
       marker.append(node('circle',{cx:w.x,cy:w.y,r:7,'class':'indoor-dot','data-step':number}));
       marker.append(node('text',{x:w.x,y:w.y,'class':'indoor-order'},number));
       marker.append(node('text',{x:w.x,y:w.y+16,'class':'indoor-waypoint-label'},'休息／换翼'));
       marker.append(node('text',{x:w.x,y:w.y+27,'class':'indoor-waypoint-time'},w.time+' · −2层方向'));
       marker.append(node('title',{},w.note));marker.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();waypointInfo(w);}});g.append(marker);
     }
     overlay.append(g);
   }svg.append(overlay);
 }
 function roomInfo(r){
   const box=$('louvre-room-info');box.replaceChildren();
   const key=data.key_rooms[r],p=document.createElement('p');p.className='louvre-room-detail';
   p.append('房间 '+r+' · '+String(floor).replace('-','−')+'层'+(key?' · '+key.title:''));
   const location=(data.rooms[String(floor)][r]||{}).location_id;
   const url=key?.url||(location?'https://collections.louvre.fr/recherche?location%5B0%5D='+encodeURIComponent(location):null);
   if(url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';a.textContent=' 查看官方介绍 ↗';p.append(a);}
   if(r==='227')p.append('；当前底图为2271／2272，具体通行房间待核。');box.append(p);
 }
 function waypointInfo(w){
   const box=$('louvre-room-info');box.replaceChildren();const p=document.createElement('p');p.className='louvre-room-detail';
   p.append(w.label+' · '+w.time+'。'+w.note);
   if(w.source_url){const a=document.createElement('a');a.href=w.source_url;a.target='_blank';a.rel='noopener';a.textContent=' 查看官方馆图 ↗';p.append(a);}box.append(p);
 }
 function transform3d(){
   const scale=Math.min(canvas.clientWidth/1100,canvas.clientHeight/900);
   stack.style.transform=`translate(-50%,-50%) scale(${scale*zoom3d}) perspective(1800px) rotateX(${pitch}deg) rotateZ(${rotation}deg)`;
   for(const p of planes)p.style.transform=`translateZ(${(Number(p.dataset.plane)-.5)*155}px)`;
 }
 function render(autoFit=true){
   if(drag){if(canvas.hasPointerCapture(drag.id))canvas.releasePointerCapture(drag.id);drag=null;}
   canvas.setAttribute('aria-label',mode==='3d'?'馆内路线图；左键按住拖动调整视角，滚轮缩放；双击楼层打开二维图':'馆内路线图；左键按住拖动平移，滚轮缩放');
   const s=stages[current];$('louvre-stage').value=s.id;
   $('louvre-stage-title').textContent=s.title+(s.optional?'〔原稿可选〕':'');$('louvre-stage-text').textContent=s.text;
   $('louvre-step-count').textContent=(current+1)+' / '+stages.length;
   $('louvre-prev').disabled=current===0;$('louvre-next').disabled=current===stages.length-1;
   const seq=$('louvre-room-sequence');seq.replaceChildren();
   s.rooms.forEach((r,i)=>{if(i)seq.append(' → ');const b=document.createElement('button');b.type='button';b.textContent=r;b.setAttribute('aria-label','查看房间'+r+'信息，第'+(i+1)+'步');b.onclick=()=>roomInfo(r);seq.append(b);});
   for(const [i,w] of (s.waypoints||[]).entries()){seq.append(' → ');const b=document.createElement('button');b.type='button';b.textContent=(s.rooms.length+i+1)+' · 休息／换翼';b.setAttribute('aria-label','查看休息与换翼安排');b.onclick=()=>waypointInfo(w);seq.append(b);}
   $('louvre-map-note').textContent='当前 '+String(floor).replace('-','−')+'层 · '+(mode==='2d'?'滚轮缩放，拖动平移；数字圆点是本段顺序，旁边是房间号。':'左键拖动调整视角，滚轮缩放；双击楼层查看二维图。红色德农、青色叙利、紫色黎塞留。')+(s.rooms.length!==new Set(s.rooms).size?' 同一房间往返经过时，序号并排显示；定位线指向同一房间。':'')+((s.waypoints||[]).length?' 绿色点为休息／换翼；大厅跨层标记仅表示方向。':'')+(s.rooms.includes('227')?' 原稿227对应官方底图2271／2272，具体通行待核。':'');
   $('louvre-room-info').replaceChildren();
   document.querySelectorAll('[data-indoor-floor]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.indoorFloor)===floor)));
   document.querySelectorAll('[data-indoor-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.indoorMode===mode)));
   canvas.classList.toggle('is-3d',mode==='3d');
   for(const p of planes){p.setAttribute('role',mode==='3d'?'button':'group');p.tabIndex=mode==='3d'?0:-1;p.setAttribute('aria-label',String(p.dataset.plane).replace('-','−')+'层馆图'+(mode==='3d'?'；双击打开二维楼层图':''));}
   document.querySelectorAll('[data-route-stage]').forEach(b=>{if(b.dataset.routeStage===s.id)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
   for(const p of planes)p.classList.toggle('active',Number(p.dataset.plane)===floor);
   for(const svg of svgs){svg.setAttribute('viewBox','0 0 949.16 477.53');const f=Number(svg.dataset.floor);draw(svg,mode==='3d'?stages.filter(t=>t.floor===f):f===floor?[s]:[]);}
   if(mode==='3d')transform3d();else{stack.style.transform='';planes.forEach(p=>p.style.transform='');if(autoFit)fit();}
 }
 function select(index,scroll=false){current=Math.max(0,Math.min(stages.length-1,index));floor=stages[current].floor;render();if(scroll)$('louvre-viewer').scrollIntoView({block:'start',behavior:'smooth'});}
 $('louvre-stage').onchange=event=>select(stages.findIndex(s=>s.id===event.target.value));
 $('louvre-prev').onclick=()=>select(current-1);$('louvre-next').onclick=()=>select(current+1);
 document.querySelectorAll('[data-show-stage]').forEach(b=>b.onclick=()=>select(stages.findIndex(s=>s.id===b.dataset.showStage),true));
 document.querySelectorAll('[data-indoor-floor]').forEach(b=>b.onclick=()=>select(stages.findIndex(s=>s.floor===Number(b.dataset.indoorFloor))));
 document.querySelectorAll('[data-indoor-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.indoorMode;render();});
 $('louvre-fit').onclick=()=>fit();$('louvre-all').onclick=()=>fit(true);

 function zoom(factor,point=null){
   if(mode==='3d'){zoom3d=Math.max(.6,Math.min(2,zoom3d/factor));transform3d();return;}
   const svg=svgs.find(s=>Number(s.dataset.floor)===floor),p=point?new DOMPoint(point.x,point.y).matrixTransform(svg.getScreenCTM().inverse()):{x:view[0]+view[2]/2,y:view[1]+view[3]/2};
   const w=Math.min(1800,Math.max(65,view[2]*factor)),ratio=w/view[2];
   setView([p.x+(view[0]-p.x)*ratio,p.y+(view[1]-p.y)*ratio,w,view[3]*ratio]);
 }
 $('louvre-zoom-in').onclick=()=>zoom(.8);$('louvre-zoom-out').onclick=()=>zoom(1.25);
 canvas.addEventListener('wheel',event=>{if(!event.deltaY)return;event.preventDefault();zoom(event.deltaY>0?1.12:.89,{x:event.clientX,y:event.clientY});},{passive:false});
 canvas.addEventListener('pointerdown',event=>{
   if(event.button!==0||!event.isPrimary)return;
   event.preventDefault();canvas.focus({preventScroll:true});
   lastPlaneHit=null;
   drag={id:event.pointerId,mode,x:event.clientX,y:event.clientY,moved:false,plane:event.target.closest('[data-plane]')?.dataset.plane};
   if(mode==='3d'){
     drag.rotation=rotation;drag.pitch=pitch;
   }else{
     const svg=svgs.find(s=>Number(s.dataset.floor)===floor);
     drag.m=svg.getScreenCTM().inverse();drag.view=[...view];
   }
   canvas.setPointerCapture(event.pointerId);
 });
 canvas.addEventListener('pointermove',event=>{
   if(!drag||drag.id!==event.pointerId||drag.mode!==mode)return;
   const dx=event.clientX-drag.x,dy=event.clientY-drag.y;
   if(Math.abs(dx)+Math.abs(dy)>5)drag.moved=true;
   if(mode==='3d'){
     rotation=((drag.rotation+dx*.35+180)%360+360)%360-180;
     pitch=Math.max(15,Math.min(80,drag.pitch-dy*.2));
     transform3d();
   }else{
     const a=new DOMPoint(drag.x,drag.y).matrixTransform(drag.m),b=new DOMPoint(event.clientX,event.clientY).matrixTransform(drag.m);
     setView([drag.view[0]+a.x-b.x,drag.view[1]+a.y-b.y,drag.view[2],drag.view[3]]);
   }
 });
 function endDrag(event){
   if(!drag||drag.id!==event.pointerId)return;
   const finished=drag;drag=null;
   if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
   if(event.type==='pointerup'&&finished.mode==='3d'&&!finished.moved&&finished.plane!==undefined)lastPlaneHit=Number(finished.plane);
   if(event.type==='pointerup'&&finished.mode==='2d'&&!finished.moved){
     const target=document.elementFromPoint(event.clientX,event.clientY),waypoint=target?.closest('[data-waypoint-id]');
     if(waypoint){const w=(stages[current].waypoints||[]).find(w=>w.id===waypoint.dataset.waypointId);if(w)waypointInfo(w);}else{const el=target?.closest('[data-route-room]');if(el)roomInfo(el.dataset.room);}
   }
 }
 canvas.addEventListener('pointerup',endDrag);
 canvas.addEventListener('pointercancel',endDrag);
 canvas.addEventListener('lostpointercapture',()=>drag=null);
 function openFloor(target){
   const index=stages[current].floor===target?current:stages.findIndex(s=>s.floor===target);
   if(index<0)return;
   mode='2d';select(index);fit(true);canvas.focus({preventScroll:true});
 }
 canvas.addEventListener('dblclick',event=>{
   if(mode!=='3d'||event.button!==0||lastPlaneHit===null)return;
   event.preventDefault();openFloor(lastPlaneHit);lastPlaneHit=null;
 });
 for(const plane of planes)plane.addEventListener('keydown',event=>{
   if(mode==='3d'&&(event.key==='Enter'||event.key===' ')){event.preventDefault();event.stopPropagation();openFloor(Number(plane.dataset.plane));}
 });
 const routeToggle=$('louvre-route-toggle'),routePopover=$('louvre-route-popover');
 function closeRoute(restoreFocus=false){routePopover.hidden=true;routeToggle.setAttribute('aria-expanded','false');if(restoreFocus)routeToggle.focus({preventScroll:true});}
 function positionRoute(){
   if(routePopover.hidden)return;
   const rect=routeToggle.getBoundingClientRect(),above=rect.top-20,below=window.innerHeight-rect.bottom-20,up=above>=below;
   routePopover.style.bottom=up?'calc(100% + 8px)':'auto';routePopover.style.top=up?'auto':'calc(100% + 8px)';
   routePopover.style.maxHeight=Math.max(80,Math.min(460,window.innerHeight*.65,up?above:below))+'px';
 }
 window.addEventListener('resize',positionRoute);window.addEventListener('scroll',positionRoute,{passive:true});
 routeToggle.onclick=()=>{const open=routePopover.hidden;routePopover.hidden=!open;routeToggle.setAttribute('aria-expanded',String(open));if(open){positionRoute();const active=routePopover.querySelector('[aria-current="step"]');if(active)routePopover.scrollTop=Math.max(0,active.offsetTop-50);}};
 $('louvre-route-close').onclick=()=>closeRoute(true);
 document.querySelectorAll('[data-route-stage]').forEach(b=>b.onclick=()=>{select(stages.findIndex(s=>s.id===b.dataset.routeStage));closeRoute(true);});
 document.addEventListener('pointerdown',event=>{if(!event.target.closest('.louvre-route-tools'))closeRoute();});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!routePopover.hidden){event.preventDefault();closeRoute(true);}});
 canvas.addEventListener('keydown',event=>{if(event.key==='+'){event.preventDefault();zoom(.8);}else if(event.key==='-'){event.preventDefault();zoom(1.25);}});
 new ResizeObserver(()=>{if(mode==='3d')transform3d();}).observe(canvas);
 render();
})();
