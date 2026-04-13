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
    "GOOGL":{"name":"Alphabet",         "weight":.40,"color":"#4fa3e0","base":800},
    "IREN": {"name":"IREN Ltd",          "weight":.40,"color":"#c9a84c","base":800},
    "MU":   {"name":"Micron Technology", "weight":.20,"color":"#3ecf8e","base":400},
}
BUDGET=2000; TARGET=500000; MONTHS=36; PF_FILE=Path("portfolio.json")
IND_P={
    "GOOGL":{"rsi":14,"sk":14,"sd":14,"macd":(12,26,9),"bbs":2.0,"atr":14,"adx":14},
    "IREN": {"rsi":20,"sk":20,"sd":10,"macd":(20,40,9),"bbs":2.5,"atr":20,"adx":20},
    "MU":   {"rsi":20,"sk":20,"sd":10,"macd":(24,52,9),"bbs":2.5,"atr":20,"adx":20},
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
def sg_googl(i): return {"mul":1,"txt":"✅ 고정 매수 (DCA 앵커)","amt":800}

def sg_iren(i):
    rv=i.get("rsi",50); at=i.get("atr",0); ata=i.get("atr_avg",1)
    px=i.get("price",0); e20=i.get("ema20",px); mh=i.get("macd_hist",0)
    mhp=i.get("macd_hist_prev",mh); sk=i.get("stoch_k",50); sd=i.get("stoch_d",50)
    hl=i.get("higher_low",False); pc=i.get("price_chg",0)
    adv=i.get("adx",20); vs=i.get("vol_spike",1.0)
    sma80=i.get("sma80",px); sma200=i.get("sma200",px)
    ax=(at>ata*2) if ata>0 else False

    # ── 장기 추세 판단 (SMA200 기준)
    above_sma200 = px > sma200  # True = 장기 상승추세 / False = 장기 하락추세

    # ── 불장 추세 조건 (RSI 과열이지만 계속 올라가는 경우)
    trend_conds={
        "ADX>30 (강한추세)": adv>30,
        "주가>SMA80 (중기추세위)": px>sma80,
        "MACD 상승중": mh>mhp and mh>0,
        "거래량 1.5× ↑": vs>=1.5,
    }
    trend_cnt=sum(trend_conds.values())
    is_trend_bull=(rv>60 and rv<=75 and trend_cnt>=2 and not ax)

    # ── 배율 결정
    if rv>75 or ax:
        mx=0
        txt="❌ STOP (RSI>75 완전과열)" if rv>75 else "❌ STOP (변동성 폭발)"

    elif is_trend_bull:
        mx=1
        txt=f"📈 추세 매수 (RSI {rv:.0f} 과열이지만 불장 {trend_cnt}/4조건 충족)"

    elif rv<25 and pc<=-10:
        # 극단적 폭락 — 추세 무관하게 3배 (단, SMA200 아래면 1.5배로 제한)
        if above_sma200:
            mx=3
            txt="🔥 3배 매수 (RSI<25 + 당일 폭락 — 장기추세 위, 공황매수 기회)"
        else:
            mx=2  # 추세 하락 중이라 3배 대신 2배
            txt=f"⚡ 2배 매수 (RSI<25 + 폭락이지만 SMA200 아래 — 추세 하락 중, 3배는 위험)"

    elif rv<35:
        # 과매도 — SMA200 위아래로 배율 조정
        if above_sma200:
            mx=2
            txt=f"⚡ 2배 매수 (RSI {rv:.0f} 과매도 + SMA200 위 — 눌림목, 적극 매수)"
        else:
            mx=1
            txt=f"✅ 1배 매수 (RSI {rv:.0f} 과매도지만 SMA200 아래 — 추세 하락 중, 섣불리 2배 금지)"

    elif rv<=60:
        mx=1
        if above_sma200:
            txt=f"✅ 기본 매수 (RSI {rv:.0f}, 장기추세 위)"
        else:
            txt=f"✅ 기본 매수 (RSI {rv:.0f}, 장기추세 아래 — 하락추세 주의)"

    else:
        mx=0
        txt=f"⏸ 대기 (RSI {rv:.0f} 과열, 추세조건 {trend_cnt}/4 미충족)"

    # ── 불타기: 과매도 + SMA200 위일 때만 (하락추세에선 불타기도 금지)
    ign={"MA20 위 회복":px>e20,"MACD 히스토 상승":mh>mhp,"Higher Low":hl,"StochRSI 20→40":sk>40 and sk>sd and sk>20}
    ic=sum(ign.values())
    if ic>=2 and mx>0 and not is_trend_bull and above_sma200:
        mx=min(mx+1,3)
        txt=txt+" 🔥불타기("+str(ic)+"/4)→"+str(mx)+"배"
    elif ic>=2 and mx>0 and not is_trend_bull and not above_sma200:
        txt=txt+" (불타기 조건 충족이지만 SMA200 아래 — 배율 유지)"

    amt=1000 if is_trend_bull else min(800*mx,1000)

    return {"mul":mx,"txt":txt,"amt":amt,"ign":ign,"ic":ic,
            "is_trend":is_trend_bull,"trend_conds":trend_conds,"trend_cnt":trend_cnt,
            "above_sma200":above_sma200}

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

def sg_mu(i,ed,earn_drop_pct=0.):
    """
    MU 3조건 독립 적용:
    조건1: $200 최소 보장 (무조건, IREN 상태 무관)
    조건2: 실적 급락 보너스 (-5%→+$200, -10%→+$400)
    조건3: RSI 과매도 보너스 (<40→+$200, <30→+$400)
    보너스 최대 $400 (중복 상한)
    총 최대 $600 (IREN STOP 시)
    """
    rv=i.get("rsi",50); zs=i.get("z_score",0)

    # 과열 판단
    is_hot=(rv>65 and zs>1.5)

    # 기본 $200 보장 (과열이어도 최소는 삼)
    base=200

    # 실적 급락 보너스
    earn_bonus=0
    earn_txt=""
    if ed:
        if earn_drop_pct<=-10:
            earn_bonus=400; earn_txt=f" +실적급락{earn_drop_pct:.0f}% +$400"
        elif earn_drop_pct<=-5:
            earn_bonus=200; earn_txt=f" +실적급락{earn_drop_pct:.0f}% +$200"
        else:
            earn_bonus=200; earn_txt=" +실적급락 +$200"

    # RSI 과매도 보너스
    rsi_bonus=0
    rsi_txt=""
    if not is_hot:
        if rv<30:
            rsi_bonus=400; rsi_txt=f" +RSI {rv:.0f} 극과매도 +$400"
        elif rv<40:
            rsi_bonus=200; rsi_txt=f" +RSI {rv:.0f} 과매도 +$200"

    # 보너스 상한 $400
    total_bonus=min(earn_bonus+rsi_bonus, 400)
    total_amt=base+total_bonus

    # 상태 텍스트
    if is_hot:
        status_txt=f"🌡️ 과열(RSI {rv:.0f}+Z{zs:+.1f}) — 최소 $200만"
    elif rv<30:
        status_txt=f"🔥 극과매도 RSI {rv:.0f}"
    elif rv<40:
        status_txt=f"⚡ 과매도 RSI {rv:.0f}"
    elif rv<50:
        status_txt=f"✅ 매수구간 RSI {rv:.0f}"
    else:
        status_txt=f"✅ 정기매수 RSI {rv:.0f}"

    full_txt=status_txt+earn_txt+rsi_txt

    return {
        "mul":1,"txt":full_txt,"amt":total_amt,
        "base":base,"earn_bonus":earn_bonus,"rsi_bonus":rsi_bonus,
        "is_hot":is_hot,"is_stop":False,  # MU는 STOP 없음, 최소 $200
    }

def allocate(sigs):
    """
    2단계 분할 집행 전략:
    ─────────────────────────────────────
    1차 집행 (월초 즉시, ~$1,000):
      GOOGL $800 고정
      MU    $200 최소 보장
    ─────────────────────────────────────
    2차 집행 (월중 IREN 최적 타이밍, ~$1,000):
      IREN 신호 나오면 → 그날 하락일에 $1,000 집중
      IREN STOP → MU 보너스 or GOOGL 추가
    ─────────────────────────────────────
    """
    iren_sig=sigs.get("IREN",{}); mu_sig=sigs.get("MU",{})
    iren_can_buy=(iren_sig.get("mul",0)>0)

    # 1차: 고정 집행
    a={"GOOGL":800,"MU":200,"IREN":0}
    # 1차 후 남은 예산
    remaining=BUDGET-800-200  # $1,000 (2차 예산)

    if iren_can_buy:
        # 2차: IREN 신호 강도에 따라 배분
        # 배율 1× → $800, 추세매수/2× → $1,000, 3× → $1,000
        iren_mul=iren_sig.get("mul",1)
        is_trend=iren_sig.get("is_trend",False)
        if iren_mul>=2 or is_trend:
            iren_get=remaining          # 강한 신호: $1,000 전부
        else:
            iren_get=min(800, remaining) # 기본 1×: $800
        a["IREN"]=iren_get
        leftover=remaining-iren_get
        if leftover>0:
            a["GOOGL"]+=leftover         # 남은 건 GOOGL
    else:
        # IREN STOP → 2차 예산을 MU 보너스 or GOOGL
        mu_bonus=mu_sig.get("amt",200)-200  # 보너스 부분만 ($0~$400)
        if mu_bonus>0:
            mu_extra=min(mu_bonus, remaining)
            a["MU"]+=mu_extra
            remaining-=mu_extra
        if remaining>0:
            a["GOOGL"]+=remaining  # 잔액 GOOGL 흡수

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

def calc_portfolio_from_trades(trades, prices):
    """
    매매일지에서 보유 주수/평균단가/총투자금 자동 계산 (FIFO)
    returns: holdings dict, total_invested, start_date
    """
    holdings = {t: {"shares":0.0,"avg_cost":0.0,"total_cost":0.0} for t in TICKERS}
    start_date = None

    for tr in sorted(trades, key=lambda x:x["date"]):
        t = tr["ticker"]
        if t not in holdings: continue
        if start_date is None: start_date = tr["date"]

        if tr["action"] == "BUY":
            prev_shares = holdings[t]["shares"]
            prev_cost   = holdings[t]["total_cost"]
            new_shares  = prev_shares + tr["shares"]
            new_cost    = prev_cost + tr["shares"] * tr["price"]
            holdings[t]["shares"]     = new_shares
            holdings[t]["total_cost"] = new_cost
            holdings[t]["avg_cost"]   = new_cost / new_shares if new_shares > 0 else 0

        elif tr["action"] == "SELL":
            sell_sh = min(tr["shares"], holdings[t]["shares"])
            if holdings[t]["shares"] > 0:
                # 평단가 유지 (FIFO에서 avg_cost는 남은 주식 기준)
                cost_per_sh = holdings[t]["avg_cost"]
                holdings[t]["shares"]     -= sell_sh
                holdings[t]["total_cost"] -= sell_sh * cost_per_sh
                if holdings[t]["shares"] <= 0:
                    holdings[t] = {"shares":0.0,"avg_cost":0.0,"total_cost":0.0}

    total_invested = sum(h["total_cost"] for h in holdings.values())
    return holdings, total_invested, start_date

@st.cache_data(ttl=300)
def fetch(t,period="1y"):
    try:
        df=yf.download(t,period=period,progress=False,auto_adjust=True)
        if df.empty: return pd.DataFrame()
        df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=1800)  # 30분 캐시
