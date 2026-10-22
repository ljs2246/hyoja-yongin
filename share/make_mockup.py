from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc";B="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def font(p,s):
    for i in range(8):
        try:
            f=ImageFont.truetype(p,s,index=i)
            if 'KR' in ''.join(f.getname()): return f
        except Exception: pass
    return ImageFont.truetype(p,s)
def phone(shot,w=340):
    s=Image.open(shot).convert('RGB');s=s.crop((0,0,s.width,int(s.width*1.9)));h=int(w*s.height/s.width);s=s.resize((w,h))
    bz=22;R=56;W,H=w+2*bz,h+2*bz;M=70
    ph=Image.new('RGBA',(W+2*M,H+2*M),(0,0,0,0))
    sh=Image.new('RGBA',ph.size,(0,0,0,0));ImageDraw.Draw(sh).rounded_rectangle((M+28,M+48,M+28+W,M+48+H),R,fill=(70,35,5,170))
    ph=Image.alpha_composite(ph,sh.filter(ImageFilter.GaussianBlur(22)))
    d=ImageDraw.Draw(ph)
    d.rounded_rectangle((M+8,M+8,M+8+W,M+8+H),R,fill='#140B04')            # 두께(옆면)
    d.rounded_rectangle((M,M,M+W,M+H),R,fill='#4A2C16')                     # 테두리
    d.rounded_rectangle((M+4,M+4,M+W-4,M+H-4),R-4,outline='#8A5A33',width=3) # 윤곽 빛
    m=Image.new('L',(w,h),0);ImageDraw.Draw(m).rounded_rectangle((0,0,w,h),R-18,fill=255)
    ph.paste(s,(M+bz,M+bz),m)
    d.ellipse((M+W//2-6,M+8,M+W//2+6,M+20),fill='#140B04')
    gm=Image.new('L',(w,h),0);ImageDraw.Draw(gm).polygon([(0,0),(int(w*.55),0),(0,int(h*.30))],fill=40)
    from PIL import ImageChops
    gm=ImageChops.multiply(gm,m)
    white=Image.new('RGBA',(w,h),(255,255,255,255));white.putalpha(gm)
    ph.alpha_composite(white,(M+bz,M+bz))
    return ph
W,H=1600,1000
im=Image.new('RGBA',(W,H),'#FFF0D6');d=ImageDraw.Draw(im)
for i in range(H):
    c=int(255-i*0.02);d.line((0,i,W,i),fill=(255,c-12,max(c-50,0)))
d.ellipse((-250,-300,650,600),fill='#FFE2A8');d.ellipse((1050,650,1900,1350),fill='#FFD58A')
a=phone('/tmp/shot_em.png').rotate(7,expand=True,resample=Image.BICUBIC)
b=phone('/tmp/shot_jobs.png').rotate(-6,expand=True,resample=Image.BICUBIC)
im.alpha_composite(b,(1050,90));im.alpha_composite(a,(690,20))
t=font(F,118)
d.text((92,104),"효자 용인",font=t,fill='#140B04');d.text((88,100),"효자 용인",font=t,fill='#4A2610')
d.text((90,270),"어르신께 꼭 필요한\n용인 정보",font=font(B,56),fill='#B8501A',spacing=12)
y=450
for txt in ["급할 때 119 · 문 연 약국","복지 · 일자리 · 나들이","큰 글씨로 편하게"]:
    d.rounded_rectangle((90,y,560,y+70),35,fill='#B8501A');d.text((325,y+35),txt,font=font(B,32),fill='white',anchor='mm');y+=86
e=cv2.QRCodeEncoder_create();q=e.encode('https://ljs2246.github.io/hyoja-yongin/');q=cv2.resize(q,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST)
qi=Image.fromarray(q).convert('RGB').resize((220,220),Image.NEAREST)
d.rounded_rectangle((95,745,585,995),28,fill='#C99A5E');d.rounded_rectangle((90,735,580,985),28,fill='white',outline='#F0D6B5',width=4)
im.paste(qi,(110,762));d.text((345,822),"폰 카메라로",font=font(F,36),fill='#B8501A');d.text((345,872),"비추면 열려요",font=font(F,36),fill='#B8501A')
im.convert('RGB').save('/tmp/hyoja_phone_mockup.png')
