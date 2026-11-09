#!/usr/bin/env python3
"""Render report.md and guideline-coverage.csv into a local, dependency-free dashboard."""
import argparse, csv, html, json, re
from pathlib import Path
from urllib.parse import quote


def render(root, title):
    def inline(s):
        s=html.escape(s)
        def link(m):
            label, url=m.groups(); url=html.unescape(url)
            if url.startswith('/'):
                url=re.sub(r':\d+$','',url)
                try: url=quote(str(Path(url).relative_to(root)))
                except ValueError: url=Path(url).as_uri()
            elif not url.startswith(('https://','http://','#')):
                return label
            return '<a href="'+html.escape(url,quote=True)+'">'+label+'</a>'
        s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,s)
        s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
        return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    raw=(root/'report.md').read_text(); lines=raw.splitlines(); out=[]; cards=[]; i=0
    while i<len(lines):
        line=lines[i]
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[: -]+',x) for x in cells): rows.append(cells)
                i+=1
            out.append('<div class="table-wrap"><table>')
            for n,row in enumerate(rows):
                tag='th' if n==0 else 'td';out.append('<tr>'+''.join(f'<{tag}>{inline(x)}</{tag}>' for x in row)+'</tr>')
                if row and re.fullmatch(r'R\d+',row[0]) and len(row)>=5: cards.append(row)
            out.append('</table></div>');continue
        if line.startswith('#'):
            level=min(4,len(line)-len(line.lstrip('#')));label=line[level:].strip()
            out.append(f'<h{level}>{inline(label)}</h{level}>')
        elif line.strip():out.append('<p>'+inline(line)+'</p>')
        i+=1
    with (root/'guideline-coverage.csv').open() as f: coverage=list(csv.DictReader(f))
    counts={s:sum(x.get('status')==s for x in coverage) for s in ['Issue','Risk','Checked','Not verified','Not applicable']}
    first=next((x for x in lines if x.startswith('**')), 'Read the scope and limitations before relying on these findings.')
    cardhtml=''.join('<article class="finding"><div class="eyebrow">'+inline(c[0]+' · '+c[1])+'</div><span class="badge">'+inline(c[2])+'</span><h3>'+inline(c[3])+'</h3><p>'+inline(c[4] if len(c)==5 else c[-1])+'</p></article>' for c in cards)
    data=json.dumps(coverage).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__ · Mock review</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:#172b3a;background:#f3f6f8;line-height:1.6}*{box-sizing:border-box}body{margin:0}header,main{max-width:1280px;margin:auto;padding:32px 40px}nav{display:flex;gap:24px;align-items:center;flex-wrap:wrap;font-size:14px}nav strong{margin-right:auto}a{color:#087f8c;text-underline-offset:3px}nav a{text-decoration:none}.hero{padding:64px 0 30px;max-width:950px}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;color:#526979}h1{font-size:clamp(36px,5vw,64px);letter-spacing:-2px;line-height:1.06;margin:18px 0 28px}h2{font-size:28px;letter-spacing:-.7px;margin:40px 0 20px}h3{font-size:19px;line-height:1.4}p{overflow-wrap:anywhere}.scope{font-size:17px;color:#455d6e}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.stat{background:white;border:1px solid #dce5eb;border-radius:16px;padding:20px}.stat b{display:block;font-size:32px;font-weight:650;line-height:1.2}.stat span{font-size:13px;color:#526979}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.finding{background:white;border:1px solid #dce5eb;border-radius:18px;padding:26px;border-top:3px solid #149b9b}.finding p{color:#526979;font-size:14px}.badge{display:inline-block;font-size:12px;background:#fff0d9;color:#855710;border-radius:6px;padding:4px 9px;margin-top:14px}.toolbar{display:flex;gap:12px;margin:18px 0}input,select{font:inherit;border:1px solid #cbd9e2;background:white;border-radius:10px;padding:12px}input{flex:1;min-width:100px}.table-wrap{overflow:auto;background:white;border:1px solid #dce5eb;border-radius:12px;margin:20px 0}table{border-collapse:collapse;width:100%;font-size:13px;text-align:left}th,td{padding:14px 16px;border-bottom:1px solid #e8eef2;vertical-align:top;min-width:100px}th{background:#edf3f6;color:#405c6f;font-weight:650}td{max-width:450px;overflow-wrap:anywhere}details{margin-top:36px;border:1px solid #cfdee7;border-radius:16px;padding:24px;background:#fff}summary{cursor:pointer;font-weight:650;font-size:20px}.report{max-width:1100px;margin:auto;font-size:15px}.report h1{font-size:32px}.report h2{font-size:24px}.report h3{margin-top:36px}code{font-size:12px;background:#edf3f6;padding:2px 4px;overflow-wrap:anywhere}.note,footer{color:#526979;font-size:13px}footer{padding:40px 0}.empty{padding:20px}@media(max-width:700px){header,main{padding:22px}.hero{padding-top:36px}.stats{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:1fr}.toolbar{flex-wrap:wrap}}@media print{nav,.toolbar{display:none}body{background:white}.cards{display:block}.finding{break-inside:avoid}details{border:0}.table-wrap{overflow:visible}.stats{display:flex}}
