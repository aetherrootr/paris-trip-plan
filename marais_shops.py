"""Render neighborhood shop lists and two progressively enhanced maps."""
import html,json,math
from urllib.parse import urlencode

def esc(s):return html.escape(str(s),quote=True)
DAYS={'Mo':'周一','Tu':'周二','We':'周三','Th':'周四','Fr':'周五','Sa':'周六','Su':'周日'}
def clock(t):return f'{t//60:02d}:{t%60:02d}'
def hours(s,day):
    v=s['hours'].get(day)
    return '资料未确认' if v is None else '未列营业／不覆盖此时段' if not v else '、'.join(clock(a)+'–'+clock(b) for a,b in v)
def covers(s,day,start=1065,end=1100):return any(a<=start and b>=end for a,b in s['hours'].get(day,[]) or [])
def nav_link(c):return 'https://www.google.com/maps/dir/?'+urlencode(dict(api=1,destination=f'{c[1]},{c[0]}',travelmode='walking'))
def svg_map(data,ids,route=False):
    lookup={s['id']:s for s in [data['start']]+data['shops']};pts=[lookup[k] for k in ids]
    legmap={q['a']+'__'+q['b']:q for q in data['legs']};legs=[legmap[a+'__'+b] for a,b in zip(ids,ids[1:])] if route else []
    raw=[q['coordinates'] for q in pts]+[c for q in legs for c in q['geometry']['coordinates']]
    def xy(c):return c[0]*73150,-c[1]*111200
    xyraw=[xy(c) for c in raw];xs=[c[0] for c in xyraw];ys=[c[1] for c in xyraw];cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
    scale=min(510/max(max(xs)-min(xs),130),300/max(max(ys)-min(ys),130))
    def project(c):x,y=xy(c);return 300+(x-cx)*scale,190+(y-cy)*scale
    out=['<title>'+('店铺步行串线' if route else '推荐地点分布')+'</title><desc>'+esc(data['start']['label']+'为'+data['start']['name'])+'；编号对应下方清单；点位可点击。路网与点位已包含在页面内。</desc>']
    for q in legs:
        poly=' '.join(','.join(f'{v:.2f}' for v in project(c)) for c in q['geometry']['coordinates'])
        out.append('<polyline points="'+poly+'" fill="none" stroke="#235f99" stroke-width="3" opacity=".85"/>')
    for q in pts:
        x,y=project(q['coordinates']);dx,dy=q.get('label_offset',[12,-10]);color=q.get('color','#546778');href='#shop-'+q['id'] if q['id']!='start' else '#shops-route'
        out.append(f'<a href="{href}" aria-label="{esc(q["label"]+" "+q["name"])}"><circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="{color}" stroke="white" stroke-width="2"/><text x="{x+dx:.2f}" y="{y+dy:.2f}" text-anchor="middle" fill="{color}" font-size="13" font-weight="700" paint-order="stroke" stroke="var(--paper)" stroke-width="4">{esc(q["label"])}</text><title>{esc(q["name"])}</title></a>')
    out.append('<text x="550" y="25" font-size="13" fill="var(--muted)">北 ↑</text>')
    return ''.join(out)
def route_info(data,order):
    legs={q['a']+'__'+q['b']:q for q in data['legs']};qs=[legs[a+'__'+b] for a,b in zip(order,order[1:])]
    return sum(q['distance_m'] for q in qs),sum(q['duration_min'] for q in qs)
def status(s,day,data):
    hs=s['hours'].get(day)
    if hs is None:return 'unknown'
    if any(a<=data['window_start'] and b>=data['window_end'] for a,b in hs):return 'open'
    if any(a<data['window_end'] and b>data['window_start'] for a,b in hs):return 'partial'
    return 'closed'
