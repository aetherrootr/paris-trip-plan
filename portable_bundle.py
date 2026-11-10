"""Bundle the existing review site, its pages and assets into one HTML file."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import base64
import json
import mimetypes
import re

LIB_BASE = 'https://unpkg.com/leaflet@1.9.4/dist/'
LIB_FILES = ['leaflet.js', 'leaflet.css', 'images/layers.png', 'images/layers-2x.png', 'images/marker-icon.png']

BRIDGE = r'''(()=>{'use strict';
const page=__PAGE__;
const send=(type,extra={})=>parent.postMessage({portablePlan:true,type,page,...extra},'*');
document.addEventListener('click',event=>{
 const link=event.target.closest('a');if(!link||event.defaultPrevented)return;
 const href=link.getAttribute('href')||'';
 if(href.startsWith('data:')&&(link.hasAttribute('download')||link.target==='_blank')){
  const match=href.match(/^data:([^,]*);base64,(.*)$/s);
  if(match){const raw=atob(match[2]),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0)),url=URL.createObjectURL(new Blob([bytes],{type:match[1]}));link.href=url;setTimeout(()=>URL.revokeObjectURL(url),60000);}
  return;
 }
 if(href==='paris-companion-plan.html'){event.preventDefault();send('download');return;}
 if(href.startsWith('#')){
  event.preventDefault();location.hash=href;reveal();return;
 }
 const match=href.match(/^(?:\.\/)?([^/?#]+\.html)(?:#(.*))?$/);
 if(match){event.preventDefault();send('navigate',{target:match[1],anchor:match[2]||''});}
},true);
function reveal(){
 let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
 const target=document.getElementById(id);
 if(target){for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));}
 send('anchor',{anchor:location.hash.slice(1)});
}
addEventListener('hashchange',reveal);
addEventListener('DOMContentLoaded',()=>{reveal();send('ready',{title:document.title});});
addEventListener('load',reveal);
})();'''

RUNTIME = r'''(()=>{'use strict';
const bundle=JSON.parse(document.getElementById('portable-data').textContent);
const frame=document.getElementById('portable-frame'),fallback=document.getElementById('portable-fallback');
const original='<!doctype html>\n'+document.documentElement.outerHTML;
const resources=new Map();let current='',pageURL=null;
function resource(key){
 if(resources.has(key))return resources.get(key);
 const asset=bundle.assets[key],url='data:'+asset.mime+';base64,'+asset.data;
 resources.set(key,url);return url;
}
function route(hash){
 const text=hash.startsWith('#/')?hash.slice(2):'review-plan.html';
 const cut=text.indexOf('#'),page=cut<0?text:text.slice(0,cut),anchor=cut<0?'':text.slice(cut+1);
 return Object.hasOwn(bundle.pages,page)?{page,anchor}:{page:'review-plan.html',anchor:''};
}
function hashFor(page,anchor){return '#/'+page+(anchor?'#'+anchor:'');}
function show(){
 const {page,anchor}=route(location.hash);if(current===page)return;
 let source=bundle.pages[page].replace(/portable-resource:([a-zA-Z0-9._/-]+)/g,(_,key)=>resource(key));
 source=source.replace('<!--portable-map-library-->',()=>'<style>'+bundle.leaflet.css+'</style><script>'+bundle.leaflet.js+'<'+ '/script>');
 const bridge=bundle.bridge.replace('__PAGE__',JSON.stringify(page));
 source=source.replace('</head>','<script>'+bridge+'<'+ '/script></head>');
 const previous=pageURL;pageURL=URL.createObjectURL(new Blob([source],{type:'text/html;charset=utf-8'}));
 current=page;frame.src=pageURL+(anchor?'#'+anchor:'');
 if(previous)setTimeout(()=>URL.revokeObjectURL(previous),3000);
}
function download(){const url=URL.createObjectURL(new Blob([original],{type:'text/html;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='paris-companion-plan.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
addEventListener('message',event=>{
 if(event.source!==frame.contentWindow||!event.data?.portablePlan)return;
 const data=event.data;
 if(data.type==='download'){download();return;}
 if(data.type==='navigate'&&Object.hasOwn(bundle.pages,data.target)){
  const next=hashFor(data.target,data.anchor);
  if(data.target===current){current='';history.pushState(null,'',next);show();}
  else location.hash=next;
 }
 if(data.type==='anchor'&&data.page===current){const next=hashFor(current,data.anchor);if(location.hash!==next)history.replaceState(null,'',next);}
 if(data.type==='ready'&&data.page===current){fallback.hidden=true;frame.style.opacity='1';frame.style.pointerEvents='auto';document.title=data.title;document.documentElement.classList.add('portable-active');}
});
addEventListener('hashchange',()=>{current='';show();});
show();
})();'''


class References(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]
    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        for key in ('href','src'):
            if key in values:self.refs.append(values[key])


def build_portable_bundle(directory, library_directory):
    root=Path(directory);library=Path(library_directory)
    pages={p.name:p.read_text(encoding='utf-8') for p in sorted(root.glob('*.html')) if p.name!='paris-companion-plan.html'}
    assets={}
    def asset(key, path):
        if key not in assets:
            mime=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
            if mime.startswith('text/') or mime=='application/json':mime+=';charset=utf-8'
            assets[key]={'mime':mime,'data':base64.b64encode(path.read_bytes()).decode('ascii')}
        return 'portable-resource:'+key
    css=(library/'leaflet.css').read_text()
    for filename in LIB_FILES[2:]:
        path=library/filename
        mime=mimetypes.guess_type(path.name)[0]
        css=css.replace(filename,'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode())
    leaflet_js=(library/'leaflet.js').read_text()
    leaflet_js=re.sub(r'//# sourceMappingURL=.*','',leaflet_js)
    for name,source in pages.items():
        parsed=References();parsed.feed(source)
        for ref in sorted(set(parsed.refs),key=len,reverse=True):
            url=urlsplit(ref)
            if url.scheme or url.netloc or not url.path:continue
            local=unquote(url.path)
            if local in pages or local=='paris-companion-plan.html':continue
            path=(root/local).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():raise ValueError(f'Missing bundled resource: {name}: {ref}')
            replacement=asset(local,path)
            source=source.replace('"'+ref+'"','"'+replacement+'"')
            if local.endswith('.txt'):
                source=source.replace('href="'+replacement+'" download>', 'href="'+replacement+'" download="'+path.name+'">')
        if LIB_BASE+'leaflet.js' in source:
            source,count=re.subn(r"const css=document\.createElement\('link'\);[^\n]+\nconst js=document\.createElement\('script'\);[^\n]+",'cssReady=true;jsReady=true;init();',source)
            if not count:
                source,count=re.subn(r"const cssReady=new Promise[^\n]+",'init();',source)
            if count!=1:raise ValueError('Unrecognized map loader in '+name)
            if LIB_BASE in source:raise ValueError('Unbundled map library URL in '+name)
            source=source.replace('</head>','<!--portable-map-library--></head>',1)
        pages[name]=source
    payload=json.dumps({'pages':pages,'assets':assets,'bridge':BRIDGE,'leaflet':{'css':css,'js':leaflet_js}},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    review=(root/'review-plan.html').read_text(encoding='utf-8')
    styles=''.join(re.findall(r'<style>(.*?)</style>',review,re.S))
    fallback=re.search(r'<body>(.*?)</body>',review,re.S).group(1)
    # A script-disabled preview can still display the original table.
    fallback=re.sub(r'href="([^"?#]+\.html)(#[^"]*)?"',lambda m:'href="#/'+m[1]+(m[2] or '')+'"',fallback)
    result='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>巴黎与凡尔赛｜同行计划总表</title><style>'+styles+'\n.portable-active,.portable-active body{height:100%;margin:0;overflow:hidden}#portable-frame{position:fixed;inset:0;width:100%;height:100%;border:0;background:var(--bg)}[hidden]{display:none!important}</style></head><body><div id="portable-fallback">'+fallback+'<noscript><p>请用浏览器打开并启用JavaScript，即可在文件内查看每日详情。</p></noscript></div><iframe id="portable-frame" title="巴黎行程：总表、每日安排与专题" style="opacity:0;pointer-events:none"></iframe><script type="application/json" id="portable-data">'+payload+'</script><script>'+RUNTIME+'</script></body></html>'
    (root/'paris-companion-plan.html').write_text(result,encoding='utf-8')
    return {'pages':len(pages),'assets':len(assets),'bytes':len(result.encode())}
