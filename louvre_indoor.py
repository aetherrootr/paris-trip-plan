"""Render the user's Louvre route over locally preserved official floor assets."""
import html, json, re
import xml.etree.ElementTree as ET

NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
def e(s):return html.escape(str(s),quote=True)

def floor_svg(root,floor):
    tree=ET.parse(root/'assets/louvre'/f'niveau{floor}.svg')
    svg=tree.getroot();prefix=f'louvre-f{str(floor).replace("-","m")}'
    ids={n.get('id'):prefix+'-'+n.get('id') for n in svg.iter() if n.get('id')}
    for n in svg.iter():
        tag=n.tag.rsplit('}',1)[-1]
        if tag in ('script','foreignObject','image','use'):
            raise ValueError('Unexpected executable or external SVG element: '+tag)
        if any(k.lower().startswith('on') or ('href' in k.lower() and not v.startswith('#')) for k,v in n.attrib.items()):
            raise ValueError('Unexpected SVG event or external reference')
        old=n.get('id','')
        if old.startswith('_') and old[1:].isdigit():n.set('data-room',old[1:])
        if old:n.set('id',ids[old])
        for k,v in list(n.attrib.items()):
            if 'href' in k.lower() and v.startswith('#'):v='#'+ids.get(v[1:],v[1:])
            for a,b in ids.items():v=v.replace('url(#'+a+')','url(#'+b+')')
            n.set(k,v)
        if tag=='style':
            n.text=re.sub(r'([^{}]+)\{',lambda m:','.join('#'+prefix+' '+s.strip() for s in m[1].split(','))+'{',n.text or '')
    svg.set('id',prefix);svg.set('class','louvre-floor-svg');svg.set('data-floor',str(floor))
    svg.set('role','img');svg.set('aria-label',f'卢浮宫官方{floor}层馆图，叠加原稿参观顺序')
    return ET.tostring(svg,encoding='unicode')

