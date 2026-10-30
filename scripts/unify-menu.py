#!/usr/bin/env python3
"""지시(2026-10-30): 첫 화면 핵심 4개 + 13개 화면 메뉴 이름·이동 통일. 테스트 브랜치 견본용. 여러 번 실행해도 같은 결과(멱등)."""
import re,sys
NAV_STYLE='margin-top: auto; background: #FFFFFF; border-top: 2px solid #F0D6B5; padding: 8px 6px; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 4px; border-radius: 22px 22px 0 0; box-shadow: 0 -4px 14px rgba(120,70,20,.08)'
A_ON='min-height: 56px; display: flex; align-items: center; justify-content: center; border-radius: 16px; font-size: 17px; font-weight: 700; background: linear-gradient(180deg,#E9843A,#B8501A); color: #FFFFFF; box-shadow: 0 3px 0 #8A3A10'
A_OFF='min-height: 56px; display: flex; align-items: center; justify-content: center; border-radius: 16px; font-size: 17px; font-weight: 700; color: #3B2314'
ITEMS=[('홈','index.html','home'),('가족 전화','index.html#hjFamily','family'),('급할 때','Emergency.html','em'),('복지·혜택','Welfare.html','wel'),('이동·교통','Transit.html','tr'),('전체 메뉴','All.html','all')]
CUR={'index.html':'home','Emergency.html':'em','Welfare.html':'wel','Transit.html':'tr','All.html':'all'}
PARENT_ALL=['Culture.html','Health.html','Jobs.html','Centers.html','Guide.html','Regions.html','Ad.html','Ad2.html']   # 「전체 메뉴」 아래에 있는 화면
def nav_html(page,tag_style=NAV_STYLE):
    cur=CUR.get(page);par=page in PARENT_ALL
    out=['<div style="%s" class="home-nav" data-hjnav="1" role="navigation" aria-label="주요 메뉴">'%tag_style]
    for lab,href,k in ITEMS:
        on=(k==cur) or (par and k=='all')
        attr=' aria-current="page"' if k==cur else (' aria-current="true"' if on else '')
        out.append('<a href="%s" style="%s"%s>%s</a>'%(href,A_ON if on else A_OFF,attr,lab))
    out.append('</div>');return '\n'.join(out)
NAVRE=re.compile(r'<div style="[^"]*border-top: 2px solid #F0D6B5; padding: 8px 6px; display: grid; grid-template-columns: repeat\([36][^"]*"[^>]*>.*?</div>',re.S)
BACK_STYLE='min-height:48px;display:flex;align-items:center;font-size:19px;font-weight:700;color:#7A3510'
def fix_page(page):
    s=open(page,encoding='utf-8').read();o=s
    if NAVRE.search(s):
        s=NAVRE.sub(lambda m:nav_html(page,NAV_STYLE.replace('repeat(6','repeat(3').replace('margin-top: auto','margin-top: 24px') if page=='Regions.html' else NAV_STYLE),s,count=1)
    elif page in('Ad.html','Ad2.html'):
        s=re.sub(r'(\n</div>\n\n\n)(<script src="site.js)',lambda m:'\n'+nav_html(page)+m.group(1)+m.group(2),s,count=1) if 'data-hjnav' not in s else s
    elif page=='Regions.html' and 'data-hjnav' not in s:
        st=NAV_STYLE.replace('repeat(6','repeat(3').replace('margin-top: auto','margin-top: 24px')
        s=s.replace('</main><script',nav_html(page,st)+'</main><script',1)
    # 뒤로 가기 통일
    s=re.sub(r'<a href="(?:Culture|index)\.html" style="min-height:48px;display:flex;align-items:center;font-size:19px;font-weight:700;color:#7A3510">(?:‹ 문화·나들이로|‹ 홈으로)</a>','<a href="index.html" style="%s" class="hj-back">← 처음 화면으로</a>'%BACK_STYLE,s)
    s=s.replace('<a href="index.html">← 처음 화면</a>','<a href="index.html">← 처음 화면으로</a>')
    if page=='Regions.html':s=re.sub(r'<title>[^<]*</title>','<title>내 지역·부모님 지역 · 효자 용인</title>',s,count=1)
    if s!=o:open(page,'w',encoding='utf-8').write(s)
    return s!=o
for p in ['All','Centers','Culture','Emergency','Guide','Health','Jobs','Transit','Welfare','Ad','Ad2','Regions','index']:
    print(p,'수정' if fix_page(p+'.html') else '변경 없음')

def cut(s,start,end_tok,incl=True):
    a=s.index(start);b=s.index(end_tok,a)+(len(end_tok) if incl else 0);return a,b
