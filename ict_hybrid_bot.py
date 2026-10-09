#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ICT / SMC Institutional Hybrid Telegram Bot & AI Co-Pilot
=============================================================================
Combines:
1. Real-time Multi-Timeframe ICT/SMC Technical Scanner (D1, H4, H1, M5)
2. Live Telegram Alert Dispatcher (Instant Entry Signals & Baseline Reports)
3. AI Trading Assistant (Gemini API) trained on ICT/SMC Books Knowledge Base
   allowing full two-way discussion and real-time chart interpretation.
=============================================================================
"""

import os
import sys
import time
import math
import json
import logging
import datetime
import requests
import pandas as pd

# Optional Yahoo Finance for standalone market data without MT5
try:
    import yfinance as yf
except ImportError:
    yf = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ICT_SMC_Bot")

# =====================================================================
# CONFIGURATION & CREDENTIALS
# =====================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8860065957:AAESKedQgtSmlAtTayKFtNZxsBhkOjUrWR4")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "912444971")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")  # Free API Key from Google AI Studio
SYMBOL             = os.getenv("SYMBOL", "GC=F")       # Gold Futures / XAUUSD (or EURUSD=X, GBPUSD=X)
CHECK_INTERVAL_SEC = int(os.getenv("CHECK_INTERVAL_SEC", "60"))

# =====================================================================
# TIME & KILLZONE ENGINE (NEW YORK EST)
# =====================================================================
def get_ny_time():
    """Returns current New York time (EST/EDT)."""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ny_tz = datetime.timezone(datetime.timedelta(hours=-5))
    return utc_now.astimezone(ny_tz)

def evaluate_killzones():
    ny_dt = get_ny_time()
    total_minutes = ny_dt.hour * 60 + ny_dt.minute

    asian_active = (total_minutes >= 20 * 60 or total_minutes == 0)
    london_active = (2 * 60 <= total_minutes < 5 * 60)
    ny_am_active = (7 * 60 <= total_minutes < 10 * 60)
    silver_bullet_active = (10 * 60 <= total_minutes < 11 * 60)
    pm_reversal_active = (13 * 60 <= total_minutes < 15 * 60 + 30)

    if silver_bullet_active:
        return "ICT SILVER BULLET (10:00 - 11:00 NY)", "REBALANCING / SCALPING EXTREMES", True
    elif ny_am_active:
        return "NEW YORK AM KILLZONE (07:00 - 10:00 NY)", "DISTRIBUTION / INSTITUTIONAL EXPANSION", True
    elif pm_reversal_active:
        return "NEW YORK PM SESSION (13:00 - 15:30 NY)", "PM REVERSAL / LIQUIDITY REBALANCING", True
    elif london_active:
        return "LONDON KILLZONE (02:00 - 05:00 NY)", "MANIPULATION (JUDAS SWING / ASIAN TRAP)", True
    elif asian_active:
        return "ASIAN SESSION (20:00 - 00:00 NY)", "ACCUMULATION (LIQUIDITY BUILDING)", False
    else:
        return "OUTSIDE OFFICIAL KILLZONES", "EQUILIBRIUM DRIFT", False

# =====================================================================
# MARKET DATA FETCHER (MULTI-TIMEFRAME)
# =====================================================================
def fetch_candles(symbol, interval, period="5d"):
    """
    Fetches real-time candles. interval can be '5m', '1h', '1d'.
    """
    if yf is None:
        logger.error("yfinance library not installed. Run: pip install yfinance")
        return pd.DataFrame()

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period=period)
        if df.empty and "GC" in symbol:
            ticker = yf.Ticker("XAUUSD=X")
            df = ticker.history(interval=interval, period=period)
        return df
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol} ({interval}): {e}")
        return pd.DataFrame()

# =====================================================================
# TECHNICAL ICT / SMC ALGORITHMIC ENGINE
# =====================================================================
def analyze_market_structure(df_d1, df_h1, df_m5):
    """
    Performs institutional top-down multi-timeframe ICT/SMC analysis:
    - Draw on Liquidity (PDH, PDL, Asian Range, Equal Highs/Lows)
    - Dealing Range (50% Equilibrium, Premium vs Discount, OTE)
    - Fair Value Gaps (FVG) and Order Blocks (OB)
    - Real-time setup scanning on M5
    """
    if df_d1.empty or df_h1.empty or df_m5.empty:
        return None

    current_price = float(df_m5['Close'].iloc[-1])

    # 1. Daily DOL (PDH / PDL)
    pdh = float(df_d1['High'].iloc[-2]) if len(df_d1) >= 2 else current_price * 1.01
    pdl = float(df_d1['Low'].iloc[-2]) if len(df_d1) >= 2 else current_price * 0.99
    pdh_swept = current_price >= pdh
    pdl_swept = current_price <= pdl

    d1_bias = "BULLISH" if df_d1['Close'].iloc[-1] > df_d1['Open'].iloc[-1] else "BEARISH"

    # 2. H1 Dealing Range & Equilibrium
    h1_high = float(df_h1['High'].tail(24).max())
    h1_low  = float(df_h1['Low'].tail(24).min())
    range_span = h1_high - h1_low
    equilibrium = h1_low + (range_span * 0.50)
    ote_62 = h1_low + (range_span * 0.62)
    ote_705 = h1_low + (range_span * 0.705) # Sweet Spot
    ote_79 = h1_low + (range_span * 0.79)

    pricing_zone = "PREMIUM (>50% - Institutional Sell Bias)" if current_price > equilibrium else "DISCOUNT (<50% - Institutional Buy Bias)"

    # 3. FVGs on M5
    fvgs = []
    for i in range(2, min(30, len(df_m5))):
        c_prev2 = df_m5.iloc[-i-1]
        c_curr  = df_m5.iloc[-i+1]
        if c_curr['Low'] > c_prev2['High']:
            top = float(c_curr['Low'])
            btm = float(c_prev2['High'])
            ce  = (top + btm) / 2.0
            fvgs.append({"type": "BULLISH (BISI)", "top": top, "bottom": btm, "ce": ce})
        elif c_curr['High'] < c_prev2['Low']:
            top = float(c_prev2['Low'])
            btm = float(c_curr['High'])
            ce  = (top + btm) / 2.0
            fvgs.append({"type": "BEARISH (SIBI)", "top": top, "bottom": btm, "ce": ce})

    nearest_fvg = None
    min_dist = float('inf')
    for f in fvgs:
        dist = abs(current_price - f['ce'])
        if dist < min_dist:
            min_dist = dist
            nearest_fvg = f

    # 4. Check Setups
    kz_name, amd_phase, is_kz_active = evaluate_killzones()
    signal = None

    # Silver Bullet Setup (10:00-11:00 NY)
    if "SILVER BULLET" in kz_name and nearest_fvg:
        if nearest_fvg['type'].startswith("BULLISH") and current_price <= nearest_fvg['top']:
            signal = {
                "name": "⚡ ICT SILVER BULLET (Bullish FVG Tap)",
                "direction": "BUY",
                "entry": current_price,
                "sl": nearest_fvg['bottom'] - 2.0,
                "tp1": current_price + 3.0,
                "tp2": h1_high,
                "reason": "Inside Silver Bullet 10-11 NY window, Bullish FVG retested in Discount zone."
            }
        elif nearest_fvg['type'].startswith("BEARISH") and current_price >= nearest_fvg['bottom']:
            signal = {
                "name": "⚡ ICT SILVER BULLET (Bearish FVG Tap)",
                "direction": "SELL",
                "entry": current_price,
                "sl": nearest_fvg['top'] + 2.0,
                "tp1": current_price - 3.0,
                "tp2": h1_low,
                "reason": "Inside Silver Bullet 10-11 NY window, Bearish FVG retested in Premium zone."
            }

    # Turtle Soup Setup
    if signal is None and len(df_m5) >= 2:
        last_m5 = df_m5.iloc[-2]
        if last_m5['High'] > pdh and last_m5['Close'] < pdh:
            signal = {
                "name": "🐢 TURTLE SOUP (PDH False Breakout SFP)",
                "direction": "SELL",
                "entry": current_price,
                "sl": float(last_m5['High']) + 2.0,
                "tp1": equilibrium,
                "tp2": pdl,
                "reason": "Wick swept Previous Day High (BSL) and closed back inside range."
            }
        elif last_m5['Low'] < pdl and last_m5['Close'] > pdl:
            signal = {
                "name": "🐢 TURTLE SOUP (PDL False Breakout SFP)",
                "direction": "BUY",
                "entry": current_price,
                "sl": float(last_m5['Low']) - 2.0,
                "tp1": equilibrium,
                "tp2": pdh,
                "reason": "Wick swept Previous Day Low (SSL) and closed back inside range."
            }

    return {
        "price": current_price,
        "d1_bias": d1_bias,
        "pdh": pdh,
        "pdl": pdl,
        "pdh_swept": pdh_swept,
        "pdl_swept": pdl_swept,
        "h1_high": h1_high,
        "h1_low": h1_low,
        "equilibrium": equilibrium,
        "ote_62": ote_62,
        "ote_705": ote_705,
        "ote_79": ote_79,
        "pricing_zone": pricing_zone,
        "killzone": kz_name,
        "amd_phase": amd_phase,
        "nearest_fvg": nearest_fvg,
        "signal": signal
    }

# =====================================================================
# TELEGRAM API CLIENT
# =====================================================================
def send_telegram_msg(token, chat_id, text):
    """Sends HTML formatted message to Telegram."""
    if not token or not chat_id:
        logger.warning("Telegram credentials not configured.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

# =====================================================================
# AI CO-PILOT AGENT (GEMINI API WITH ICT KNOWLEDGE BASE)
# =====================================================================
ICT_KNOWLEDGE_SYSTEM_PROMPT = """
أنت 'ICT/SMC Institutional Co-Pilot' خبير التداول المؤسسي العالمي والمحلل الفني البنكي.
أنت مستند ومبني بالكامل على مكتبة المراجع الـ 52 المعتمدة في مدرسة ICT و SMC (مثل كتاب ICT Mentorship 2022، MMXM، Liquidity University، Power of 3، Order Flow Setups، وغيرها).