</style><header><nav><strong>APP STORE / MOCK REVIEW</strong><a href="#findings">Findings</a><a href="#coverage">Coverage</a><a href="#report">Full report</a><a href="report.md">Markdown ↗</a></nav><div class="hero"><div class="eyebrow">Local review · Evidence first</div><h1>__TITLE__</h1><div class="scope">__SCOPE__</div></div><div class="stats">__STATS__</div><p class="note">Counts represent guideline entries, not independent findings or completed runtime tests.</p></header><main><section id="findings"><h2>What needs attention</h2><div class="cards">__CARDS__</div></section><section id="coverage"><h2>Explore guideline coverage</h2><p class="note">Checked applies only to each row’s recorded scope. Unverified checks remain open.</p><div class="toolbar"><input id="search" aria-label="Search guideline coverage" placeholder="Search clauses, findings, or evidence…"><select id="status" aria-label="Filter status"><option value="">All statuses</option>__OPTIONS__</select></div><p id="count" role="status" class="note"></p><div class="table-wrap"><table><thead><tr><th>Clause</th><th>Status</th><th>Assessment</th><th>Evidence / next check</th></tr></thead><tbody id="rows"></tbody></table></div><a href="guideline-coverage.csv">Download coverage CSV</a></section><details id="report" open><summary>Full review & evidence</summary><div class="report">__REPORT__</div></details><footer>Mock review, not Apple’s decision. This dashboard runs locally with no external assets, analytics, or network requests. Keep the review folder together to preserve evidence links.</footer></main><script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent), tbody=document.getElementById('rows');function update(){const q=document.getElementById('search').value.toLowerCase(),s=document.getElementById('status').value;const rows=data.filter(r=>(!s||r.status===s)&&JSON.stringify(r).toLowerCase().includes(q));tbody.replaceChildren();for(const r of rows){const tr=document.createElement('tr');for(const text of [r.clause,r.status,(r.applicability||'')+' — '+(r.reason||r.notes||''),(r.evidence||'')+' '+(r.next_check||'')]){const td=document.createElement('td');td.textContent=typeof text==='string'?text:JSON.stringify(text);tr.append(td)}tbody.append(tr)}document.getElementById('count').textContent=rows.length+' of '+data.length+' entries';}document.getElementById('search').addEventListener('input',update);document.getElementById('status').addEventListener('change',update);update();</script></html>'''
    values={'TITLE':html.escape(title),'SCOPE':inline(first),'STATS':''.join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>' for k,v in counts.items()),'CARDS':cardhtml or '<p>See the full report for findings.</p>','OPTIONS':''.join('<option>'+s+'</option>' for s in counts),'REPORT':'\n'.join(out),'DATA':data}
    for k,v in values.items():page=page.replace('__'+k+'__',v)
    (root/'index.html').write_text(page)
    print(root/'index.html')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review-dir',required=True,type=Path);p.add_argument('--title',required=True);a=p.parse_args();render(a.review_dir.resolve(),a.title)
