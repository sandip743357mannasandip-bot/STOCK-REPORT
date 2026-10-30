from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
import streamlit as st
import pandas as pd

ROOT = Path(__file__).resolve().parent
TRADER = ROOT / 'trader'
TRADER.mkdir(exist_ok=True)
PORTFOLIO = TRADER / 'paper_portfolio.json'
WATCHLIST = TRADER / 'watchlist.json'
NEWS_OUT = TRADER / 'dashboard_news.txt'
CONFIG = TRADER / 'config.json'
DEFAULT_CONFIG = {
    'budget': 1000, 'cash_buffer_pct': 10, 'max_position_pct': 50,
    'max_order_usd': 500, 'min_order_usd': 5, 'max_loss_per_trade_usd': 10,
    'max_daily_loss_usd': 20, 'max_trades_per_day': 3, 'max_orders_per_day': 10,
    'min_reward_risk': 1.5, 'require_stop': True, 'no_entries_before': '09:45',
    'no_entries_after': '15:30', 'flat_by': '15:55', 'fractional': False,
    'broker': 'none', 'paper': True, 'blocked': [], 'allow_options': False,
    'allow_margin': False, 'allow_short': False, 'pdt_guard': False,
    'sec_user_agent': 'Paper Trading Dashboard contact@example.com'
}

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
    except Exception:
        return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def run_script(args, timeout=900):
    try:
        p = subprocess.run([sys.executable, *map(str,args)], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + ('\n' + p.stderr if p.stderr else '')
    except subprocess.TimeoutExpired:
        return 124, 'The command timed out. Try a smaller scan.'
    except Exception as e:
        return 1, str(e)

if not CONFIG.exists():
    save_json(CONFIG, DEFAULT_CONFIG)

st.set_page_config(page_title='US Paper Trading Dashboard', page_icon='📈', layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.5rem;max-width:1500px}
[data-testid="stMetric"]{background:rgba(120,130,150,.08);padding:14px;border-radius:12px}
.small-muted{color:#8b949e;font-size:.85rem}
</style>''', unsafe_allow_html=True)
st.title('US Stocks · Paper Trading Dashboard')
st.caption('NYSE / Nasdaq research workspace · simulated trades only · no broker connection')

cfg = read_json(CONFIG, DEFAULT_CONFIG)
if cfg.get('paper') is not True:
    cfg['paper'] = True
    cfg['broker'] = 'none'
    save_json(CONFIG, cfg)

portfolio = read_json(PORTFOLIO, {'starting_cash': 1000.0, 'cash': 1000.0, 'positions': [], 'trades': []})
portfolio.setdefault('starting_cash', 1000.0); portfolio.setdefault('cash', portfolio['starting_cash'])
portfolio.setdefault('positions', []); portfolio.setdefault('trades', [])
open_positions = portfolio['positions']
realized = sum(float(t.get('pnl',0)) for t in portfolio['trades'])
unrealized = sum((float(p.get('last_price',p['entry']))-float(p['entry']))*int(p['qty']) for p in open_positions)
equity = float(portfolio['cash']) + sum(float(p.get('last_price',p['entry']))*int(p['qty']) for p in open_positions)

with st.sidebar:
    st.header('Controls')
    st.success('PAPER MODE ON')
    st.caption('No live orders or broker API is used by this dashboard.')
    page = st.radio('Navigate', ['Overview','Market Scanner','News','Paper Trading','Trade Journal','Settings'])
    st.divider()
    st.caption('Market data comes from public Yahoo Finance endpoints and may be delayed, incomplete or rate-limited.')

if page == 'Overview':
    st.subheader('Account overview')
    a,b,c,d = st.columns(4)
    a.metric('Paper equity', f'${equity:,.2f}')
    b.metric('Cash available', f"${float(portfolio['cash']):,.2f}")
    c.metric('Realized P&L', f'${realized:,.2f}', delta=f'{realized:+,.2f}')
    d.metric('Open positions', len(open_positions))
    st.caption(f"Starting paper capital: ${float(portfolio['starting_cash']):,.2f} · Unrealized P&L: ${unrealized:+,.2f}")
    left,right=st.columns([1.2,1])
    with left:
        st.markdown('#### Current paper positions')
        if open_positions:
            df=pd.DataFrame([{**p,'market_value':float(p.get('last_price',p['entry']))*int(p['qty']),'unrealized_pnl':(float(p.get('last_price',p['entry']))-float(p['entry']))*int(p['qty'])} for p in open_positions])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: st.info('No open simulated positions yet. Use Paper Trading to record a practice trade.')
    with right:
        st.markdown('#### Latest scanner results')
        wl=read_json(WATCHLIST,{})
        hits=wl.get('hits',[]) if isinstance(wl,dict) else []
        if hits:
            st.dataframe(pd.DataFrame(hits).head(8), use_container_width=True, hide_index=True)
            st.caption(f"{len(hits)} setup(s) · {wl.get('mode','')} · {wl.get('as_of','')}")
        else: st.info('No saved scan yet. Open Market Scanner to run one.')
    st.warning('A scanner match is a research candidate, not a buy recommendation. Verify the chart, news, spread and risk before recording any simulated trade.')

elif page == 'Market Scanner':
    st.subheader('Market scanner')
    mode=st.radio('Scan type',['Daily setups','Opening-range breakout'], horizontal=True)
    c1,c2,c3=st.columns([1,1,1])
    with c1: limit=st.number_input('Maximum symbols to scan', min_value=5,max_value=1000,value=100,step=25)
    with c2: min_price=st.number_input('Minimum share price ($)',min_value=0.0,value=5.0,step=1.0)
    with c3: min_volume=st.number_input('Minimum daily volume',min_value=0,value=1000000,step=100000)
    st.caption('The daily scan uses completed daily closes. The ORB scan requires an active US regular session and completed 5-minute bars.')
    if st.button('Run market scan', type='primary'):
        cmd=['trader-scanner/scan.py','daily' if mode=='Daily setups' else 'orb','--limit',str(int(limit)),'--min-price',str(min_price),'--min-volume',str(int(min_volume)),'--show','100']
        with st.spinner('Fetching public market data…'):
            code,out=run_script(cmd, timeout=1200)
        st.session_state['scan_output']=out
        st.session_state['scan_code']=code
        st.rerun()
    if 'scan_output' in st.session_state:
        st.code(st.session_state['scan_output'][-12000:])
        if st.session_state.get('scan_code') in (0,1):
            st.caption('Scan finished. Exit code 1 can simply mean no setups matched; check the output for errors.')
    wl=read_json(WATCHLIST,{})
    hits=wl.get('hits',[]) if isinstance(wl,dict) else []
    if hits:
        st.markdown('#### Saved scan results')
        st.caption(f"Mode: {wl.get('mode','—')} · As of: {wl.get('as_of','—')} · Scanned: {wl.get('scanned','—')} · Source: {wl.get('source','—')}")
        st.dataframe(pd.DataFrame(hits),use_container_width=True,hide_index=True)
    else: st.info('No saved results yet. Run a scan above.')

elif page == 'News':
    st.subheader('Stock news')
    tickers=st.text_input('Tickers (comma-separated)', 'AAPL,MSFT,NVDA,TSLA')
    hours=st.slider('Look back (hours)',1,168,24)
    if st.button('Fetch headlines',type='primary'):
        syms=','.join(x.strip().upper() for x in tickers.split(',') if x.strip())
        with st.spinner('Fetching headlines…'):
            code,out=run_script(['trader-news/news.py','--tickers',*syms.split(','),'--hours',str(hours),'--no-sec','--dry-run'],timeout=180)
        st.session_state['news_output']=out
        st.session_state['news_code']=code
    if 'news_output' in st.session_state: st.code(st.session_state['news_output'][-16000:])
    st.caption('Headlines are informational and may be delayed. SEC filings are not fetched in this quick headline view.')

elif page == 'Paper Trading':
    st.subheader('Record a simulated trade')
    st.caption('This form only updates a local paper-trading ledger. It never sends an order anywhere.')
    with st.form('paper_buy'):
        c1,c2,c3=st.columns(3)
        symbol=c1.text_input('Ticker','AAPL').strip().upper()
        qty=c2.number_input('Whole shares',min_value=1,value=1,step=1)
        entry=c3.number_input('Simulated entry price ($)',min_value=0.01,value=100.0,step=0.5)
        c4,c5=st.columns(2)
        stop=c4.number_input('Planned stop price ($)',min_value=0.0,value=98.0,step=0.5)
        target=c5.number_input('Planned target ($)',min_value=0.0,value=104.0,step=0.5)
        note=st.text_input('Setup / reason','')
        submitted=st.form_submit_button('Record paper BUY',type='primary')
    if submitted:
        cost=int(qty)*float(entry)
        risk=(float(entry)-float(stop))*int(qty)
        rr=(float(target)-float(entry))/(float(entry)-float(stop)) if entry>stop else 0
        if not symbol or not symbol.replace('.','').isalpha(): st.error('Enter a valid ticker symbol.')
        elif stop<=0 or stop>=entry: st.error('Stop must be positive and below entry for this long-only practice ledger.')
        elif target<=entry: st.error('Target must be above entry.')
        elif cost>float(portfolio['cash']): st.error(f'Insufficient paper cash. Required ${cost:,.2f}; available ${portfolio["cash"]:,.2f}.')
        elif risk>float(cfg.get('max_loss_per_trade_usd',10)): st.error(f'Risk ${risk:,.2f} exceeds configured per-trade limit ${float(cfg.get("max_loss_per_trade_usd",10)):,.2f}.')
        elif rr<float(cfg.get('min_reward_risk',1.5)): st.error(f'Reward/risk {rr:.2f} is below configured minimum {cfg.get("min_reward_risk",1.5):.2f}.')
        else:
            portfolio['cash']=round(float(portfolio['cash'])-cost,2)
            portfolio['positions'].append({'symbol':symbol,'qty':int(qty),'entry':float(entry),'last_price':float(entry),'stop':float(stop),'target':float(target),'note':note,'opened_at':datetime.now(timezone.utc).isoformat()})
            save_json(PORTFOLIO,portfolio); st.success(f'Recorded simulated BUY: {qty} {symbol} at ${entry:.2f}.'); st.rerun()
    st.markdown('#### Update price or close a simulated position')
    if open_positions:
        labels=[f"{i}: {p['symbol']} · {p['qty']} shares · entry ${p['entry']:.2f}" for i,p in enumerate(open_positions)]
        idx=st.selectbox('Choose position',range(len(labels)),format_func=lambda x:labels[x])
        pos=open_positions[idx]
        newprice=st.number_input('Latest / exit price ($)',min_value=0.01,value=float(pos.get('last_price',pos['entry'])),step=0.5,key=f'price_{idx}')
        x,y=st.columns(2)
        if x.button('Update mark price'):
            pos['last_price']=float(newprice); save_json(PORTFOLIO,portfolio); st.success('Paper mark updated.'); st.rerun()
        if y.button('Close position at this price',type='primary'):
            pnl=(float(newprice)-float(pos['entry']))*int(pos['qty'])
            portfolio['cash']=round(float(portfolio['cash'])+float(newprice)*int(pos['qty']),2)
            portfolio['trades'].append({'symbol':pos['symbol'],'qty':pos['qty'],'entry':pos['entry'],'exit':float(newprice),'pnl':round(pnl,2),'closed_at':datetime.now(timezone.utc).isoformat(),'note':pos.get('note','')})
            portfolio['positions'].pop(idx); save_json(PORTFOLIO,portfolio); st.success(f'Closed simulated trade. P&L: ${pnl:+,.2f}'); st.rerun()
    else: st.info('No open paper positions.')

elif page == 'Trade Journal':
    st.subheader('Trade journal & performance')
    trades=portfolio.get('trades',[])
    if trades:
        df=pd.DataFrame(trades)
        pnlcol=pd.to_numeric(df['pnl'],errors='coerce').fillna(0)
        wins=int((pnlcol>0).sum()); losses=int((pnlcol<0).sum())
        a,b,c=st.columns(3); a.metric('Closed trades',len(df)); b.metric('Win rate',f'{wins/len(df)*100:.1f}%'); c.metric('Net realized P&L',f'${pnlcol.sum():+,.2f}')
        st.dataframe(df.sort_values('closed_at',ascending=False),use_container_width=True,hide_index=True)
        st.line_chart(df.sort_values('closed_at').assign(cumulative_pnl=pnlcol.loc[df.sort_values('closed_at').index].cumsum()).set_index('closed_at')['cumulative_pnl'])
        csv=df.to_csv(index=False).encode('utf-8')
        st.download_button('Download trade journal CSV',csv,'paper_trade_journal.csv','text/csv')
    else: st.info('Your closed simulated trades will appear here.')
    if st.button('Reset paper account',type='secondary'):
        st.session_state['confirm_reset']=True
    if st.session_state.get('confirm_reset'):
        st.warning('This permanently clears the local simulated portfolio and journal.')
        if st.button('Confirm reset paper account'):
            save_json(PORTFOLIO,{'starting_cash':float(cfg.get('budget',1000)),'cash':float(cfg.get('budget',1000)),'positions':[],'trades':[]})
            st.session_state['confirm_reset']=False; st.rerun()

elif page == 'Settings':
    st.subheader('Paper account settings')
    st.info('Settings apply to the local simulation and sizing checks only. No broker is connected.')
    with st.form('settings'):
        budget=st.number_input('Starting paper capital ($)',min_value=100.0,value=float(cfg.get('budget',1000)),step=100.0)
        maxrisk=st.number_input('Maximum loss per trade ($)',min_value=1.0,value=float(cfg.get('max_loss_per_trade_usd',10)),step=1.0)
        daily=st.number_input('Maximum daily loss ($)',min_value=1.0,value=float(cfg.get('max_daily_loss_usd',20)),step=1.0)
        rrmin=st.number_input('Minimum reward/risk ratio',min_value=0.5,value=float(cfg.get('min_reward_risk',1.5)),step=0.25)
        if st.form_submit_button('Save settings'):
            cfg.update({'budget':budget,'max_loss_per_trade_usd':maxrisk,'max_daily_loss_usd':daily,'min_reward_risk':rrmin,'paper':True,'broker':'none','allow_options':False,'allow_margin':False,'allow_short':False})
            save_json(CONFIG,cfg); st.success('Settings saved. Existing portfolio cash was not changed.')
    st.json({k:v for k,v in cfg.items() if k not in ('sec_user_agent',)})

st.divider()
st.caption('Educational paper-trading tool only. Data may be delayed or inaccurate. No strategy guarantees profit. Do not use scanner output alone to make investment decisions.')