def render_indoor(root,data):
    stages=data['stages'];byid={s['id']:s for s in stages}
    h='<section class="louvre-section" id="louvre-route" aria-labelledby="louvre-heading"><p class="eyebrow">D06 · 馆内路线审阅</p><h2 id="louvre-heading">卢浮宫三翼：原稿路线与馆图</h2><p>保留德农2.5小时、叙利3小时、黎塞留3小时的参观预算。先用馆图核对房间与楼层，再结合下方原稿箭头图讨论调整。</p>'
    h+='<div class="louvre-source-actions"><a target="_blank" rel="noopener" href="https://collections.louvre.fr/plan">官方互动馆图 ↗</a><a target="_blank" rel="noopener" href="assets/louvre/official-plan-2026-05-en.pdf">官方完整馆图 PDF ↗</a><a target="_blank" rel="noopener" href="'+e(data['source_doc'])+'">原Google文档 ↗</a></div>'
    h+='<div class="louvre-viewer" id="louvre-viewer"><div class="louvre-toolbar"><div class="louvre-mode" aria-label="馆图展示方式"><button type="button" data-indoor-mode="2d" aria-pressed="true">二维馆图</button><button type="button" data-indoor-mode="3d" aria-pressed="false">3D楼层示意</button></div><label>参观段落 <select id="louvre-stage">'+''.join('<option value="'+e(s['id'])+'">'+str(i)+' · '+e(s['title'])+('〔可选〕' if s['optional'] else '')+'</option>' for i,s in enumerate(stages,1))+'</select></label></div>'
    h+='<div class="louvre-toolbar"><div class="louvre-floor-tabs" aria-label="选择楼层">'+''.join('<button type="button" data-indoor-floor="'+str(f)+'" aria-pressed="'+str(f==1).lower()+'">'+str(f).replace('-','−')+'层</button>' for f in (-1,0,1,2))+'</div><div class="louvre-map-tools"><button type="button" id="louvre-zoom-in" aria-label="放大馆图">＋</button><button type="button" id="louvre-zoom-out" aria-label="缩小馆图">−</button><button type="button" id="louvre-fit">看当前段落</button><button type="button" id="louvre-all">看整层</button></div></div>'
    h+='<div class="louvre-canvas" id="louvre-canvas" tabindex="0" aria-label="馆内路线图；左键按住拖动平移，滚轮缩放"><div class="louvre-stack" id="louvre-stack">'+''.join('<div class="louvre-plane" data-plane="'+str(f)+'"><span class="louvre-plane-label">'+str(f).replace('-','−')+'层</span>'+floor_svg(root,f)+'</div>' for f in (-1,0,1,2))+'</div></div>'
    h+='<div class="louvre-route-tools"><button type="button" id="louvre-route-toggle" aria-haspopup="dialog" aria-expanded="false" aria-controls="louvre-route-popover">查看路线 ☷</button><div class="louvre-route-popover" id="louvre-route-popover" role="dialog" aria-label="馆内参观路线" hidden><header><h3>馆内参观路线</h3><button type="button" id="louvre-route-close" aria-label="关闭路线弹窗">×</button></header><ol>'+''.join('<li><button type="button" data-route-stage="'+e(s['id'])+'"><strong>'+e(s['title'])+('〔可选〕' if s['optional'] else '')+'</strong><small>'+e(' → '.join(s['rooms']+[w['label'] for w in s.get('waypoints',[])]))+'</small></button></li>' for s in stages)+'</ol></div></div>'
    h+='<p class="louvre-credit">'+e(data['map_credit'])+'</p><div class="louvre-stage-info" aria-live="polite"><div class="louvre-step-nav"><button type="button" id="louvre-prev">← 上一段</button><span id="louvre-step-count"></span><button type="button" id="louvre-next">下一段 →</button></div><h3 id="louvre-stage-title"></h3><p id="louvre-stage-text"></p><p class="louvre-room-sequence" id="louvre-room-sequence"></p><p id="louvre-map-note" class="muted"></p><div id="louvre-room-info"></div></div><p class="muted louvre-caution">实线边框突出原稿房间；虚线仅连接房间中心表达先后顺序，可能跨越墙体，不能据此判断门洞可通行。馆图不显示实时关闭与展品借展。接待大厅在−2层；灰色背景上的休息点只标示其方向，需要换层，未绘制同层直达路线。</p><noscript><p>开启JavaScript可切换馆图楼层；原稿文字、11张截图及官方PDF仍可直接查看。</p></noscript></div>'
    h+='<h2>按三翼阅读原参观计划</h2><p class="muted">文字沿用原稿的三翼顺序；09:00仍为入馆目标，德农参观起点留到09:15，以容纳入馆转场。各段没有再分配未经核实的逐室时长。</p>'
    for w in data['wings']:
        h+='<article class="louvre-wing" id="wing-'+e(w['id'])+'"><div class="louvre-wing-heading"><h3>'+e(w['title'])+'</h3><span>'+e(w['time'])+' · '+e(w['duration'])+'</span></div><p>'+e(w['intro'])+'</p><ol class="louvre-stages">'
        for sid in w['stage_ids']:
            s=byid[sid]
            h+='<li><h4>'+e(s['title'])+('〔可选〕' if s['optional'] else '')+'</h4><p>'+e(s['text'])+'</p><p class="louvre-room-sequence">'+e(' → '.join(s['rooms']+[w['label'] for w in s.get('waypoints',[])]))+'</p><button type="button" data-show-stage="'+e(sid)+'">在馆图上查看 ↑</button></li>'
        h+='</ol><details class="louvre-originals"><summary>原稿路线截图 · '+str(len(w['images']))+'张（点击展开）</summary><div class="louvre-image-grid">'
        for im in w['images']:
            titles=list(dict.fromkeys(s['title'] for s in stages if im in s['images']))
            title='／'.join(titles);src=f'assets/louvre/original-{im:02d}.png'
            h+='<figure><a target="_blank" rel="noopener" href="'+src+'"><img loading="lazy" src="'+src+'" alt="原稿截图'+str(im)+'：'+e(title)+'，包含原绘参观箭头"></a><figcaption>原图'+str(im)+' · '+e(title)+' · 点击看大图</figcaption></figure>'
        h+='</div></details></article>'
    h+='<details class="louvre-original-text"><summary>原文文字摘录（保留原措辞）</summary><div>'+e((root/'assets/louvre/original-plan-text.txt').read_text()).replace('\n','<br>')+'</div></details>'
    h+='<details><summary>地图来源与尚待核实的连接</summary><p>官方底图和PDF保存自2026-11-09，PDF版本为2026-05。原文11张图片完整保留，未重绘其箭头。2027年展区开放、门洞和楼梯通行仍需按实际参观日复核。</p><p>原图0层标注的227在当前官方SVG中拆为2271与2272，本页保留原文227的写法，并同时突出两块区域，不推断经过其中哪一间。当前装修信息只作为核对提示，不代表2027年的关闭安排。</p><p><a href="assets/louvre/provenance.json">查看底图与原稿来源记录</a> · <a href="assets/louvre/original-plan-text.txt">原稿文字摘录</a></p></details></section>'
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    return h,'<script id="louvre-data" type="application/json">'+payload+'</script><script>'+ (root/'templates/louvre-indoor.js').read_text()+'</script>'
