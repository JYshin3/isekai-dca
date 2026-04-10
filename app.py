"""
이세계 DCA — Adaptive DCA Dashboard
Target: $500,000 in 3 years | Monthly Investment: $2,000
pandas-ta 없이 numpy로 모든 지표 직접 계산
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
from pathlib import Path

st.set_page_config(page_title="이세계 DCA", page_icon="⚔️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;900&family=IBM+Plex+Mono:wght@300;400;600&display=swap');
:root{--bg:#070a0f;--card:#0f1620;--gold:#c9a84c;--blue:#4fa3e0;--green:#3ecf8e;--red:#e05c5c;--orange:#e08c3c;--text:#e8e6f0;--muted:#6b7a99;--border:#1e2a3a;}
html,body,[class*="css"]{font-family:'IBM Plex Mono',monospace;background-color:var(--bg);color:var(--text);}
.stApp{background:radial-gradient(ellipse at top left,#0d1628 0%,#070a0f 60%);}
.hd{text-align:center;padding:1.5rem 0 1rem;border-bottom:1px solid var(--border);margin-bottom:1.5rem;}
.hd h1{font-family:'Cinzel',serif;font-size:2.4rem;font-weight:900;background:linear-gradient(135deg,#c9a84c,#f0d080,#c9a84c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px;margin:0;}
.hd p{color:var(--muted);font-size:.75rem;letter-spacing:2px;margin-top:.4rem;}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;margin-bottom:1rem;}
.card-g{border-color:var(--gold);box-shadow:0 0 20px #c9a84c22;}
.mb{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem;text-align:center;}
.ml{font-size:.62rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}
.mv{font-family:'Cinzel',serif;font-size:1.5rem;font-weight:600;color:var(--gold);margin:.3rem 0;}
.ms{font-size:.68rem;color:var(--muted);}
.st2{font-family:'Cinzel',serif;font-size:.85rem;color:var(--gold);letter-spacing:3px;border-bottom:1px solid var(--border);padding-bottom:.5rem;margin-bottom:1rem;text-transform:uppercase;}
.warn{background:#2a1a0a;border:1px solid #e08c3c55;border-left:3px solid var(--orange);border-radius:4px;padding:.7rem 1rem;margin:.4rem 0;font-size:.76rem;color:#e08c3c;}
.info{background:#0a1a2a;border:1px solid #4fa3e055;border-left:3px solid var(--blue);border-radius:4px;padding:.7rem 1rem;margin:.4rem 0;font-size:.76rem;color:#4fa3e0;}
.ok{background:#0a2a1a;border:1px solid #3ecf8e55;border-left:3px solid var(--green);border-radius:4px;padding:.7rem 1rem;margin:.4rem 0;font-size:.76rem;color:#3ecf8e;}
section[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid var(--border);}
.stButton>button{background:var(--card);color:var(--gold);border:1px solid var(--gold);border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.75rem;letter-spacing:1px;}
.stButton>button:hover{background:var(--gold);color:var(--bg);}
.stTabs [data-baseweb="tab"]{font-family:'IBM Plex Mono',monospace;font-size:.72rem;letter-spacing:1px;color:var(--muted);}
.stTabs [aria-selected="true"]{color:var(--gold)!important;}
table{width:100%;border-collapse:collapse;font-size:.78rem;}
th{color:var(--muted);font-size:.62rem;letter-spacing:2px;border-bottom:1px solid var(--border);padding:.5rem;}
td{padding:.55rem .5rem;border-bottom:1px solid #1e2a3a30;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──
TICKERS = {
    "GOOGL":{"name":"Alphabet",         "weight":.30,"color":"#4fa3e0","base":600},
    "IREN": {"name":"IREN Ltd",          "weight":.40,"color":"#c9a84c","base":800},
    "NXE":  {"name":"NexGen Energy",     "weight":.10,"color":"#9b6dff","base":200},
    "IONQ": {"name":"IonQ",              "weight":.05,"color":"#e05c5c","base":100},
    "MU":   {"name":"Micron Technology", "weight":.15,"color":"#3ecf8e","base":300},
}
BUDGET=2000; TARGET=500000; MONTHS=36; PF_FILE=Path("portfolio.json")
IND_P={
    "GOOGL":{"rsi":14,"sk":14,"sd":14,"macd":(12,26,9),"bbs":2.0,"atr":14,"adx":14},
    "IREN": {"rsi":20,"sk":20,"sd":10,"macd":(20,40,9),"bbs":2.5,"atr":20,"adx":20},
    "NXE":  {"rsi":20,"sk":20,"sd":10,"macd":(20,40,9),"bbs":2.0,"atr":20,"adx":20},
    "MU":   {"rsi":20,"sk":20,"sd":10,"macd":(24,52,9),"bbs":2.5,"atr":20,"adx":20},
    "IONQ": {"rsi":14,"sk":14,"sd":14,"macd":(24,52,9),"bbs":2.0,"atr":14,"adx":14},
}

# ── INDICATORS ──
def rsi(c,p):
    if len(c)<p+1: return 50.
    d=np.diff(c); g=np.where(d>0,d,0.); l=np.where(d<0,-d,0.)
    ag,al=np.mean(g[:p]),np.mean(l[:p])
    for i in range(p,len(g)):
        ag=(ag*(p-1)+g[i])/p; al=(al*(p-1)+l[i])/p
    return 100. if al==0 else float(100-100/(1+ag/al))

def ema(a,p):
    e=np.full(len(a),np.nan); 
    if len(a)<p: return e
    e[p-1]=np.mean(a[:p]); k=2/(p+1)
    for i in range(p,len(a)): e[i]=a[i]*k+e[i-1]*(1-k)
    return e

def sma(a,p):
    s=np.full(len(a),np.nan)
    for i in range(p-1,len(a)): s[i]=np.mean(a[i-p+1:i+1])
    return s

def macd(c,f,sl,sg):
    ef=ema(c,f); es=ema(c,sl); ml=ef-es
    si=np.full(len(c),np.nan)
    v=~np.isnan(ml); idx=np.where(v)[0]
    if idx.sum()>=sg:
        tmp=ema(ml[idx],sg); si[idx]=tmp
    return ml,si,ml-si

def bb(c,p=20,std=2.):
    m=sma(c,p); s=np.full(len(c),np.nan)
    for i in range(p-1,len(c)): s[i]=np.std(c[i-p+1:i+1],ddof=0)
    return m+std*s, m, m-std*s

def atr(h,l,c,p):
    tr=np.maximum(h[1:]-l[1:],np.maximum(np.abs(h[1:]-c[:-1]),np.abs(l[1:]-c[:-1])))
    a=np.full(len(c),np.nan)
    if len(tr)<p: return a
    a[p]=np.mean(tr[:p])
    for i in range(p+1,len(c)): a[i]=(a[i-1]*(p-1)+tr[i-1])/p
    return a

def adx(h,l,c,p):
    if len(c)<p*2: return 20.
    um=h[1:]-h[:-1]; dm=l[:-1]-l[1:]
    pd_=np.where((um>dm)&(um>0),um,0.); md_=np.where((dm>um)&(dm>0),dm,0.)
    tr=np.maximum(h[1:]-l[1:],np.maximum(np.abs(h[1:]-c[:-1]),np.abs(l[1:]-c[:-1])))
    def sm(a,pp):
        s=np.empty(len(a)); s[pp-1]=np.sum(a[:pp])
        for i in range(pp,len(a)): s[i]=s[i-1]-s[i-1]/pp+a[i]
        return s
    at=sm(tr,p); ps=sm(pd_,p); ms=sm(md_,p)
    pdi=100*ps/np.where(at==0,1,at); mdi=100*ms/np.where(at==0,1,at)
    dx=100*np.abs(pdi-mdi)/np.where((pdi+mdi)==0,1,pdi+mdi)
    return float(np.mean(dx[-p:])) if len(dx)>=p else 20.

def stochrsi(c,rp,kp,dp):
    if len(c)<rp+kp+5: return 50.,50.
    rv=np.array([rsi(c[:i+1],rp) for i in range(rp,len(c))])
    sk=np.full(len(rv),np.nan)
    for i in range(kp-1,len(rv)):
        w=rv[i-kp+1:i+1]; mn,mx=w.min(),w.max()
        sk[i]=0 if mx==mn else (rv[i]-mn)/(mx-mn)*100
    vk=sk[~np.isnan(sk)]
    if len(vk)<1: return 50.,50.
    k=float(vk[-1]); d=float(np.mean(vk[-dp:])) if len(vk)>=dp else k
    return k,d

def zscore(c,p=30):
    if len(c)<p: return 0.
    w=c[-p:]; return float((c[-1]-np.mean(w))/(np.std(w)+1e-9))

def compute(df,p):
    if df.empty or len(df)<60: return {}
    c=df["Close"].astype(float).values; h=df["High"].astype(float).values
    l=df["Low"].astype(float).values;   v=df["Volume"].astype(float).values
    rv=rsi(c,p["rsi"]); sk,sd=stochrsi(c,p["rsi"],p["sk"],p["sd"])
    f,sl,sg=p["macd"]; ml,si,mh=macd(c,f,sl,sg)
    mhv=float(mh[-1]) if not np.isnan(mh[-1]) else 0.
    mhp=float(mh[-2]) if len(mh)>1 and not np.isnan(mh[-2]) else mhv
    bu,bm,bl=bb(c,20,p["bbs"])
    s80=sma(c,80); s200=sma(c,200); e20=ema(c,20)
    at=atr(h,l,c,p["atr"])
    va=at[~np.isnan(at)]; atv=float(at[-1]) if not np.isnan(at[-1]) else 0.
    ata=float(np.mean(va[-30:])) if len(va)>=30 else atv
    adv=adx(h,l,c,p["adx"])
    va2=float(np.mean(v[-20:])) if len(v)>=20 else float(np.mean(v))
    vs=float(v[-1])/va2 if va2>0 else 1.
    zs=zscore(c,30)
    px=float(c[-1]); pc=(px-float(c[-2]))/float(c[-2])*100 if len(c)>1 else 0.
    w1=(px-float(c[-6]))/float(c[-6])*100 if len(c)>6 else 0.
    rl5=float(np.min(l[-5:])); pl5=float(np.min(l[-10:-5])) if len(l)>=10 else rl5
    rsi_idx=range(p["rsi"],len(c))
    rsi_arr=np.array([rsi(c[:i+1],p["rsi"]) for i in rsi_idx])
    return {
        "price":px,"price_chg":pc,"chg_1w":w1,
        "rsi":rv,"stoch_k":sk,"stoch_d":sd,
        "macd_hist":mhv,"macd_hist_prev":mhp,
        "bb_upper":float(bu[-1]) if not np.isnan(bu[-1]) else px,
        "bb_lower":float(bl[-1]) if not np.isnan(bl[-1]) else px,
        "sma80":float(s80[-1]) if not np.isnan(s80[-1]) else px,
        "sma200":float(s200[-1]) if not np.isnan(s200[-1]) else px,
        "ema20":float(e20[-1]) if not np.isnan(e20[-1]) else px,
        "atr":atv,"atr_avg":ata,"adx":adv,"vol_spike":vs,"z_score":zs,
        "higher_low":rl5>pl5,
        "_c":c,"_h":h,"_l":l,"_idx":df.index,
        "_s80":s80,"_s200":s200,"_bu":bu,"_bl":bl,
        "_rsi_arr":rsi_arr,"_rsi_start":p["rsi"],"_mh":mh,
    }

# ── SIGNALS ──
def sg_googl(i): return {"mul":1,"txt":"✅ 고정 매수 (DCA 앵커)","amt":600}

def sg_iren(i):
    rv=i.get("rsi",50); at=i.get("atr",0); ata=i.get("atr_avg",1)
    px=i.get("price",0); e20=i.get("ema20",px); mh=i.get("macd_hist",0)
    mhp=i.get("macd_hist_prev",mh); sk=i.get("stoch_k",50); sd=i.get("stoch_d",50)
    hl=i.get("higher_low",False); pc=i.get("price_chg",0)
    ax=(at>ata*2) if ata>0 else False
    # RSI 기반 기본 배율
    if rv>60 or ax:
        mx,txt=0,"❌ 매수 중단 (RSI 과열)" if rv>60 else "❌ 변동성 과다"
    elif rv<25 and pc<=-10:
        mx,txt=3,"🔥 3배 매수 (RSI<25+폭락)"
    elif rv<35:
        mx,txt=2,"⚡ 2배 매수 (RSI<35)"
    else:
        mx,txt=1,"✅ 기본 매수"
    # 불타기: 2개↑ 충족 시 배율 1단계 업 (예:에A개서 B배, 최대 3배)
    ign={"MA20 위 회복":px>e20,"MACD 히스토 상승":mh>mhp,"Higher Low":hl,"StochRSI 20→40":sk>40 and sk>sd and sk>20}
    ic=sum(ign.values())
    if ic>=2 and mx>0:
        mx=min(mx+1,3)
        txt=txt+" 🔥불타기("+str(ic)+"/4)\u2192"+str(mx)+"배"
    return {"mul":mx,"txt":txt,"amt":min(800*mx,BUDGET-600),"ign":ign,"ic":ic}

def sg_nxe(i,u):
    if u>82: mx,txt=0,f"❌ 매수 중단 (${u:.0f})"
    elif u>=75: mx,txt=1,f"✅ 기본 매수 (${u:.0f})"
    elif u>=70: mx,txt=2,f"⚡ 2배 매수 (${u:.0f})"
    else: mx,txt=3,f"🔥 3배 매수 (${u:.0f}<$70)"
    return {"mul":mx,"txt":txt,"amt":200*mx}

def sg_ionq(i):
    rv=i.get("rsi",50)
    if rv>65: mx,txt=0,f"❌ 매수 중단 (RSI {rv:.0f})"
    elif rv>=45: mx,txt=1,f"✅ 기본 매수 (RSI {rv:.0f})"
    elif rv>=30: mx,txt=2,f"⚡ 2배 매수 (RSI {rv:.0f})"
    else: mx,txt=3,f"🔥 3배 매수 (RSI {rv:.0f})"
    return {"mul":mx,"txt":txt,"amt":100*mx}

def sg_mu(i,ed):
    rv=i.get("rsi",50)
    if rv>65: mx,txt=0,f"❌ 매수 중단 (RSI {rv:.0f})"
    elif rv>=45: mx,txt=1,f"✅ 기본 매수 (RSI {rv:.0f})"
    else: mx,txt=2,f"⚡ 2배 매수 (RSI {rv:.0f})"
    b=300 if(ed and mx>0) else 0
    if b: txt+=" +실적급락$300"
    return {"mul":mx,"txt":txt,"amt":300*mx+b}

def allocate(sigs):
    a={"GOOGL":600}; sp=600
    for t in ["IREN","MU","NXE","IONQ"]:
        amt=sigs[t]["amt"]
        if amt>0 and sp+amt<=BUDGET: a[t]=amt; sp+=amt
        elif amt>0 and sp<BUDGET: a[t]=BUDGET-sp; sp=BUDGET
        else: a[t]=0
    lft=BUDGET-sp
    if lft>0: a["GOOGL"]+=lft
    return a

# ── PORTFOLIO ──
def load_pf():
    d={"holdings":{t:{"shares":0.,"avg_cost":0.} for t in TICKERS},
       "total_invested":0.,"start_date":datetime.now().strftime("%Y-%m-%d"),"uranium":68.,"earn_mu":False}
    if PF_FILE.exists():
        try:
            with open(PF_FILE) as f: x=json.load(f)
            for k,v in d.items():
                if k not in x: x[k]=v
            return x
        except: return d
    return d

def save_pf(p):
    with open(PF_FILE,"w") as f: json.dump(p,f,indent=2,default=str)

@st.cache_data(ttl=300)
def fetch(t,period="1y"):
    try:
        df=yf.download(t,period=period,progress=False,auto_adjust=True)
        if df.empty: return pd.DataFrame()
        df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)  # 1시간 캐시
def fetch_uranium():
    """
    우라늄 현물가 자동 수집
    1순위: UX=F (CME 우라늄 선물, U3O8 $/lb) — 현물가와 거의 동일
    2순위: CCJ(Cameco) 주가 기반 추정
    """
    # UX=F: CME Uranium Futures (U3O8 $/lb)
    try:
        df=yf.download("UX=F",period="5d",progress=False,auto_adjust=True)
        if not df.empty:
            df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
            px=float(df["Close"].dropna().iloc[-1])
            if 20<px<300:
                return round(px,2),"UX=F (CME 우라늄 선물)"
    except: pass
    # 백업: Global X Uranium ETF NAV 기반 (거칠지만 방향성 맞음)
    try:
        df=yf.download("CCJ",period="5d",progress=False,auto_adjust=True)
        if not df.empty:
            df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
            px=float(df["Close"].dropna().iloc[-1])
            # CCJ ≈ 우라늄가 * 0.55 경험적 환산
            est=round(px/0.55,1)
            if 20<est<300:
                return est,"CCJ 기반 추정"
    except: pass
    return None,"자동 수집 실패"

def price_chart(df,t,ind):
    p=IND_P[t]; col=TICKERS[t]["color"]
    df2=df.copy()
    df2.columns=[c[0] if isinstance(c,tuple) else c for c in df2.columns]

    # ── 전체 배열 (지표 계산은 1y 기준)
    full_idx=ind.get("_idx",df2.index)
    ra=ind.get("_rsi_arr",np.array([])); rs=ind.get("_rsi_start",p["rsi"])  # 종목별 RSI period
    mh=ind.get("_mh",np.array([])); s80=ind.get("_s80",np.array([]))
    s200=ind.get("_s200",np.array([])); bu=ind.get("_bu",np.array([])); bl=ind.get("_bl",np.array([]))

    # ── 3개월(63거래일)로 슬라이스
    N=63
    df3=df2.iloc[-N:] if len(df2)>N else df2
    idx=df3.index
    o=df3["Open"].astype(float).values
    h2=df3["High"].astype(float).values
    l2=df3["Low"].astype(float).values
    cl=df3["Close"].astype(float).values

    # 보조지표도 3개월치만
    def tail(arr): return arr[-N:] if len(arr)>=N else arr
    s80_=tail(s80); s200_=tail(s200); bu_=tail(bu); bl_=tail(bl); mh_=tail(mh)

    # RSI 배열 — rsi_start 이후부터 시작하므로 별도 처리
    rsi_full_idx=full_idx[rs:] if len(full_idx)>rs else full_idx
    if len(ra)>0 and len(rsi_full_idx)==len(ra):
        ra_=ra[-N:]; ri_=rsi_full_idx[-N:]
    else:
        ra_=np.array([]); ri_=np.array([])

    # ── 종목별 RSI 기준선 (신호 구간)
    rsi_p=IND_P[t]["rsi"]
    if t=="IREN":
        # STOP>60, 기본1×:35~60, 2×:<35, 3×:<25+폭락
        zones=[
            (0,25,"rgba(62,207,142,0.18)","🔥 3× 구간"),
            (25,35,"rgba(62,207,142,0.10)","⚡ 2× 구간"),
            (35,60,"rgba(79,163,224,0.08)","✅ 1× 구간"),
            (60,100,"rgba(224,92,92,0.10)","❌ STOP"),
        ]
        thresholds=[(25,"#3ecf8e","25"),(35,"#c9a84c","35"),(60,"#e05c5c","60")]
    elif t=="IONQ":
        zones=[
            (0,30,"rgba(62,207,142,0.18)","🔥 3×"),
            (30,45,"rgba(62,207,142,0.10)","⚡ 2×"),
            (45,65,"rgba(79,163,224,0.08)","✅ 1×"),
            (65,100,"rgba(224,92,92,0.10)","❌ STOP"),
        ]
        thresholds=[(30,"#3ecf8e","30"),(45,"#c9a84c","45"),(65,"#e05c5c","65")]
    elif t=="MU":
        zones=[
            (0,45,"rgba(62,207,142,0.12)","⚡ 2×"),
            (45,65,"rgba(79,163,224,0.08)","✅ 1×"),
            (65,100,"rgba(224,92,92,0.10)","❌ STOP"),
        ]
        thresholds=[(45,"#c9a84c","45"),(65,"#e05c5c","65")]
    else:  # GOOGL, NXE
        zones=[]; thresholds=[]

    fig=make_subplots(
        rows=3,cols=1,row_heights=[.52,.26,.22],
        shared_xaxes=True,vertical_spacing=.02,
        subplot_titles=("","RSI("+str(rsi_p)+") — 매수 신호 구간","MACD 히스토그램"))

    # ── 캔들
    fig.add_trace(go.Candlestick(x=idx,open=o,high=h2,low=l2,close=cl,
        increasing=dict(line=dict(color=col)),
        decreasing=dict(line=dict(color="#e05c5c")),
        name=t),row=1,col=1)

    # MA
    if len(s80_)==len(idx) and not np.all(np.isnan(s80_)):
        fig.add_trace(go.Scatter(x=idx,y=s80_,name="SMA80",line=dict(color="#c9a84c",width=1.2,dash="dot")),row=1,col=1)
    if len(s200_)==len(idx) and not np.all(np.isnan(s200_)):
        fig.add_trace(go.Scatter(x=idx,y=s200_,name="SMA200",line=dict(color="#9b6dff",width=1.2,dash="dot")),row=1,col=1)

    # BB
    if len(bu_)==len(idx):
        fig.add_trace(go.Scatter(x=idx,y=bu_,line=dict(color="rgba(79,163,224,0.25)",width=1),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=idx,y=bl_,line=dict(color="rgba(79,163,224,0.25)",width=1),
            fill="tonexty",fillcolor="rgba(79,163,224,0.06)",showlegend=False),row=1,col=1)

    # ── RSI + 신호 구간 색칠
    if len(ra_)>0 and len(ri_)==len(ra_):
        # 배경 존
        for y0,y1,fc,label in zones:
            fig.add_hrect(y0=y0,y1=y1,fillcolor=fc,line_width=0,row=2,col=1,
                annotation_text=label,
                annotation_position="left",
                annotation_font=dict(size=8,color="rgba(255,255,255,0.5)"))
        # RSI 선
        fig.add_trace(go.Scatter(x=ri_,y=ra_,name=f"RSI({rsi_p})",
            line=dict(color=col,width=2)),row=2,col=1)
        # 기준선 + 라벨
        for yv,lc,label in thresholds:
            fig.add_hline(y=yv,line_color=lc,line_dash="dash",line_width=1,row=2,col=1)
            fig.add_annotation(x=ri_[-1],y=yv,text=f" {label}",
                font=dict(size=9,color=lc),showarrow=False,xanchor="left",row=2,col=1)

    # ── MACD 히스토그램
    if len(mh_)==len(idx):
        hc=["#3ecf8e" if(not np.isnan(v) and v>=0) else "#e05c5c" for v in mh_]
        fig.add_trace(go.Bar(x=idx,y=mh_,marker_color=hc,opacity=.85,name="MACD Hist"),row=3,col=1)
        fig.add_hline(y=0,line_color="rgba(255,255,255,0.2)",line_width=1,row=3,col=1)

    fig.update_layout(
        height=560,paper_bgcolor="#0f1620",plot_bgcolor="#070a0f",
        font=dict(family="IBM Plex Mono",size=10,color="#6b7a99"),
        margin=dict(l=0,r=40,t=30,b=0),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=9),x=0,y=1),
        xaxis_rangeslider_visible=False)
    for i in range(1,4):
        fig.update_xaxes(gridcolor="#1e2a3a",row=i,col=1)
        fig.update_yaxes(gridcolor="#1e2a3a",row=i,col=1)
    # RSI y축 고정
    fig.update_yaxes(range=[0,100],row=2,col=1)
    return fig

def pie_chart(wts,vals):
    lb=list(wts.keys()); vl=[vals.get(t,0) for t in lb]; cl=[TICKERS[t]["color"] for t in lb]
    fig=go.Figure(go.Pie(labels=lb,values=vl,hole=.65,marker=dict(colors=cl,line=dict(color="#070a0f",width=2)),
        textinfo="label+percent",textfont=dict(family="IBM Plex Mono",size=11),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>"))
    fig.update_layout(paper_bgcolor="#0f1620",font=dict(color="#e8e6f0"),margin=dict(l=0,r=0,t=0,b=0),height=230,showlegend=False)
    return fig

# ── INIT ──
pf=load_pf()
st.markdown('<div class="hd"><h1>⚔ 이세계 DCA ⚔</h1><p>ADAPTIVE DCA SYSTEM · TARGET $500,000 · 36 MONTHS</p></div>',unsafe_allow_html=True)

# 데이터를 sidebar보다 먼저 fetch (sidebar에서 prices 사용하므로)
with st.spinner("시장 데이터 로딩 중..."):
    mdata,inds,prices={},{},{}
    for t in TICKERS:
        df=fetch(t); mdata[t]=df
        if not df.empty:
            ind=compute(df,IND_P[t]); inds[t]=ind; prices[t]=ind.get("price",0)
        else: inds[t]={}; prices[t]=0
    # 우라늄 현물가 자동 수집
    u_auto,u_src=fetch_uranium()

with st.sidebar:
    st.markdown('<div class="st2">⚙ 설정</div>',unsafe_allow_html=True)
    # 우라늄 자동수집 — 범위 강제 클램프 후 사용
    saved_u=float(pf.get("uranium",68.))
    if u_auto and 30<=u_auto<=148:
        u_default=u_auto
        st.markdown(f'<div style="font-size:.65rem;color:#3ecf8e;margin-bottom:.3rem">🤖 자동: ${u_auto:.1f}/lb ({u_src})</div>',unsafe_allow_html=True)
    else:
        u_default=min(max(saved_u,30.),148.)  # 항상 30~148 범위
        msg=f"자동수집 실패 — 저장값 ${saved_u:.1f}" if not u_auto else f"범위초과(${u_auto}) — 저장값 사용"
        st.markdown(f'<div style="font-size:.65rem;color:#e08c3c;margin-bottom:.3rem">⚠️ {msg}</div>',unsafe_allow_html=True)
    uranium=st.number_input("우라늄 ($/lb) 수동보정",30.,148.,float(u_default),.5,
        help="자동값 이상할 때만 조정")
    pf["uranium"]=uranium
    earn_mu=st.checkbox("MU 실적 후 -10% 급락?",value=pf.get("earn_mu",False))
    pf["earn_mu"]=earn_mu
    st.markdown("---")
    st.markdown('<div class="st2">📁 포트폴리오</div>',unsafe_allow_html=True)
    with st.expander("보유 주식 입력"):
        for t in TICKERS:
            h=pf["holdings"][t]
            px_now=prices.get(t,0)
            st.markdown(f'<div style="font-size:.75rem;color:#c9a84c;margin-top:.7rem;font-family:Cinzel,serif;border-bottom:1px solid #1e2a3a;padding-bottom:2px">{t} · 현재가 ${px_now:,.2f}</div>',unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1:
                h["shares"]=st.number_input(
                    "보유 주수",0.,
                    value=round(float(h["shares"]),2),
                    step=0.01,format="%.2f",
                    key=f"sh{t}")
            with c2:
                h["avg_cost"]=st.number_input(
                    "평균단가 ($)",0.,
                    value=float(h["avg_cost"]) if h["avg_cost"]>0 else float(px_now),
                    step=0.01,format="%.2f",
                    key=f"a{t}")
            # 미리보기
            cur_val=h["shares"]*px_now
            pnl_pct=(px_now-h["avg_cost"])/h["avg_cost"]*100 if h["avg_cost"]>0 else 0.
            col_c="#3ecf8e" if pnl_pct>=0 else "#e05c5c"
            if h["shares"]>0:
                st.markdown(f'<div style="font-size:.65rem;color:{col_c};margin-bottom:.2rem">평가액 ${cur_val:,.0f} ({pnl_pct:+.1f}%)</div>',unsafe_allow_html=True)
        pf["total_invested"]=sum(h["shares"]*h["avg_cost"] for h in pf["holdings"].values())
        pf["start_date"]=st.text_input("시작일 (YYYY-MM-DD)",pf.get("start_date",datetime.now().strftime("%Y-%m-%d")))
    if st.button("💾 저장"): save_pf(pf); st.success("저장됨!")
    if st.button("🔄 새로고침"): st.cache_data.clear(); st.rerun()
    st.markdown(f'<div style="color:#6b7a99;font-size:.65rem;margin-top:1rem">{datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</div>',unsafe_allow_html=True)

sigs={
    "GOOGL":sg_googl(inds.get("GOOGL",{})),
    "IREN": sg_iren(inds.get("IREN",{})),
    "NXE":  sg_nxe(inds.get("NXE",{}),uranium),
    "IONQ": sg_ionq(inds.get("IONQ",{})),
    "MU":   sg_mu(inds.get("MU",{}),earn_mu),
}
alloc=allocate(sigs)

hl=pf["holdings"]
pv=sum(hl[t]["shares"]*prices.get(t,0) for t in TICKERS)
inv=pf.get("total_invested",0); pnl=pv-inv; pnl_p=pnl/inv*100 if inv>0 else 0; gp=pv/TARGET*100
try: start=datetime.strptime(pf.get("start_date",datetime.now().strftime("%Y-%m-%d")),"%Y-%m-%d")
except: start=datetime.now()
elapsed=max((datetime.now()-start).days/30,.1); remaining=max(MONTHS-elapsed,0)
pvt={t:hl[t]["shares"]*prices.get(t,0) for t in TICKERS}
cw={t:v/pv if pv>0 else 0 for t,v in pvt.items()}

ta0,ta1,ta2,ta3,ta4,ta5=st.tabs(["🎯 오늘 살까?","📡 신호 현황","📊 종목 분석","📅 이번달 계획","⚖ 리밸런싱","🏆 목표 추적"])
ta0,ta1,ta2,ta3=st.tabs(["🎯 오늘 살까?","📊 종목 분석","⚖ 리밸런싱","🏆 목표 추적"])

with ta0:
    st.markdown('<div class="st2">🎯 오늘의 매수 결정</div>',unsafe_allow_html=True)

    today=datetime.now()
    is_month_start=today.day<=7  # 1~7일 = 월초 GOOGL 매수 타이밍

    def buy_decision(t, ind, sg, alloc_amt, uranium=68.):
        """
        오늘 살까? 3단계 판정:
        🟢 지금 사세요 / 🟡 관망 (조건 안좋음) / 🔴 오늘은 패스
        """
        rv   = ind.get("rsi",50)
        pc   = ind.get("price_chg",0)    # 오늘 변동률
        zs   = ind.get("z_score",0)
        mh   = ind.get("macd_hist",0)
        mhp  = ind.get("macd_hist_prev",mh)
        atr  = ind.get("atr",0)
        atr_a= ind.get("atr_avg",1)
        adv  = ind.get("adx",20)
        chg1w= ind.get("chg_1w",0)
        sk   = ind.get("stoch_k",50)
        mul  = sg.get("mul",0)

        if t=="GOOGL":
            if is_month_start:
                return "🟢","지금 사세요","월초(1~7일) — 고정 DCA 집행 타이밍","$600 매수"
            else:
                return "🟡","월말 대기","GOOGL은 매월 1~7일에 매수. 아직 기다리세요","—"

        if t=="IREN":
            # 과열 판단
            if rv>60 or (atr>atr_a*2 and atr_a>0):
                return "🔴","오늘은 패스","RSI 과열(>60) 또는 변동성 폭발 — 눌림 기다려요","매수 금지"
            # 강한 매수 (2~3배 구간)
            if rv<35:
                reasons=[]
                if zs<-1.5: reasons.append(f"Z-Score {zs:+.1f} 저평가")
                if mh>mhp:  reasons.append("MACD 반등 중")
                if chg1w<-5:reasons.append(f"1주 -{abs(chg1w):.0f}% 낙폭")
                r=", ".join(reasons) if reasons else "RSI 과매도"
                return "🟢","지금 사세요 ⚡",f"RSI {rv:.0f} — {r}",f"${alloc_amt:,.0f} ({mul}×)"
            # 불타기 조건 충족
            ic=sg.get("ic",0)
            if ic>=2 and rv<60:
                return "🟢","지금 사세요 🔥",f"불타기 {ic}/4 충족 — 모멘텀 확인됨",f"${alloc_amt:,.0f} ({mul}×)"
            # 중립 구간
            if 35<=rv<=50:
                return "🟡","조금 기다려요",f"RSI {rv:.0f} 중립 — 더 눌리면 더 좋음. 급하지 않으면 대기","$800 (1×)"
            if 50<rv<=60:
                return "🟡","관망","RSI {:.0f} 중상단 — 오늘보단 내일이 나을 수도".format(rv),"—"

        if t=="NXE":
            if uranium>82:
                return "🔴","오늘은 패스",f"우라늄 ${uranium:.0f} > $82 — 매수 구간 아님","매수 금지"
            if uranium<70:
                return "🟢","지금 사세요 🔥",f"우라늄 ${uranium:.0f} < $70 — 3배 구간. 사이클 바닥",f"${alloc_amt:,.0f} (3×)"
            if uranium<75:
                return "🟢","지금 사세요",f"우라늄 ${uranium:.0f} 2배 구간",f"${alloc_amt:,.0f} (2×)"
            return "🟡","기본 매수",f"우라늄 ${uranium:.0f} 1배 구간 — 급하진 않음",f"${alloc_amt:,.0f} (1×)"

        if t=="IONQ":
            if rv>65:
                return "🔴","오늘은 패스",f"RSI {rv:.0f} 과열 — 조정 기다려요","매수 금지"
            if rv<30:
                return "🟢","지금 사세요 🔥",f"RSI {rv:.0f} 극과매도 — 3배 구간",f"${alloc_amt:,.0f}"
            if rv<45:
                return "🟢","지금 사세요",f"RSI {rv:.0f} 매수 구간",f"${alloc_amt:,.0f}"
            return "🟡","관망",f"RSI {rv:.0f} 중립 — IONQ는 더 눌릴 때 사는 게 유리","—"

        if t=="MU":
            if rv>65:
                return "🔴","오늘은 패스",f"RSI {rv:.0f} 과열","매수 금지"
            if rv<45:
                return "🟢","지금 사세요",f"RSI {rv:.0f} — AI 메모리 사이클 눌림목",f"${alloc_amt:,.0f}"
            return "🟡","관망",f"RSI {rv:.0f} 중립 — 실적발표 전후 급락 시 매수 기회","—"

        return "🟡","관망","—","—"

    # ── 판정 실행
    decisions={}
    for t,info in TICKERS.items():
        ind=inds.get(t,{}); sg=sigs[t]; amt=alloc.get(t,0)
        emoji,label,reason,action=buy_decision(t,ind,sg,amt,uranium)
        decisions[t]=(emoji,label,reason,action)

    # ── 오늘 총 추천 매수액
    today_buy=0
    for t,(em,lb,rs,ac) in decisions.items():
        if em=="🟢" and "$" in ac:
            try: today_buy+=int(ac.replace("$","").replace(",","").split()[0])
            except: pass

    # ── 요약 카드
    green_cnt=sum(1 for em,_,_,_ in decisions.values() if em=="🟢")
    red_cnt  =sum(1 for em,_,_,_ in decisions.values() if em=="🔴")
    c1,c2,c3=st.columns(3)
    with c1:
        gc="#3ecf8e" if green_cnt>=2 else "#c9a84c"
        st.markdown(f'<div class="mb card-g"><div class="ml">매수 추천</div><div class="mv" style="color:{gc}">{green_cnt}종목</div><div class="ms">오늘 사세요</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mb"><div class="ml">오늘 예상 지출</div><div class="mv">${today_buy:,.0f}</div><div class="ms">/ 월 $2,000</div></div>',unsafe_allow_html=True)
    with c3:
        sc2="#e05c5c" if red_cnt>=3 else "#c9a84c" if red_cnt>=1 else "#3ecf8e"
        market_feel="과열 주의" if red_cnt>=3 else "혼조" if red_cnt>=1 else "매수 우호적"
        st.markdown(f'<div class="mb"><div class="ml">시장 온도</div><div class="mv" style="color:{sc2}">{market_feel}</div><div class="ms">{red_cnt}종목 과열</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── 종목별 결정 카드
    priority_order=["IREN","GOOGL","MU","NXE","IONQ"]  # 수익 기여도 순
    for t in priority_order:
        info=TICKERS[t]; em,lb,rs,ac=decisions[t]
        ind=inds.get(t,{}); rv=ind.get("rsi",0); pc=ind.get("price_chg",0)
        px=prices.get(t,0)

        if em=="🟢":
            bg="#0a2a0a"; border="#3ecf8e"; tc="#3ecf8e"
        elif em=="🔴":
            bg="#2a0a0a"; border="#e05c5c"; tc="#e05c5c"
        else:
            bg="#1a1a0a"; border="#c9a84c"; tc="#c9a84c"

        pc_c="#3ecf8e" if pc>=0 else "#e05c5c"
        pc_s="▲" if pc>=0 else "▼"
        rsi_c="#e05c5c" if rv>65 else "#e08c3c" if rv>50 else "#3ecf8e" if rv<35 else "#4fa3e0"

        st.markdown(f'''<div style="background:{bg};border:1px solid {border};border-radius:8px;padding:1rem;margin-bottom:.6rem">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
    <div>
      <span style="font-family:Cinzel,serif;font-size:1rem;color:#e8e6f0">{t}</span>
      <span style="font-size:.65rem;color:#6b7a99;margin-left:.5rem">{info["name"]}</span>
    </div>
    <div style="text-align:right">
      <span style="font-size:.7rem;color:{info["color"]}">${px:,.2f}</span>
      <span style="font-size:.65rem;color:{pc_c};margin-left:.3rem">{pc_s}{abs(pc):.1f}%</span>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="font-size:1.1rem">{em}</span>
      <span style="font-size:.9rem;color:{tc};font-weight:600;margin-left:.3rem">{lb}</span>
    </div>
    <div style="text-align:right">
      <span style="background:#0f1620;color:{tc};border:1px solid {border};padding:2px 10px;border-radius:4px;font-size:.75rem;font-family:Cinzel,serif">{ac}</span>
    </div>
  </div>
  <div style="margin-top:.5rem;font-size:.7rem;color:#9ba8bb;border-top:1px solid {border}33;padding-top:.4rem">
    💬 {rs} &nbsp;·&nbsp; RSI <span style="color:{rsi_c}">{rv:.0f}</span>
  </div>
</div>''',unsafe_allow_html=True)

    # ── IREN 특별 설명
    st.markdown("---")
    iren_ind=inds.get("IREN",{}); iren_rv=iren_ind.get("rsi",50)
    iren_chg=iren_ind.get("price_chg",0); iren_1w=iren_ind.get("chg_1w",0)
    st.markdown('<div class="st2">⚡ IREN 매수 전략 가이드</div>',unsafe_allow_html=True)
    st.markdown(f'''<div class="card">
<div style="font-size:.78rem;line-height:2">
  <b style="color:#c9a84c">IREN은 모멘텀 + 역추세 혼합 전략</b><br>
  📌 <b>언제 사야 하나?</b><br>
  &nbsp;&nbsp;• RSI &lt; 35 → <span style="color:#3ecf8e">⚡ 2배 매수</span> — 과매도 구간, 평균단가 낮추기 최적<br>
  &nbsp;&nbsp;• RSI &lt; 25 + 당일 -10% → <span style="color:#3ecf8e">🔥 3배 매수</span> — 공황 매수, 최고 기회<br>
  &nbsp;&nbsp;• 불타기 2개↑ + RSI &lt; 60 → <span style="color:#3ecf8e">배율 1단계 UP</span> — 추세 전환 확인<br>
  📌 <b>언제 기다려야 하나?</b><br>
  &nbsp;&nbsp;• RSI &gt; 60 → <span style="color:#e05c5c">❌ 과열, 무조건 패스</span><br>
  &nbsp;&nbsp;• RSI 50~60 → <span style="color:#c9a84c">🟡 오늘보단 내일</span> — 더 눌릴 때 사는 게 유리<br>
  📊 <b>현재 상태:</b> RSI <span style="color:{"#3ecf8e" if iren_rv<35 else "#e05c5c" if iren_rv>60 else "#c9a84c"}">{iren_rv:.0f}</span>
  &nbsp;·&nbsp; 오늘 <span style="color:{"#3ecf8e" if iren_chg>=0 else "#e05c5c"}">{iren_chg:+.1f}%</span>
  &nbsp;·&nbsp; 1주 <span style="color:{"#3ecf8e" if iren_1w>=0 else "#e05c5c"}">{iren_1w:+.1f}%</span>
</div></div>''',unsafe_allow_html=True)


with ta1:
    sel=st.selectbox("종목 선택",list(TICKERS.keys()),format_func=lambda x:f"{x} — {TICKERS[x]['name']}")
    df=mdata.get(sel,pd.DataFrame()); ind=inds.get(sel,{}); p=IND_P[sel]
    if not df.empty and ind:
        ms2=[
            ("RSI",       f"{ind.get('rsi',0):.1f}",      f"기간 {p['rsi']}"),
            ("StochRSI K",f"{ind.get('stoch_k',0):.1f}",  f"K={p['sk']}/D={p['sd']}"),
            ("MACD Hist", f"{ind.get('macd_hist',0):+.3f}",f"({p['macd'][0]},{p['macd'][1]},{p['macd'][2]})"),
            ("Z-Score",   f"{ind.get('z_score',0):+.2f}",  "기간 30"),
            ("ATR",       f"{ind.get('atr',0):.2f}",       f"기간 {p['atr']}"),
            ("ADX",       f"{ind.get('adx',0):.1f}",       f"기간 {p['adx']}"),
            ("BB σ",      f"{p['bbs']}σ",                  "볼린저밴드 폭"),
            ("SMA80",     f"${ind.get('sma80',0):,.2f}",   "중기 추세선"),
            ("SMA200",    f"${ind.get('sma200',0):,.2f}",  "장기 추세선"),
            ("1주 수익률",f"{ind.get('chg_1w',0):+.1f}%",  "5거래일"),
        ]
        cs2=st.columns(5)
        for i,(lb,vl,sb) in enumerate(ms2):
            with cs2[i%5]: st.markdown(f'<div class="mb" style="margin-bottom:.5rem"><div class="ml">{lb}</div><div style="font-size:1rem;color:{TICKERS[sel]["color"]};font-family:Cinzel,serif">{vl}</div><div class="ms">{sb}</div></div>',unsafe_allow_html=True)
        st.plotly_chart(price_chart(df,sel,ind),use_container_width=True)
    else: st.info("데이터 로딩 중...")
    # 파라미터 요약 테이블
    st.markdown("---")
    st.markdown('<div class="st2">📋 전체 종목 지표 파라미터 (미세튜닝 최종값)</div>',unsafe_allow_html=True)
    param_rows=[]
    for tk,pp in IND_P.items():
        param_rows.append({
            "종목":tk,
            "RSI기간":pp["rsi"],
            "StochRSI K/D":f"{pp['sk']}/{pp['sd']}",
            "MACD":f"({pp['macd'][0]},{pp['macd'][1]},{pp['macd'][2]})",
            "BB σ":pp["bbs"],
            "ATR":pp["atr"],
            "ADX":pp["adx"],
            "MA":"SMA80 / SMA200",
            "Z-Score기간":30,
            "거래량배율":"2.0× (IREN) / 1.5×",
        })
    st.dataframe(pd.DataFrame(param_rows),use_container_width=True,hide_index=True)

# ── TAB 2: 리밸런싱 ──
with ta2:
    st.markdown('<div class="st2">⚖ 분기별 리밸런싱</div>',unsafe_allow_html=True)
    if pv>0:
        c1,c2=st.columns(2)
        with c1: st.plotly_chart(pie_chart(cw,pvt),use_container_width=True)
        with c2:
            st.markdown('<div class="st2">비중 비교</div>',unsafe_allow_html=True)
            for t,info in TICKERS.items():
                cur=cw.get(t,0)*100; tgt=info["weight"]*100; diff=cur-tgt
                dc="#e05c5c" if abs(diff)>5 else "#c9a84c" if abs(diff)>2 else "#6b7a99"
                st.markdown(f'<div style="margin-bottom:.5rem"><div style="display:flex;justify-content:space-between;font-size:.72rem;margin-bottom:2px"><span style="color:{info["color"]}">{t}</span><span style="color:{dc}">{cur:.1f}% / 목표 {tgt:.0f}% ({diff:+.1f}%)</span></div><div style="background:#1a2233;border-radius:3px;height:7px"><div style="width:{min(cur,100):.0f}%;height:7px;background:{info["color"]};border-radius:3px"></div></div></div>',unsafe_allow_html=True)

        st.markdown("---")
        # ── 현황 테이블
        rw2=[]
        for t,info in TICKERS.items():
            h=pf["holdings"][t]; px3=prices.get(t,0); val=h["shares"]*px3; avg=h["avg_cost"]
            pp=(px3-avg)/avg*100 if avg>0 else 0
            rw2.append({"종목":t,"주수":f"{h['shares']:.4f}","평균단가":f"${avg:,.2f}","현재가":f"${px3:,.2f}","평가액":f"${val:,.0f}","수익률":f"{pp:+.1f}%","현재비중":f"{cw.get(t,0)*100:.1f}%","목표":f"{info['weight']*100:.0f}%"})
        st.dataframe(pd.DataFrame(rw2),use_container_width=True,hide_index=True)

        st.markdown("---")
        st.markdown('<div class="st2">🧮 리밸런싱 추천 계산기</div>',unsafe_allow_html=True)
        st.markdown('<div class="info">💡 원칙: <b>매수 우선</b>으로 비중 조정. 매도는 세금 최소화를 위해 꼭 필요한 경우만.</div>',unsafe_allow_html=True)

        extra_budget = st.number_input("추가 투입 가능 금액 ($)", min_value=0., value=float(BUDGET), step=100., key="rebal_budget",
            help="이번 달 DCA 예산 또는 추가 투입금. 이 금액으로 매수 비중 조정 우선 시도.")

        if st.button("⚖ 리밸런싱 추천 계산", key="rebal_btn"):
            st.session_state["show_rebal"] = True

        if st.session_state.get("show_rebal", False):
            # ── 리밸런싱 계산 엔진
            # 목표 비중 기준 각 종목의 이상적 평가액
            target_vals = {t: pv * info["weight"] for t,info in TICKERS.items()}
            cur_vals    = {t: pvt.get(t,0) for t in TICKERS}
            diffs       = {t: target_vals[t]-cur_vals[t] for t in TICKERS}  # +면 부족, -면 초과

            # 1단계: 부족한 종목을 extra_budget으로 매수
            buy_orders  = {}
            sell_orders = {}
            remaining_budget = extra_budget
            shortfalls = {t:v for t,v in diffs.items() if v>0}
            surpluses  = {t:-v for t,v in diffs.items() if v<0}

            # 부족분 합계
            total_shortfall = sum(shortfalls.values())

            if total_shortfall > 0 and remaining_budget > 0:
                # 예산 안에서 비율대로 매수
                for t,need in sorted(shortfalls.items(), key=lambda x:-x[1]):
                    buy_amt = min(need, remaining_budget * (need/total_shortfall))
                    buy_amt = min(buy_amt, need)  # 초과 매수 방지
                    if buy_amt > 10:
                        buy_orders[t] = buy_amt
                        remaining_budget -= buy_amt

            # 매수 후 재계산
            new_vals = {t: cur_vals[t]+buy_orders.get(t,0) for t in TICKERS}
            new_total = sum(new_vals.values())
            new_weights = {t: new_vals[t]/new_total if new_total>0 else 0 for t in TICKERS}
            new_diffs = {t: TICKERS[t]["weight"]-new_weights[t] for t in TICKERS}

            # 2단계: 매수 후에도 5% 이상 초과인 종목만 최소 매도
            for t in TICKERS:
                if new_weights.get(t,0) - TICKERS[t]["weight"] > 0.05:  # 5% 이상 초과만
                    excess_val = (new_weights[t] - TICKERS[t]["weight"]) * new_total
                    sell_orders[t] = excess_val

            # ── 결과 표시
            st.markdown("### 📋 추천 액션")

            has_action = False

            # 매수 추천
            if buy_orders:
                st.markdown('<div class="ok" style="margin-bottom:.5rem">✅ <b>매수 추천</b> (비중 부족 → 매수로 조정)</div>',unsafe_allow_html=True)
                for t,amt in sorted(buy_orders.items(), key=lambda x:-x[1]):
                    px_t=prices.get(t,0); sh=amt/px_t if px_t>0 else 0
                    before=cw.get(t,0)*100; after=new_weights.get(t,0)*100
                    info=TICKERS[t]
                    st.markdown(f'''<div style="background:#0a2a0a;border:1px solid #3ecf8e44;border-radius:6px;padding:.8rem;margin-bottom:.4rem;display:flex;justify-content:space-between;align-items:center">
  <div>
    <span style="font-family:Cinzel,serif;color:{info["color"]}">{t}</span>
    <span style="font-size:.7rem;color:#6b7a99;margin-left:.5rem">매수</span><br>
    <span style="font-size:.7rem;color:#9ba8bb">비중 {before:.1f}% → {after:.1f}% (목표 {info["weight"]*100:.0f}%)</span>
  </div>
  <div style="text-align:right">
    <div style="font-family:Cinzel,serif;color:#3ecf8e;font-size:1.1rem">${amt:,.0f}</div>
    <div style="font-size:.7rem;color:#6b7a99">{sh:.4f}주 @ ${px_t:,.2f}</div>
  </div>
</div>''',unsafe_allow_html=True)
                    has_action = True

            # 매도 추천 (최소화)
            if sell_orders:
                st.markdown('<div class="warn" style="margin-top:.5rem;margin-bottom:.5rem">⚠️ <b>매도 필요</b> (매수 후에도 5%↑ 초과 — 세금 고려해 최소 매도)</div>',unsafe_allow_html=True)
                for t,amt in sorted(sell_orders.items(), key=lambda x:-x[1]):
                    px_t=prices.get(t,0); sh=amt/px_t if px_t>0 else 0
                    avg_c=pf["holdings"][t].get("avg_cost",0)
                    gain=(px_t-avg_c)*sh if avg_c>0 else 0
                    tax_est=gain*0.15  # 미국 장기 양도세 추정 (15%)
                    info=TICKERS[t]
                    st.markdown(f'''<div style="background:#2a0a0a;border:1px solid #e05c5c44;border-radius:6px;padding:.8rem;margin-bottom:.4rem">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="font-family:Cinzel,serif;color:{info["color"]}">{t}</span>
      <span style="font-size:.7rem;color:#6b7a99;margin-left:.5rem">매도</span>
    </div>
    <div style="text-align:right">
      <div style="font-family:Cinzel,serif;color:#e05c5c;font-size:1.1rem">${amt:,.0f}</div>
      <div style="font-size:.7rem;color:#6b7a99">{sh:.4f}주</div>
    </div>
  </div>
  <div style="font-size:.68rem;color:#e08c3c;margin-top:.3rem">⚠️ 예상 세금(장기 15%): ~${tax_est:,.0f} — 가능하면 매수로만 조정 권장</div>
</div>''',unsafe_allow_html=True)
                    has_action = True

            if not has_action:
                st.markdown('<div class="ok">✅ 현재 비중이 목표 범위 내 — 리밸런싱 불필요</div>',unsafe_allow_html=True)

            # 리밸런싱 후 예상 비중
            st.markdown("---")
            st.markdown('<div class="st2">📊 리밸런싱 후 예상 비중</div>',unsafe_allow_html=True)
            for t,info in TICKERS.items():
                cur=cw.get(t,0)*100; aft=new_weights.get(t,0)*100; tgt=info["weight"]*100
                st.markdown(f'<div style="margin-bottom:.4rem"><div style="display:flex;justify-content:space-between;font-size:.7rem;margin-bottom:2px"><span style="color:{info["color"]}">{t}</span><span style="color:#6b7a99">{cur:.1f}% → <b style="color:#e8e6f0">{aft:.1f}%</b> (목표 {tgt:.0f}%)</span></div><div style="background:#1a2233;border-radius:3px;height:6px"><div style="width:{min(aft,100):.0f}%;height:6px;background:{info["color"]};border-radius:3px"></div></div></div>',unsafe_allow_html=True)

    else:
        st.markdown('<div class="info">📌 사이드바에서 보유 주식을 입력하면 활성화됩니다.</div>',unsafe_allow_html=True)

    st.markdown("""<div class="card" style="margin-top:1rem"><div class="st2">📋 리밸런싱 원칙</div>
