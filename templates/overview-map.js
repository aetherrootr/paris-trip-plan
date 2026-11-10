(()=>{'use strict';
const source=document.getElementById('overview-data');if(!source)return;
const data=JSON.parse(source.textContent),svg=document.getElementById('overview-offline'),streetDiv=document.getElementById('overview-street'),status=document.getElementById('overview-status'),modeButton=document.getElementById('overview-map-toggle'),optional=document.getElementById('overview-optional'),summary=document.getElementById('overview-count'),detail=document.getElementById('overview-detail'),filters=[...document.querySelectorAll('[data-map-day]')];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let map=null,layer=null,ready=false,tilesReady=false,useStreet=false,wantStreet=true,cssReady=false,jsReady=false,errors=0;
let groups=[],visibleLegs=[],visibleDays=[];
function choose(){
 const selected=new Set(filters.filter(f=>f.checked).map(f=>Number(f.dataset.mapDay)));
 visibleDays=data.days.filter(d=>selected.has(d.day));
 const points=visibleDays.flatMap(d=>d.points.filter(p=>optional.checked||!p.optional).map(p=>({...p,color:d.color,day:d.day,dayTitle:d.title})));
 const active=new Set(points.map(p=>p.day+':'+p.id));
 visibleLegs=visibleDays.flatMap(d=>d.legs.filter(l=>active.has(d.day+':'+l.a)&&active.has(d.day+':'+l.b)).map(l=>({...l,color:d.color,day:d.day})));
 const byId=new Map();
 for(const p of points){if(!byId.has(p.id))byId.set(p.id,{id:p.id,name:p.name,coordinates:p.coordinates,items:[]});byId.get(p.id).items.push(p);}
 groups=[...byId.values()];
 summary.textContent=`已选 ${visibleDays.length} 天 · ${groups.length} 个位置 · ${visibleLegs.length} 段步行路网`;
 for(const f of filters)f.closest('label').classList.toggle('is-selected',f.checked);
}
function label(g){return g.items.length>1?[...new Set(g.items.map(p=>String(p.day).padStart(2,'0')))].join('/'):String(g.items[0].day).padStart(2,'0')+'·'+g.items[0].label;}
function popup(g){return '<strong>'+esc(g.name)+'</strong>'+g.items.map(p=>'<p><span class="day-chip" style="--route-color:'+p.color+'">'+esc(p.code)+'</span> '+(p.optional?'可选／顺路':'拟安排')+(p.time?'<br>'+esc(p.time):'')+'<br><a href="'+esc(p.href)+'">查看 Day '+p.day+' 的行程卡片 →</a></p>').join('');}
function pick(g){detail.innerHTML='<h3>'+esc(g.name)+'</h3>'+g.items.map(p=>'<div class="overview-assignment"><span class="day-chip" style="--route-color:'+p.color+'">'+esc(p.code)+'</span><span>'+esc(p.dayTitle)+(p.optional?'〔可选／顺路〕':'')+(p.time?'<br><small>'+esc(p.time)+'</small>':'')+'</span><a href="'+esc(p.href)+'">打开日程 →</a></div>').join('');}
function rawCoordinates(){return groups.map(g=>g.coordinates).concat(visibleLegs.flatMap(l=>l.geometry.coordinates));}
function offline(){
 const raw=rawCoordinates(),w=Math.max(300,svg.clientWidth||850),h=560;
 svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
 if(!raw.length){svg.innerHTML='<title>跨日路线地图</title><text x="'+w/2+'" y="'+h/2+'" text-anchor="middle" fill="var(--muted)">请选择至少一天查看点位与路线</text>';return;}
 const xy=c=>[(c[0]-2.33)*73150,(48.86-c[1])*111200],rawXY=raw.map(xy),xs=rawXY.map(c=>c[0]),ys=rawXY.map(c=>c[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),cx=(minX+maxX)/2,cy=(minY+maxY)/2,scale=Math.min((w-90)/Math.max(maxX-minX,1000),(h-100)/Math.max(maxY-minY,1000));
 const project=c=>{const p=xy(c);return[w/2+(p[0]-cx)*scale,h/2+(p[1]-cy)*scale];};
 let out='<title>按日期分色的跨日路线</title><desc>标记为日期与当天顺序，点击查看所属日程。</desc>';
 const step=Math.max(500,10**Math.floor(Math.log10(Math.max(maxX-minX,maxY-minY,500)))/2);
 for(let x=Math.floor(minX/step)*step;x<=maxX+step;x+=step){const a=w/2+(x-cx)*scale;out+=`<line x1="${a}" x2="${a}" y1="20" y2="${h-35}" stroke="var(--line)"/>`;}
 for(let y=Math.floor(minY/step)*step;y<=maxY+step;y+=step){const b=h/2+(y-cy)*scale;out+=`<line x1="20" x2="${w-20}" y1="${b}" y2="${b}" stroke="var(--line)"/>`;}
 for(const l of visibleLegs)out+=`<polyline points="${l.geometry.coordinates.map(c=>project(c).join(',')).join(' ')}" fill="none" stroke="${l.color}" stroke-width="3" opacity=".85"><title>${esc('D'+l.day+' '+l.label)}</title></polyline>`;
 for(const g of groups){const[x,y]=project(g.coordinates),p=g.items[0],multi=g.items.length>1,fill=p.optional||multi?'var(--paper)':p.color,fg=p.optional?p.color:multi?'var(--fg)':'#fff';out+=`<a href="#overview-detail" data-place="${esc(g.id)}" aria-label="${esc(label(g)+' '+g.name)}"><rect x="${x-24}" y="${y-12}" width="48" height="24" rx="8" fill="${fill}" stroke="${p.color}" stroke-width="2"${p.optional?' stroke-dasharray="3 2"':''}/><text x="${x}" y="${y+4}" text-anchor="middle" font-size="10" font-weight="650" fill="${fg}">${esc(label(g))}</text><title>${esc(g.name+' '+g.items.map(p=>p.code).join(' / '))}</title></a>`;}
 const meters=[100,200,500,1000,2000,5000,10000].filter(m=>m*scale<=120).pop()||100;
 out+=`<line x1="25" x2="${25+meters*scale}" y1="${h-27}" y2="${h-27}" stroke="var(--fg)" stroke-width="3"/><text x="25" y="${h-8}" font-size="12" fill="var(--fg)">${meters>=1000?meters/1000+' km':meters+' m'}</text><text x="${w-55}" y="25" font-size="14" fill="var(--fg)">北 ↑</text>`;
 svg.innerHTML=out;
}
function street(){
 if(!ready)return;layer.clearLayers();
 for(const l of visibleLegs){const route=L.geoJSON({type:'Feature',properties:{},geometry:l.geometry},{style:{color:l.color,weight:3.5,opacity:.85}}).bindTooltip(esc('D'+String(l.day).padStart(2,'0')+' '+l.label));route.on('click',()=>{detail.innerHTML='<h3><span class="day-chip" style="--route-color:'+l.color+'">D'+String(l.day).padStart(2,'0')+'</span> '+esc(l.label)+'</h3><p>步行路网约 '+(l.distance/1000).toFixed(2)+' km · 模型约 '+Math.ceil(l.duration/5)*5+' 分钟</p><a href="'+esc(l.href)+'">查看当天行程 →</a>';});route.addTo(layer);}
 for(const g of groups){const p=g.items[0],multi=g.items.length>1,colors=[...new Set(g.items.map(x=>x.color))],bar=multi?'background:linear-gradient(90deg,'+colors.map((c,i)=>c+' '+i*100/colors.length+'% '+(i+1)*100/colors.length+'%').join(',')+');':'';
 const icon=L.divIcon({className:'overview-marker-host',html:'<span class="overview-marker'+(p.optional?' is-optional':'')+(multi?' is-multi':'')+'" style="--route-color:'+p.color+'">'+esc(label(g))+(multi?'<i style="'+bar+'"></i>':'')+'</span>',iconSize:[48,28],iconAnchor:[24,14]});
 L.marker([g.coordinates[1],g.coordinates[0]],{icon,title:g.name+' '+g.items.map(p=>p.code).join(' / ')}).bindTooltip(esc(g.name+' '+g.items.map(p=>p.code).join(' / '))).bindPopup(popup(g)).on('click',()=>pick(g)).addTo(layer);}
 fit();
}
function fit(){if(ready&&groups.length){const raw=rawCoordinates();map.fitBounds(L.latLngBounds(raw.map(c=>[c[1],c[0]])).pad(.12),{animate:false,maxZoom:16});}}
function refresh(){choose();offline();street();detail.innerHTML=groups.length?'<p>点击点位查看所属日期与当天顺序；点击彩色路线可查看区间距离。</p>':'<p>尚未选择日期，请在右侧勾选要比较的日程。</p>';}
function mode(on){useStreet=Boolean(on&&tilesReady);wantStreet=useStreet;Object.assign(streetDiv.style,{display:useStreet?'block':'none',position:'relative',inset:'',height:'',opacity:'1',pointerEvents:'auto'});svg.style.display=useStreet?'none':'block';modeButton.disabled=!tilesReady;modeButton.textContent=useStreet?'切换坐标路线图':tilesReady?'切换街道底图':'使用离线坐标路线图';if(useStreet){map.invalidateSize();fit();}status.textContent=useStreet?'底图 © IGN – Plan IGN；点位与路线按日期分色。':'当前为离线坐标路线图，点位与路网数据已包含在本页。';}
function fail(message){mode(false);status.textContent=message+'；仍可查看和筛选本地坐标路线图。';}
for(const f of filters)f.addEventListener('change',refresh);
optional.addEventListener('change',refresh);
for(const b of document.querySelectorAll('[data-map-preset]'))b.addEventListener('click',()=>{const preset=b.dataset.mapPreset;for(const f of filters){const day=Number(f.dataset.mapDay);f.checked=preset==='all'||preset==='paris'&&day!==13||preset==='versailles'&&day===13||preset==='compare'&&(day===2||day===3)||preset==='rebalance'&&[4,9,5].includes(day)||preset==='west'&&[9,11,10,12].includes(day);}refresh();});
for(const b of document.querySelectorAll('[data-map-focus]'))b.addEventListener('click',()=>{const day=Number(b.dataset.mapFocus);for(const f of filters)f.checked=Number(f.dataset.mapDay)===day;refresh();});
modeButton.addEventListener('click',()=>{if(tilesReady)mode(!useStreet);});
svg.addEventListener('click',event=>{const a=event.target.closest('[data-place]');if(!a)return;event.preventDefault();const g=groups.find(g=>g.id===a.dataset.place);if(g)pick(g);detail.scrollIntoView({block:'nearest'});});
window.addEventListener('resize',offline);refresh();
const timer=setTimeout(()=>{if(!tilesReady)fail('街道底图加载超时');},10000);
function init(){
 if(!cssReady||!jsReady||!window.L||ready)return;
 try{Object.assign(streetDiv.style,{display:'block',position:'absolute',inset:'0',height:'100%',opacity:'0',pointerEvents:'none'});map=L.map(streetDiv,{scrollWheelZoom:true}).setView([48.86,2.34],12);layer=L.layerGroup().addTo(map);ready=true;street();
 const tiles=L.tileLayer('https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',{maxZoom:19,attribution:'&copy; <a href="https://cartes.gouv.fr/">IGN – Plan IGN</a>'});
 tiles.on('tileload',()=>{if(tilesReady)return;tilesReady=true;clearTimeout(timer);mode(wantStreet);});tiles.on('tileerror',()=>{if(++errors>=3){clearTimeout(timer);fail('底图图片未能完整加载');}});tiles.addTo(map);
 }catch(error){clearTimeout(timer);fail('底图初始化失败');}
}
const css=document.createElement('link');css.rel='stylesheet';css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';css.onload=()=>{cssReady=true;init();};css.onerror=()=>{clearTimeout(timer);fail('底图样式无法加载');};document.head.append(css);
const js=document.createElement('script');js.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';js.onload=()=>{jsReady=true;init();};js.onerror=()=>{clearTimeout(timer);fail('底图库无法加载');};document.head.append(js);
})();