قواعد تفكيرك وفلسفتك:
1. الأسعار تحركها خوارزمية بنكية (IPDA) بدافعين فقط: سحب السيولة (Liquidity Sweeps) وإعادة موازنة الفراغات السعرية (FVG Rebalancing).
2. التوقيت يسبق السعر (Time & Price): التداول حصراً داخل الكيلزونات (London, NY AM, Silver Bullet).
3. الفريمات الهرمية (Top-Down): الديلي والأربع ساعات يحددان المغناطيس السعري (DOL)، والساعة تحدد نطاق التعامل (50% Equilibrium)، والخمس دقائق والدقيقة للتنفيذ.
4. يمنع الشراء في منطقة العلاوة (Premium)، ويمنع البيع في منطقة الخصم (Discount).
5. تجيب باللغة العربية بأسلوب محترف وموجز ودقيق، مع ربط إجابتك بحالة الشارت الحالية وقواعد كتب ICT.
"""

def ask_gemini_copilot(user_query, market_context=""):
    """
    Sends user question and live market snapshot to Gemini API.
    """
    if not GEMINI_API_KEY:
        return "⚠️ لم يتم تفعيل مفتاح Gemini API بعد. يُرجى إضافة المفتاح في متغير GEMINI_API_KEY لتفعيل المحادثة الذكية ومناقشة الكتب."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
{ICT_KNOWLEDGE_SYSTEM_PROMPT}

سياق الشارت الفعلي اللحظي الآن:
{market_context}

سؤال أو استفسار المتداول:
{user_query}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"عذراً، حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {res.text}"
    except Exception as e:
        return f"حدث خطأ في الاتصال: {e}"

# =====================================================================
# FORMATTERS FOR BASELINE REPORT & LIVE ALERTS
# =====================================================================
def build_baseline_report(analysis):
    ny_dt = get_ny_time()
    p = analysis["price"]
    
    fvg_txt = "لا توجد فجوات نقية قريبة"
    if analysis["nearest_fvg"]:
        nf = analysis["nearest_fvg"]
        fvg_txt = f"{nf['type']} | الحدود: <code>{nf['bottom']:.2f}</code> ➔ <code>{nf['top']:.2f}</code> (المنتصف: <code>{nf['ce']:.2f}</code>)"

    msg = f"""<b>🏛️ [تقرير التحليل المؤسسي الذكي - PYTHON HYBRID BOT]</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>الأصل:</b> #{SYMBOL} | <b>السعر اللحظي:</b> <code>{p:.2f}</code>
