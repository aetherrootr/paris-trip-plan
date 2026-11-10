"""Read only public IGN routing data for the review draft; no accounts or keys."""
from pathlib import Path
import json, math, time, urllib.request, urllib.parse, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

ROOT=Path(__file__).resolve().parent
plan=json.loads((ROOT/'data/plan.json').read_text())
out=ROOT/'data/routes.json'
cache=json.loads(out.read_text()) if out.exists() else {}
rate_lock=Lock()
next_request=0.0

if '--check-basemap' in sys.argv:
    for name,lon,lat in [('paris',2.3376,48.8606),('versailles',2.1204,48.8049)]:
        zoom=14; scale=2**zoom
        x=int((lon+180)/360*scale)
        y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*scale)
        query=dict(SERVICE='WMTS',REQUEST='GetTile',VERSION='1.0.0',LAYER='GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',STYLE='normal',FORMAT='image/png',TILEMATRIXSET='PM',TILEMATRIX=zoom,TILEROW=y,TILECOL=x)
        url='https://data.geopf.fr/wmts?'+urllib.parse.urlencode(query)
        request=urllib.request.Request(url,headers={'User-Agent':'ParisTripPersonalReview/1.0'})
        with urllib.request.urlopen(request,timeout=25) as response:
            content=response.read();content_type=response.headers.get('Content-Type','')
            if response.status!=200 or not content.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Unexpected map response: '+str(response.status)+' '+content_type)
            path=ROOT/'data'/('ign-basemap-check-'+name+'.png');path.write_bytes(content)
            print(name,response.status,content_type,len(content),'bytes',path,flush=True)
    raise SystemExit(0)

def haversine(a,b):
    lon1,lat1,lon2,lat2=map(math.radians, a+b)
    return 6371008.8*2*math.asin(math.sqrt(math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2))

def fetch(pair):
    global next_request
    a,b=pair; key=a+'__'+b
    if key in cache and cache[key].get('status')=='ok': return key,cache[key]
    start,end=[plan['places'][k]['coordinates'] for k in pair]
    base=dict(a=a,b=b,straight_m=round(haversine(start,end)),checked_date=plan['checked_date'])
    query=dict(resource='bdtopo-osrm',start=','.join(map(str,start)),end=','.join(map(str,end)),profile='pedestrian',optimization='shortest',geometryFormat='geojson',getSteps='false',getBbox='true',distanceUnit='meter',timeUnit='minute',crs='EPSG:4326')
    url='https://data.geopf.fr/navigation/itineraire?'+urllib.parse.urlencode(query)
    base['request_url']=url
    for attempt in range(2):
        with rate_lock:
            delay=max(0,next_request-time.monotonic())
            if delay: time.sleep(delay)
            next_request=time.monotonic()+0.35
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ParisTripPersonalReview/1.0','Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=22) as r: data=json.load(r)
            if 'distance' not in data or 'geometry' not in data: raise ValueError(str(data)[:300])
            result=base|dict(status='ok',distance_m=data['distance'],duration_min=data.get('duration'),geometry=data['geometry'],resource=data.get('resource'),resourceVersion=data.get('resourceVersion'),raw=data)
            return key,result
        except Exception as e:
            base['error']=type(e).__name__+': '+str(e)
            if attempt==0: time.sleep(0.5)
    return key,base|dict(status='unavailable')

with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(fetch,p) for p in plan['route_pairs']]
    for f in as_completed(futures):
        key,value=f.result(); cache[key]=value
        out.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
        print(key,value['status'],round(value.get('distance_m',value['straight_m'])),'m',flush=True)
print('Saved',len(cache),'pairs to',out,flush=True)
