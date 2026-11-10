"""Build current per-day review pages from canonical plan and route data."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
import hashlib, html, json, math, shutil
from louvre_indoor import render_indoor
from marais_shops import render_shop_page
from exhibition_review import render_exhibition_review

ROOT=Path(__file__).resolve().parent
PREPARATION_PAGES=(
    ('visa.html','签证','办理流程与材料清单','travel-visa.html'),
    ('museum-pass.html','巴黎博物馆通票','TODO · 待比较与确认','travel-museum-pass.html'),
    ('travel-guide.html','法国旅行指南','电源、eSIM、支付与实用信息','travel-guide.html'),
)
def esc(value):return html.escape(str(value),quote=True)
def serial(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(value.encode()).hexdigest()[:10]

def build():
    plan=json.loads((ROOT/'data/plan.json').read_text(encoding='utf-8'))
    cache=json.loads((ROOT/'data/routes.json').read_text(encoding='utf-8'))
    routes={a+'__'+b:cache[a+'__'+b] for a,b in plan['route_pairs'] if a+'__'+b in cache}
    css=(ROOT/'templates/daily.css').read_text(encoding='utf-8')+(ROOT/'templates/louvre-indoor.css').read_text(encoding='utf-8')+(ROOT/'templates/marais-shops.css').read_text(encoding='utf-8')+(ROOT/'templates/exhibition-review.css').read_text(encoding='utf-8')
    js=(ROOT/'templates/daily-map.js').read_text(encoding='utf-8')
    todo_js=(ROOT/'templates/daily-todos.js').read_text(encoding='utf-8')
    overview_js=(ROOT/'templates/overview-map.js').read_text(encoding='utf-8')
    shop_js=(ROOT/'templates/marais-shops.js').read_text(encoding='utf-8')
    shop_code=(ROOT/'marais_shops.py').read_text(encoding='utf-8')
    exhibition_js=(ROOT/'templates/exhibition-review.js').read_text(encoding='utf-8')
    exhibition_code=(ROOT/'exhibition_review.py').read_text(encoding='utf-8')
    site_ui=(ROOT/'templates/site-ui.js').read_text(encoding='utf-8')
    preparation={name:(ROOT/'templates'/template).read_text(encoding='utf-8') for name,title,description,template in PREPARATION_PAGES}
    data_id=digest(serial({'plan':plan,'routes':routes}))
    indoor_hash=hashlib.sha256()
    for asset in sorted((ROOT/'assets/louvre').iterdir()):
        if asset.is_file():indoor_hash.update(asset.name.encode());indoor_hash.update(asset.read_bytes())
    indoor_code=(ROOT/'louvre_indoor.py').read_text()+(ROOT/'templates/louvre-indoor.js').read_text()
    build_id=digest(data_id+css+js+todo_js+overview_js+shop_js+shop_code+exhibition_js+exhibition_code+indoor_code+indoor_hash.hexdigest()+Path(__file__).read_text(encoding='utf-8'))
    build_id=digest(build_id+site_ui+''.join(preparation.values()))
    live=ROOT/'web/current'
    previous=ROOT/'web/.previous-current'
    out=ROOT/'web'/('.build-'+build_id)
    for generated in (live,previous,out):
        if generated.is_symlink():raise ValueError('Generated output must not be a symlink: '+str(generated))
    if previous.exists() and not live.exists():previous.rename(live)
    if out.exists():shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(ROOT/'assets/louvre',out/'assets/louvre',dirs_exist_ok=True)
    made=datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M %Z')
    days=plan['days'];places=plan['places'];wd=['周一','周二','周三','周四','周五','周六','周日']
    plan_label=esc(plan.get('display_version','v2'))
    def route(a,b):return routes.get(a+'__'+b)
    def stop_ref(day,key,optional,index):
        number=day['day']
        label=('O' if optional else '')+str(index)
        code=f'D{number:02d}-'+('O' if optional else '')+f'{index:02d}'
        anchor='stop-'+code.lower()
        for group in day.get('card_groups',[]):
            if group.get('number') is not None and key in group['members']:
                parent=int(group['number']);child=group['members'].index(key)
                label=f'{parent}-{child}';code=f'D{number:02d}-{parent:02d}-{child}'
                break
        return label,code,anchor

    def evening_map_points(day):
        result=[]
        for choice in day.get('evening_options',{}).get('choices',[]):
            for point in choice.get('map_points',[]):
                result.append(dict(id=point['id'],name=point['name'],coordinates=point['coordinates'],label=point['label'],code=f'D{day["day"]:02d}-'+point['label'],anchor='evening-'+choice['id'],optional=True,evening_option=choice['id'],color=choice['color'],note=choice['title']+'；'+choice['time']+'；'+point['coordinate_source'],time=choice['time'],coordinate_source=point['coordinate_source']))
        return result

    def meal_map_points(day):
        result=[]
        for market in day.get('market_suggestions',[]):
            if not market.get('meal_id') or not market.get('coordinates'):continue
            result.append(dict(id=market['id'],name=market['name']+'〔午餐候选〕',coordinates=market['coordinates'],label=market['map_label'],code=f'D{day["day"]:02d}-'+market['map_label'],anchor=market['anchor'],optional=True,meal_option=market['meal_id'],note=market['hours']+'；'+market['arrangement']+'；'+market['coordinate_source'],time=market['hours'],coordinate_source=market['coordinate_source']))
        return result

    def meal_market_options(day,meal):
        choices=[m for m in day.get('market_suggestions',[]) if m.get('meal_id')==meal['id']]
        result=''
        for market in choices:
            navigation=map_link(market)
            result+='<div class="meal-market-option"><h4>'+esc(market['map_label']+' · '+market['name']+'〔午餐候选〕')+'</h4><p><strong>市集日：</strong>'+esc(market['hours'])+'</p><p>'+esc(market['nearby'])+'</p><p>'+esc(market['arrangement'])+'</p><details><summary>启用后的时间分配与午餐条件</summary><p>'+esc(market['budget'])+'</p><p>'+esc(market['lunch_note'])+'</p></details><div class="source-links"><a target="_blank" rel="noopener" href="'+esc(navigation)+'">到市场路段去 ↗</a><a target="_blank" rel="noopener" href="'+esc(market['url'])+'">市政府：位置与营业时间 ↗</a></div></div>'
        return result

    def map_link(p):
        c=p['coordinates']
        return 'https://www.google.com/maps/dir/?'+urlencode(dict(api=1,destination=f'{c[1]},{c[0]}',travelmode='walking')) if c else None
    def guide_link(n,key):
        day=next(d for d in days if d['day']==n)
        return day.get('guide',{}).get(key,{}).get('href',f'day-{n:02d}-guide.html#place-{key}')
    link_icon='<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7 .1l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7-.1l-3 3a5 5 0 0 0 7 7l2-2"/></svg>'
    def nav(current):
        links=['<a class="overview" href="index.html"'+(' aria-current="page"' if current==0 else '')+'>行程总览</a>']
        links.insert(0,'<a class="overview" href="review-plan.html"'+(' aria-current="page"' if current=='review-plan.html' else '')+'>同行计划总表</a>')
        links.append('<section class="side-topics side-preparation" aria-labelledby="side-preparation-heading"><h2 id="side-preparation-heading">出行准备</h2>'+''.join('<a href="'+name+'"'+(' aria-current="page"' if current==name else '')+'>'+esc(title)+'</a>' for name,title,description,template in PREPARATION_PAGES)+'</section>')
        previous_area=None
        for d in days:
            if d.get('area_group')!=previous_area:
                previous_area=d.get('area_group')
                if previous_area:links.append('<p class="side-area">'+esc(previous_area)+'</p>')
            label=d['title'].split('：')[0]
            links.append(f'<a href="day-{d["day"]:02d}.html"'+(' aria-current="page"' if current==d['day'] else '')+f'>D{d["day"]:02d}<span class="day-label"> · {esc(label)}</span></a>')
        topic_links=[]
        if plan.get('performance_discussion'):
            topic=plan['performance_discussion']
            topic_links.append('<a href="'+esc(topic['filename'])+'"'+(' aria-current="page"' if current==topic['filename'] else '')+'>歌剧／芭蕾演出讨论</a><p>场馆、预算、字幕与待定项</p>')
        if plan.get('liberty_topic'):
            topic=plan['liberty_topic']
            topic_links.append('<a href="'+esc(topic['filename'])+'"'+(' aria-current="page"' if current==topic['filename'] else '')+'>'+esc(topic['nav_title'])+'</a><p>本次版本、所在日期与参观条件</p>')
        if topic_links:links.append('<section class="side-topics" aria-labelledby="side-topic-heading"><h2 id="side-topic-heading">专题与决议</h2>'+''.join(topic_links)+'</section>')
        return '<nav class="side" aria-label="按日查看与专题" data-site-nav><button type="button" class="nav-toggle" data-nav-toggle aria-controls="site-nav-links" aria-expanded="true" hidden>行程导航</button><div class="side-links" id="site-nav-links" data-nav-links>'+''.join(links)+'</div></nav>'
    def range_text(values,suffix=''):
        return f'{values[0]:g}–{values[1]:g}'+suffix
    def walking_numbers(day):
        w=day['walking_estimate']
        if w.get('unknown'):return None
        lo,hi=w['full_day_km']
        return dict(distance=range_text(w['full_day_km'],'公里'),time=range_text([math.floor(lo/4*60/5)*5,math.ceil(hi/3*60/5)*5],'分钟'),steps=range_text([math.floor(lo*1000/.75/500)*500,math.ceil(hi*1000/.60/500)*500],'步'))
    def walking_panel(day):
        w=day.get('walking_estimate')
        if not w:return ''
        values=walking_numbers(day)
        if values is None:return '<section class="walking-summary"><h2>本日步行</h2><p>'+esc(w['assumptions'])+'</p></section>'
        return '<section class="walking-summary" aria-label="本日步行估算"><h2>本日预计步行</h2><div class="walking-facts"><div><small>全天距离粗估 · 含馆内</small><strong>'+esc(values['distance'])+'</strong></div><div><small>累计移动 · 不含驻足</small><strong>'+esc(values['time'])+'</strong></div><div><small>估算步数</small><strong>'+esc(values['steps'])+'</strong></div></div><p>'+esc(w['assumptions'])+'</p><details><summary>室外路网与估算口径</summary><p>室外步行规划约'+esc(range_text(w['outdoor_km'],'公里'))+'；地图中馆间路网合计'+esc(w['route_reference_km'])+'公里／模型'+esc(w['route_reference_min'])+'分钟，包含公共交通段的步行替代路网，不能直接当作实际必走距离。</p><p>'+esc(w['method'])+'</p></details></section>'
    def companion_content():
        info=plan['companion_review'];body='<section class="companion-review"><p class="eyebrow">同行审阅</p><h1>'+esc(info['title'])+'</h1><p>'+esc(info['intro'])+'</p><div class="guide-actions"><a href="'+esc(info['text_filename'])+'" download>下载简表文本</a><button type="button" onclick="window.print()">打印／保存PDF</button><a href="index.html">地图与每日详情</a></div><p class="muted">步行栏为含馆内、园内的全天粗估；累计移动不含观展驻足、吃饭与乘车，不是在参观时长外另外加的一段时间。酒店往返另计，凡尔赛车站段已计入。</p>'
        lines=[info['title'],info['intro'],''];previous=None
        for row in info['rows']:
            day=next(d for d in days if d['day']==row['day']);values=walking_numbers(day)
            if row['area']!=previous:
                if previous is not None:body+='</tbody></table></div>'
                body+='<h2>'+esc(row['area'])+'</h2><div class="table-wrap"><table class="review-table"><thead><tr><th>日程</th><th>上午</th><th>下午</th><th>晚上</th><th>步行与强度</th><th>一起确认</th></tr></thead><tbody>'
                previous=row['area'];lines+=['',row['area']]
            walk=values['distance']+' · '+values['time']+' · '+values['steps'] if values else '随航班与住宿确定'
            body+='<tr><td data-label="日程"><a href="day-'+f'{day["day"]:02d}'+'.html"><strong>D'+f'{day["day"]:02d}'+'</strong><br>'+esc(day['title'])+'</a></td><td data-label="上午">'+esc(row['morning'])+'</td><td data-label="下午">'+esc(row['afternoon'])+'</td><td data-label="晚上">'+esc(row['evening'])+'</td><td data-label="步行与强度"><strong>'+esc(row['intensity'])+'</strong><p>'+esc(walk)+'</p></td><td data-label="一起确认">'+esc(row['focus'])+'</td></tr>'
            lines += [f'D{day["day"]:02d} '+day['title'],'上午：'+row['morning'],'下午：'+row['afternoon'],'晚上：'+row['evening'],'步行：'+walk+'；强度：'+row['intensity'],'一起确认：'+row['focus'],'']
        body+='</tbody></table></div><h2>希望大家反馈的内容</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in info['feedback'])+'</ul><p class="muted">'+esc(info['note'])+'</p><p><a href="index.html">查看地图与逐日安排 →</a></p></section>'
        lines+=['希望大家反馈：']+info['feedback']+['',info['note'],'步行是未实测的宽区间：步长按0.60–0.75米、移动速度按3–4公里／小时折算；不含观展驻足。室外路线、公共交通和馆内假设详见每日页。']
        return body,'\n'.join(lines)+'\n'

    def page(title,current,content,body_js='',road_credit='法国 IGN BD TOPO'):
        if isinstance(current,int) and current>0:
            day=next(d for d in days if d['day']==current)
            content=content.replace('</h1>','</h1>'+walking_panel(day),1)
        return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Cache-Control" content="no-cache"><title>'+esc(title)+'｜巴黎行程</title><style>'+css+'</style></head><body><div class="shell"><header class="top"><div><a class="brand" href="index.html">巴黎与凡尔赛 · 行程</a><p class="muted">2027年2–3月，日期待定 · 北京往返 · 原稿旅行密度</p></div><div class="version">行程 '+plan_label+' · 按日页面 v3<br>数据 '+data_id+'<br>'+esc(made)+'</div></header><div class="layout">'+nav(current)+'<main>'+content+'<footer class="foot">讨论依据：行程 '+plan_label+'／数据 '+data_id+'。页面景点、顺序和路线均来自同一份日程数据。<br>时刻与预约尚未确定；原Google Doc与在线地图未修改。<br>步行路网：'+esc(road_credit)+'；底图 © IGN – Plan IGN。距离不含酒店往返、馆内步行、排队或现场入口差异。</footer></main></div></div><script>'+site_ui+'</script>'+body_js+'</body></html>'
    def market_section(day=None):
        choices=[(d,m,False) for d in ([day] if day else days) for m in d.get('market_suggestions',[]) if day is None or not m.get('meal_id')]
        if day is None:choices += [(d,m,True) for d in days for m in d.get('planned_markets',[])]
        if not choices:return ''
        choices.sort(key=lambda item:item[0]['day'])
        rows=[]
        for d,m,planned in choices:
            anchor=m.get('anchor','market-suggestions')
            slot=('<a href="day-'+f'{d["day"]:02d}'+'.html#'+esc(anchor)+'">D'+f'{d["day"]:02d}'+'</a> · ' if day is None else '')+esc(m['nearby'])
            status='已安排' if planned else '按星期候选'
            rows.append('<tr><td><a target="_blank" rel="noopener" href="'+esc(m['url'])+'"><strong>'+esc(m['name'])+'</strong> ↗</a><p class="muted">'+status+'</p></td><td>'+slot+'</td><td>'+esc(m['hours'])+'</td><td><strong>'+esc(m['duration'])+'</strong><p>'+esc(m['arrangement'])+'</p>'+('<p class="muted">'+esc(m['budget'])+'</p>' if day else '')+'</td></tr>')
        title='食品市场：已安排与顺路候选' if day is None else '顺路食品市场候选'
        intro='D07的Bourse市场已正式加入主线午餐与逛摊；D04、D11仍按实际星期选择候选。' if day is None else '按实际星期选择，尚未加入固定时间表。'
        return '<section class="place-guide" id="market-suggestions"><h2>'+title+'</h2><p>'+intro+'均为定期食品市场，现场出摊、午餐选择与座位需再核。D10不再安排市场。</p><div class="table-wrap"><table><thead><tr><th>市场／状态</th><th>对应行程与位置</th><th>当前官方营业时间</th><th>安排与时间</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p class="muted">营业与位置核对于2026-11-10；2027出行前按实际日期复核临时停市、天气和商户出摊。D04候选需提早出门，D11候选计入片区总预算；D07先在市场安排80分钟（含午餐1小时），再逛拱廊。不默认三个都去。</p></section>'

    def evening_section(day):
        info=day.get('evening_options')
        if not info:return ''
        result='<section class="meal-card evening-options" id="evening-options" aria-labelledby="evening-options-title"><span class="stop-code">D'+f'{day["day"]:02d}'+' · 晚间选择</span><h3 id="evening-options-title">'+esc(info['title'])+'</h3><p>'+esc(info['intro'])+'</p>'
        for choice in info['choices']:
            point_key='地图标记：'+' · '.join(point['label']+' '+point['name'] for point in choice.get('map_points',[])) if choice.get('map_points') else ''
            result+='<details class="evening-choice" id="evening-'+esc(choice['id'])+'"><summary>'+esc(choice['title'])+'</summary>'+('<p class="muted">'+esc(point_key)+'</p>' if point_key else '')+'<p class="meal-time">'+esc(choice['time'])+'</p><p>'+esc(choice['description'])+'</p><p class="muted">'+esc(choice['timing'])+'</p><div class="source-links"><a target="_blank" rel="noopener" href="'+esc(choice['navigation'])+'">'+esc(info.get('navigation_label','从邮政馆出发查看路线'))+' ↗</a><a target="_blank" rel="noopener" href="'+esc(choice['url'])+'">介绍与营业依据 ↗</a></div></details>'
        return result+'<p class="muted">'+esc(info['note'])+' <a target="_blank" rel="noopener" href="'+esc(info['note_url'])+'">'+esc(info.get('note_link_label','观景台官方状态 ↗'))+'</a></p></section>'

    def transport_section(day):
        data=day.get('transport_info')
        if not data:return ''
        result='<section class="place-guide" id="transport-info"><h2>'+esc(data['title'])+'</h2><p>'+esc(data['intro'])+'</p>'
        for group in data['sections']:
            result+='<h3>'+esc(group['title'])+'</h3><div class="table-wrap"><table><thead><tr><th>方案／事项</th><th>交通与操作</th><th>时间与预算</th></tr></thead><tbody>'+''.join('<tr><td><strong>'+esc(item['name'])+'</strong></td><td>'+esc(item['detail'])+' <a target="_blank" rel="noopener" href="'+esc(item['url'])+'">来源 ↗</a></td><td>'+esc(item['budget'])+'</td></tr>' for item in group['rows'])+'</tbody></table></div>'
        return result+'<p class="muted">'+esc(data['note'])+'</p></section>'

    def nearby_section(day):
        choices=day.get('nearby_suggestions',[])
        if not choices:return ''
        cards=''
        for item in choices:
            cards+='<article><h3>'+esc(item['name'])+'</h3><p class="muted">'+esc(item['where'])+' · '+esc(item['duration'])+'</p><p>'+esc(item['content'])+'</p><p><strong>怎样安排：</strong>'+esc(item['timing'])+'</p><a target="_blank" rel="noopener" href="'+esc(item['url'])+'">官方介绍／开放规则 ↗</a></article>'
        return '<section class="place-guide" id="nearby-suggestions"><h2>沿路与附近：短停和取舍</h2><p>除已写明纳入主线的地点，其余只作候选；先保留现有场馆、用餐、休息和转场，不默认全部叠加。</p><div class="highlight-grid">'+cards+'</div></section>'

    def overview_map():
        palette=['#2563A8','#B32935','#087F8C','#7751A8','#8C5A28','#C86200','#23834D','#B93787','#4F46A8','#007B66','#777012','#58677C']
        mapped=[];filters=[]
        for d in days:
            if not d['core']:continue
            n=d['day'];color=palette[n-2];points=[];legs=[]
            for optional,keys in [(False,d['core']),(True,d['optional']+d['alternative'])]:
                for i,key in enumerate(keys,1):
                    p=places[key]
                    if not p['coordinates']:continue
                    label,code,anchor=stop_ref(d,key,optional,i)
                    points.append(dict(id=key,name=p['name'],coordinates=p['coordinates'],label=label,code=code,optional=optional,time=d.get('visits',{}).get(key,{}).get('time',''),href=f'day-{n:02d}.html#'+anchor))
            for point in evening_map_points(d)+meal_map_points(d):points.append(point|dict(href=f'day-{n:02d}.html#'+point['anchor']))
            for i,(a,b) in enumerate(zip(d['core'],d['core'][1:]),1):
                item=route(a,b)
                if item and item.get('status')=='ok':legs.append(dict(a=a,b=b,label=places[a]['name']+' → '+places[b]['name'],distance=item['distance_m'],duration=item['duration_min'],geometry=item['geometry'],href=f'day-{n:02d}.html#stop-d{n:02d}-{i:02d}'))
            mapped.append(dict(day=n,title=d['title'],color=color,points=points,legs=legs))
            checked=' checked' if n!=13 else ''
            filters.append('<div class="day-layer-row"><label class="day-layer" style="--route-color:'+color+'"><input type="checkbox" data-map-day="'+str(n)+'"'+checked+'><span class="day-swatch" aria-hidden="true"></span><span><strong>D'+f'{n:02d}'+'</strong><small>'+esc(d['title'])+'</small></span></label><button type="button" data-map-focus="'+str(n)+'" aria-label="仅看Day '+str(n)+'">仅看</button></div>')
        section='<section class="overview-section" aria-labelledby="overview-heading"><h2 id="overview-heading">跨日路线地图</h2><p>同时勾选要比较的日期，查看相邻点位与每天的路线。点位数字是“日期·当天顺序”，点击可打开所属日程卡片。</p><div class="overview-presets" aria-label="地图快捷选择"><button type="button" data-map-preset="paris">巴黎市区</button><button type="button" data-map-preset="versailles">凡尔赛</button><button type="button" data-map-preset="all">全部行程</button><button type="button" data-map-preset="compare">对比 D02 与 D03</button><button type="button" data-map-preset="rebalance">对比 D04／D09／D05</button><button type="button" data-map-preset="west">对比 D09／D11／D10／D12</button><button type="button" data-map-preset="none">清空</button></div><p class="muted overview-hint">默认显示巴黎市区；凡尔赛可单独查看，也可与其他日期同时勾选。</p><div class="overview-layout"><div class="overview-map-column"><div class="overview-controls"><label><input type="checkbox" id="overview-optional" checked>显示可选／顺路点</label><button type="button" id="overview-map-toggle" disabled>底图加载中</button></div><div class="overview-map-frame"><div id="overview-street" aria-label="按日期分色的跨日街道地图"></div><svg id="overview-offline" role="img" aria-label="按日期分色的跨日坐标路线图"></svg></div><p class="map-status" id="overview-status">坐标与路线已包含在本页；正在尝试加载IGN底图。</p><p class="overview-count" id="overview-count" aria-live="polite">正在整理所选日期的点位与路线。</p><div id="overview-detail" class="overview-detail" aria-live="polite"><p>点击点位查看所属日期与当天顺序。</p></div></div><aside class="overview-layers" aria-label="按日筛选路线"><h3>按日筛选／颜色图例</h3>'+''.join(filters)+'</aside></div><p class="muted overview-hint">实心标记为拟安排景点，空心虚线标记为可选点；重复地点会合并显示所属日期。路线按当天顺序连接，只绘制已有的步行路网，不表示必须全程步行。酒店与机场尚未确定，不画假点。</p></section>'
        payload=json.dumps(dict(days=mapped),ensure_ascii=False).replace('<',chr(92)+'u003c')
        return section,'<script id="overview-data" type="application/json">'+payload+'</script><script>'+overview_js+'</script>'
    overview_section,overview_body_js=overview_map()
    overview='<section class="review-entry"><h2>同行计划总表</h2><p>按片区查看每天的上午、下午、晚上、参观强度和步行负担。</p><div class="guide-actions"><a href="review-plan.html">打开计划总表 →</a><a href="review-plan.txt" download>下载文本</a></div></section><p class="eyebrow">按日审阅</p><h1>先确定每天去哪里，再讨论怎么调整</h1><p>点击任意一天查看独立页面。景点序号、当天地图与区间距离一一对应；讨论时可直接使用“D02-04”这样的编号。</p><div class="policy">以原稿密度保留已安排项目。D01抵达巴黎、D14离开巴黎仍是航班待定时的计算假设；当前只审阅巴黎游览与离境安排。D04集中玛黑区，D09给奥赛留4小时，D11下水道后先看展、片区连午餐共3–4小时，D10荣军院／罗丹后参观从D03移来的邮政馆，D03取消蒙帕纳斯绕行并留白天卢森堡公园休息，D07大小皇宫、Bourse午餐、拱廊与歌剧院街区，D12上午登顶铁塔、下午夏乐宫两馆及必选自由女神像；D06三翼与D05中央片区保留。所有时段仍须按实际日期及预约确认。</div>'+overview_section+'<h2>每日行程</h2><div class="day-grid">'
    for d in days:
        names=' → '.join(places[k]['name'] for k in d['core']) or d['intro']
        counts=f'{len(d["core"])}处拟安排'+(f' · {len(d["optional"])}项可选／待review' if d['optional'] else '') if d['core'] else '交通日'
        overview+=f'<a class="day-card" href="day-{d["day"]:02d}.html"><span class="num">DAY {d["day"]:02d} · {esc(d["theme"])}</span><br><strong>{esc(d["title"])}</strong><p>{esc(names)}</p><p>{esc(counts)}</p></a>'
    overview+='</div><h2>后续讨论方式</h2><p>例如：“把D02-05移到Day 03”“Day 09先看海军府再去小皇宫”。确认调整后，统一更新日程数据并生成新版本；旧版本会保留，便于比较。</p><p class="muted">固定入口为web/current/index.html；每次构建更新同一组页面。已经打开的本地页面请刷新，并核对页首的数据标识和生成时间。</p>'
    (out/'index.html').write_text(page('按日总览',0,overview,overview_body_js),encoding='utf-8')
    mode_notes={'grandpalais':'沿用原稿先看外观；入内特展另核实。','moulin':'原稿按外观，未计入演出。'}
    for d in days:
        n=d['day'];points=[];legs=[];cards=[];discussion=[f'巴黎行程{plan_label}，数据{data_id}，Day {n:02d}：{d["title"]}']
        place_cards={};meal_cards={}
        grouped_optional={key for group in d.get('card_groups',[]) for key in group['members'][1:]}
        for optional,keys in [(False,d['core']),(True,d['optional']+d['alternative'])]:
            if optional and any(key not in grouped_optional for key in keys):cards.append('<h2>'+esc(d.get('optional_heading','原稿可选／顺路项目'))+'</h2>')
            for i,key in enumerate(keys,1):
                p=places[key];label,code,anchor=stop_ref(d,key,optional,i)
                note=d.get('place_notes',{}).get(key,mode_notes.get(key,p.get('note',''))) or ('新增近邻建议，待你review。' if key in ('garnier','vivienne') else '保留原稿项目，具体入场时段下一阶段确定。')
                badge=p.get('badge') or ('新增近邻建议' if key in ('garnier','vivienne') else '原稿可选·已纳入路线' if p.get('note','').startswith('原稿可选') else '原稿可选／顺路' if optional else '原稿项目')
                visit=d.get('visits',{}).get(key)
                badge_html='' if d.get('hide_origin_badges') else f'<span class="badge">{esc(badge)}</span>'
                if visit:
                    note=visit['time']+'；'+visit['description']
                    fields=[('时间',visit['time']+'〔建议，未预约〕'),('耗时',visit['duration'])]
                    if visit.get('focus'):fields.append(('看点',visit['focus']))
                    fields += [('开放',visit['opening']),('票务',visit['tickets']),('交通',visit['transport'])]
                    detail_html='<p>'+esc(visit['description'])+'</p><dl class="visit-details">'+''.join('<dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd>' for label,value in fields)+'</dl><div class="source-links">'+''.join('<a target="_blank" rel="noopener" href="'+esc(s['url'])+'">'+esc(s['title'])+'</a>' for s in visit['sources'])+'</div>'
                else:detail_html='<p>'+esc(note)+'</p>'
                if key in {v['place'] for v in d.get('exhibition_review',{}).get('venues',[])}:
                    detail_html+='<a class="map-directions" href="#exhibitions-'+esc(key)+'" aria-label="查看'+esc(p['name'])+'的2027年2至3月展览">查看2027年2—3月展览 →</a>'
                link=map_link(p)
                title_html=esc(p['name'])
                directions_html='<a class="map-directions" target="_blank" rel="noopener" aria-label="到这里去：'+esc(p['name'])+'（Google Maps步行导航）" title="Google Maps步行导航" href="'+esc(link)+'">到这里去</a>' if link else ''
                guide_label=d.get("guide_meta",{}).get("label","景点介绍与看点")
                info_link='<a class="guide-link" href="'+guide_link(n,key)+'" aria-label="查看'+esc(p['name'])+'的'+esc(guide_label)+'" title="'+esc(guide_label)+'">'+link_icon+'</a>' if key in d.get('guide',{}) else ''
                card_html=f'<section class="stop'+(' optional' if optional else '')+f'" id="{anchor}"><div class="stop-top"><span class="stop-number">{label}</span><div class="stop-title"><span class="stop-code">{code}</span><h3>'+title_html+'</h3>'+directions_html+'</div>'+info_link+'</div>'+badge_html+detail_html+('' if link else '<span class="muted">位置待确认，暂不提供定位导航。</span>')+'</section>'
                cards.append(card_html);place_cards[key]=card_html
                for group in d.get('card_groups',[]):
                    if group.get('number') is not None and key==group['members'][0]:
                        discussion.append(f'D{n:02d}-{int(group["number"]):02d} '+group['title'])
                discussion.append(code+' '+p['name']+('〔可选〕' if optional else ''))
                if visit:discussion.append('  建议时间：'+visit['time']+'；票务：'+visit['tickets'])
                if p['coordinates']:points.append(dict(id=key,name=p['name'],coordinates=p['coordinates'],label=label,code=code,anchor=anchor,optional=optional,note=note))
                if not optional and key==d.get('evening_options',{}).get('after') and not d['evening_options'].get('after_meals'):
                    cards.append(evening_section(d))
                    discussion.append(d['evening_options']['title'])
                    discussion.extend('  '+choice['title']+'：'+choice['time']+'；'+choice['timing'] for choice in d['evening_options']['choices'])
                for meal in d.get('interludes',[]):
                    if optional or meal['after']!=key:continue
                    cards.append('<section class="meal-card" id="meal-'+esc(meal['id'])+'"><div class="meal-top"><span aria-hidden="true">☷</span><div><span class="stop-code">'+esc(meal['code'])+'</span><h3>'+esc(meal['title'])+'</h3></div></div><p class="meal-time">'+esc(meal['time'])+' · '+esc(meal['duration'])+'</p><p>'+esc(meal['description'])+'</p><p class="muted">'+esc(meal['note'])+'</p>'+meal_market_options(d,meal)+'</section>')
                    meal_cards[meal['id']]=cards[-1]
                    discussion.append(meal['code']+' '+meal['title']+' '+meal['time']+'；'+meal['note'])
                if not optional and key==d.get('evening_options',{}).get('after') and d['evening_options'].get('after_meals'):
                    cards.append(evening_section(d))
                    discussion.append(d['evening_options']['title'])
                    discussion.extend('  '+choice['title']+'：'+choice['time']+'；'+choice['timing'] for choice in d['evening_options']['choices'])
                if not optional and i<len(keys):
                    b=keys[i];r=route(key,b);label_text=p['name']+' → '+places[b]['name']
                    transfer_note=d.get('transfer_notes',{}).get(key+'__'+b,{})
                    transfer_extra=('<p>'+esc(transfer_note['text'])+'</p><div class="source-links">'+''.join('<a target="_blank" rel="noopener" href="'+esc(link['url'])+'">'+esc(link['title'])+'</a>' for link in transfer_note.get('links',[]))+'</div>') if transfer_note else ''
                    if r and r['status']=='ok':
                        metric=f'{r["distance_m"]/1000:.2f} km · 步行模型约{math.ceil(r["duration_min"]/5)*5}分钟'
                        hint='；长段可用公交／地铁衔接' if r['distance_m']>1500 else ''
                        cards.append('<div class="transfer">↓ '+esc(transfer_note.get('label',metric+hint))+transfer_extra+'</div>')
                        legs.append(dict(a=key,b=b,label=label_text,distance=r['distance_m'],duration=r['duration_min'],straight=r['straight_m'],geometry=r['geometry'],transport_label=transfer_note.get('label')))
                    else:
                        cards.append('<div class="transfer">↓ 下一段位置／入口待确认</div>')
                        legs.append(dict(a=key,b=b,label=label_text,distance=None,duration=None,straight=None,geometry=None))
        points.extend(evening_map_points(d))
        points.extend(meal_map_points(d))
        for group in d.get('card_groups',[]):
            members=group['members'];host=members[0]
            assert host in d['core'] and all(key in d['optional']+d['alternative'] for key in members[1:])
            group_id='shared-'+group['id']
            group_meals=set(group.get('interlude_ids',[]))
            grouped_parts=[]
            for key in members:
                grouped_parts.append(place_cards[key])
                grouped_parts.extend(meal_cards[meal['id']] for meal in d.get('interludes',[]) if meal['id'] in group_meals and meal['after']==key)
            assert group_meals.issubset(meal_cards)
            group_number='<span class="stop-number">'+esc(group['number'])+'</span>' if group.get('number') is not None else ''
            grouped_html='<section class="shared-visit" id="'+esc(group_id)+'" aria-labelledby="'+esc(group_id)+'-title"><h3 class="shared-visit-title" id="'+esc(group_id)+'-title">'+group_number+'<span>'+esc(group['title'])+'</span></h3><p class="shared-visit-note">'+esc(group['note'])+'</p>'+''.join(grouped_parts)+'</section>'
            cards[cards.index(place_cards[host])]=grouped_html
            consumed=[place_cards[key] for key in members[1:]]+[meal_cards[key] for key in group_meals]
            cards=[card for card in cards if card not in consumed]
        head=f'<p class="eyebrow">DAY {n:02d} · {esc(d["theme"])}</p><h1>{esc(d["title"])}</h1><p>{esc(d["intro"])}</p><div class="facts"><span>日期待定</span><span>{len(d["core"])}处拟安排</span><span>讨论编号 D{n:02d}-01 起</span></div><p><strong>全天耗时估算：</strong>{esc(d["duration"])}</p><div class="policy"><strong>待确认：</strong>{esc(d["review"])}</div>'
        if d.get('todos'):
            review_panel='<details class="todo-panel" id="todo-panel"><summary class="todo-summary" id="todo-heading"><span>待确认与待办</span><small id="todo-progress">'+str(sum(bool(item.get('done')) for item in d['todos']))+' / '+str(len(d['todos']))+' 已完成</small></summary><div class="todo-content"><p>'+esc(d.get('todo_summary',d['review']))+'</p>'
            groups=list(dict.fromkeys(item['group'] for item in d['todos']))
            for group in groups:
                review_panel+='<fieldset class="todo-group"><legend>'+esc(group)+'</legend>'
                for item in d['todos']:
                    if item['group']!=group:continue
                    checked=' checked' if item.get('done') else ''
                    signature=digest(serial({'title':item['title'],'detail':item['detail']}))
                    review_panel+='<label class="todo-item"><input type="checkbox" data-todo-key="paris-trip:d'+f'{d.get("todo_storage_day",n):02d}'+':'+esc(item['id'])+'" data-todo-signature="'+signature+'"'+checked+'><span><strong>'+esc(item['title'])+'</strong><small>'+esc(item['detail'])+'</small></span></label>'
                review_panel+='</fieldset>'
            review_panel+='<p class="todo-save-status" id="todo-save-status" role="status">可勾选记录进度，勾选状态保存在当前浏览器；日程文件中的正式进度由我们确认后更新。</p></div></details>'
            head=head.replace('<div class="policy"><strong>待确认：</strong>'+esc(d['review'])+'</div>',review_panel)
            discussion.append('\n待确认与待办：')
            discussion.extend(('☑ ' if item.get('done') else '□ ')+item['title']+'：'+item['detail'] for item in d['todos'])
        if d.get('related_pages'):
            head+='<p class="source-links">'+''.join('<a href="'+esc(link['href'])+'">'+esc(link['title'])+'</a>' for link in d['related_pages'])+'</p>'
        if d['avoid_weekdays']:head+='<p class="muted">当前组合的排期条件：避开'+'、'.join(wd[i] for i in d['avoid_weekdays'])+'；真实日期确定后复核。</p>'
        head+=market_section(d)
        head+=transport_section(d)
        if d.get('schedule'):
            head+='<h2>建议时间表</h2><p class="muted">'+esc(d['schedule_note'])+'</p><div class="table-wrap"><table><thead><tr><th>建议时段</th><th>安排与缓冲</th></tr></thead><tbody>'+''.join('<tr><td class="metric">'+esc(row['time'])+'</td><td>'+esc(row['activity'])+'</td></tr>' for row in d['schedule'])+'</tbody></table></div>'
            head+='<div class="policy"><strong>'+esc(d.get('connection_title','古街区与中世纪馆的衔接'))+'：</strong>'+esc(d['connection_review'])+'</div>'
        if d.get('sources'):
            head+='<details><summary>本日核对来源（'+esc(d.get('checked_date',plan['checked_date']))+'，2027年再复核）</summary><ul>'+''.join('<li><a target="_blank" rel="noopener" href="'+esc(source['url'])+'">'+esc(source['title'])+'</a></li>' for source in d['sources'])+'</ul></details>'
        if d.get('audit'):
            audit=d['audit']
            head+='<details class="review-audit"'+(' id="'+esc(audit['id'])+'"' if audit.get('id') else '')+'><summary>'+esc(audit['title'])+'</summary><p>'+esc(audit['intro'])+'</p><div class="table-wrap"><table><thead><tr><th>项目</th><th>本版安排</th><th>核对与说明</th></tr></thead><tbody>'+''.join('<tr><td>'+esc(row['name'])+'</td><td>'+esc(row['status'])+'</td><td>'+esc(row['detail'])+(' <a target="_blank" rel="noopener" href="'+esc(row['url'])+'">来源 ↗</a>' if row.get('url') else '')+'</td></tr>' for row in audit['rows'])+'</tbody></table></div></details>'
        head+=nearby_section(d)
        exhibition_body_js=''
        if d.get('exhibition_review'):
            exhibition_html,exhibition_body_js=render_exhibition_review(d['exhibition_review'],exhibition_js)
            head+=exhibition_html
        indoor_body_js='';indoor_html=''
        if d.get('indoor'):
            indoor_html,indoor_body_js=render_indoor(ROOT,d['indoor'])
        day_index=days.index(d)
        prev_day=days[day_index-1]['day'] if day_index>0 else None
        next_day=days[day_index+1]['day'] if day_index+1<len(days) else None
        prev=f'<a href="day-{prev_day:02d}.html">← Day {prev_day:02d}</a>' if prev_day is not None else '<a href="index.html">← 总览</a>'
        nxt=f'<a href="day-{next_day:02d}.html">Day {next_day:02d} →</a>' if next_day is not None else '<a href="index.html">返回总览 →</a>'
        pager='<nav class="pager" aria-label="前后日程">'+prev+nxt+'</nav>'
        map_section=''
        if points:
            rows=[]
            for leg in legs:
                metric=f'{leg["distance"]/1000:.2f} km<br>约{math.ceil(leg["duration"]/5)*5}分钟' if leg['distance'] is not None else '待确认'
                if leg.get('transport_label'):metric=esc(leg['transport_label'])+'<br><small>步行对照：'+metric+'</small>'
                straight=f'{leg["straight"]/1000:.2f} km' if leg['straight'] is not None else '—'
                rows.append('<tr><td>'+esc(leg['label'])+'</td><td class="metric">'+metric+'</td><td class="metric">'+straight+'</td></tr>')
            if not rows:rows=['<tr><td colspan="3">单一大场馆；本日没有固定馆间移动段。</td></tr>']
            map_section='<aside class="map-column"><h2>本日地图</h2><div class="map-controls"><label><input type="checkbox" id="show-optional" checked>地图显示可选项目</label><button type="button" id="map-toggle" disabled>底图加载中</button></div><div class="map-frame"><div id="street-map" aria-label="本日街道地图"></div><svg id="offline-map" role="img" aria-label="本日景点与步行路线"></svg></div><p class="map-status" id="map-status">地点与路线已包含在本页；正在尝试加载IGN底图。</p><p class="legend">数字 = 本日顺序 · O = 可选项目 · 点击标记查看对应条目</p><h2>区间距离</h2><div class="table-wrap"><table><thead><tr><th>区间</th><th>步行路网／模型</th><th>直线</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p class="muted">距离用于判断位置，不要求全程步行；园区路径与入口仍需现场核对。</p></aside>'
            if any(group.get('number') is not None for group in d.get('card_groups',[])):
                map_section=map_section.replace('数字 = 本日顺序 · O = 可选项目','数字 = 本日顺序 · 2-0／2-1 = 第2块子项 · 空心标记 = 可选项目')
            if d.get('evening_options'):map_section=map_section.replace('数字 = 本日顺序 · O = 可选项目 · 点击标记查看对应条目',d['evening_options'].get('map_legend','实心数字 = 主线 · 空心字母标记 = 晚间可选点，点击查看方案'))
            if any(leg.get('transport_label') for leg in legs):map_section=map_section.replace('步行路网／模型','建议交通／步行对照')
            if d.get('map_note'):map_section=map_section.replace('</aside>','<p class="muted">'+esc(d['map_note'])+'</p></aside>')
            group_link='<a class="group-guide" href="'+esc(d.get('guide_meta',{}).get('href',f'day-{n:02d}-guide.html'))+'" aria-label="打开本日指南">'+esc(d.get('guide_meta',{}).get('label','景点介绍'))+' ↗</a>' if d.get('guide') else ''
            content=head+pager+'<div class="review-layout"><section class="stops"><div class="group-heading"><h2>参观顺序</h2>'+group_link+'</div>'+''.join(cards)+'</section>'+map_section+'</div>'+indoor_html
        else:content=head+pager+'<section class="flight"><h2>交通与入住</h2><p>'+esc(d['review'])+'</p><p class="muted">机场、航班与住宿未定，本页暂不绘制位置或虚构路线。</p></section>'
        if n==1:
            content+='<section class="place-guide"><h2>出发前准备</h2><div class="highlight-grid">'+''.join('<article><h3><a href="'+name+'">'+esc(title)+' →</a></h3><p>'+esc(description)+'</p></article>' for name,title,description,template in PREPARATION_PAGES)+'</div></section>'
        content+='<details><summary>本日讨论提纲（可复制）</summary><textarea readonly aria-label="本日讨论提纲">'+esc('\n'.join(discussion)+'\n\n我希望调整：')+'</textarea></details>'+pager
        safe=json.dumps(dict(day=n,points=points,legs=legs),ensure_ascii=False).replace('<','\\u003c')
        body_js='<script id="day-data" type="application/json">'+safe+'</script><script>'+js+'</script>' if points else ''
        if d.get('todos'):body_js+='<script>'+todo_js+'</script>'
        body_js+=indoor_body_js+exhibition_body_js
        (out/f'day-{n:02d}.html').write_text(page(f'Day {n:02d} {d["title"]}',n,content,body_js),encoding='utf-8')
        if d.get('guide') and not d.get('guide_meta',{}).get('external_only'):
            meta=d.get('guide_meta',{})
            guide_stops=[(key,stop_ref(d,key,optional,i)[0],stop_ref(d,key,optional,i)[2]) for optional,keys in [(False,d['core']),(True,d['optional']+d['alternative'])] for i,key in enumerate(keys,1)]
            guide='<p class="eyebrow">DAY '+f'{n:02d}'+' · '+esc(meta.get('label','景点介绍'))+'</p><h1>'+esc(meta.get('title','今天看什么'))+'</h1><p>'+esc(meta.get('intro','按当天行程顺序阅读简介与重点。下面的看点和参观顺序是建议，展品借展、开放区域与现场路线以实际参观日为准。'))+'</p><p><a href="day-'+f'{n:02d}'+'.html">← 返回本日日程与地图</a></p><nav class="guide-toc" aria-label="景点介绍目录">'+''.join('<a href="#place-'+key+'">'+esc(places[key]['name'])+'</a>' for key,label,anchor in guide_stops if key in d['guide'])+'</nav>'
            for key,label,anchor in guide_stops:
                if key not in d['guide']:continue
                item=d['guide'][key];p=places[key];visit=d.get('visits',{}).get(key,{})
                guide+='<section class="place-guide" id="place-'+key+'"><div class="guide-section-heading"><span class="stop-number">'+esc(label)+'</span><h2>'+esc(p['name'])+'</h2></div><p>'+esc(item['intro'])+'</p><p class="guide-slot">当天建议：'+esc(visit.get('time','时段待定'))+'</p><h3>'+esc(item.get('highlights_heading','值得看的内容'))+'</h3><div class="highlight-grid">'+''.join('<article><h4>'+esc(h['title'])+'</h4><p>'+esc(h['text'])+'</p></article>' for h in item['highlights'])+'</div><h3>'+esc(item.get('route_heading','怎么安排这段参观'))+'</h3><p>'+esc(item['route'])+'</p><p class="muted">'+esc(item['note'])+'</p><div class="guide-actions"><a href="day-'+f'{n:02d}'+'.html#'+anchor+'">返回日程卡片</a><a target="_blank" rel="noopener" href="'+esc(map_link(p))+'">Google Maps导航 ↗</a>'+''.join('<a href="'+esc(link['href'])+'">'+esc(link['title'])+'</a>' for link in item.get('links',[]))+'</div><details><summary>介绍来源</summary><ul>'+''.join('<li><a target="_blank" rel="noopener" href="'+esc(s['url'])+'">'+esc(s['title'])+'</a></li>' for s in item['sources'])+'</ul></details></section>'
            (out/f'day-{n:02d}-guide.html').write_text(page(meta.get('title',f'Day {n:02d} 景点介绍与看点'),n,guide),encoding='utf-8')
        if d.get('shop_guide'):
            shop_content,shop_body_js=render_shop_page(n,d['shop_guide'],shop_js)
            (out/f'day-{n:02d}-shops.html').write_text(page(f'Day {n:02d} 推荐店铺与步行地图',n,shop_content,shop_body_js,road_credit=d['shop_guide'].get('road_credit','IGN BD TOPO；相邻店铺短段 © OpenStreetMap contributors／FOSSGIS')),encoding='utf-8')
    if plan.get('performance_discussion'):
        topic=plan['performance_discussion']
        topic_html='<p class="eyebrow">专题讨论 · 演出待选</p><h1>'+esc(topic['title'])+'</h1><p>'+esc(topic['intro'])+'</p><p><a href="'+esc(topic['return_href'])+'">← '+esc(topic['return_title'])+'</a></p>'
        if topic.get('budget_language'):
            info=topic['budget_language']
            topic_html+='<section id="budget-language"><h2>'+esc(info['heading'])+'</h2><p>'+esc(info['preference'])+'</p><div class="policy"><strong>当前建议：</strong>'+esc(info['recommendation'])+'</div><h3>语言、字幕与座位</h3><div class="highlight-grid">'
            for item in info['language_cards']:
                topic_html+='<article><h4>'+esc(item['title'])+'</h4><p>'+esc(item['text'])+'</p><div class="source-links">'+''.join('<a target="_blank" rel="noopener" href="'+esc(s['url'])+'">'+esc(s['title'])+'</a>' for s in item['sources'])+'</div></article>'
            topic_html+='</div><h3>按每人票价比较候选</h3><p class="muted">'+esc(info['price_note'])+'</p><div class="table-wrap"><table><thead><tr><th>节目／场馆</th><th>公布票档 · 欧元／人</th><th>语言支持</th><th>理解负担与建议</th></tr></thead><tbody>'
            for item in info['rows']:
                topic_html+='<tr><td><strong>'+esc(item['name'])+'</strong><br>'+esc(item['venue'])+'<div class="source-links"><a target="_blank" rel="noopener" href="'+esc(item['show_source'])+'">官方节目</a><a target="_blank" rel="noopener" href="'+esc(item['price_source'])+'">官方价目</a></div></td><td>'+esc(item['prices'])+'</td><td>'+esc(item['language'])+'</td><td><strong>'+esc(item['assessment'])+'</strong><p>'+esc(item['advice'])+'</p></td></tr>'
            topic_html+='</tbody></table></div><h3>怎样计算整晚预算</h3><ul>'+''.join('<li>'+esc(note)+'</li>' for note in info['budget_notes'])+'</ul><h3>减少看不懂的风险</h3><div class="highlight-grid">'+''.join('<article><h4>'+esc(item['title'])+'</h4><p>'+esc(item['text'])+'</p></article>' for item in info['preparation'])+'</div></section>'
        topic_html+='<h2>两种体验怎么选</h2><div class="highlight-grid">'+''.join('<article><h3>'+esc(item['title'])+'</h3><p>'+esc(item['text'])+'</p></article>' for item in topic['choices'])+'</div>'
        topic_html+='<h2>节目、时间与参观方式</h2><p class="muted">官方资料核验于'+esc(topic['checked_date'])+'；演期内并非每日有场，库存与实际场次另核。</p>'
        for i,row in enumerate(topic['rows'],1):
            topic_html+='<section class="place-guide" id="option-'+str(i)+'"><h3>'+esc(row['name'])+'</h3><p><strong>'+esc(row['status'])+'</strong></p><p>'+esc(row['detail'])+'</p><a target="_blank" rel="noopener" href="'+esc(row['url'])+'">官方资料 ↗</a></section>'
        topic_html+='<h2>接下来要决定</h2><ul>'+''.join('<li><strong>'+esc(item['title'])+'</strong>：'+esc(item['detail'])+'</li>' for item in topic['todos'])+'</ul>'
        topic_html+='<details><summary>参考来源</summary><ul>'+''.join('<li><a target="_blank" rel="noopener" href="'+esc(item['url'])+'">'+esc(item['title'])+'</a></li>' for item in topic['sources'])+'</ul></details><p><a href="'+esc(topic['return_href'])+'">← '+esc(topic['return_title'])+'</a></p>'
        (out/topic['filename']).write_text(page(topic['title'],topic['filename'],topic_html),encoding='utf-8')
    if plan.get('liberty_topic'):
        topic=json.loads(json.dumps(plan['liberty_topic']))
        content='<p class="eyebrow">专题与决议 · 自由女神像</p><h1>'+esc(topic['title'])+'</h1><p>'+esc(topic['intro'])+'</p><div class="policy">'+esc(topic['policy'])+'</div><p class="muted">资料核验：'+esc(topic['checked_date'])+'；实际日程、预约和藏品展位出发前复核。</p><h2>按行程快速查看</h2><div class="table-wrap"><table><thead><tr><th>对象</th><th>对应行程</th><th>实物类型</th><th>本次状态</th></tr></thead><tbody>'
        for item in topic['entries']:
            day=next(day for day in days if day['day']==item['day'])
            label,code,stop=stop_ref(day,item['place'],False,day['core'].index(item['place'])+1)
            item['day_href']=f'day-{day["day"]:02d}.html#'+stop
            item['slot']=day.get('visits',{}).get(item['place'],{}).get('time','时段待定')
            content+='<tr><td><a href="#liberty-'+esc(item['id'])+'">'+esc(item['name'])+'</a></td><td><a href="'+esc(item['day_href'])+'">D'+f'{day["day"]:02d}'+' · '+esc(places[item['place']]['name'])+'</a></td><td>'+esc(item['kind'])+'</td><td>'+esc(item['status'])+'</td></tr>'
        content+='</tbody></table></div><h2>逐处寻找与记录</h2>'
        for item in topic['entries']:
            content+='<section class="place-guide" id="liberty-'+esc(item['id'])+'"><p class="eyebrow">'+esc(item['status'])+'</p><h2>'+esc(item['name'])+'</h2><p><strong>类型：</strong>'+esc(item['kind'])+'</p><p>'+esc(item['about'])+'</p><div class="highlight-grid"><article><h3>怎么找、看什么</h3><p>'+esc(item['look'])+'</p></article><article><h3>时间与参观条件</h3><p>'+esc(item['time'])+'</p><p>'+esc(item['access'])+'</p></article></div><p class="muted">对应场馆／街区现有安排：'+esc(item['slot'])+'。候选和外借对象不据此视作已经排入。</p><div class="guide-actions"><a href="'+esc(item['day_href'])+'">查看对应日程</a>'+('<a target="_blank" rel="noopener" href="'+esc(item['navigation'])+'">地图查找 ↗</a>' if item['navigation'] else '')+'</div><div class="source-links">'+''.join('<a target="_blank" rel="noopener" href="'+esc(s['url'])+'">'+esc(s['title'])+' ↗</a>' for s in item['sources'])+'</div></section>'
        content+='<h2>与2027年出行有关的展览</h2>'
        for item in topic['exhibitions']:
            content+='<section class="place-guide"><h3>'+esc(item['title'])+'</h3><p><strong>'+esc(item['status'])+'</strong></p><p>'+esc(item['text'])+'</p><div class="source-links">'+''.join('<a target="_blank" rel="noopener" href="'+esc(s['url'])+'">'+esc(s['title'])+' ↗</a>' for s in item['sources'])+'</div></section>'
        content+='<h2>出发前逐项落实</h2><ul>'+''.join('<li>'+esc(item)+'</li>' for item in topic['todos'])+'</ul><details><summary>原文与核对口径</summary><p>'+esc(topic['reference_note'])+'</p><a target="_blank" rel="noopener" href="'+esc(topic['reference']['url'])+'">'+esc(topic['reference']['title'])+' ↗</a></details><p><a href="index.html">← 返回行程总览</a></p>'
        (out/topic['filename']).write_text(page(topic['title'],topic['filename'],content),encoding='utf-8')
    for name,title,description,template in PREPARATION_PAGES:
        (out/name).write_text(page(title,name,preparation[name]),encoding='utf-8')
    if plan.get('companion_review'):
        review_html,review_text=companion_content()
        review=plan['companion_review']
        (out/review['filename']).write_text(page(review['title'],review['filename'],review_html),encoding='utf-8')
        (out/review['text_filename']).write_text(review_text,encoding='utf-8')
    manifest=dict(page_version=3,output_mode='current',plan_version=plan['version'],data_id=data_id,build_id=build_id,generated_at=made,entry=str(live/'index.html'),days=[str(live/f'day-{d["day"]:02d}.html') for d in days])
    (out/'revision.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'plan.snapshot.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    # Generate a complete replacement before changing the fixed live directory.
    if previous.exists():shutil.rmtree(previous)
    if live.exists():live.rename(previous)
    try:
        out.rename(live)
    except Exception:
        if previous.exists() and not live.exists():previous.rename(live)
        raise
    out=live
    if previous.exists():shutil.rmtree(previous)
    (ROOT/'data/web-current.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    # Root aliases and the live directory keep the same URL across builds.
    relative=out.relative_to(ROOT).as_posix()+'/index.html'
    entry='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Cache-Control" content="no-cache"><meta http-equiv="refresh" content="0;url='+relative+'"><title>巴黎行程按日总览</title><body><h1>巴黎行程｜按日页面 v3</h1><p>行程'+plan_label+' · 数据 '+data_id+'</p><p><a href="'+relative+'">打开当前版本：按日总览</a></p></body></html>'
    for name in ('itinerary.html','map-review.html','map-template.html','index.html'):(ROOT/name).write_text(entry,encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))
    return manifest

if __name__=='__main__':build()
