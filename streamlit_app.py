from pathlib import Path
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Trade Intelligence", page_icon="◈", layout="wide")

APP_DIR = Path(__file__).parent
DEFAULT_FILE = APP_DIR / "data" / "daily_trade_sheet.xlsx"

st.markdown("""
<style>
.block-container{padding-top:1.4rem;padding-bottom:3rem;max-width:1500px}
[data-testid="stSidebar"]{background:#0b1411;border-right:1px solid #1c2a24}
h1,h2,h3{letter-spacing:-.035em}.eyebrow{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:#91a39a;font-weight:700}
.hero{padding:1.4rem 1.5rem;border:1px solid #213029;border-radius:18px;background:linear-gradient(135deg,#101b17 0%,#0a120f 70%);margin-bottom:1.1rem}
.hero h1{font-size:2.5rem;margin:.15rem 0 .25rem}.hero p{color:#9fb0a7;margin:0;max-width:800px}
.metric-card{border:1px solid #213029;background:#0d1713;border-radius:16px;padding:1rem 1.1rem;min-height:112px}
.metric-label{font-size:.72rem;color:#91a39a;text-transform:uppercase;letter-spacing:.11em;font-weight:700}.metric-value{font-size:1.65rem;font-weight:750;margin-top:.3rem}.metric-sub{font-size:.78rem;color:#789086;margin-top:.15rem}
.good{color:#57d58b}.bad{color:#ff7373}.accent{color:#f5c542}.muted{color:#91a39a}
div[data-testid="stDataFrame"]{border:1px solid #213029;border-radius:14px;overflow:hidden}
</style>""", unsafe_allow_html=True)

DAYS = {"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"}
HEADER_KEYS = {"trade","trades"}

def clean_col(x):
    return re.sub(r"\s+", " ", str(x).strip()) if x is not None else ""

def parse_workbook(file):
    xl = pd.ExcelFile(file)
    trades=[]; sections=[]; raw={}
    for sheet in xl.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet, header=None)
        raw[sheet]=df
        if "profitability" in sheet.lower():
            continue
        current_day=None
        i=0
        while i < len(df):
            first=clean_col(df.iat[i,0]) if df.shape[1] else ""
            if first in DAYS:
                current_day=first
                i+=1; continue
            if first.lower() in HEADER_KEYS:
                headers=[clean_col(v) for v in df.iloc[i].tolist()]
                j=i+1; block=[]
                while j < len(df):
                    marker=clean_col(df.iat[j,0])
                    if marker in DAYS or marker.lower() in HEADER_KEYS: break
                    if marker.lower() in {"total","average","total profit/loss ratio(%)","total loss/profit ratio(%)"}: j+=1; continue
                    try: num=float(df.iat[j,0])
                    except: num=np.nan
                    if not np.isnan(num): block.append(df.iloc[j].tolist())
                    j+=1
                for vals in block:
                    row={headers[k]: vals[k] for k in range(min(len(headers),len(vals))) if headers[k]}
                    def pick(*names):
                        for n in names:
                            for k,v in row.items():
                                if clean_col(k).lower()==n.lower(): return v
                        return np.nan
                    capital=pd.to_numeric(pick("Capital allocated(ZAR)","Capital allocated (ZAR)"),errors="coerce")
                    profit_zar=pd.to_numeric(pick("Actual Profit (ZAR)"),errors="coerce")
                    loss_zar=pd.to_numeric(pick("Actual Loss (ZAR)"),errors="coerce")
                    total=pd.to_numeric(pick("Total (ZAR)"),errors="coerce")
                    pnl=(0 if pd.isna(profit_zar) else profit_zar)+(0 if pd.isna(loss_zar) else loss_zar)
                    trades.append({
                        "Sheet":sheet,"Day":current_day or "Unspecified","Trade":int(num),"Coin":pick("Coin"),
                        "Capital (ZAR)":capital,"Stop Loss %":pd.to_numeric(pick("Target Stop Loss (%)"),errors="coerce"),
                        "Profit Target %":pd.to_numeric(pick("Profit Target (%)"),errors="coerce"),
                        "Actual Profit %":pd.to_numeric(pick("Actual Profit (%)"),errors="coerce"),
                        "Actual Profit (ZAR)":profit_zar,"Actual Loss %":pd.to_numeric(pick("Actual Loss (%)"),errors="coerce"),
                        "Actual Loss (ZAR)":loss_zar,"Workbook Total (ZAR)":total,"P/L (ZAR)":pnl,
                    })
                sections.append({"Sheet":sheet,"Day":current_day,"Trades":len(block)})
                i=j; continue
            i+=1
    return xl.sheet_names, pd.DataFrame(trades), pd.DataFrame(sections), raw

@st.cache_data(show_spinner=False)
def load_default(): return parse_workbook(DEFAULT_FILE)

with st.sidebar:
    st.markdown("### ◈ Trade Intelligence")
    st.caption("Workbook-powered analytics")
    uploaded=st.file_uploader("Replace workbook",type=["xlsx"],help="Upload another workbook using the same trade-sheet structure.")
    st.divider()
    page=st.radio("Workspace",["Executive Dashboard","Trade Explorer","Risk & Targets","Coin Analytics","Profitability Model","Workbook Audit"],label_visibility="collapsed")
    st.divider(); st.caption("Built with Streamlit • pandas • Plotly")