<b>توقيت نيويورك:</b> {ny_dt.strftime('%H:%M EST')}
<b>الجلسة والكيلزون:</b> {analysis['killzone']}
<b>مرحلة دورة IPDA:</b> {analysis['amd_phase']}

<b>1️⃣ مصفوفة الهيكل المؤسسي (HTF Structure):</b>
• <b>اتجاه اليومي (D1):</b> {'🟢 صاعد' if analysis['d1_bias'] == 'BULLISH' else '🔴 هابط'}
• <b>بيئة التسعير الحالية:</b> {analysis['pricing_zone']}

<b>2️⃣ مغانط السيولة الكبرى (Draw on Liquidity):</b>
• <b>قمة الأمس (PDH - BSL):</b> <code>{analysis['pdh']:.2f}</code> [{'✅ مسحوبة' if analysis['pdh_swept'] else '🎯 مفتوحة'}]
• <b>قاع الأمس (PDL - SSL):</b> <code>{analysis['pdl']:.2f}</code> [{'✅ مسحوب' if analysis['pdl_swept'] else '🎯 مفتوح'}]

<b>3️⃣ نطاق التعامل والتسعير على H1:</b>
• <b>نطاق الموجة:</b> <code>{analysis['h1_low']:.2f}</code> ➔ <code>{analysis['h1_high']:.2f}</code>
• <b>مستوى التوازن 50%:</b> <code>{analysis['equilibrium']:.2f}</code>
• <b>مستويات OTE الذهبية:</b> 62%: <code>{analysis['ote_62']:.2f}</code> | 70.5%: <code>{analysis['ote_705']:.2f}</code> | 79%: <code>{analysis['ote_79']:.2f}</code>

