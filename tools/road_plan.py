"""Road plan W45N8 + W45N7 (analysis only). Reuses remote_eval pathing."""
import sys,os,json,math;sys.argv=['x'];sys.path.insert(0,'tools')
import importlib.util as u
s=u.spec_from_file_location('re','tools/remote_eval.py');m=u.module_from_spec(s)
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): s.loader.exec_module(m)
T,roads,OFF=m.T,m.roads,m.OFF
S=(37,31);C8=(63,11);SRC7=(50+21,100-50+16-0) if False else (50+21,50+16)
def route(goal,paved):
    d,p=m.path(S,goal,1,paved);return p
r8=route(C8,True); r7=route(SRC7,True)
def summ(p):
    out={}
    for q in p:
        k=(m.room_of(q),'road' if q in roads else T[q]);out[k]=out.get(k,0)+1
    return out
shared=[q for q in r7 if q in set(r8)]
new8=[q for q in r8 if q not in roads]; new7=[q for q in r7 if q not in roads and q not in set(r8)]
cost=lambda L:sum(1500 if T[q]=='swamp' else 300 for q in L)
dec=lambda L:sum(0.005 if T[q]=='swamp' else 0.001 for q in L)
# tick sim of hauler round trip
def sim(p,body,paved_set):
    t=0
    for loaded in(True,False):
        f=0
        for q in p:
            heavy=sum(1 for b in body if b!='m' and (b!='c' or loaded)); mv=body.count('m')
            c=1 if q in paved_set else (10 if T[q]=='swamp' else 2)
            f+=c*heavy; t+=1
            while f>0: f-=2*mv; t+=1 if f>0 else 0
            f=max(f,0)
    return t
res={}
for name,p,new in(('W45N8',r8,new8),('W45N7',r7,new8+new7)):
    full=set(roads)|set(p)
    for body,lab in((['c']*8+['m']*8,'8C8M'),(['c']*16+['m']*8,'16C8M'),(['c']*24+['m']*12,'24C12M')):
        for ps,pl in((roads,'今'),(full,'全铺')):
            rt=sim(p,body,ps)+4; cap=50*body.count('c'); need=10*rt/cap
            res[f'{name}|{lab}|{pl}']=dict(len=len(p),rt=rt,need=round(need,2),formula_rt=None)
    res[name+'_summary']={f'{a}:{b}':n for (a,b),n in summ(p).items()}
res['new8']=len(new8);res['new8_swamp']=sum(T[q]=='swamp' for q in new8);res['cost8']=cost(new8);res['decay8']=dec(new8)
res['new7']=len(new7);res['new7_swamp']=sum(T[q]=='swamp' for q in new7);res['cost7']=cost(new7);res['decay7']=dec(new7)
res['shared']=len(shared)
res['r8']=[(m.room_of(q),q[0]%50,q[1]%50) for q in r8];res['r7']=[(m.room_of(q),q[0]%50,q[1]%50) for q in r7]
json.dump(res,open('metrics/road_plan.json','w'))
for k,v in res.items():
    if k not in('r8','r7'):print(k,v)
print('R7',[f'{a}({x},{y})' for a,x,y in res['r7']])
# image
from PIL import Image,ImageDraw,ImageFont
Z=8;W,H=100*Z,100*Z;im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
col={'wall':(60,60,60),'swamp':(110,150,80),'plain':(225,225,215)}
for (x,y),t in T.items():d.rectangle([x*Z,y*Z,x*Z+Z-1,y*Z+Z-1],fill=col[t])
for q in roads:d.rectangle([q[0]*Z+2,q[1]*Z+2,q[0]*Z+5,q[1]*Z+5],fill=(120,120,120))
for q in new8:d.rectangle([q[0]*Z+1,q[1]*Z+1,q[0]*Z+6,q[1]*Z+6],fill=(30,100,230))
for q in new7:d.rectangle([q[0]*Z+1,q[1]*Z+1,q[0]*Z+6,q[1]*Z+6],fill=(230,120,20))
fp=[f for f in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'] if os.path.exists(f)]
import glob;fp=fp or glob.glob('/home/box/**/*CJK*.tt*',recursive=True)+glob.glob('/workspace/**/*.tt[fc]',recursive=True)
F=ImageFont.truetype(fp[0],16) if fp else ImageFont.load_default()
for r,(ox,oy) in OFF.items():d.text((ox*Z+5,oy*Z+5),r,fill='red',font=F)
for p,t in((S,'仓库'),(C8,'W45N8 容器'),(SRC7,'W45N7 能量源')):d.ellipse([p[0]*Z-5,p[1]*Z-5,p[0]*Z+5,p[1]*Z+5],fill='red');d.text((p[0]*Z+8,p[1]*Z-8),t,fill='black',font=F)
d.text((10,H-60),'蓝=W45N8 新路(一期)  橙=W45N7 新路(二期)  灰=已有路',fill='black',font=F)
im.save('/workspace/remote_roads_cn.png');print('font',fp[:1])