LABELS={'open':'常规时间覆盖全段','closed':'当前星期不覆盖此时段','unknown':'营业资料未确认','partial':'仅覆盖部分散步时段'}
def render_shop_page(day,data,js):
    n=f'{day:02d}';dayurl=f'day-{n}.html';anchor=data.get('return_anchor',f'stop-d{n}-08');back=dayurl+'#'+anchor
    guideurl=data.get('guide_href',f'day-{n}-guide.html');default=data['default_day'];allids=['start']+[s['id'] for s in data['shops']];byid={s['id']:s for s in [data['start']]+data['shops']}
    preset=data['orders'][0];ids=[k for k in preset['keys'] if k=='start' or status(byid[k],default,data)=='open'];dist,walk=route_info(data,ids);stopping=sum(byid[k]['stop_minutes'] for k in ids if k!='start');budget=data['window_end']-data['window_start']
    intro=data.get('intro','先按店铺类型和营业时间挑选，再看路线。这里的六家是可选择的停留点；原日程只有35分钟，建议进2–3家。')
    content='<p class="eyebrow">DAY '+n+' · 街巷与店铺</p><h1>'+esc(data['title'])+'</h1><p>'+esc(intro)+'</p><nav class="guide-actions"><a href="'+back+'">← 返回街巷散步卡片</a>'+('<a href="'+esc(guideurl)+'">本日景点介绍</a>' if guideurl else '')+'<a href="#shop-list">'+esc(data.get('list_title','店铺与市场清单'))+' ↓</a>'+('<a href="#market-lunch">'+esc(data['market_lunch'].get('link_label','集市午餐候选 ↓'))+'</a>' if data.get('market_lunch') else '')+'</nav>'
    content+='<div class="policy"><strong>当天窗口：'+esc(data['time_window'])+'（巴黎当地时间）</strong><p>'+esc(data['note'])+'</p><p>'+esc(data.get('market_note','红孩儿市场内部与街面店分开判断；市场火灾后恢复安排仍待核。'))+(' <a href="'+esc(data['market_source'])+'" target="_blank" rel="noopener">'+esc(data.get('market_link_label','市政府更新'))+' ↗</a>' if data.get('market_source') else '')+'</p></div>'
    if data.get('market_lunch'):
        lunch=data['market_lunch'];content+='<section class="place-guide" id="market-lunch"><h2>'+esc(lunch['title'])+'</h2><p>'+esc(lunch['intro'])+'</p>'
        for option in lunch['options']:
            content+='<article><h3>'+esc(option['title'])+'</h3><p>'+esc(option['description'])+'</p>'
            if option.get('steps'):content+='<div class="table-wrap"><table><thead><tr><th>候选时段</th><th>安排</th></tr></thead><tbody>'+''.join('<tr><td class="metric">'+esc(q['time'])+'</td><td>'+esc(q['activity'])+'</td></tr>' for q in option['steps'])+'</tbody></table></div>'
            content+='<p class="muted">'+esc(option['note'])+'</p><div class="source-links">'+''.join('<a target="_blank" rel="noopener" href="'+esc(q['url'])+'">'+esc(q['title'])+' ↗</a>' for q in option['sources'])+'</div></article>'
        content+='</section>'
    count=sum(status(s,default,data)=='open' for s in data['shops']);summary_note=data.get('summary_note','书店依据地图资料，其他依据官网。')
    summary=DAYS[default]+'：本页'+str(len(data['shops']))+'个地点中，'+str(count)+'个常规规则覆盖'+data['time_window']+'；'+summary_note
    content+='<section class="shops-toolbar" aria-label="营业筛选"><label for="shops-day">参观星期<select id="shops-day">'+''.join('<option value="'+k+'"'+(' selected' if k==default else '')+'>'+DAYS[k]+'</option>' for k in data.get('weekday_options',['We','Th','Fr','Sa','Su']))+'</select></label><label class="shops-check"><input type="checkbox" id="shops-open-only">仅看常规时间覆盖全段的地点</label><p id="shops-summary" role="status" aria-live="polite">'+esc(summary)+'</p></section><div class="shops-map-grid">'
    for kind,title,pointids,isroute in [('distribution',data.get('distribution_title','店铺与市场分布：先挑想看的'),allids,False),('route','推荐步行串线',ids,True)]:
        content+='<section class="shops-map-panel" id="shops-'+kind+'" aria-labelledby="shops-'+kind+'-heading"><h2 id="shops-'+kind+'-heading">'+title+'</h2>'
        if isroute:content+='<label class="shops-route-select" for="shops-route-preset">选择串线<select id="shops-route-preset">'+''.join('<option value="'+q['id']+'">'+esc(q['title'])+'</option>' for q in data['orders'])+'</select></label>'
        else:content+='<p class="shops-panel-intro">'+esc(data.get('distribution_intro','编号对应下方清单，颜色区分类型。点击点位查看信息；定期市场也列在图上，按营业时间判断。'))+'</p>'
        content+='<div class="shops-map-actions"><button type="button" data-map-zoom="'+kind+':1" aria-label="放大'+title+'">＋</button><button type="button" data-map-zoom="'+kind+':-1" aria-label="缩小'+title+'">−</button><button type="button" data-map-fit="'+kind+'">看全图</button><button type="button" data-map-mode="'+kind+'" disabled>底图加载中</button></div><div class="shops-map-frame"><div class="shops-street" id="shops-street-'+kind+'" aria-label="'+title+'街道地图"></div><svg class="shops-offline" id="shops-offline-'+kind+'" viewBox="0 0 600 380" role="img" aria-label="'+title+'坐标地图">'+svg_map(data,pointids,isroute)+'</svg></div><p class="map-status" id="shops-map-status-'+kind+'">坐标图可离线查看；鼠标滚轮缩放、左键拖动，正在加载IGN街道底图。</p>'
        if isroute:
            content+='<p class="shops-route-metric" id="shops-route-metric" role="status">约'+str(round(dist))+'米 · 纯步行约'+str(math.ceil(walk))+'分钟 · '+str(len(ids)-1)+'处建议短停另留约'+str(stopping)+'分钟</p><ol class="shops-route-order" id="shops-route-order">'+''.join('<li>'+('<a href="#shop-'+key+'">'+esc(byid[key]['label']+' '+byid[key]['name'])+'</a>' if key!='start' else esc(data['start']['label']+' '+data['start']['name']))+'</li>' for key in pointids)+'</ol><p class="muted" id="shops-route-note">'+esc(preset['note'])+'</p><div class="guide-actions" id="shops-route-nav"></div>'
        content+='</section>'
    content+='</div><section aria-labelledby="shop-list"><h2 id="shop-list">'+esc(data.get('list_title','推荐店铺与市场清单'))+'</h2><p class="muted">这是供选择的短名单；“覆盖”指常规规则覆盖整个散步时段，不代表当天已确认开门。未知营业不会自动加入串线。</p><div class="shops-card-grid">'
    for s in data['shops']:
        st=status(s,default,data)
        content+='<article class="shop-card" id="shop-'+s['id']+'" data-shop-id="'+s['id']+'" style="--shop-color:'+s['color']+'"><div class="shop-card-heading"><span class="shop-code">'+s['label']+'</span><div><span class="shop-type">'+esc(s['type'])+'</span><h3>'+esc(s['name'])+'</h3></div></div><p>'+esc(s['description'])+'</p><p class="shop-address">'+esc(s['address'])+'</p><p class="shop-coverage is-'+('open' if st=='open' else 'closed' if st=='closed' else 'unknown')+'" data-shop-coverage="'+s['id']+'">'+LABELS[st]+'</p><p data-shop-hours="'+s['id']+'">'+DAYS[default]+'：'+esc(hours(s,default))+'</p><p class="muted">建议短停约'+str(s['stop_minutes'])+'分钟 · '+esc(s['confidence'])+'</p><details><summary>每周营业时间</summary><dl class="shop-week">'+''.join('<dt>'+DAYS[k]+'</dt><dd>'+esc(hours(s,k))+'</dd>' for k in DAYS)+'</dl></details><div class="shop-actions"><button type="button" data-shop-locate="'+s['id']+'">在分布图定位</button><a class="map-directions" href="'+esc(nav_link(s['coordinates']))+'" target="_blank" rel="noopener">到这里去</a></div><div class="source-links">'+''.join('<a href="'+esc(q['url'])+'" target="_blank" rel="noopener">'+esc(q['title'])+' ↗</a>' for q in s['sources'])+'</div></article>'
    content+='</div><p id="shops-empty" class="policy" hidden>当前筛选没有地点；取消“仅看营业”可查看其他资料。</p></section><details><summary>地图、路线与营业资料来源</summary><p>资料核对日：'+esc(data['checked_date'])+'。'+esc(data.get('source_note','五家根据商家官网，书店按OpenStreetMap营业标签；2027出行前复核。店铺坐标来自OSM及IGN地址匹配，不保证为精确店门。'))+'</p><p>'+esc(data.get('route_source_note','步行串线使用IGN BD TOPO／Valhalla，相邻巧克力店—书店短段另经OSM／FOSSGIS复核。纯步行时长不含试香、排队、挑书或购物；全部六店并非35分钟内逐店细逛的承诺。'))+'</p><p>商铺与部分短段数据 © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>；步行服务 <a href="https://routing.openstreetmap.de/">FOSSGIS</a>；街道底图 © IGN – Plan IGN。</p></details><noscript><p class="policy">当前静态清单采用'+DAYS[default]+'，每周时间仍可展开阅读。星期筛选和地图缩放需要JavaScript。</p></noscript><p><a href="'+back+'">← 返回D'+n+'街巷散步</a></p>'
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    return content,'<script id="shops-data" type="application/json">'+payload+'</script><script>'+js+'</script>'