def fetch_uranium():
    """
    우라늄 현물가 자동 수집 (4단계 폴백)

    1순위: UX=F  — CME 우라늄 선물 (U3O8 $/lb) 직접값
    2순위: U-UN.TO — Sprott Physical Uranium Trust
           실물 U3O8 보유 펀드. NAV ÷ 보유량으로 현물가 역산
           환산계수 ≈ 0.2lb/unit (Sprott 공시 기준)
    3순위: URA ETF + 회귀계수
           URA는 우라늄 채굴사 ETF. 가격과 상관관계 높음
           2023~2025 회귀: uranium ≈ URA × 2.85
    4순위: CCJ × 1.82 (Cameco 주가 기반)
    """
    results=[]

    # ── 1순위: UX=F CME 선물 (가장 직접적)
    try:
        df=yf.download("UX=F",period="10d",progress=False,auto_adjust=True)
        if not df.empty:
            df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
            px=float(df["Close"].dropna().iloc[-1])
            if 20<px<200:
                results.append((px,"UX=F · CME 우라늄 선물 $/lb",1))
    except: pass

    # ── 2순위: U-UN.TO Sprott Physical Uranium Trust
    # NAV per share = 우라늄 보유량(lb) × 현물가
    # 2024년말 기준 보유량: ~62M lb / ~316M shares ≈ 0.196 lb/share
    try:
        df=yf.download("U-UN.TO",period="5d",progress=False,auto_adjust=True)
        if not df.empty:
            df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
            px_cad=float(df["Close"].dropna().iloc[-1])
            # CAD→USD 환율 yfinance로 가져오기
            fx=yf.download("CADUSD=X",period="2d",progress=False,auto_adjust=True)
            fx.columns=[c[0] if isinstance(c,tuple) else c for c in fx.columns]
            cad_usd=float(fx["Close"].dropna().iloc[-1]) if not fx.empty else 0.74
            px_usd=px_cad*cad_usd
            # 환산: 1 unit ≈ 0.196 lb U3O8
            uranium_est=round(px_usd/0.196,2)
            if 20<uranium_est<200:
                results.append((uranium_est,"U-UN.TO · Sprott 실물 ETF 역산",2))
    except: pass

    # ── 3순위: URA ETF 회귀 추정
    try:
        df=yf.download("URA",period="5d",progress=False,auto_adjust=True)
        if not df.empty:
            df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
            px=float(df["Close"].dropna().iloc[-1])
            est=round(px*2.85,1)
            if 20<est<200:
                results.append((est,"URA ETF × 2.85 추정",3))
    except: pass

    # ── 4순위: CCJ Cameco
    try:
        df=yf.download("CCJ",period="5d",progress=False,auto_adjust=True)
        if not df.empty:
            df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
            px=float(df["Close"].dropna().iloc[-1])
            est=round(px*1.82,1)
            if 20<est<200:
                results.append((est,"CCJ Cameco × 1.82 추정",4))
    except: pass

    if results:
        # 우선순위 가장 높은 것 반환
        best=sorted(results,key=lambda x:x[2])[0]
        return best[0],best[1]
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
        zones=[
            (0,25,"rgba(62,207,142,0.18)","🔥 3×"),
            (25,35,"rgba(62,207,142,0.10)","⚡ 2×"),
            (35,60,"rgba(79,163,224,0.08)","✅ 1×"),
            (60,75,"rgba(255,165,0,0.08)","📈 추세매수"),
            (75,100,"rgba(224,92,92,0.10)","❌ STOP"),
        ]
        thresholds=[(25,"#3ecf8e","25"),(35,"#c9a84c","35"),(60,"#e08c3c","60"),(75,"#e05c5c","75")]
    elif t=="MU":
        zones=[
            (0,30,"rgba(62,207,142,0.18)","🔥 과매도+$400"),
            (30,40,"rgba(62,207,142,0.10)","⚡ 과매도+$200"),
            (40,65,"rgba(79,163,224,0.08)","✅ 정기$200"),
            (65,100,"rgba(224,92,92,0.08)","🌡️ 과열"),
        ]
        thresholds=[(30,"#3ecf8e","30"),(40,"#c9a84c","40"),(65,"#e05c5c","65")]
    else:  # GOOGL
        zones=[]
        thresholds=[]
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
    u_auto,u_src=None,"미사용"  # NXE 제외