def fix_home():
    s=open('index.html',encoding='utf-8').read()
    if 'id="core4-title"' in s:return False
    blocks={}
    a,b=cut(s,'<a href="Regions.html" style="display:block;border:1px solid #e7dbd1','</a>');blocks['region']=s[a:b];s=s[:a]+s[b:]
    a,b=cut(s,'<a href="Emergency.html" style="background: linear-gradient(180deg,#E5493C','</a>');blocks['em']=s[a:b];em_pos=a;s=s[:a]+'@@CORE@@'+s[b:]
    a,b=cut(s,'<section class="family-hero"','</section>');blocks['hero']=s[a:b];s=s[:a]+s[b:]
    a,b=cut(s,'<div id="hjFamily"></div>','</div>');blocks['fam']=s[a:b];s=s[:a]+s[b:]
    a=s.index('<h2 style="font-size: 24px; font-weight: 900; margin-top: 4px" class="home-menu-title" id="menu-title">');b=s.index('</div><div style="background: #FFFFFF; border: 2px solid #F0D6B5; border-radius: 28px; padding: 18px',a)+6
    menu=s[a:b];s=s[:a]+s[b:]
    import re as _re
    links=_re.findall(r'<a href="(Culture|Health|Jobs|Welfare|Transit)\.html".*?</a>',menu,_re.S)
    keep=[m.group(0) for m in _re.finditer(r'<a href="(?:Welfare|Transit)\.html".*?</a>',menu,_re.S)]
    assert len(keep)==2
    h2='<h2 style="font-size: 26px; font-weight: 900; margin: 4px 0 0" class="home-menu-title" id="core4-title">꼭 필요한 4가지</h2>'
    menu_div='<div style="display: flex; flex-direction: column; gap: 14px" class="primary-menu" role="navigation" aria-labelledby="core4-title">'+''.join(keep)+'</div>'
    allbtn=('<a href="All.html" class="hj-all-menu" style="display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:84px;box-sizing:border-box;padding:12px 18px;border-radius:28px;background:#FFFFFF;border:2px solid #D9A066;box-shadow:0 6px 0 #E8C79B;color:#3B2314">'
            '<span style="display:flex;flex-direction:column;gap:2px"><span style="font-size:24px;font-weight:900">전체 메뉴</span><span style="font-size:17px;color:#6A4A33">나들이·건강교실·일자리 등 더 보기</span></span><span style="font-size:30px;font-weight:900;color:#B8501A">›</span></a>')
    core=h2+blocks['fam']+blocks['em']+menu_div+allbtn+blocks['region']+blocks['hero']
    s=s.replace('@@CORE@@',core)
    open('index.html','w',encoding='utf-8').write(s);return True
def fix_all():
    s=open('All.html',encoding='utf-8').read()
    if 'id="all-core"' in s:return False
    s=s.replace('‘우리 동네 센터’','‘우리 동네 행정복지센터’').replace('<span style="font-size: 23px; font-weight: 900">우리 동네 센터</span>','<span style="font-size: 23px; font-weight: 900">우리 동네 행정복지센터</span>')
    a=s.index('<div style="display: flex; flex-direction: column; gap: 10px">');b=s.index('</div>\n\n<div s',a)
    inner=s[a+len('<div style="display: flex; flex-direction: column; gap: 10px">'):b]
    import re as _re
    m={}
    for x in _re.finditer(r'<a href="([A-Za-z]+)\.html".*?</a>',inner,_re.S):m[x.group(1)]=x.group(0)
    fam=('<a href="index.html#hjFamily" style="min-height: 84px; box-sizing: border-box; background: #FFFFFF; color: #12344D; border: 2px solid #F0D6B5; border-radius: 22px; box-shadow: 0 8px 0 #E8C79B; padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px"><span style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 23px; font-weight: 900">가족 전화</span><span style="font-size: 17px; font-weight: 500">가족 사진을 보고 바로 전화</span></span><span style="font-size: 28px; font-weight: 700">›</span></a>')
    H=lambda t,i='':'<h2 %sstyle="font-size:22px;font-weight:900;margin:10px 0 0;color:#6A4A33">%s</h2>'%(i,t)
    new=(H('꼭 필요한 4가지','id="all-core" ')+fam+m['Emergency']+m['Welfare']+m['Transit']+H('더 알아보기')+m['Culture']+m['Health']+m['Jobs']+m['Centers']+H('처음 쓰시는 분 · 설정')+m['Guide']+m['Regions'])
    assert len(m)==9,m.keys()
    s=s[:a]+'<div style="display: flex; flex-direction: column; gap: 10px">'+new+s[b:]
    open('All.html','w',encoding='utf-8').write(s);return True
print('home','수정' if fix_home() else '변경 없음');print('All 구성','수정' if fix_all() else '변경 없음')