<b>4️⃣ أقرب مناطق الاهتمام (Nearest POI on M5):</b>
• <b>أقرب FVG:</b> {fvg_txt}

<b>💡 توجيه المساعد الذكي:</b>
{'🚫 يمنع الشراء تماماً في منطقة العلاوة الحالية! انتظر كسر هيكل M5 للدخول بيعاً.' if 'PREMIUM' in analysis['pricing_zone'] else '🚫 يمنع البيع في منطقة الخصم! ابحث عن صفقات الشراء مع فجوات الطلب.'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 <i>تقدر تتناقش وياي مباشرة! اكتب لي أي سؤال أو استفسار وسأجيبك فوراً استناداً إلى كتب ICT وموقع الشارت الحالي.</i>"""
    return msg

# =====================================================================
# MAIN RUN LOOP & TELEGRAM INTERACTIVE LISTENER
# =====================================================================
def run_bot():
    logger.info("Starting ICT/SMC Hybrid Python Bot...")
    
    # 1. Initial Analysis & Baseline Report
    df_d1 = fetch_candles(SYMBOL, "1d", "1mo")
    df_h1 = fetch_candles(SYMBOL, "1h", "5d")
    df_m5 = fetch_candles(SYMBOL, "5m", "2d")
    
    analysis = analyze_market_structure(df_d1, df_h1, df_m5)
    if analysis:
        report = build_baseline_report(analysis)
        send_telegram_msg(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, report)
        logger.info("Baseline report sent to Telegram.")

    # 2. Main Monitoring & Chat Listener Loop
    last_update_id = 0
    last_signal_hash = ""

    while True:
        try:
            # Poll Telegram Updates for user chat messages
            updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=5"
            res = requests.get(updates_url, timeout=10)
            if res.status_code == 200:
                updates = res.json().get("result", [])
                for upd in updates:
                    last_update_id = upd["update_id"]
                    msg_obj = upd.get("message", {})
                    chat_id = str(msg_obj.get("chat", {}).get("id", ""))
                    text = msg_obj.get("text", "")

                    if text and chat_id == str(TELEGRAM_CHAT_ID):
                        logger.info(f"User message received: {text}")
                        if text == "/report":
                            cur_analysis = analyze_market_structure(
                                fetch_candles(SYMBOL, "1d", "1mo"),
                                fetch_candles(SYMBOL, "1h", "5d"),
                                fetch_candles(SYMBOL, "5m", "2d")
                            )
                            if cur_analysis:
                                send_telegram_msg(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, build_baseline_report(cur_analysis))
                        else:
                            cur_analysis = analyze_market_structure(
                                fetch_candles(SYMBOL, "1d", "1mo"),
                                fetch_candles(SYMBOL, "1h", "5d"),
                                fetch_candles(SYMBOL, "5m", "2d")
                            )
                            ctx = f"السعر: {cur_analysis['price'] if cur_analysis else 'N/A'}, الكيلزون: {cur_analysis['killzone'] if cur_analysis else 'N/A'}, البيئة: {cur_analysis['pricing_zone'] if cur_analysis else 'N/A'}"
                            ai_reply = ask_gemini_copilot(text, ctx)
                            send_telegram_msg(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"🧠 <b>المساعد المؤسسي:</b>\n\n{ai_reply}")

            # Check for M5 Trade Signals
            df_m5_fresh = fetch_candles(SYMBOL, "5m", "1d")
            if not df_m5_fresh.empty:
                cur_analysis = analyze_market_structure(df_d1, df_h1, df_m5_fresh)
                if cur_analysis and cur_analysis.get("signal"):
                    sig = cur_analysis["signal"]
                    sig_hash = sig["name"] + str(round(sig["entry"], 2))
                    if sig_hash != last_signal_hash:
                        last_signal_hash = sig_hash
                        alert_msg = f"""<b>🎯 [{sig['name']}]</b>
━━━━━━━━━━━━━━━━━━━━
<b>الأصل:</b> #{SYMBOL} | <b>الاتجاه:</b> {'🟢 شراء (BUY)' if sig['direction'] == 'BUY' else '🔴 بيع (SELL)'}
• <b>سعر الدخول:</b> <code>{sig['entry']:.2f}</code>
• <b>وقف الخسارة:</b> <code>{sig['sl']:.2f}</code>
• <b>الهدف الأول:</b> <code>{sig['tp1']:.2f}</code>
• <b>الهدف الثاني:</b> <code>{sig['tp2']:.2f}</code>
• <b>التعليل المؤسسي:</b> <i>{sig['reason']}</i>"""
                        send_telegram_msg(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, alert_msg)
                        logger.info(f"Signal alert sent: {sig['name']}")

        except Exception as e:
            logger.error(f"Error in main loop: {e}")

        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    run_bot()
