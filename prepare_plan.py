from pathlib import Path
import json, math, shutil, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
SOURCE = Path('/home/aether/Downloads/巴黎行程草稿.kmz')
ns = {'k': 'http://www.opengis.net/kml/2.2'}
with zipfile.ZipFile(SOURCE) as z:
    tree = ET.fromstring(z.read('doc.kml'))
raw = []
for folder in tree.findall('.//k:Folder', ns):
    for p in folder.findall('k:Placemark', ns):
        coord = p.findtext('k:Point/k:coordinates', '', ns).strip()
        raw.append({'layer': folder.findtext('k:name', '', ns), 'name': p.findtext('k:name', '', ns), 'description': p.findtext('k:description', '', ns), 'coordinates': [float(v) for v in coord.split(',')][:2]})
(DATA / 'original-markers.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
shutil.copy2(SOURCE, DATA / SOURCE.name)

mapping = [
('pantheon','Panthéon 先贤祠','先贤祠'),('cluny','Musée de Cluny 国立中世纪博物馆','国立中世纪博物馆'),
('flore','Café de Flore 圣日耳曼咖啡馆','花神咖啡馆'),('notredame','Notre-Dame Cathedral 巴黎圣母院','巴黎圣母院'),
('sainte','Sainte-Chapelle 圣徒礼拜堂','圣礼拜堂'),('conciergerie','Conciergerie 巴黎古监狱','巴黎古监狱'),
('louvre','Louvre Museum 卢浮宫','卢浮宫'),('royal','Palais Royal 巴黎皇家宫殿','巴黎皇家宫殿'),
('pinault','Bourse de Commerce 皮诺私人美术馆','皮诺美术馆'),('arts','Musée des Arts et Métiers 国立工艺博物馆','巴黎工艺博物馆'),
('hunt','狩猎自然博物馆','狩猎自然博物馆'),('carnavalet','卡纳瓦莱博物馆','卡纳瓦莱博物馆'),
('bastille','巴士底广场','巴士底广场'),('picasso','毕加索博物馆','毕加索博物馆'),('vosges','孚日广场','孚日广场'),
('decorative','Musée des Arts Décoratifs 装饰艺术博物馆','装饰艺术博物馆'),('arc','Arc de Triomphe 凯旋门','凯旋门'),
('champs','Champs-Élysées 香榭丽舍大街','香榭丽舍大街'),('grandpalais','Grand Palais 大皇宫','大皇宫'),
('orangerie','橘园美术馆','橘园美术馆'),('concorde','协和广场','协和广场'),('marinehotel','海军府','海军府'),
('dior','Dior Gallery 迪奥艺廊','迪奥艺廊'),('cruise','Seine Cruise 塞纳河晚餐游船','塞纳河游船〔码头未定〕'),
('tokyo','Palais de Tokyo 东京宫','东京宫'),('modern','Musée d’Art Moderne de Paris 现代艺术博物馆','巴黎现代艺术博物馆'),
('homme','Musée de l’Homme 人类博物馆','人类博物馆'),('architecture','建筑与遗产之城','建筑与遗产之城'),
('trocadero','Esplanade Joseph-Wresinski','夏乐宫观景平台'),('aquarium','Aquarium de Paris','巴黎水族馆'),
('liberty','Statue de la Liberté 巴黎自由女神','巴黎自由女神像'),('orsay','Musée d’Orsay 奥赛博物馆','奥赛博物馆'),
('rodin','Musée Rodin 罗丹美术馆','罗丹美术馆'),('invalides','军事博物馆','荣军院／军事博物馆'),
('sewer','巴黎下水道博物馆','巴黎下水道博物馆'),('eiffel','Eiffel Tower 埃菲尔铁塔','埃菲尔铁塔'),
('versailles','Palace of Versailles 凡尔赛宫','凡尔赛宫'),('venise','La Petite Venise 午餐','La Petite Venise〔餐厅待选〕'),
('grandtrianon','Grand Trianon 大特里亚农宫','大特里亚农宫'),('petittrianon','Petit Trianon 小特里亚农宫','小特里亚农宫'),
('datadog','Datadog','Datadog〔个人到访点待确认〕'),('sacre','Sacré-Cœur 圣心堂','圣心堂'),
('tertre','Place du Tertre 艺术家广场','艺术家广场'),('moulin','Moulin Rouge 红磨坊','红磨坊〔外观〕'),
('philharmonie','巴黎爱乐厅','巴黎爱乐厅'),('science','科学与工业城','科学与工业城'),
('romantic','浪漫生活博物馆','浪漫生活博物馆'),('catacombs','Catacombes de Paris 地下墓穴','巴黎地下墓穴'),
('natural','Muséum National d’Histoire Naturelle 自然历史博物馆','自然历史博物馆／进化大展馆'),
('plants','Lunch Jardin des Plantes 花园午餐','植物园'),('post','法国邮政博物馆','法国邮政博物馆'),
('observatory','巴黎天文台','巴黎天文台'),('msm','Mont Saint-Michel 圣米歇尔山','圣米歇尔山'),
('poulard','La Mère Poulard 午餐','La Mère Poulard〔本次取消〕')]
places = {}
for key, old, name in mapping:
    m = next(m for m in raw if m['name'] == old)
    places[key] = dict(id=key, name=name, coordinates=m['coordinates'], coordinate_source='用户原始KMZ；地点标记，不保证是入口', original_name=old, status='候选', day=None, note='', source_url='')
places['petittrianon'].update(coordinates=[2.109712,48.815647], original_coordinates=places['petittrianon']['coordinates'], coordinate_source='凡尔赛旅游目的地网站GPS；原KMZ偏移约0.6公里，已在派生稿修正', source_url='https://en.versailles-summergames.com/historic-site-and-monument/the-petit-trianon.html')
places['curie'] = dict(id='curie',name='居里博物馆',coordinates=[2.34479,48.84424],coordinate_source='OpenStreetMap node 11259580512（经Mapcarta核对）；地点中心',source_url='https://www.openstreetmap.org/node/11259580512',status='候选',day=None,note='参观入口及开放时间以馆方为准')
places['petitpalais'] = dict(id='petitpalais',name='小皇宫',coordinates=[2.31454,48.86603],coordinate_source='OpenStreetMap/GeoNames（经Mapcarta核对）；建筑位置',source_url='https://mapcarta.com/26952168',status='候选',day=None,note='')
places['maritime'] = dict(id='maritime',name='国家海军博物馆',coordinates=[2.28734,48.86182],coordinate_source='OpenStreetMap node 1296754169（经Mapcarta核对）；地点位置',source_url='https://www.openstreetmap.org/node/1296754169',status='候选',day=None,note='与海军府是两个不同地点')

def day(n,title,core,optional,alternative,theme,duration,intro,review,avoid=()):
    return dict(day=n,title=title,core=core,optional=optional,alternative=alternative,theme=theme,duration=duration,intro=intro,review=review,avoid_weekdays=list(avoid))

days = [
day(1,'北京 → 巴黎',[],[],[],'往返交通','全天留给飞行、入境及入住','这一天先完成长途移动。抵达后在酒店附近吃饭和散步，不预订必须准时入场的景点。','按当天抵达巴黎的航班假设；若次日抵达，需要整体调整。'),
day(2,'西岱岛：巴黎的起点',['sainte','conciergerie','notredame'],[],[],'历史／建筑','参观约3–4小时，另留午餐、步行与排队','我们先从西岱岛开始。圣礼拜堂和古监狱放在同一段，之后前往巴黎圣母院；下午后段保留休息。','确认三处是否全部保留；不叠加拉丁区博物馆。'),
day(3,'卢浮宫',['louvre'],['royal'],[],'艺术','展厅约5–6小时；连同午餐和休息留出全天','这一天主要游览卢浮宫。先保留你原先的三翼研究，但把每翼分为必看和有余力再看，避免把全天写成连续8小时以上的参观。','皇家宫殿只在仍有体力时散步，也可直接取消。',[1]),
day(4,'拉维莱特：科学与探索',['science'],['philharmonie'],[],'科学／音乐建筑','科学城约3–4小时，爱乐厅可选约1小时','我们把科学与工业城单独留出半天以上。爱乐厅位于同一区域，可以按实际展览或参观开放情况补充，不与蒙马特合并。','爱乐厅先按建筑外观／可用展览候选；音乐会不自动计入。',[0]),
day(5,'拉丁区：科学家与自然历史',['pantheon','curie','natural'],['plants'],['cluny'],'历史／科学／自然','先贤祠约1小时、居里约45分钟、进化大展馆约2–2.5小时','这一天从先贤祠和居里博物馆了解人物与科学史，再前往植物园区域参观进化大展馆。国立中世纪博物馆保留为替换方案，不在这一天额外叠加。','R1：默认自然历史；若更想看中世纪艺术，用Cluny替换进化大展馆。居里按下午开放安排，具体顺序下阶段确认。',[0,1,6]),
day(6,'奥赛与罗丹',['orsay','rodin'],[],[],'艺术','奥赛约3–4小时，罗丹约1.5小时','我们给奥赛留足半天，下午再参观罗丹。花园放在白天，不再把荣军院、下水道和铁塔一起放进这一天。','如果奥赛想深度看，罗丹改为可选；不为了赶罗丹提前结束奥赛。',[0]),
day(7,'玛黑区：巴黎城市史',['bastille','vosges','carnavalet'],['picasso'],['hunt'],'历史／艺术','广场散步约45分钟，卡纳瓦莱约2小时；选一个小馆约1.5小时','这一天主要留给玛黑区。从巴士底广场和孚日广场慢慢进入街区，卡纳瓦莱是重点。毕加索和狩猎自然只选择一个追加。','R2：毕加索／狩猎自然／都不加，三选一；不把工艺和皮诺接在后面。',[0]),
day(8,'凡尔赛：宫廷与庄园',['versailles','grandtrianon'],['petittrianon'],[],'历史／建筑','酒店出发至返回约9–11小时的规划预算','这一天完整留给凡尔赛。上午主宫，午餐和园区移动之后参观大特里亚农宫；小特里亚农宫按体力和开放情况决定。','默认不要求大小特里亚农全部完成；冬季园区移动、入口及小火车运营下一阶段核对。',[0]),
day(9,'工艺与当代艺术',['arts','pinault'],[],[],'科学技术／艺术','工艺约2.5–3小时，皮诺约1.5–2小时','我们将工艺博物馆和皮诺单独安排一天。两馆之间留出午餐和步行，不再接在玛黑区后面赶场。','皮诺具体展览尚未定；若兴趣不足，下午留空。',[0,1]),
day(10,'荣军院与城市工程',['invalides'],['sewer'],[],'历史／工程科学','荣军院约3–4小时；下水道可选约1小时','这一天主要游览荣军院军事博物馆及拿破仑之墓。浮雕模型与解放勋章按兴趣选看；下水道博物馆作为下午候选，也可直接休息。','保留半天可取消内容；下水道是否开放以最终参观日为准。'),
day(11,'蒙马特与半天机动',['sacre','tertre','moulin'],['romantic'],[],'街区／艺术史','街区约2.5–3.5小时，下午原则上留空','我们用一个轻松的上午逛蒙马特，参观圣心堂、艺术家广场，走到红磨坊看外观。下午留作休息、天气调整或补一个遗漏项目。','这是机动空间，不再默认加歌剧院、地下墓穴或跨城科学馆；浪漫生活博物馆只在有余力时加入。'),
day(12,'装饰艺术、橘园与城市轴线',['decorative','orangerie','concorde'],['arc'],['marinehotel','petitpalais','grandpalais'],'艺术／建筑','两馆合计约3.5–4小时，凯旋门另留约1小时及排队','从装饰艺术博物馆往西穿过杜乐丽花园，前往橘园，再到协和广场。凯旋门可以留作傍晚可选项目，较长的一段用公共交通衔接。','R3：装饰艺术或海军府二选一；大小皇宫看展须替换一个馆，不全部追加。',[0,1]),
day(13,'现代艺术与埃菲尔铁塔',['modern','trocadero','eiffel'],[],['dior','tokyo','maritime'],'艺术／城市景观','现代艺术约2小时，平台约30分钟，铁塔约2–3小时','我们先参观一个现代艺术或时装主题场馆，再前往夏乐宫观景平台，最后按预约登铁塔。中间保留午餐、步行及休息。','R4：现代艺术／迪奥／东京宫／海军博物馆先选一个；不默认四个馆连看。游船另作替换晚间项目，不叠加在登塔之后。',[0]),
day(14,'巴黎 → 北京',[],[],[],'往返交通','离境日','这一天收拾行李、前往机场并离开巴黎。先不安排必须入场的博物馆。','航班、机场与酒店未定，市内到机场时间下一阶段补。'),
day(15,'抵达北京',[],[],[],'往返交通','抵达与休息','完成返程，回家休息。','若航班跨日方式不同，调整日程边界。')]

# 凡尔赛之后先安排轻松街区日；不假定某个真实出发日期。
days[8], days[9], days[10] = days[10], days[8], days[9]
for n,d in enumerate(days,1): d['day']=n

for d in days:
    for field,status in [('core','建议主线'),('optional','当日可选'),('alternative','替换候选')]:
        for key in d[field]:
            places[key].update(status=status,day=d['day'])
for key,reason in {
    'msm':'用户明确本次不去圣米歇尔山。','poulard':'随圣米歇尔山取消。',
    'observatory':'不作为常规入内项目；公众开放活动另核实。',
    'catacombs':'暂不占主线；若列为必去，替换半天，不直接追加。',
    'post':'暂留待选池，不为填满日程额外跨区。','datadog':'个人到访目的尚未确认，不自动纳入。',
    'cruise':'原KMZ坐标误与人类博物馆重合。未定码头，不在派生地图中画假位置。',
    'liberty':'原稿候选；暂不为它单独绕行。','aquarium':'原文优先级低，暂不排入。',
    'homme':'保留为夏乐宫替换候选。','architecture':'保留为夏乐宫替换候选。',
    'flore':'餐饮候选，未锁定。','venise':'凡尔赛餐饮候选，未锁定。','champs':'凯旋门周边按体力散步，不要求全程步行。'
}.items():
    places[key]['note']=reason
    if key in ('msm','poulard'): places[key]['status']='本次取消'
    elif key in ('flore','venise'): places[key]['status']='餐饮候选'
    else: places[key]['status']='待选池'
places['cruise']['coordinates']=None
places['cruise']['coordinate_source']='原点位有冲突；本稿不沿用'

sources = [
('Google Doc（原文风格和现有研究）','https://docs.google.com/document/d/1hr9SfHkTNf0C3pzJcuCzOzFhn72AtTBt7MxH8j8GXWw/edit'),
('IGN步行路线服务说明','https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/calcul-itineraire/'),
('卢浮宫开放时间','https://www.louvre.fr/en/visit/hours-admission/tickets-and-prices'),
('奥赛开放时间','https://www.musee-orsay.fr/fr/visite'),
('橘园开放时间','https://www.musee-orangerie.fr/fr/visite/acces-horaires-tarifs'),
('居里博物馆访客规则','https://curiotheque.musee.curie.fr/s/fr/page/reglement-interieur'),
('自然历史进化大展馆／工程提示','https://www.mnhn.fr/fr/grande-galerie-de-l-evolution'),
('工艺博物馆开放时间','https://www.arts-et-metiers.net/musee/horaires-et-acces'),
('皮诺开放时间','https://www.pinaultcollection.com/fr/boursedecommerce/infos-pratiques'),
('科学城访客问答','https://messervices.cite-sciences.fr/faq'),
('现代艺术博物馆开放时间','https://www.mam.paris.fr/node/20'),
('装饰艺术博物馆访客信息','https://madparis.fr/Opening-hours-and-admission-fees-1534'),
('荣军院开放时间','https://www.musee-armee.fr/votre-visite/horaires-et-tarifs.html'),
('凡尔赛访客指南','https://en.chateauversailles.fr/plan-your-visit'),
('凡尔赛园区移动与Trianon入口','https://www.chateauversailles.fr/preparer-ma-visite/faq'),
('小特里亚农GPS核对','https://en.versailles-summergames.com/historic-site-and-monument/the-petit-trianon.html'),
('天文台公众访问限制','https://observatoiredeparis.psl.eu/-visites-des-sites-a-paris-318-.html'),
('下水道博物馆','https://musee-egouts.paris.fr/')]

from density_v2 import make_days
days=make_days(places,day)
sources.extend([
('罗丹开放与冬季花园','https://www.musee-rodin.fr/preparer-sa-visite/informations-pratiques'),
('东京宫开放时间','https://palaisdetokyo.com/horaires-acces/'),
('迪奥开放时间','https://www.galeriedior.com/informations-pratiques'),
('地下墓穴开放时间','https://www.catacombes.paris.fr/visiter/informations-pratiques'),
('加尼叶歌剧院（新增近邻建议）','https://www.operadeparis.fr/visites/palais-garnier')])
pairs=set()
def addseq(seq):
    for a,b in zip(seq,seq[1:]):
        if places[a]['coordinates'] and places[b]['coordinates']: pairs.add((a,b))
for d in days:
    addseq(d['core'])
for seq in [
 ['louvre','royal'],['science','philharmonie'],['cluny','pantheon','curie'],
 ['curie','natural','plants'],['carnavalet','picasso','hunt'],['versailles','grandtrianon','petittrianon'],
 ['petittrianon','versailles'],['invalides','sewer'],['moulin','romantic'],
 ['orangerie','marinehotel','petitpalais','grandpalais','arc'],['concorde','arc'],
 ['modern','dior'],['dior','trocadero'],['tokyo','trocadero'],['maritime','trocadero'],
 ['sacre','science'],['natural','science'],['louvre','versailles'],['natural','catacombs']]:
    addseq(seq)
plan={'version':'v2-original-density','checked_date':'2026-11-08','departure_window':'2027-02 or 2027-03; exact dates undecided',
 'constraints':['总15天含北京往返巴黎','圣米歇尔山取消','以原稿旅行密度为准，尽量保留全部原有安排','不强制二选一，不默认保留半天空白；优先调整顺序和邻近挪动','只提供本地草稿，不写回Google Doc','先审景点与分日；不细排小时、不购买通票'],
 'boundary_assumption':'D1抵达巴黎、D14离开巴黎、D15抵达北京，D2–D13为12个完整游览日；须按实际航班复核。',
 'days':days,'places':places,'route_pairs':[list(p) for p in sorted(pairs)],'sources':[{'title':t,'url':u} for t,u in sources]}
(DATA/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared:',len(days),'days;',len(places),'places;',len(pairs),'walking-route pairs')
