(()=>{'use strict';
const payload=document.getElementById('day-data');if(!payload)return;
const data=JSON.parse(payload.textContent),points=data.points,legs=data.legs;
const svg=document.getElementById('offline-map'),toggle=document.getElementById('show-optional'),button=document.getElementById('map-toggle'),status=document.getElementById('map-status');
if(!svg||!points.length)return;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let map=null,layer=null,ready=false,tilesReady=false,useStreet=false,wantStreet=true,cssReady=false,jsReady=false,errors=0;
const active=()=>points.filter(p=>!p.optional||toggle.checked);
const coord=c=>[(c[0]-2.33)*73150,(48.86-c[1])*111200];
function offline(){
 const visible=active(),ids=new Set(visible.map(p=>p.id)),visibleLegs=legs.filter(l=>ids.has(l.a)&&ids.has(l.b)&&l.geometry);
 const raw=visible.map(p=>p.coordinates).concat(visibleLegs.flatMap(l=>l.geometry.coordinates));
 if(!raw.length)return;
 const xy=raw.map(coord),xs=xy.map(p=>p[0]),ys=xy.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
 const w=Math.max(300,svg.clientWidth||720),h=480,cx=(minX+maxX)/2,cy=(minY+maxY)/2,scale=Math.min((w-70)/Math.max(maxX-minX,700),(h-95)/Math.max(maxY-minY,700));
 svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
 const project=c=>{const p=coord(c);return[w/2+(p[0]-cx)*scale,h/2+(p[1]-cy)*scale];};
 let out='<title>Day '+data.day+' 景点顺序与步行路网</title><desc>数字对应左侧参观顺序。没有街道底图时仍可离线查看。</desc>';
 const step=Math.max(200,Math.pow(10,Math.floor(Math.log10(Math.max(maxX-minX,maxY-minY,500))))/2);
 for(let x=Math.floor(minX/step)*step;x<=maxX+step;x+=step){const px=w/2+(x-cx)*scale;out+=`<line x1="${px}" x2="${px}" y1="30" y2="${h-30}" stroke="var(--line)"/>`;}
 for(let y=Math.floor(minY/step)*step;y<=maxY+step;y+=step){const py=h/2+(y-cy)*scale;out+=`<line x1="25" x2="${w-25}" y1="${py}" y2="${py}" stroke="var(--line)"/>`;}
 for(const l of visibleLegs){const poly=l.geometry.coordinates.map(c=>project(c).join(',')).join(' ');out+=`<polyline points="${poly}" fill="none" stroke="var(--blue)" stroke-width="3" opacity=".8"><title>${esc(l.label)}</title></polyline>`;}
 for(const p of visible){const[x,y]=project(p.coordinates),color=p.color||(p.optional?'var(--orange)':'var(--blue)'),fill=p.optional?'var(--paper)':'var(--blue)',stroke=color,fg=p.optional?color:'var(--paper)';out+=`<a href="#${p.anchor}">${p.evening_option?`<rect x="${x-16}" y="${y-13}" width="32" height="26" rx="6" fill="${fill}" stroke="${stroke}" stroke-width="2"><title>${esc(p.label+' '+p.name)}</title></rect>`:`<circle cx="${x}" cy="${y}" r="14" fill="${fill}" stroke="${stroke}" stroke-width="2"><title>${esc(p.label+' '+p.name)}</title></circle>`}<text x="${x}" y="${y+4}" text-anchor="middle" font-size="12" font-family="sans-serif" fill="${fg}">${p.label}</text></a>`;}
 const meters=[100,200,500,1000,2000,5000].filter(m=>m*scale<=110).pop()||100;
 out+=`<line x1="25" x2="${25+meters*scale}" y1="${h-27}" y2="${h-27}" stroke="var(--fg)" stroke-width="3"/><text x="25" y="${h-8}" font-size="12" fill="var(--fg)">${meters>=1000?meters/1000+' km':meters+' m'}</text><text x="${w-55}" y="25" font-size="14" fill="var(--fg)">北 ↑</text>`;
 svg.innerHTML=out;
}
function street(){
 if(!ready)return;layer.clearLayers();const shown=active(),ids=new Set(shown.map(p=>p.id));
 for(const l of legs){if(l.geometry&&ids.has(l.a)&&ids.has(l.b))L.geoJSON({type:'Feature',properties:{},geometry:l.geometry},{style:{color:'#235f99',weight:4,opacity:.8}}).bindTooltip(esc(l.label)).addTo(layer);}
 for(const p of shown){const c=p.coordinates,icon=L.divIcon({className:'number-marker'+(p.optional?' optional-marker':'')+(p.evening_option?' evening-marker':''),html:p.evening_option?'<span style="color:'+esc(p.color)+';border-color:'+esc(p.color)+'">'+esc(p.label)+'</span>':esc(p.label),iconSize:[28,28],iconAnchor:[14,14]});L.marker([c[1],c[0]],{icon}).bindTooltip(esc(p.label+' '+p.name)).bindPopup(`<strong>${esc(p.code+' '+p.name)}</strong><br>${esc(p.note)}<br><a href="#${p.anchor}">${p.evening_option?'查看对应晚间方案':'查看行程条目'}</a>`).addTo(layer);}
 if(shown.length)map.fitBounds(L.latLngBounds(shown.map(p=>[p.coordinates[1],p.coordinates[0]])).pad(.2),{maxZoom:16,animate:false});
}
function render(){offline();street();}
function mode(on){
 useStreet=Boolean(on&&tilesReady);wantStreet=useStreet;const div=document.getElementById('street-map');
 Object.assign(div.style,{display:useStreet?'block':'none',position:'relative',inset:'',height:'',opacity:'1',pointerEvents:'auto'});svg.style.display=useStreet?'none':'block';
 button.disabled=!tilesReady;button.textContent=useStreet?'切换坐标路线图':tilesReady?'切换街道底图':'使用离线坐标路线图';
 if(useStreet){map.invalidateSize();street();}status.textContent=useStreet?'底图 © IGN – Plan IGN；数字对应本日景点顺序。':'地点、路线与距离已包含在本页；当前显示离线坐标路线图。';
}
function fail(message){mode(false);status.textContent=message+'；本日景点与路线仍可离线查看。';}
if(points.some(p=>p.evening_option)){
 const reveal=()=>{const id=decodeURIComponent(window.location.hash.slice(1)),target=document.getElementById(id);if(target&&target.matches('details.evening-choice'))target.open=true;};
 window.addEventListener('hashchange',reveal);
 document.addEventListener('click',event=>{const link=event.target.closest('a[href^="#evening-"]');if(!link)return;const target=document.getElementById(link.getAttribute('href').slice(1));if(target&&target.matches('details.evening-choice'))target.open=true;});
 reveal();
}
toggle.addEventListener('change',render);button.addEventListener('click',()=>{if(tilesReady)mode(!useStreet);});window.addEventListener('resize',offline);render();
const timer=setTimeout(()=>{if(!tilesReady)fail('街道底图加载超时');},10000);
function init(){
 if(!cssReady||!jsReady||!window.L||ready)return;
 try{const div=document.getElementById('street-map');Object.assign(div.style,{display:'block',position:'absolute',inset:'0',height:'100%',opacity:'0',pointerEvents:'none'});
 map=L.map(div,{scrollWheelZoom:true}).setView([48.86,2.34],13);layer=L.layerGroup().addTo(map);ready=true;street();
 const tiles=L.tileLayer('https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',{maxZoom:19,attribution:'&copy; <a href="https://cartes.gouv.fr/">IGN – Plan IGN</a>'});
 tiles.on('tileload',()=>{if(tilesReady)return;tilesReady=true;clearTimeout(timer);const wanted=wantStreet;mode(wanted);});tiles.on('tileerror',()=>{if(++errors>=3){clearTimeout(timer);fail('底图图片未能完整加载');}});tiles.addTo(map);
 }catch(error){clearTimeout(timer);fail('街道底图初始化失败');}
}
const css=document.createElement('link');css.rel='stylesheet';css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';css.onload=()=>{cssReady=true;init();};css.onerror=()=>{clearTimeout(timer);fail('底图样式无法加载');};document.head.append(css);
const js=document.createElement('script');js.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';js.onload=()=>{jsReady=true;init();};js.onerror=()=>{clearTimeout(timer);fail('底图库无法加载');};document.head.append(js);
})();