if uploaded:
    sheet_names,trades,sections,raw=parse_workbook(uploaded)
else:
    sheet_names,trades,sections,raw=load_default()

if trades.empty:
    st.error("No trade rows could be parsed from the workbook."); st.stop()

trades["Outcome"]=np.select([trades["P/L (ZAR)"]>0,trades["P/L (ZAR)"]<0],["Win","Loss"],default="Flat")
trades["Coin"]=trades["Coin"].astype(str).replace("nan","Unknown")

st.markdown('<div class="hero"><div class="eyebrow">Trading performance system</div><h1>Trade Intelligence Dashboard</h1><p>Professional analytics generated directly from every weekly trade sheet and the workbook profitability model. Filter performance, inspect risk, compare assets and audit the source workbook from one interface.</p></div>',unsafe_allow_html=True)

f1,f2,f3=st.columns([1.4,1,1])
with f1: selected_weeks=st.multiselect("Weeks",trades["Sheet"].unique(),default=list(trades["Sheet"].unique()))
with f2: selected_days=st.multiselect("Days",[d for d in ["Monday","Tuesday","Wednesday","Thursday","Friday"] if d in trades.Day.unique()],default=[d for d in ["Monday","Tuesday","Wednesday","Thursday","Friday"] if d in trades.Day.unique()])
with f3: selected_outcomes=st.multiselect("Outcome",["Win","Loss","Flat"],default=["Win","Loss","Flat"])
f=trades[trades.Sheet.isin(selected_weeks)&trades.Day.isin(selected_days)&trades.Outcome.isin(selected_outcomes)].copy()
if f.empty: st.warning("No trades match the current filters."); st.stop()

wins=(f.Outcome=="Win").sum(); losses=(f.Outcome=="Loss").sum(); n=len(f); net=f["P/L (ZAR)"].sum(); capital=f["Capital (ZAR)"].sum(); winrate=wins/n if n else 0
profit=f.loc[f["P/L (ZAR)"]>0,"P/L (ZAR)"].sum(); loss=abs(f.loc[f["P/L (ZAR)"]<0,"P/L (ZAR)"].sum()); pf=profit/loss if loss else np.inf

def card(label,value,sub="",cls=""):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value {cls}">{value}</div><div class="metric-sub">{sub}</div></div>',unsafe_allow_html=True)

if page=="Executive Dashboard":
    c=st.columns(5)
    with c[0]: card("Net P/L",f"R {net:,.2f}","Actual profit + actual loss","good" if net>=0 else "bad")
    with c[1]: card("Win rate",f"{winrate:.1%}",f"{wins} wins • {losses} losses","accent")
    with c[2]: card("Trades",f"{n:,}",f"Across {f.Sheet.nunique()} weekly sheets")
    with c[3]: card("Capital allocated",f"R {capital:,.0f}","Cumulative trade allocation")
    with c[4]: card("Profit factor",("∞" if np.isinf(pf) else f"{pf:.2f}"),"Gross profit ÷ gross loss")
    st.write("")
    daily=f.groupby(["Sheet","Day"],as_index=False)["P/L (ZAR)"].sum(); daily["Period"]=daily["Sheet"]+" · "+daily["Day"]
    left,right=st.columns([1.6,1])
    with left:
        fig=px.bar(daily,x="Period",y="P/L (ZAR)",title="Daily realised P/L",color="P/L (ZAR)",color_continuous_scale=["#ff7373","#26362f","#57d58b"])
        fig.update_layout(height=410,coloraxis_showscale=False,margin=dict(l=10,r=10,t=55,b=10)); st.plotly_chart(fig,use_container_width=True)
    with right:
        oc=f.Outcome.value_counts().reindex(["Win","Loss","Flat"]).fillna(0)
        fig=go.Figure(go.Pie(labels=oc.index,values=oc.values,hole=.68,marker_colors=["#57d58b","#ff7373","#718079"]))
        fig.update_layout(title="Outcome mix",height=410,margin=dict(l=10,r=10,t=55,b=10),showlegend=True); st.plotly_chart(fig,use_container_width=True)
    coin=f.groupby("Coin",as_index=False).agg(Trades=("Trade","count"),Net_PL=("P/L (ZAR)","sum"),Capital=("Capital (ZAR)","sum")); coin=coin.sort_values("Net_PL",ascending=False)
    st.subheader("Asset contribution")
    fig=px.bar(coin.head(15),x="Net_PL",y="Coin",orientation="h",hover_data=["Trades","Capital"]); fig.update_layout(height=500,yaxis={"categoryorder":"total ascending"},xaxis_title="Net P/L (ZAR)",yaxis_title=""); st.plotly_chart(fig,use_container_width=True)

