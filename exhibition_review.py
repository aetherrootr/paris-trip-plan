"""Render source-backed, date-filterable exhibition notes for daily review pages."""
import html

def esc(value):return html.escape(str(value),quote=True)

def render_exhibition_review(data,script):
    day_label='D'+f"{data.get('day',6):02d}"
    content='<section class="exhibition-review" id="day-exhibitions" aria-labelledby="exhibition-heading"><p class="eyebrow">'+esc(day_label)+' · 展览选择</p><h2 id="exhibition-heading">'+esc(data['title'])+'</h2><p>'+esc(data['intro'])+'</p>'
    content+='<div class="exhibition-filter"><label for="exhibition-date">预计'+esc(day_label)+'日期</label><input type="date" id="exhibition-date" min="2027-02-01" max="2027-03-31"><button type="button" id="exhibition-reset">显示全部候选</button><p id="exhibition-filter-status" role="status">未选日期：显示与2027年2—3月相关的已公布展览及待核项目。</p></div>'
    content+='<p class="muted exhibition-help">筛选仅用于比较，出行日期仍待定。展期覆盖不等于当天开馆或仍有票；建议耗时是本行程的预算，不是馆方保证。</p>'
    content+='<details class="exhibition-dates"><summary>先看日期对参观选择的影响</summary><div class="table-wrap"><table><thead><tr><th>预计日期</th><th>对'+esc(day_label)+'的影响</th></tr></thead><tbody>'+''.join('<tr><td>'+esc(r['period'])+'</td><td>'+esc(r['advice'])+'</td></tr>' for r in data['periods'])+'</tbody></table></div></details>'
    for venue in data['venues']:
        content+='<details class="exhibition-venue" id="exhibitions-'+esc(venue['place'])+'"><summary><span>'+esc(venue['name'])+'</span><small>'+esc(venue['summary'])+'</small></summary><div class="exhibition-venue-content"><p class="policy">'+esc(venue['advice'])+'</p><p class="muted">'+esc(venue['notice'])+'</p><div class="exhibition-list">'
        for item in venue['items']:
            content+='<article class="exhibition-item" data-exhibition-kind="'+esc(item['kind'])+'" data-exhibition-start="'+esc(item.get('start',''))+'" data-exhibition-end="'+esc(item.get('end',''))+'"><div class="exhibition-item-heading"><h3>'+esc(item['title'])+'</h3><span class="exhibition-date-state">'+esc('常设' if item['kind']=='permanent' else '活动日另核' if item['kind']=='programme' else '日期待核' if item['kind']=='uncertain' else '已公布展期')+'</span></div><p class="exhibition-range">'+esc(item['dates'])+'</p><p>'+esc(item['about'])+'</p><p class="exhibition-advice"><strong>本行程建议：</strong>'+esc(item['advice'])+'</p><p class="muted">建议预算：'+esc(item['budget'])+'</p><div class="exhibition-sources">'+''.join('<a target="_blank" rel="noopener" href="'+esc(s['url'])+'">'+esc(s['title'])+' ↗</a>' for s in item['sources'])+'</div></article>'
        content+='</div><p class="exhibition-empty" hidden>所选日期暂无本清单中展期匹配的项目。请查看上方待核说明与馆方最新日历，不能据此判断全馆关闭。</p></div></details>'
    content+='<p class="muted exhibition-help">核验：'+esc(data['checked_date'])+'。'+esc(data['footnote'])+'</p></section>'
    return content,'<script>'+script+'</script>'