with st.sidebar:
    st.markdown('<div class="st2">⚙ 설정</div>',unsafe_allow_html=True)
    # 우라늄 자동수집 — 범위 강제 클램프 후 사용
    earn_mu=st.checkbox("MU 실적 발표 후 급락?",value=pf.get("earn_mu",False))
    pf["earn_mu"]=earn_mu
    if earn_mu:
        earn_drop_pct=st.number_input("급락 폭 (%)",min_value=-50.,max_value=0.,
            value=float(pf.get("earn_drop_pct",-5.)),step=0.5,
            help="-5% → +$200 보너스 / -10% → +$400 보너스")
        pf["earn_drop_pct"]=earn_drop_pct
    else:
        pf["earn_drop_pct"]=0.
    uranium=68.  # NXE 제외로 우라늄 모니터 불필요
    st.markdown("---")
    st.markdown('<div class="st2">📁 포트폴리오</div>',unsafe_allow_html=True)
    # 매매일지에서 자동 계산
    trades=pf.get("trades",[])
    if trades:
        calc_h, calc_inv, calc_start = calc_portfolio_from_trades(trades, prices)
        pf["holdings"] = calc_h
        pf["total_invested"] = calc_inv
        if calc_start: pf["start_date"] = calc_start
        # 현황 요약
        pv_side = sum(calc_h[t]["shares"]*prices.get(t,0) for t in TICKERS)
        pnl_side = pv_side - calc_inv
        pc_side = "#3ecf8e" if pnl_side>=0 else "#e05c5c"
        st.markdown(f'<div style="font-size:.72rem;color:#3ecf8e;margin-bottom:.3rem">🤖 매매일지 {len(trades)}건에서 자동 계산됨</div>',unsafe_allow_html=True)
        st.markdown(f'<div class="mb" style="margin-bottom:.3rem"><div class="ml">포트 가치</div><div style="font-size:1.1rem;color:#c9a84c;font-family:Cinzel,serif">${pv_side:,.0f}</div><div class="ms" style="color:{pc_side}">손익 ${pnl_side:+,.0f}</div></div>',unsafe_allow_html=True)
        for t in TICKERS:
            h=calc_h[t]; px_n=prices.get(t,0); val=h["shares"]*px_n
            if h["shares"]>0:
                pp=(px_n-h["avg_cost"])/h["avg_cost"]*100 if h["avg_cost"]>0 else 0
                pc2="#3ecf8e" if pp>=0 else "#e05c5c"
                st.markdown(f'<div style="font-size:.68rem;display:flex;justify-content:space-between;padding:.2rem 0;border-bottom:1px solid #1e2a3a"><span style="color:{TICKERS[t]["color"]}">{t}</span><span style="color:#e8e6f0">{h["shares"]:.2f}주</span><span style="color:{pc2}">{pp:+.1f}%</span></div>',unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:.7rem;color:#e08c3c">⚠️ 매매일지에 거래 기록 없음<br>📋 매매일지 탭에서 입력하세요</div>',unsafe_allow_html=True)
    if st.button("🔄 새로고침"): st.cache_data.clear(); st.rerun()
    st.markdown(f'<div style="color:#6b7a99;font-size:.65rem;margin-top:1rem">{datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</div>',unsafe_allow_html=True)

earn_drop_pct=pf.get("earn_drop_pct",0.)
sigs={
    "GOOGL":sg_googl(inds.get("GOOGL",{})),
    "IREN": sg_iren(inds.get("IREN",{})),
    "MU":   sg_mu(inds.get("MU",{}),earn_mu,earn_drop_pct),
}
alloc=allocate(sigs)

# ── 매매일지 기반 포트폴리오 자동 계산
trades_all = pf.get("trades",[])
if trades_all:
    calc_h2, calc_inv2, calc_start2 = calc_portfolio_from_trades(trades_all, prices)
    pf["holdings"] = calc_h2
    pf["total_invested"] = calc_inv2
    if calc_start2: pf["start_date"] = calc_start2

hl=pf["holdings"]
pv=sum(hl[t]["shares"]*prices.get(t,0) for t in TICKERS)
inv=pf.get("total_invested",0); pnl=pv-inv; pnl_p=pnl/inv*100 if inv>0 else 0; gp=pv/TARGET*100
try: start=datetime.strptime(pf.get("start_date",datetime.now().strftime("%Y-%m-%d")),"%Y-%m-%d")
except: start=datetime.now()
elapsed=max((datetime.now()-start).days/30,.1); remaining=max(MONTHS-elapsed,0)
pvt={t:hl[t]["shares"]*prices.get(t,0) for t in TICKERS}
cw={t:v/pv if pv>0 else 0 for t,v in pvt.items()}

ta0,ta1,ta2,ta3,ta4=st.tabs(["🎯 오늘 살까?","📋 매매일지","📊 종목 분석","⚖ 리밸런싱","🏆 목표 추적"])

with ta0:
    st.markdown('<div class="st2">🎯 오늘 살까?</div>',unsafe_allow_html=True)

    today=datetime.now()
    weekday=today.weekday()  # 0=월,1=화,...,4=금
    day_of_month=today.day
    is_month_start=day_of_month<=7
    is_mid_month=10<=day_of_month<=20

    # ── 매수 적합도 점수 계산 (0~100)
    def calc_score(t, ind, sg):
        """오늘 이 종목을 사기 좋은 날인지 점수로 판단"""
        rv   = ind.get("rsi",50)
        pc   = ind.get("price_chg",0)      # 오늘 변동률
        zs   = ind.get("z_score",0)
        mh   = ind.get("macd_hist",0)
        mhp  = ind.get("macd_hist_prev",mh)
        vs   = ind.get("vol_spike",1.0)
        bb_l = ind.get("bb_lower",0)
        px   = ind.get("price",0)
        adv  = ind.get("adx",20)
        above200 = sg.get("above_sma200",True) if t=="IREN" else True

        score=0
        reasons=[]

        # 1. 당일 변동률 (최대 30점)
        if pc<=-3:
            score+=30; reasons.append(f"오늘 {pc:.1f}% 하락 +30점")
        elif pc<=-1.5:
            score+=20; reasons.append(f"오늘 {pc:.1f}% 하락 +20점")
        elif pc<=-0.5:
            score+=10; reasons.append(f"오늘 {pc:.1f}% 소폭 하락 +10점")
        elif pc>=2:
            score-=15; reasons.append(f"오늘 {pc:.1f}% 상승 -15점 (비쌈)")

        # 2. RSI 위치 (최대 25점)
        if rv<30:
            score+=25; reasons.append(f"RSI {rv:.0f} 극과매도 +25점")
        elif rv<40:
            score+=20; reasons.append(f"RSI {rv:.0f} 과매도 +20점")
        elif rv<50:
            score+=10; reasons.append(f"RSI {rv:.0f} 중립하단 +10점")
        elif rv>70:
            score-=20; reasons.append(f"RSI {rv:.0f} 과열 -20점")
        elif rv>60:
            score-=10; reasons.append(f"RSI {rv:.0f} 상단 -10점")

        # 3. 볼린저밴드 하단 근접 (최대 20점)
        if px>0 and bb_l>0:
            bb_dist=(px-bb_l)/px*100
            if bb_dist<1:
                score+=20; reasons.append(f"BB 하단 터치 +20점")
            elif bb_dist<3:
                score+=12; reasons.append(f"BB 하단 근접 +12점")
            elif bb_dist<5:
                score+=5; reasons.append(f"BB 하단 접근 +5점")

        # 4. 요일 (최대 15점)
        if weekday==0:
            score+=15; reasons.append("월요일 +15점 (주초 약세)")
        elif weekday==1:
            score+=10; reasons.append("화요일 +10점")
        elif weekday==4:
            score+=5; reasons.append("금요일 +5점 (포지션 정리 마무리)")

        # 5. 월중 시기 (최대 10점)
        if is_mid_month:
            score+=10; reasons.append(f"{day_of_month}일 월중 +10점")
        elif is_month_start:
            score+=5; reasons.append(f"{day_of_month}일 월초 +5점")

        # 6. IREN 전용: SMA200 위 여부
        if t=="IREN" and not above200:
            score-=15; reasons.append("SMA200 아래 -15점 (하락추세)")

        # 7. MACD 방향
        if mh>mhp and mh>0:
            score+=5; reasons.append("MACD 상승 +5점")
        elif mh<mhp and mh<0:
            score-=5; reasons.append("MACD 하락 -5점")

        score=max(0,min(100,score))
        return score, reasons

    # ── 판정
    def get_verdict(score, mul, t):
        if mul==0:
            return "🔴","오늘은 패스","신호 자체가 없음"
        if score>=85:
            return "🟢","오늘이 최적!","지금 사세요"
        elif score>=65:
            return "🟢","오늘 사세요","좋은 타이밍"
        elif score>=45:
            return "🟡","사도 되지만","내일이 더 좋을 수도"
        elif score>=30:
            return "🟡","기다려요","며칠 더 지켜봐요"
        else:
            return "🔴","오늘은 패스","타이밍 안 좋음"

    # ── 각 종목 계산
    results={}
    for t,info in TICKERS.items():
        ind=inds.get(t,{}); sg=sigs[t]
        mul=sg.get("mul",0)
        score,reasons=calc_score(t,ind,sg)
        em,verdict,advice=get_verdict(score,mul,t)
        amt=alloc.get(t,0)
        results[t]={
            "score":score,"reasons":reasons,
            "em":em,"verdict":verdict,"advice":advice,
            "mul":mul,"amt":amt,
            "rsi":ind.get("rsi",0),"pc":ind.get("price_chg",0),
            "px":prices.get(t,0),"ind":ind,"sg":sg,
        }

    # ── 상단 요약
    buy_today=[t for t,r in results.items() if r["em"]=="🟢"]
    total_today=sum(results[t]["amt"] for t in buy_today)
    avg_score=sum(r["score"] for r in results.values())/len(results)

    c1,c2,c3=st.columns(3)
    with c1:
        gc="#3ecf8e" if len(buy_today)>=2 else "#c9a84c"
        st.markdown(f'<div class="mb card-g"><div class="ml">오늘 매수 추천</div><div class="mv" style="color:{gc}">{len(buy_today)}종목</div><div class="ms">오늘 사세요</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mb"><div class="ml">오늘 예상 지출</div><div class="mv">${total_today:,.0f}</div><div class="ms">/ 월 $2,000</div></div>',unsafe_allow_html=True)
    with c3:
        day_names=["월","화","수","목","금","토","일"]
        sc="#3ecf8e" if avg_score>=65 else "#c9a84c" if avg_score>=45 else "#e05c5c"
        st.markdown(f'<div class="mb"><div class="ml">오늘 타이밍 점수</div><div class="mv" style="color:{sc}">{avg_score:.0f}점</div><div class="ms">{day_names[weekday]}요일 · {day_of_month}일</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── 종목별 카드 (IREN 우선)
    for t in ["IREN","GOOGL","MU"]:
        r=results[t]; info=TICKERS[t]
        score=r["score"]; em=r["em"]; verdict=r["verdict"]
        advice=r["advice"]; amt=r["amt"]; mul=r["mul"]
        rv=r["rsi"]; pc=r["pc"]; px=r["px"]

        # 색상
        if em=="🟢" and score>=85:
            bg="#041a04"; border="#2fff9e"; tc="#2fff9e"; bw="4px"
        elif em=="🟢":
            bg="#061a06"; border="#3ecf8e"; tc="#3ecf8e"; bw="3px"
        elif em=="🔴":
            bg="#1a0606"; border="#e05c5c"; tc="#e05c5c"; bw="3px"
        else:
            bg="#141406"; border="#c9a84c"; tc="#c9a84c"; bw="2px"

        pc_c="#3ecf8e" if pc>=0 else "#e05c5c"
        pc_s="▲" if pc>=0 else "▼"
        rsi_c="#e05c5c" if rv>65 else "#e08c3c" if rv>50 else "#3ecf8e" if rv<35 else "#4fa3e0"

        # 점수 바
        bar_color="#2fff9e" if score>=85 else "#3ecf8e" if score>=65 else "#c9a84c" if score>=45 else "#e05c5c"
        score_bar=f'<div style="background:#0f1620;border-radius:4px;height:6px;margin:.3rem 0"><div style="width:{score}%;height:6px;background:{bar_color};border-radius:4px"></div></div>'

        amt_display=f"${amt:,.0f}" if amt>0 else "—"
        mul_display=f"{mul}×" if mul>0 else "STOP"

        st.markdown(f'''<div style="background:{bg};border-left:{bw} solid {border};border:1px solid {border}44;border-left:{bw} solid {border};border-radius:10px;padding:1.2rem 1.1rem;margin-bottom:.8rem">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.5rem">
    <div>
      <span style="font-family:Cinzel,serif;font-size:1.3rem;color:#e8e6f0">{t}</span>
      <span style="font-size:.7rem;color:#6b7a99;margin-left:.5rem">{info["name"]}</span>
    </div>
    <div style="text-align:right">
      <div style="font-size:1rem;color:{info["color"]};font-family:Cinzel,serif">${px:,.2f}</div>
      <div style="font-size:.75rem;color:{pc_c}">{pc_s} {abs(pc):.1f}%</div>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem">
    <div>
      <span style="font-size:1.4rem;font-weight:700;color:{tc}">{em} {verdict}</span><br>
      <span style="font-size:.8rem;color:#9ba8bb">{advice}</span>
    </div>
    <div style="text-align:right">
      <div style="font-family:Cinzel,serif;font-size:1.3rem;color:{tc}">{amt_display}</div>
      <div style="font-size:.72rem;color:#6b7a99">배율 {mul_display} · RSI <span style="color:{rsi_c}">{rv:.0f}</span></div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem">
    <span style="font-size:.72rem;color:#6b7a99;white-space:nowrap">타이밍 점수</span>
    <div style="flex:1;background:#0f1620;border-radius:4px;height:8px"><div style="width:{score}%;height:8px;background:{bar_color};border-radius:4px"></div></div>
    <span style="font-family:Cinzel,serif;font-size:1rem;color:{bar_color};font-weight:700;min-width:2.5rem;text-align:right">{score}점</span>
  </div>''',unsafe_allow_html=True)

        # 점수 이유 (펼치기)
        with st.expander(f"  {t} 점수 상세 ({score}점)"):
            for reason in r["reasons"]:
                color="#3ecf8e" if "+" in reason and "-" not in reason.split("+")[0] else "#e05c5c" if "-" in reason else "#6b7a99"
                st.markdown(f'<div style="font-size:.72rem;color:{color};padding:.15rem 0">• {reason}</div>',unsafe_allow_html=True)
            # 날짜 정보
            st.markdown(f'<div style="font-size:.68rem;color:#6b7a99;margin-top:.3rem;border-top:1px solid #1e2a3a;padding-top:.3rem">요일: {["월","화","수","목","금","토","일"][weekday]}요일 · 월중 {day_of_month}일 · {"월초(1~7일)" if is_month_start else "월중(10~20일)" if is_mid_month else "기타"}</div>',unsafe_allow_html=True)

        # IREN 전용: SMA200, 불장 조건 표시
        if t=="IREN":
            sg=sigs["IREN"]
            above200=sg.get("above_sma200",True)
            trend_conds=sg.get("trend_conds",{})
            trend_cnt=sg.get("trend_cnt",0)
            ic=sg.get("ic",0)
            s200c="#3ecf8e" if above200 else "#e05c5c"
            s200t="SMA200 위 ✅ 장기 상승추세" if above200 else "SMA200 아래 ⚠️ 하락추세 — 2배 자동 제한"
            st.markdown(f'<div style="font-size:.72rem;color:{s200c};padding:.3rem .5rem;background:#0f1620;border-radius:4px;margin-top:.3rem">{s200t}</div>',unsafe_allow_html=True)
            if trend_cnt>0:
                cond_txt=" · ".join(f"{"✅" if v else "❌"} {k}" for k,v in trend_conds.items())
                st.markdown(f'<div style="font-size:.68rem;color:#6b7a99;margin-top:.2rem">불장조건 {trend_cnt}/4: {cond_txt}</div>',unsafe_allow_html=True)
            if ic>0:
                ign=sg.get("ign",{})
                ign_txt=" · ".join(f"{"✅" if v else "❌"} {k}" for k,v in ign.items())
                st.markdown(f'<div style="font-size:.68rem;color:#c9a84c;margin-top:.2rem">🔥 불타기 {ic}/4: {ign_txt}</div>',unsafe_allow_html=True)

        st.markdown("",unsafe_allow_html=True)

    # ── 원칙 알림
    st.markdown("---")
    month_plan=sum(alloc.values())
    month_left=BUDGET-month_plan
    # "집행 완료"가 아니라 "이번 달 계획" 표시 (실제 집행 여부는 매매일지 기준)
    if month_left>0:
        st.markdown(f'<div class="info">📋 이번 달 계획: ${ month_plan:,.0f} 배정 / ${month_left:,.0f} 미배정 (IREN 신호 대기 or 월말 GOOGL 집행)</div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info">📋 이번 달 예산 ${month_plan:,.0f} 전액 배정 완료 — 실제 집행은 매매일지에 기록하세요</div>',unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="st2">📅 이번달 DCA 계획</div>',unsafe_allow_html=True)

    # 1차/2차 집행 현황
    first_exec=800+200  # GOOGL+MU 고정
    second_exec=alloc.get("IREN",0)
    googl_extra=alloc.get("GOOGL",0)-800
    mu_extra=alloc.get("MU",0)-200

    cc1,cc2=st.columns(2)
    with cc1:
        st.markdown(f'''<div style="background:#0a1a2a;border:1px solid #4fa3e044;border-left:3px solid #4fa3e0;border-radius:8px;padding:.9rem">
  <div style="font-size:.65rem;color:#4fa3e0;letter-spacing:2px;margin-bottom:.3rem">1차 집행 · 월초 즉시</div>
  <div style="font-family:Cinzel,serif;font-size:1.4rem;color:#e8e6f0">${first_exec:,.0f}</div>
  <div style="font-size:.72rem;color:#6b7a99;margin-top:.3rem">GOOGL $800 + MU $200<br>신호 무관 고정 집행</div>
</div>''',unsafe_allow_html=True)
    with cc2:
        iren_rdy=alloc.get("IREN",0)>0
        c2bg="#0a2a0a" if iren_rdy else "#1a1a0a"
        c2border="#3ecf8e" if iren_rdy else "#c9a84c"
        c2color="#3ecf8e" if iren_rdy else "#c9a84c"
        c2status="신호 발생 — 하락일 기다려 집행" if iren_rdy else "IREN 신호 없음 — 다른 용도"
        c2amt=alloc.get("IREN",0) if iren_rdy else (200+mu_extra+googl_extra)
        st.markdown(f'''<div style="background:{c2bg};border:1px solid {c2border}44;border-left:3px solid {c2border};border-radius:8px;padding:.9rem">
  <div style="font-size:.65rem;color:{c2color};letter-spacing:2px;margin-bottom:.3rem">2차 집행 · 월중 최적 타이밍</div>
  <div style="font-family:Cinzel,serif;font-size:1.4rem;color:#e8e6f0">${c2amt:,.0f}</div>
  <div style="font-size:.72rem;color:#6b7a99;margin-top:.3rem">{"IREN 집중 — 오늘 점수 65↑ 하락일에 집행" if iren_rdy else "IREN STOP → MU보너스 or GOOGL 추가"}</div>
</div>''',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    rw_plan=[]
    for t_p,info_p in TICKERS.items():
        sg_p=sigs[t_p]; amt_p=alloc.get(t_p,0); px_p=prices.get(t_p,0)
        sh_p=amt_p/px_p if px_p>0 and amt_p>0 else 0
        score_p=results[t_p]["score"]
        phase="1차 월초" if t_p in ["GOOGL","MU"] else "2차 타이밍"
        rw_plan.append({"집행":phase,"종목":t_p,"신호":sg_p["txt"],
                        "오늘점수":f"{score_p}점","배정액":f"${amt_p:,.0f}",
                        "매수주수":f"{sh_p:.4f}" if sh_p>0 else "—","현재가":f"${px_p:,.2f}"})
    st.dataframe(pd.DataFrame(rw_plan),use_container_width=True,hide_index=True)

    st.markdown('''<div class="card" style="margin-top:.8rem"><div class="st2">📌 2단계 집행 원칙</div>
<table><tr><th>단계</th><th>시기</th><th>행동</th><th>금액</th></tr>
<tr><td>1차</td><td>월초 즉시</td><td>GOOGL + MU 고정 집행</td><td>$1,000</td></tr>
<tr><td>2차</td><td>월중 최적일</td><td>IREN 신호 + 점수65↑ + 하락일</td><td>$1,000</td></tr>
<tr><td>2차 대체</td><td>IREN STOP 시</td><td>MU 보너스 or GOOGL 추가</td><td>$1,000</td></tr>
<tr><td>★ 원칙</td><td>월말까지</td><td>신호 없어도 반드시 전액 집행</td><td>100%</td></tr>
</table></div>''',unsafe_allow_html=True)



with ta2:
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

# ── TAB 1: 매매일지 ──
with ta1:
    st.markdown('<div class="st2">📋 매매일지</div>',unsafe_allow_html=True)

    # 거래내역 저장 구조: pf["trades"] = [{date, ticker, action, shares, price}, ...]
    if "trades" not in pf:
        pf["trades"] = []

    # ── 거래 입력 폼
    st.markdown('<div class="st2">➕ 거래 기록 입력</div>',unsafe_allow_html=True)
    with st.form("trade_form", clear_on_submit=True):
        fc1,fc2,fc3=st.columns(3)
        with fc1:
            trade_date=st.date_input("거래일", value=datetime.now().date(), key="td_date")
            trade_ticker=st.selectbox("종목", list(TICKERS.keys()), key="td_ticker")
        with fc2:
            trade_action=st.selectbox("구분", ["BUY","SELL"], key="td_action")
            trade_shares=st.number_input("주수", min_value=0.0001, value=1.0, step=0.01, format="%.4f", key="td_shares")
        with fc3:
            trade_price=st.number_input("단가 ($)", min_value=0.01, value=float(prices.get("IREN",30)), step=0.01, format="%.2f", key="td_price")
            trade_memo=st.text_input("메모 (선택)", key="td_memo", placeholder="DCA, 불타기 등")
        submitted=st.form_submit_button("✅ 거래 추가", use_container_width=True)
        if submitted:
            pf["trades"].append({
                "date": str(trade_date),
                "ticker": trade_ticker,
                "action": trade_action,
                "shares": float(trade_shares),
                "price": float(trade_price),
                "memo": trade_memo,
                "total": float(trade_shares)*float(trade_price),
            })
            save_pf(pf)
            st.success(f"✅ {trade_ticker} {trade_action} {trade_shares:.4f}주 @ ${trade_price:.2f} 추가됨!")
            st.rerun()

    st.markdown("---")

    if pf["trades"]:
        trades=pf["trades"]

        # ── 거래내역 테이블
        st.markdown('<div class="st2">📊 전체 거래내역</div>',unsafe_allow_html=True)

        # 필터
        fl1,fl2=st.columns(2)
        with fl1: filter_t=st.selectbox("종목 필터",["전체"]+list(TICKERS.keys()),key="fl_t")
        with fl2: filter_a=st.selectbox("구분 필터",["전체","BUY","SELL"],key="fl_a")

        filtered=[t for t in trades
                  if (filter_t=="전체" or t["ticker"]==filter_t)
                  and (filter_a=="전체" or t["action"]==filter_a)]
        filtered_sorted=sorted(filtered,key=lambda x:x["date"],reverse=True)

        if filtered_sorted:
            df_trades=pd.DataFrame(filtered_sorted)
            df_trades["수익/비용"]=df_trades.apply(
                lambda r: f"-${r['total']:,.0f}" if r["action"]=="BUY" else f"+${r['total']:,.0f}", axis=1)
            df_trades["구분색"]=df_trades["action"].map({"BUY":"매수","SELL":"매도"})
            display_cols={"date":"날짜","ticker":"종목","구분색":"구분",
                          "shares":"주수","price":"단가","수익/비용":"금액","memo":"메모"}
            df_show=df_trades[list(display_cols.keys())].rename(columns=display_cols)
            df_show["주수"]=df_show["주수"].apply(lambda x: f"{x:.4f}" if isinstance(x,float) else x)
            df_show["단가"]=df_show["단가"].apply(lambda x: f"${x:,.2f}" if isinstance(x,float) else x)
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            # 삭제
            with st.expander("🗑 거래 삭제"):
                del_idx=st.number_input("삭제할 행 번호 (최신순 1번부터)",1,len(filtered_sorted),1,key="del_idx")
                if st.button("삭제 확인",key="del_btn"):
                    target=filtered_sorted[del_idx-1]
                    pf["trades"].remove(target)
                    save_pf(pf)
                    st.success("삭제됨"); st.rerun()
        else:
            st.info("해당 조건의 거래내역이 없습니다.")

        st.markdown("---")

        # ── FIFO 분석 (종목별 보유 배치 계산)
        st.markdown('<div class="st2">🧮 FIFO 보유 현황 & 세금 분석</div>',unsafe_allow_html=True)
        st.markdown('<div class="info">💡 FIFO(선입선출): 먼저 산 주식부터 먼저 파는 방식. 1년 이상 보유분 우선 매도 시 세금 최소화.</div>',unsafe_allow_html=True)

        sel_tax_t=st.selectbox("종목 선택",list(TICKERS.keys()),key="tax_ticker")

        # FIFO 배치 계산
        buy_lots=[]  # [(date, shares, price), ...]
        for tr in sorted(trades,key=lambda x:x["date"]):
            if tr["ticker"]!=sel_tax_t: continue
            if tr["action"]=="BUY":
                buy_lots.append({"date":tr["date"],"shares":tr["shares"],"price":tr["price"],"remaining":tr["shares"]})
            elif tr["action"]=="SELL":
                sell_rem=tr["shares"]
                for lot in buy_lots:
                    if sell_rem<=0: break
                    if lot["remaining"]>0:
                        used=min(lot["remaining"],sell_rem)
                        lot["remaining"]-=used; sell_rem-=used

        active_lots=[l for l in buy_lots if l["remaining"]>0.0001]
        today_str=datetime.now().strftime("%Y-%m-%d")

        if active_lots:
            lot_rows=[]
            total_value_fifo=0
            for lot in active_lots:
                days_held=(datetime.now()-datetime.strptime(lot["date"],"%Y-%m-%d")).days
                is_long=days_held>=365
                px_now=prices.get(sel_tax_t,0)
                cur_val=lot["remaining"]*px_now
                cost=lot["remaining"]*lot["price"]
                gain=cur_val-cost
                tax_rate=0.15 if is_long else 0.37
                tax_if_sold=max(gain*tax_rate,0)
                total_value_fifo+=cur_val
                lot_rows.append({
                    "매수일":lot["date"],
                    "주수":f"{lot['remaining']:.4f}",
                    "매수단가":f"${lot['price']:,.2f}",
                    "현재가":f"${px_now:,.2f}",
                    "평가액":f"${cur_val:,.0f}",
                    "수익":f"${gain:+,.0f}",
                    "보유일":f"{days_held}일",
                    "세율":"장기 15%" if is_long else "단기 37%",
                    "매도시 세금":f"~${tax_if_sold:,.0f}",
                })
            st.dataframe(pd.DataFrame(lot_rows),use_container_width=True,hide_index=True)

            # 매도 시나리오: 얼마 팔 때 세금 얼마?
            st.markdown('<div class="st2">💰 매도 시나리오 계산</div>',unsafe_allow_html=True)
            sell_amt_fifo=st.number_input(f"{sel_tax_t} 매도할 금액 ($)",0.,float(total_value_fifo),
                value=min(1000.,float(total_value_fifo)),step=100.,key="sell_amt_fifo")

            if sell_amt_fifo>0:
                px_now=prices.get(sel_tax_t,0)
                sell_sh=sell_amt_fifo/px_now if px_now>0 else 0
                # FIFO로 세금 계산
                rem=sell_sh; tax_total=0; gain_total=0; detail=[]
                for lot in active_lots:
                    if rem<=0.0001: break
                    used=min(lot["remaining"],rem)
                    days_held=(datetime.now()-datetime.strptime(lot["date"],"%Y-%m-%d")).days
                    is_long=days_held>=365
                    gain=(px_now-lot["price"])*used
                    tax=max(gain*(0.15 if is_long else 0.37),0)
                    tax_total+=tax; gain_total+=gain; rem-=used
                    detail.append({"date":lot["date"],"used":used,"gain":gain,"tax":tax,"long":is_long})

                rc1,rc2,rc3=st.columns(3)
                net=sell_amt_fifo-tax_total
                with rc1: st.markdown(f'<div class="mb" style="border-color:#e05c5c"><div class="ml">매도금액</div><div class="mv" style="color:#e05c5c;font-size:1.3rem">${sell_amt_fifo:,.0f}</div></div>',unsafe_allow_html=True)
                with rc2: st.markdown(f'<div class="mb" style="border-color:#e08c3c"><div class="ml">예상 세금 (FIFO)</div><div class="mv" style="color:#e08c3c;font-size:1.3rem">${tax_total:,.0f}</div><div class="ms">수익 ${gain_total:+,.0f}</div></div>',unsafe_allow_html=True)
                with rc3: st.markdown(f'<div class="mb" style="border-color:#3ecf8e"><div class="ml">실수령액</div><div class="mv" style="color:#3ecf8e;font-size:1.3rem">${net:,.0f}</div></div>',unsafe_allow_html=True)

                for d in detail:
                    tc="#3ecf8e" if d["long"] else "#e05c5c"
                    tl="장기 15%" if d["long"] else "단기 37%"
                    st.markdown(f'<div style="font-size:.72rem;padding:.3rem .5rem;background:#0f1620;border-radius:4px;margin-bottom:.2rem;display:flex;justify-content:space-between"><span style="color:#6b7a99">{d["date"]} · {d["used"]:.4f}주</span><span style="color:{tc}">{tl} · 수익 ${d["gain"]:+,.0f} → 세금 ${d["tax"]:,.0f}</span></div>',unsafe_allow_html=True)
        else:
            st.info(f"{sel_tax_t} 매수 기록이 없습니다. 거래를 먼저 입력해주세요.")
    else:
        st.markdown('<div class="info">📌 거래를 입력하면 FIFO 세금 분석이 활성화됩니다.</div>',unsafe_allow_html=True)


# ── TAB 2: 리밸런싱 ──
with ta3:
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

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("⚖ 매수 우선 리밸런싱", key="rebal_btn", use_container_width=True):
                st.session_state["show_rebal"] = True
                st.session_state["show_sell"] = False
        with c_btn2:
            if st.button("🔴 매도 플랜 계산", key="sell_btn", use_container_width=True):
                st.session_state["show_sell"] = True
                st.session_state["show_rebal"] = False

        # ── 매도 플랜 (FIFO 기반)
        if st.session_state.get("show_sell", False):
            st.markdown("---")
            st.markdown('<div class="st2">🔴 매도 플랜 — FIFO 세금 최소화</div>',unsafe_allow_html=True)

            has_trades = bool(pf.get("trades",[]))
            if not has_trades:
                st.markdown('<div class="warn">⚠️ 매매일지에 거래 기록이 없습니다. 📋 매매일지 탭에서 먼저 매수 기록을 입력하면 FIFO로 정확한 세금 계산이 가능합니다.</div>',unsafe_allow_html=True)
                st.markdown('<div style="font-size:.75rem;color:#6b7a99;margin-top:.5rem">매매일지 없이도 아래 수동 추정으로 진행할 수 있습니다.</div>',unsafe_allow_html=True)

            st.markdown('<div class="info">📌 FIFO 원칙: 먼저 산 주식부터 먼저 매도. 1년 이상 보유분은 장기세율(15%) 적용.</div>',unsafe_allow_html=True)

            surplus_items=[]
            for t_s,info_s in TICKERS.items():
                cur_s=cw.get(t_s,0); tgt_s=info_s["weight"]
                if cur_s-tgt_s<=0.01: continue
                surplus_val=(cur_s-tgt_s)*pv
                px_s=prices.get(t_s,0)
                sh_s=surplus_val/px_s if px_s>0 else 0

                # FIFO 세금 계산 (매매일지 있을 때)
                tax_fifo=0; gain_fifo=0; fifo_detail=[]; fifo_used=True
                if has_trades:
                    buy_lots_s=[]
                    for tr in sorted(pf["trades"],key=lambda x:x["date"]):
                        if tr["ticker"]!=t_s: continue
                        if tr["action"]=="BUY":
                            buy_lots_s.append({"date":tr["date"],"shares":tr["shares"],"price":tr["price"],"remaining":tr["shares"]})
                        elif tr["action"]=="SELL":
                            rem_s=tr["shares"]
                            for lot in buy_lots_s:
                                if rem_s<=0: break
                                if lot["remaining"]>0:
                                    u=min(lot["remaining"],rem_s); lot["remaining"]-=u; rem_s-=u
                    active_s=[l for l in buy_lots_s if l["remaining"]>0.0001]
                    rem_sell=sh_s
                    for lot in active_s:
                        if rem_sell<=0.0001: break
                        used=min(lot["remaining"],rem_sell)
                        days=(datetime.now()-datetime.strptime(lot["date"],"%Y-%m-%d")).days
                        is_long=days>=365
                        g=(px_s-lot["price"])*used; t_amt=max(g*(0.15 if is_long else 0.37),0)
                        tax_fifo+=t_amt; gain_fifo+=g; rem_sell-=used
                        fifo_detail.append({"date":lot["date"],"used":used,"days":days,"gain":g,"tax":t_amt,"long":is_long})
                    if not active_s: fifo_used=False
                else:
                    fifo_used=False

                if not fifo_used:
                    # 매매일지 없으면 평단가 기반 추정
                    avg_s=pf["holdings"][t_s].get("avg_cost",0)
                    gain_fifo=max((px_s-avg_s)*sh_s,0) if avg_s>0 else 0
                    tax_fifo=gain_fifo*0.15  # 장기 가정 (보수적)
                    fifo_detail=[]

                surplus_items.append({
                    "t":t_s,"info":info_s,"surplus_val":surplus_val,"sh":sh_s,"px":px_s,
                    "gain":gain_fifo,"tax":tax_fifo,"cur_pct":cur_s*100,"tgt_pct":tgt_s*100,
                    "fifo_detail":fifo_detail,"fifo_used":fifo_used,
                })

            if surplus_items:
                surplus_items.sort(key=lambda x:x["tax"])
                total_sell=sum(x["surplus_val"] for x in surplus_items)
                total_tax=sum(x["tax"] for x in surplus_items)
                net_sell=total_sell-total_tax

                sc1,sc2,sc3=st.columns(3)
                with sc1: st.markdown(f'<div class="mb" style="border-color:#e05c5c"><div class="ml">총 매도금액</div><div class="mv" style="color:#e05c5c">${total_sell:,.0f}</div></div>',unsafe_allow_html=True)
                with sc2: st.markdown(f'<div class="mb" style="border-color:#e08c3c"><div class="ml">예상 세금</div><div class="mv" style="color:#e08c3c">${total_tax:,.0f}</div><div class="ms">{"FIFO 계산" if has_trades else "추정(장기 15%)"}</div></div>',unsafe_allow_html=True)
                with sc3: st.markdown(f'<div class="mb" style="border-color:#3ecf8e"><div class="ml">실수령액</div><div class="mv" style="color:#3ecf8e">${net_sell:,.0f}</div></div>',unsafe_allow_html=True)

                st.markdown("<br>",unsafe_allow_html=True)
                for rank_s,item_s in enumerate(surplus_items,1):
                    t2=item_s["t"]; info2=item_s["info"]
                    sv=item_s["surplus_val"]; sh2=item_s["sh"]; px2=item_s["px"]
                    gn=item_s["gain"]; tx=item_s["tax"]
                    c1p=item_s["cur_pct"]; t2p=item_s["tgt_pct"]

                    st.markdown(f'''<div style="background:#1a0a0a;border:1px solid #e05c5c88;border-left:4px solid #e05c5c;border-radius:8px;padding:1.1rem;margin-bottom:.7rem">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.6rem">
    <div>
      <div style="font-size:.7rem;color:#6b7a99;margin-bottom:.2rem">#{rank_s} 우선 매도 {"· FIFO" if item_s["fifo_used"] else "· 추정"}</div>
      <div style="font-family:Cinzel,serif;font-size:1.3rem;color:{info2["color"]}">{t2}</div>
      <div style="font-size:.75rem;color:#9ba8bb;margin-top:.2rem">비중 {c1p:.1f}% → 목표 {t2p:.0f}%</div>
    </div>
    <div style="text-align:right">
      <div style="font-family:Cinzel,serif;color:#e05c5c;font-size:1.6rem">${sv:,.0f}</div>
      <div style="font-size:.78rem;color:#6b7a99">{sh2:.2f}주 @ ${px2:,.2f}</div>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;background:#2a0a0a;border-radius:4px;padding:.5rem .7rem;font-size:.8rem">
    <span style="color:#9ba8bb">수익 <b style="color:#e8e6f0">${gn:+,.0f}</b></span>
    <span style="color:#e08c3c">세금 <b style="color:#e05c5c">${tx:,.0f}</b></span>
    <span style="color:#3ecf8e">실수령 <b>${sv-tx:,.0f}</b></span>
  </div>''',unsafe_allow_html=True)

                    if item_s["fifo_detail"]:
                        with st.expander(f"  {t2} FIFO 상세 내역"):
                            for d in item_s["fifo_detail"]:
                                tc="#3ecf8e" if d["long"] else "#e05c5c"
                                tl="장기(15%)" if d["long"] else "단기(37%)"
                                st.markdown(f'<div style="font-size:.72rem;padding:.2rem .4rem;background:#0f1620;border-radius:3px;margin-bottom:.2rem;display:flex;justify-content:space-between"><span style="color:#6b7a99">{d["date"]} {d["days"]}일 보유 · {d["used"]:.4f}주</span><span style="color:{tc}">{tl} → 세금 ${d["tax"]:,.0f}</span></div>',unsafe_allow_html=True)

                # 재배분 제안 (크게)
                st.markdown("---")
                st.markdown('<div class="st2">💡 매도 후 재배분 제안</div>',unsafe_allow_html=True)
                st.markdown('<div class="info">Rule 1 기준: IREN 초과분 → GOOGL 50% / MU 50%로 재투자</div>',unsafe_allow_html=True)
                for rt,rw_r in [("GOOGL",0.50),("MU",0.50)]:
                    ri_amt=net_sell*rw_r  # 세후 실수령액 기준
                    ri_px=prices.get(rt,0); ri_sh=ri_amt/ri_px if ri_px>0 else 0
                    ri_col=TICKERS[rt]["color"]
                    st.markdown(f'''<div style="background:#0a1a0a;border:1px solid #3ecf8e44;border-radius:8px;padding:1rem;margin-bottom:.5rem;display:flex;justify-content:space-between;align-items:center">
  <div>
    <div style="font-family:Cinzel,serif;font-size:1.2rem;color:{ri_col}">{rt}</div>
    <div style="font-size:.75rem;color:#6b7a99">{rw_r*100:.0f}% 배분 · {ri_sh:.2f}주 @ ${ri_px:,.2f}</div>
  </div>
  <div style="font-family:Cinzel,serif;font-size:1.5rem;color:#3ecf8e">${ri_amt:,.0f}</div>
</div>''',unsafe_allow_html=True)
            else:
                st.markdown('<div class="ok">✅ 매도 필요 없음 — 모든 종목 목표 비중 내</div>',unsafe_allow_html=True)

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
<tr><td>Rule 1</td><td>IREN >50% → GOOGL 50%/MU 50%</td></tr>
<tr><td>Rule 2</td><td>GOOGL >40% → IREN 로테이션</td></tr>


</table></div>""",unsafe_allow_html=True)

with ta4:
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