<table><tr><th>원칙</th><th>설명</th></tr>
<tr><td>매수 우선</td><td>비중 조정은 부족한 종목 매수로 먼저 해결</td></tr>
<tr><td>매도 최소화</td><td>매수 후에도 5%↑ 초과 시에만 최소 매도</td></tr>
<tr><td>세금 고려</td><td>1년 이상 보유 → 장기 양도세(15%) 적용</td></tr>
<tr><td>Rule 1</td><td>IREN >50% → GOOGL 50%/MU 30%/NXE 20%</td></tr>
<tr><td>Rule 2</td><td>GOOGL >40% → IREN 로테이션</td></tr>
<tr><td>Rule 3</td><td>NXE 3개월 음봉 → 비중 +5%</td></tr>
<tr><td>Rule 4</td><td>IONQ >10% → GOOGL 이동</td></tr>
</table></div>""",unsafe_allow_html=True)

with ta3:
    st.markdown('<div class="st2">🎯 $500,000 목표 추적</div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="mb card-g"><div class="ml">현재 포트 가치</div><div class="mv">${pv:,.0f}</div><div class="ms">목표 $500,000</div></div>',unsafe_allow_html=True)
    with c2: gc2="#3ecf8e" if gp>50 else "#c9a84c"; st.markdown(f'<div class="mb"><div class="ml">목표 달성률</div><div class="mv" style="color:{gc2}">{gp:.1f}%</div><div class="ms">{elapsed:.0f}개월 경과</div></div>',unsafe_allow_html=True)
    with c3: pc4="#3ecf8e" if pnl>=0 else "#e05c5c"; st.markdown(f'<div class="mb"><div class="ml">평가 손익</div><div class="mv" style="color:{pc4}">{pnl_p:+.1f}%</div><div class="ms">${pnl:+,.0f}</div></div>',unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="mb"><div class="ml">총 투자금</div><div class="mv" style="color:#4fa3e0">${inv:,.0f}</div><div class="ms">잔여 {remaining:.0f}개월</div></div>',unsafe_allow_html=True)
    gp2=min(gp,100)
    st.markdown(f'<div style="margin:1.5rem 0"><div style="display:flex;justify-content:space-between;font-size:.68rem;color:#6b7a99;margin-bottom:4px"><span>$0</span><span style="color:#c9a84c">${pv:,.0f}</span><span>$500,000</span></div><div style="background:#1a2233;border-radius:6px;height:14px"><div style="width:{gp2:.1f}%;height:14px;background:linear-gradient(90deg,#c9a84c,#f0d080);border-radius:6px"></div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="st2">📈 목표 달성 시뮬레이션</div>',unsafe_allow_html=True)
    def proj(sv,m,r,n=36):
        v=[sv]
        for _ in range(n): v.append(v[-1]*(1+r)+m)
        return v
    mo=list(range(37)); opt=proj(pv,BUDGET,.035); mid=proj(pv,BUDGET,.015); con=proj(pv,BUDGET,.003)
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=mo,y=opt,name="낙관 (월 3.5%)",line=dict(color="#3ecf8e",width=2)))
    fig2.add_trace(go.Scatter(x=mo,y=mid,name="중립 (월 1.5%)",line=dict(color="#c9a84c",width=2)))
    fig2.add_trace(go.Scatter(x=mo,y=con,name="보수 (월 0.3%)",line=dict(color="#4fa3e0",width=2,dash="dot")))
    fig2.add_hline(y=500000,line_color="#e05c5c",line_dash="dash",annotation_text="목표 $500K",annotation_font_color="#e05c5c")
    fig2.add_trace(go.Scatter(x=[0],y=[pv],mode="markers",marker=dict(color="#fff",size=8),name="현재"))
    fig2.update_layout(height=320,paper_bgcolor="#0f1620",plot_bgcolor="#070a0f",font=dict(family="IBM Plex Mono",size=10,color="#6b7a99"),margin=dict(l=0,r=0,t=10,b=0),legend=dict(bgcolor="#0f1620",font=dict(size=10)),xaxis=dict(title="개월",gridcolor="#1e2a3a"),yaxis=dict(title="포트 가치 ($)",gridcolor="#1e2a3a",tickformat="$,.0f"))
    st.plotly_chart(fig2,use_container_width=True)
    c1,c2,c3=st.columns(3)
    for col,(lb,fv,fc) in zip([c1,c2,c3],[("🐂 낙관",opt[-1],"#3ecf8e"),("⚖ 중립",mid[-1],"#c9a84c"),("🐻 보수",con[-1],"#4fa3e0")]):
        hit="✅ 달성" if fv>=TARGET else f"❌ {fv/TARGET*100:.0f}%"
        with col: st.markdown(f'<div class="mb"><div class="ml">{lb}</div><div class="mv" style="color:{fc}">${fv:,.0f}</div><div class="ms">36개월 | {hit}</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="st2">☢ NXE 3개월 연속 음봉 모니터 (Rule 3)</div>',unsafe_allow_html=True)
    ndf=mdata.get("NXE",pd.DataFrame())
    if not ndf.empty and len(ndf)>=60:
        mr=ndf["Close"].resample("ME").last().pct_change().dropna().tail(4)
        neg=0
        for r in mr.values:
            if r<0: neg+=1
            else: neg=0
        sc2="#e05c5c" if neg>=3 else "#c9a84c" if neg>=2 else "#6b7a99"
        mg2="🔥 <b>바닥 시그널!</b> NXE 3개월 연속 음봉 — 비중 +5% 검토" if neg>=3 else f"NXE 연속 음봉: <b style='color:{sc2}'>{neg}개월</b> (3개월 시 비중 +5%)"
        bx2="warn" if neg>=3 else "card"
        st.markdown(f'<div class="{bx2}">{mg2}</div>',unsafe_allow_html=True)
    else: st.markdown('<div class="info">NXE 데이터 로딩 중...</div>',unsafe_allow_html=True)