elif page=="Trade Explorer":
    st.subheader("Trade ledger")
    q=st.text_input("Search coin",placeholder="e.g. ETHENA, ONDO, ARB")
    view=f[f.Coin.str.contains(q,case=False,na=False)] if q else f
    st.dataframe(view[["Sheet","Day","Trade","Coin","Capital (ZAR)","Stop Loss %","Profit Target %","Actual Profit %","Actual Profit (ZAR)","Actual Loss %","Actual Loss (ZAR)","P/L (ZAR)","Outcome"]],use_container_width=True,hide_index=True,column_config={"Stop Loss %":st.column_config.NumberColumn(format="%.2%%"),"Profit Target %":st.column_config.NumberColumn(format="%.2%%"),"Actual Profit %":st.column_config.NumberColumn(format="%.2%%"),"Actual Loss %":st.column_config.NumberColumn(format="%.2%%")})
    st.download_button("Download filtered trades (CSV)",view.to_csv(index=False).encode(),"filtered_trades.csv","text/csv")

elif page=="Risk & Targets":
    st.subheader("Risk and target discipline")
    a,b=st.columns(2)
    with a:
        fig=px.scatter(f,x="Stop Loss %",y="Profit Target %",size="Capital (ZAR)",color="Outcome",hover_name="Coin",hover_data=["Sheet","Day","P/L (ZAR)"],color_discrete_map={"Win":"#57d58b","Loss":"#ff7373","Flat":"#718079"},title="Planned stop vs profit target")
        fig.update_layout(height=470); st.plotly_chart(fig,use_container_width=True)
    with b:
        rr=(f["Profit Target %"]/f["Stop Loss %"]).replace([np.inf,-np.inf],np.nan).dropna()
        card("Median target / stop",f"{rr.median():.1f}×" if len(rr) else "—","Planned reward-to-risk multiple","accent")
        st.write("")
        risk=f.groupby("Sheet",as_index=False).agg(Avg_Stop=("Stop Loss %","mean"),Avg_Target=("Profit Target %","mean"),Net_PL=("P/L (ZAR)","sum"))
        st.dataframe(risk,use_container_width=True,hide_index=True,column_config={"Avg_Stop":st.column_config.NumberColumn(format="%.2%%"),"Avg_Target":st.column_config.NumberColumn(format="%.2%%")})
    fig=px.box(f,x="Outcome",y="P/L (ZAR)",points="all",hover_name="Coin",title="P/L distribution by outcome"); fig.update_layout(height=430); st.plotly_chart(fig,use_container_width=True)

elif page=="Coin Analytics":
    coin=f.groupby("Coin").agg(Trades=("Trade","count"),Wins=("Outcome",lambda x:(x=="Win").sum()),Losses=("Outcome",lambda x:(x=="Loss").sum()),Net_PL=("P/L (ZAR)","sum"),Gross_Profit=("Actual Profit (ZAR)","sum"),Gross_Loss=("Actual Loss (ZAR)","sum"),Capital=("Capital (ZAR)","sum")).reset_index(); coin["Win_Rate"]=coin.Wins/coin.Trades
    st.subheader("Coin performance leaderboard")
    st.dataframe(coin.sort_values(["Net_PL","Win_Rate"],ascending=False),use_container_width=True,hide_index=True,column_config={"Win_Rate":st.column_config.ProgressColumn(min_value=0,max_value=1,format="%.1%%")})
    fig=px.scatter(coin,x="Trades",y="Net_PL",size="Capital",color="Win_Rate",hover_name="Coin",color_continuous_scale="Viridis",title="Frequency vs realised performance"); fig.update_layout(height=500); st.plotly_chart(fig,use_container_width=True)

elif page=="Profitability Model":
    st.subheader("Workbook profitability model")
    pnames=[s for s in sheet_names if "profitability" in s.lower()]
    if pnames:
        pdf=raw[pnames[0]].copy(); pdf=pdf.dropna(how="all").dropna(axis=1,how="all")
        st.caption("Displayed directly from the source workbook so model assumptions and calculations remain visible.")
        st.dataframe(pdf,use_container_width=True,hide_index=True,height=620)
    else: st.info("No profitability model sheet found.")

else:
    st.subheader("Workbook audit")
    c1,c2,c3=st.columns(3)
    with c1: card("Workbook sheets",str(len(sheet_names)),"Including profitability model")
    with c2: card("Parsed trade rows",f"{len(trades):,}","Across all weekly sheets")
    with c3: card("Unique coins",str(trades.Coin.nunique()),"Assets represented")
    st.write("")
    audit=pd.DataFrame({"Sheet":sheet_names,"Rows":[len(raw[s]) for s in sheet_names],"Columns":[raw[s].shape[1] for s in sheet_names],"Type":["Profitability model" if "profitability" in s.lower() else "Weekly trades" for s in sheet_names]})
    st.dataframe(audit,use_container_width=True,hide_index=True)
    st.subheader("Parsed coverage")
    coverage=trades.groupby(["Sheet","Day"]).size().reset_index(name="Trades")
    st.dataframe(coverage,use_container_width=True,hide_index=True)

st.divider(); st.caption("Source: supplied Excel trading workbook • Analytics are descriptive and do not constitute financial advice.")
