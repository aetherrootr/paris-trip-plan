from pathlib import Path
import json, math, sys
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent

def main():
    plan=json.loads((ROOT/'data/plan.json').read_text(encoding='utf-8'))
    routes=json.loads((ROOT/'data/routes.json').read_text(encoding='utf-8'))
    places=plan['places']; days=plan['days']; weekday=['周一','周二','周三','周四','周五','周六','周日']
    def names(keys):return '、'.join(places[k]['name'] for k in keys) or '按航班安排'
    def km(m):return f'{m/1000:.2f}公里'
    def pair(a,b):return routes.get(a+'__'+b)
    def desc(a,b):
        r=pair(a,b)
        if not r or r.get('status')!='ok':return names([a,b]).replace('、',' → ',1)+'：路线／入口待确认'
        return f'{places[a]["name"]} → {places[b]["name"]}：步行路网约{km(r["distance_m"])}，模型约{math.ceil(r["duration_min"]/5)*5}分钟'
    def directions(a,b):
        x,y=places[a]['coordinates'],places[b]['coordinates']
        if not x or not y:return None
        return 'https://www.google.com/maps/dir/?'+urlencode(dict(api=1,origin=f'{x[1]},{x[0]}',destination=f'{y[1]},{y[0]}',travelmode='walking'))
    def render_map():
        from build_daily import build
        build()
    if '--map-only' in sys.argv:
        render_map();print('Updated map entry points only; text drafts left untouched.');return

    intro='''Travel to Paris 2027｜15天行程草稿 v2
恢复原稿旅行密度｜供review与人工修改
更新日期：2026年11月8日

时间
2027年2月或3月出发，日期待定。总旅程15天，包含北京往返巴黎；先按Day1抵达巴黎、Day14离开巴黎、Day15抵达北京计算，Day2–13为12个完整游览日。具体航班确定后调整跨日边界。

规划原则
以你原来Google Doc和KMZ中的旅行密度为基准，尽可能保留已有参观项目与参观时长，恢复完整的主题日。
不再把一天两处、固定半天休息或强制二选一当作默认。原稿“可选”身份保留，但先在路线中给出位置，由你根据兴趣决定是否进入。
先用开放窗口调整顺序；若确有冲突，优先在相邻地区的其他一天平移同一个项目。附近新增建议单独注明，不取代原稿项目。
本次明确取消的只有圣米歇尔山及其餐饮点。天文台入内、工程关闭场馆等实际限制单独说明。

当前阶段
先确认景点与分日，不锁定具体入场小时、馆内路线、票种、餐厅与交通班次。以下总耗时是按原稿参观预算加午餐、转场的估算，不表示每个真实日期都已验证可行。
没有把长距离都按步行处理：地铁、公交、园内交通均可用于衔接。地图上的步行路网用于判断相对位置，不等于要求全天走完。

'''
    text=[intro,'日程总览\n']
    for d in days:text.append(f'Day {d["day"]:02d}｜{d["title"]}\n  拟安排：{names(d["core"])}\n')
    text.append('\n逐日草稿\n'+'='*36+'\n')
    for d in days:
        text.append(f'\nParis Trip Day {d["day"]:02d} — {d["title"]}\n\n{d["intro"]}\n主题：{d["theme"]}\n时间：日期与入场时段待定\n耗时：{d["duration"]}\n')
        if d['core']:
            text.append('拟安排景点：\n'+''.join('  □ '+places[k]['name']+'\n' for k in d['core']))
            text.append('位置与交通：\n')
            for a,b in zip(d['core'],d['core'][1:]):text.append('  '+desc(a,b)+'\n')
            segments=[pair(a,b) for a,b in zip(d['core'],d['core'][1:])]
            if segments and all(r and r.get('status')=='ok' for r in segments):
                text.append('  上述点对点路网合计约'+km(sum(r['distance_m'] for r in segments))+'；不含酒店往返、馆内步行与现场入口差异，也不是必须全程步行。\n')
            if len(d['core'])==1:text.append('  单一大场馆，按原稿馆内路线安排全天，不以场馆数量判断密度。\n')
        if d['optional']:text.append('原稿可选／顺路延伸：'+names(d['optional'])+'。先保留位置，按你的兴趣review。\n')
        if d['alternative']:text.append('附近建议：'+names(d['alternative'])+'。不是必须替换原稿项目。\n')
        if d['avoid_weekdays']:text.append('排期条件：本组合目前避开'+'、'.join(weekday[n] for n in d['avoid_weekdays'])+'；日期确定后再核对全部开放窗口。\n')
        text.append('Review：'+d['review']+'\n')
        if d['core']:text.append('午餐／晚餐：TODO，按原路线与最后预约选择。\n票务：下一阶段核实，当前不预订。\n')
        text.append('我的修改：____________________________\n')
    text.append('''
原稿保留与位置调整说明
原Day1的圣母院、圣礼拜堂、古监狱、中世纪馆、居里和先贤祠全部恢复Day2，不再要求中世纪馆与自然历史二选一。
原Day2卢浮宫三翼目标恢复Day3，优先考虑夜场承载原参观时长。
原Day3的玛黑区、毕加索、狩猎自然和工艺均恢复Day4；皮诺保留本日夜场可能，同时在Day13有确定落位，择合适的日期完成一次。
原Day4的橘园、装饰艺术、海军府、大小皇宫、香榭丽舍和凯旋门恢复Day5；大皇宫依原稿先按外观。
原Day5的现代艺术、东京宫、迪奥、平台和游船恢复Day6；国家海军、人类、建筑馆、水族馆和自由女神集中在Day12相邻区域，均未因“密度”删除。
原Day6的奥赛、罗丹、荣军院和铁塔恢复Day7。罗丹提前是为白天花园；下水道在Day12同一区域参观，内容不丢。
凡尔赛恢复主宫与大小特里亚农；蒙马特恢复浪漫生活馆与红磨坊；科学城、爱乐厅、自然历史、植物园、地下墓穴和邮政馆均有分日位置。
天文台恢复为路线上可经过的外观点；入内仍需实际访问安排。Datadog保留待确认到访，不猜测私人访问目的。

需要review的事项
1. 是否认可这些原稿项目的分日位置？可直接在每天下面改，不需要先接受任何强制替换。
2. 原本标注“可选”的项目，现在是否希望作为确定参观？它们已恢复到完整路线里。
3. Day7是全程最饱和的组合之一。后续先核对罗丹白天窗口、荣军院闭馆与铁塔预约；如确有冲突，优先与Day12同一区域调动，不先删项目。
4. Day13的歌剧院和拱廊是新增近邻建议，原稿项目优先；是否加入由你决定。
5. 游船仍保留，需确认普通观光／晚餐航程与实际码头。原坐标错误，不据此推算登船距离。

下一阶段
你review后再按真实日期处理闭馆日、实际预约和公交／地铁；继续沿用原稿各景点的细节与写作方式逐日展开。Google Doc与原地图未修改。
''')
    (ROOT/'01-itinerary-draft.txt').write_text(''.join(text),encoding='utf-8')

    review=['巴黎15天｜原稿项目保留检查表 v2\n\n在每项后写“保留／按原稿可选／调整到第X天”。不要求先做二选一。\n\n']
    for d in days:
        if not d['core']:continue
        review.append(f'【Day {d["day"]:02d} {d["title"]}】\n')
        for field,label in [('core','拟安排'),('optional','原稿可选／待确认'),('alternative','附近建议')]:
            for key in d[field]:
                p=places[key];review.append(f'□ {p["name"]}｜{label}｜{p.get("note","")}\n  我的意见：\n')
        review.append('\n')
    review.append('【荣军院内部】\n□ 军事博物馆与拿破仑之墓\n□ 浮雕模型博物馆\n□ 解放勋章博物馆〔沿用原稿可选〕\n\n【中心区顺路】\n□ Forum des Halles〔原文购物候选，近皮诺〕\n\n【开放条件待核实】\n□ 发现宫〔按2027实际重开公告核实，不因旅行密度删除，也不默认届时能参观〕\n\n【明确取消】\n圣米歇尔山、La Mère Poulard。\n')
    (ROOT/'02-place-review.txt').write_text(''.join(review),encoding='utf-8')

    distance=['巴黎15天｜距离核对 v2\n\n法国IGN步行路网；不是全程步行指令。直线／路网分列，场馆入口、等灯、安检和馆内步数另计。\n本版拟核对'+str(len(plan['route_pairs']))+'段连接，历史缓存'+str(len(routes))+'段；只把状态ok的结果作为已查询。\n科学城至爱乐厅算法有园区绕行，凡尔赛园路需再核对入口。\n\n']
    for a,b in plan['route_pairs']:
        r=pair(a,b);distance.append(desc(a,b)+'\n')
        if r:distance.append('  坐标直线约'+km(r['straight_m'])+'；查询状态 '+r['status']+'\n')
        url=directions(a,b)
        if url:distance.append('  人工导航核对：'+url+'\n')
        distance.append('\n')
    distance.append('游船仍在Day6，因码头未定不画假位置，也不计算到未知码头的距离。\n')
    (ROOT/'03-distance-review.txt').write_text(''.join(distance),encoding='utf-8')

    sources=['巴黎15天｜来源与实际排期条件 v2\n核验日期2026-11-08。日期未定，当前不声称某一天已通过全部预约校验。\n\n']
    for s in plan['sources']:sources.append(s['title']+'\n'+s['url']+'\n\n')
    sources.append('''
本版明确的排期条件
卢浮宫完整三翼优先周三／周五夜场；不缩减原定参观预算来适应普通闭馆日。
居里常规周三至周六下午开放，西岱岛与拉丁区整天组合须围绕此安排。
东京宫常规中午开门，迪奥周二闭馆；不能把两个馆都写成上午同一时段。
罗丹冬季花园随天黑提前关闭，因此原左岸线路中提前参观罗丹；这是顺序修正，不是删馆。
皮诺若接在玛黑／工艺后面，需合适夜场；否则仍在Day13保留完整参观位置。
凡尔赛特里亚农从中午开放；大小特里亚农均恢复，园区交通另核对。
地下墓穴目前常规可参观至晚间、周一闭馆；邮政馆周二闭馆。自然历史这里指进化大展馆；不能把工程关闭的古生物馆算作可入内。
巴黎天文台普通公众入内仍受开放活动限制，保留外观或实际获邀访问的可能；不假定有已确认预约。
地图里的步行线是IGN模型，不保证景区门、园路和临时道路在2027年全部开放。酒店往返、馆内步行未计入。
游船、演出、特展和个人拜访尚未预约。相同馆跨两日标注时，只安排去一次，除非用户明确要求重访。
新增歌剧院与拱廊独立标注，未用来强制替换原稿景点。
''')
    (ROOT/'04-sources-and-limits.txt').write_text(''.join(sources),encoding='utf-8')

    K='http://www.opengis.net/kml/2.2';ET.register_namespace('',K)
    def el(parent,tag,text=None):
        e=ET.SubElement(parent,'{'+K+'}'+tag)
        if text is not None:e.text=str(text)
        return e
    root=ET.Element('{'+K+'}kml');doc=el(root,'Document');el(doc,'name','巴黎15天 v2｜原稿旅行密度')
    for d in days:
        if not d['core']:continue
        f=el(doc,'Folder');el(f,'name',f'Day {d["day"]:02d} {d["title"]}')
        for key in d['core']+d['optional']:
            p=places[key]
            if not p['coordinates']:continue
            m=el(f,'Placemark');el(m,'name',p['name']);el(m,'description',d['review']+'；'+p.get('note',''))
            el(el(m,'Point'),'coordinates',','.join(map(str,p['coordinates']))+',0')
        for a,b in zip(d['core'],d['core'][1:]):
            r=pair(a,b)
            if not r or r.get('status')!='ok':continue
            m=el(f,'Placemark');el(m,'name',desc(a,b));line=el(m,'LineString');el(line,'tessellate','1');el(line,'coordinates',' '.join(','.join(map(str,c))+',0' for c in r['geometry']['coordinates']))
    ET.ElementTree(root).write(ROOT/'paris-15-days-review.kml',encoding='utf-8',xml_declaration=True)
    (ROOT/'README.txt').write_text('''巴黎15天｜行程v2，按日网页v3

后续讨论以按日网页显示的内容为准。打开itinerary.html进入当前版本总览，每个Day都有独立网页、景点序号、当天地图与距离。
每页显示数据标识；data/web-current.json记录最新页面入口。固定入口为web/current/index.html，构建后刷新同一页面并以数据标识确认版本。

01-itinerary-draft.txt：原稿景点优先的15天总览与逐日草稿。
02-place-review.txt：按天核对保留项目，不要求强制二选一。
itinerary.html／map-review.html／index.html／map-template.html：均进入最新按日总览。web下的版本目录保留可追溯页面。
03-distance-review.txt：本版各段距离和人工导航链接。
04-sources-and-limits.txt：官方来源与真实的排期条件。
paris-15-days-review.kml：可手动导入新的My Maps地图。

旧版及已有人工修改已保存在archive/v1-before-density-*，原Google Doc和KMZ未改动。
本版按照用户要求提高密度，恢复原有组合；只根据开放窗口、路线和预约处理顺序与邻近挪动。
歌剧院、拱廊为单独标注的新增近邻建议，原有项目优先。
确认后再细排小时、交通、票务、餐厅和馆内路线。

data/plan.json为后续讨论的唯一日程数据源；data/routes.json保存路网查询结果。网页由这两份数据一起生成，文字文件作为派生阅读稿。
prepare_plan.py调用density_v2.py生成方案；render_review.py生成地图和文字。
人工改过txt后不要直接重跑完整生成。仅刷新地图可用：python render_review.py --map-only。
仅刷新按日网页也可用：python build_daily.py，不会改动txt。prepare_plan.py用于从初始定义重建，不用于覆盖已经review的plan.json修改。
确认人工意见后先统一写入plan.json，再重生成网页；网页、地图不独立维护另一份行程。
''',encoding='utf-8')
    render_map();print('Rendered original-density v2 review files.')

if __name__=='__main__':main()
