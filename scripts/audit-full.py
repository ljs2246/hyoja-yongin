import json,re,collections,subprocess
from pathlib import Path
from html.parser import HTMLParser
root=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self): super().__init__(); self.ids=[]; self.refs=[]; self.blank=[]; self.img=[]; self.inline=[]; self.in_script=False
 def handle_starttag(self,t,a):
  a=dict(a)
  if 'id' in a:self.ids.append(a['id'])
  for k in ['href','src']:
   if k in a:self.refs.append(a[k])
  if t=='a' and a.get('target')=='_blank' and 'noopener' not in a.get('rel',''):self.blank.append(a.get('href'))
  if t=='img' and 'alt' not in a:self.img.append(a.get('src'))
  if t=='script' and not a.get('src'):self.in_script=True;self.inline.append('')
 def handle_endtag(self,t):
  if t=='script':self.in_script=False
 def handle_data(self,d):
  if self.in_script:self.inline[-1]+=d
inventory=set(json.loads((root/'inventory.json').read_text()))
pages=[]
for f in sorted(root.glob('*.html')):
 p=Page();p.feed(f.read_text()); missing=[]
 for u in p.refs:
  if not u or u.startswith(('#','https:','http:','tel:','mailto:','data:','javascript:','intent:','nmap:')):continue
  path=u.split('#')[0].split('?')[0].removeprefix('./')
  if path and path not in inventory and not (root/path).is_file():missing.append(path)
 pages.append(dict(page=f.name,missing_files=sorted(set(missing)),duplicate_ids=[k for k,v in collections.Counter(p.ids).items() if v>1],new_tab_without_noopener=p.blank,images_without_alt=p.img))
syntax=[]
for f in list(root.glob('*.js'))+list((root/'scripts').glob('*.cjs')):
 r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True);syntax.append(dict(file=str(f.relative_to(root)),pass_check=r.returncode==0,error=r.stderr[:500]))
data={}
for n in ['emergency','pharmacy']:
 obj=json.loads((root/'data'/f'{n}.json').read_text());data[n]=dict(type=type(obj).__name__,count=len(obj) if isinstance(obj,list) else len(obj.get('목록',[])))
out=dict(source_commit=(root/'source-commit.txt').read_text().strip(),scope='13 app HTML pages plus Review; static reference, DOM IDs, JS syntax; no factual or device certification',pages=pages,syntax=syntax,data=data)
(root/'docs/full-structural-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))
