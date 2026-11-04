"""Cino 节奏大师 自动打谱（三档难度）
用法: python gen3.py 歌.mp3 输出前缀 "歌名"     → 输出前缀_easy.txt / _normal.txt / _hard.txt
所有音符都卡在节拍网格上（简单=四分音符，普通/困难=八分音符）。
  简单：只跟人声的主要字，一拍最多一个；长音给长按；偶尔滑键；没有折线、没有双押
  普通：跟人声每个音；长按、折线（连唱）、句尾滑键；间奏补鼓点
  困难：人声 + 鼓点两层，鼓点放在另一只手那一侧；副歌重拍双押；更多滑键和折线；速度更快
需要: pip install librosa"""
import librosa, numpy as np, sys, random
import scipy.ndimage as nd
f,prefix,name=sys.argv[1],sys.argv[2],sys.argv[3]
SR,HOP=22050,512
y,sr=librosa.load(f,sr=SR,mono=True); dur=len(y)/sr
# ================= 分析（三档共用） =================
S,ph=librosa.magphase(librosa.stft(y,n_fft=2048,hop_length=HOP))
Sf=np.minimum(S,librosa.decompose.nn_filter(S,aggregate=np.median,metric='cosine',width=int(librosa.time_to_frames(2,sr=sr,hop_length=HOP))))
Sv=librosa.util.softmask(S-Sf,10*Sf,power=2)*S
fr=librosa.fft_frequencies(sr=sr,n_fft=2048); Sv[(fr<120)|(fr>5000)]*=0.1
yv=librosa.istft(Sv*ph,hop_length=HOP,length=len(y))
f0,vf,vp=librosa.pyin(yv,fmin=110,fmax=1000,sr=sr,frame_length=2048,hop_length=HOP)
tt=librosa.times_like(f0,sr=sr,hop_length=HOP)
midi=librosa.hz_to_midi(np.where(vf,f0,np.nan))
yp=librosa.effects.hpss(y)[1]
penv=librosa.onset.onset_strength(y=yp,sr=sr,hop_length=HOP)
pt=librosa.times_like(penv,sr=sr,hop_length=HOP)
tempo,beats=librosa.beat.beat_track(onset_envelope=penv,sr=sr,hop_length=HOP,units='time')
beats=np.asarray(beats); per=float(np.median(np.diff(beats)))
pre=[]; x=beats[0]-per
while x>0.2: pre.insert(0,x); x-=per
beats=np.concatenate([pre,beats])
g8=np.sort(np.concatenate([beats,(beats[:-1]+beats[1:])/2]))
def q8(t): return float(g8[np.argmin(np.abs(g8-t))])
def q4(t): return float(beats[np.argmin(np.abs(beats-t))])
def fi(t,arr=tt): return int(np.clip(np.searchsorted(arr,t),0,len(arr)-1))
beatIdx=lambda t:int(np.argmin(np.abs(beats-t)))
rms=librosa.feature.rms(y=y,hop_length=HOP)[0]
barE=np.array([rms[fi(beats[i],pt):fi(beats[min(i+4,len(beats)-1)],pt)+1].mean() for i in range(0,len(beats),4)])
elo,ehi=np.percentile(barE,30),np.percentile(barE,65)
def energy(t):
    e=barE[min(beatIdx(t)//4,len(barE)-1)]; return 2 if e>=ehi else (1 if e>=elo else 0)
def drum(t):   # 局部归一化的鼓点强度
    i=fi(t,pt); loc=penv[max(0,i-90):i+90].mean()+1e-6; return penv[max(0,i-2):i+3].max()/loc
print(f'BPM {60/per:.1f}  时长 {dur:.0f}s')
# ---- 人声旋律转写 ----
vv=vf&(vp>0.1)
for i in range(2,len(vv)-2):
    if not vv[i] and vv[i-1] and (vv[i+1] or vv[i+2]): vv[i]=True
sm=np.copy(midi)
for i in range(len(sm)):
    w=midi[max(0,i-2):i+3]; w=w[~np.isnan(w)]; sm[i]=np.median(w) if len(w) and vv[i] else np.nan
segs=[]; i=0; n=len(sm)
while i<n:
    if np.isnan(sm[i]): i+=1; continue
    j=i; ref=sm[i]; vals=[]
    while j<n and not np.isnan(sm[j]):
        if abs(sm[j]-ref)>=1.0:
            k=j; c=0
            while k<n and c<3 and not np.isnan(sm[k]) and abs(sm[k]-ref)>=1.0: k+=1; c+=1
            if c>=3: break
        vals.append(sm[j]); ref=np.median(vals[-8:]); j+=1
    if tt[min(j,n-1)]-tt[i]>=0.09: segs.append((float(tt[i]),float(tt[min(j,n-1)]),float(np.median(vals))))
    i=max(j,i+1)
allp=np.array([s[2] for s in segs]); plo,phi=np.percentile(allp,10),np.percentile(allp,90)
print('人声音符', len(segs))
def vocalEvents(qf,mingap):
    ev=[]; L={}; P={}; W={}
    for a,b,p in segs:
        t=round(qf(a),4)
        if ev and t-ev[-1]<mingap-1e-3:
            L[ev[-1]]=max(L[ev[-1]],b-ev[-1]); W[ev[-1]]+=b-a; continue
        ev.append(t); L[t]=b-t; P[t]=p; W[t]=b-a
    return ev,L,P,W
def absLane(p): return int(np.clip(round((p-plo)/(phi-plo+1e-6)*3),0,3))
def stepLane(lane,p,lp,tog,maxstep=2):
    d=p-lp
    if abs(d)<0.8:
        nl=lane+tog
        if nl<0 or nl>3: tog=-tog; nl=lane+tog
        return nl,-tog
    st=1 if abs(d)<5 or maxstep==1 else 2
    return int(np.clip(lane+(st if d>0 else -st),0,3)),tog

# ================= 生成 =================
def build(level):
    random.seed(7+level)
    fast=60/per>160   # 很快的歌（>160 BPM）整体放宽一档，免得太密
    if level==0: ev,L,P,W=vocalEvents(q4,per*(1.98 if fast else 0.99)); qf=q4
    elif level==1 and fast: ev,L,P,W=vocalEvents(q4,per*0.99); qf=q4
    else: ev,L,P,W=vocalEvents(q8,per*(0.99 if fast else 0.49)); qf=q8
    # 简单：去掉很短的过渡音（保留主要字）
    if level==0: ev=[t for t in ev if W[t]>=0.12 or energy(t)==2]
    notes=[]; lane=1; lp=np.nan; lt=-9; tog=1; lastPath=-99; lastFlick=-99
    pathGap={0:1e9,1:per*12,2:per*7}[level]; flickGap={0:per*24,1:per*14,2:per*7}[level]
    flickRest={0:2.0,1:1.6,2:1.0}[level]; holdMin={0:per*1.5,1:per*0.9,2:per*0.9}[level]
    k=0
    while k<len(ev):
        t=ev[k]; nxt=ev[k+1] if k+1<len(ev) else dur; p=P.get(t,np.nan)
        if np.isnan(p): p=lp if not np.isnan(lp) else (plo+phi)/2
        if t-lt>1.2 or np.isnan(lp): lane=absLane(p)
        else: lane,tog=stepLane(lane,p,lp,tog,1 if level==0 else 2)
        # 折线：连唱的一串
        j=k
        while j+1<len(ev) and ev[j+1]-(ev[j]+L[ev[j]])<0.09 and L[ev[j]]>=per*0.4 and j-k<3: j+=1
        runEnd=ev[j]+L[ev[j]]
        if level>=1 and j>k and runEnd-t>=per*(2 if level==1 else 1.5) and t-lastPath>pathGap:
            pts=[(t,lane)]; cur=lane; cp=p; tg=tog
            for m in range(k+1,j+1):
                pm=P.get(ev[m],cp); nl,tg=stepLane(cur,pm,cp,tg)
                if nl!=cur: pts.append((ev[m],nl)); cur=nl
                cp=pm
            na=ev[j+1] if j+1<len(ev) else dur; end=qf(min(runEnd,na-per*0.5))
            if len(pts)>=2 and end-pts[-1][0]>=per*0.4:
                notes.append(dict(type=3,lane=lane,t=t,end=end,path=pts,src='v')); lastPath=t; lane=cur; lp=cp; lt=end; k=j+1; continue
        Ln=min(L[t],nxt-t)
        if Ln>=holdMin and nxt-t>=per*1.0:
            end=qf(min(t+Ln,nxt-per*0.5))
            if end-t>=holdMin*0.95:
                notes.append(dict(type=1,lane=lane,t=t,end=end,src='v')); lp=p; lt=t; k+=1; continue
        if nxt-t>=flickRest and Ln<0.6 and t-lastFlick>flickGap and level>=0:
            notes.append(dict(type=2,lane=lane,t=t,end=t,dir=1 if lane<=1 else -1,src='v')); lastFlick=t
        else: notes.append(dict(type=0,lane=lane,t=t,end=t,src='v'))
        lp=p; lt=t; k+=1
    vocalTimes=np.array(sorted(n['t'] for n in notes))
    spans=[(n['t'],n['end'],n) for n in notes]
    def nearV(t,w): return len(vocalTimes) and np.min(np.abs(vocalTimes-t))<w
    def laneAtV(t):
        best=None
        for a,b,nn in spans:
            if a-0.05<=t<=b+0.05:
                if nn['type']==3: return [q_[1] for q_ in nn['path'] if q_[0]<=t+1e-3][-1]
                return nn['lane']
            if a<=t: best=nn['lane']
        return best if best is not None else 1
    # ---- 鼓点层 ----
    side=0
    if level==0:     # 简单：只在没人声的地方，每两拍一个
        for b in beats[::2]:
            if not nearV(b,per*3) and drum(b)>1.0: notes.append(dict(type=0,lane=random.choice([1,2]),t=float(b),end=float(b),src='d'))
    elif level==1:   # 普通：间奏里四分音符
        for b in beats:
            if not nearV(b,per*1.9) and drum(b)>1.0: notes.append(dict(type=0,lane=random.choice([0,1,2,3]),t=float(b),end=float(b),src='d'))
    else:            # 困难：鼓点一直在，放在人声的另一侧
        cnt=0
        for i,b in enumerate(g8):
            e=energy(b); onbeat=(i%2==0)
            th=1.0 if onbeat else (1.5 if e==2 and 60/per<=160 else 9)
            if e==0 and not onbeat: continue
            if drum(b)<th: continue
            vl=laneAtV(b); half=[2,3] if vl<=1 else [0,1]
            dl=half[cnt%2]; cnt+=1
            if nearV(b,0.02):
                # 和人声同时：只在副歌的重拍做双押
                if not(e==2 and onbeat and beatIdx(b)%2==0): continue
            elif nearV(b,per*0.24): continue
            # 特别重的重音给滑键
            if e==2 and onbeat and drum(b)>2.6 and random.random()<0.35:
                notes.append(dict(type=2,lane=dl,t=float(b),end=float(b),dir=1 if dl<=1 else -1,src='d'))
            else: notes.append(dict(type=0,lane=dl,t=float(b),end=float(b),src='d'))
    # ---- 冲突清理：同车道重叠、同一时刻最多 2 个、长按期间那只手不再塞音符 ----
    notes.sort(key=lambda n:(n['t'],0 if n['src']=='v' else 1,n['lane']))
    busy=[]; clean=[]
    def lanesOf(n):
        s_={n['lane']}
        if n['type']==2: s_|={n['lane']+n['dir']}
        if n['type']==3: s_|={p_[1] for p_ in n['path']}
        return s_
    for n in notes:
        a,b=n['t'],n['end']; ls=lanesOf(n)
        if any(0<=x+0 and (ls&l2) and not(b<x-0.12 or a>y_+0.12) for x,y_,l2 in busy): 
            if n['type'] in (0,) and n['src']=='d': continue
            free=[l for l in range(4) if not any((l in l2) and not(b<x-0.12 or a>y_+0.12) for x,y_,l2 in busy)]
            if n['type'] in (0,1) and free: n['lane']=min(free,key=lambda l:abs(l-n['lane'])); ls={n['lane']}
            else: continue
        simult=sum(1 for x,y_,l2 in busy if abs(x-a)<0.02)
        if simult>=2: continue
        clean.append(n); busy.append((a,b,ls))
    # ---- 顺手：避免同一车道快速连打（八分音符的“叠键”），换到同一只手的另一格 ----
    clean.sort(key=lambda n:n['t'])
    lastHit={l:-9 for l in range(4)}; occ=[]
    def freeAt(l,t): return all(not(x-0.1<=t<=y_+0.1) or l not in ls_ for x,y_,ls_ in occ)
    for n in clean:
        t=n['t']
        if n['type'] in (0,1) and t-lastHit[n['lane']]<0.3:
            mate=n['lane']^1   # 0↔1, 2↔3
            for c in [mate]+[l for l in range(4) if l not in (n['lane'],mate)]:
                if t-lastHit[c]>=0.3 and freeAt(c,t) and not any(abs(m['t']-t)<0.02 and m['lane']==c for m in clean if m is not n):
                    n['lane']=c; break
        lastHit[n['lane']]=n['end'] if n['type']!=3 else n['end']
        if n['type']==3:
            for p_ in n['path']: lastHit[p_[1]]=n['end']
        occ.append((n['t'],n['end'],lanesOf(n)))
    return clean
def write(notes,path):
    def lanes(l): return ''.join('1' if k==l else '0' for k in range(4))
    out=[]
    for n in notes:
        t=f"{n['t']:.4f}"; e=f"{n['end']:.4f}"
        if n['type']==0: out.append(f"0#{lanes(n['lane'])}#{t}#{t}")
        elif n['type']==1: out.append(f"1#{lanes(n['lane'])}#{t}#{e}")
        elif n['type']==2: out.append(f"2#{lanes(n['lane'])}#{t}#{t}#{'R' if n['dir']>0 else 'L'}")
        else: out.append(f"3#{lanes(n['lane'])}#{t}#{e}#"+';'.join(f"{a:.4f}:{l}" for a,l in n['path']))
    out.append(f'[{name}]')
    open(path,'w',encoding='utf-8').write('\n'.join(out)+'\n')
from collections import Counter
for lv,tag in enumerate(['easy','normal','hard']):
    ns=build(lv); write(ns,f'{prefix}_{tag}.txt')
    c=Counter(n['type'] for n in ns); chords=Counter(round(n['t'],3) for n in ns); ch=sum(1 for v in chords.values() if v>1)
    print(f'{tag:6s} 音符 {len(ns):4d}  每秒 {len(ns)/dur:.2f}  点按 {c[0]} 长按 {c[1]} 滑键 {c[2]} 折线 {c[3]} 双押 {ch}')
