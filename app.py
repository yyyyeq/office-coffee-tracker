import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import plotly.express as px

# 1. 頁面設定
st.set_page_config(
    page_title="辦公室咖啡續命站",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🎨 絲滑流暢特調色盤：消滅死白與生硬跳色
st.markdown("""
<style>
    /* 全站溫潤燕麥奶底色 */
    .stApp {
        background-color: #FAF6F0;
        color: #3C2A21;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    
    /* 頂部 Header 造型區塊 */
    .header-box {
        background: linear-gradient(135deg, #4A3428 0%, #2D1E17 100%);
        border-radius: 20px;
        padding: 24px 30px;
        color: #FDFBF7;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(45, 30, 23, 0.15);
    }
    .header-title {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-desc {
        color: #D7C4B7;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    /* 四張質感指標卡片 */
    .card-base {
        border-radius: 18px;
        padding: 20px 22px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.6);
    }
    .card-base:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(74, 52, 40, 0.12);
    }
    
    .card-stock {
        background: linear-gradient(135deg, #FFFDF8 0%, #F5EBE1 100%);
        border-left: 6px solid #C87D55;
        box-shadow: 0 6px 16px rgba(200, 125, 85, 0.1);
    }
    .card-speed {
        background: linear-gradient(135deg, #FDFAF5 0%, #F3EBDD 100%);
        border-left: 6px solid #D4A373;
        box-shadow: 0 6px 16px rgba(212, 163, 115, 0.1);
    }
    .card-days {
        background: linear-gradient(135deg, #FBF8F5 0%, #EBDBCB 100%);
        border-left: 6px solid #8C6239;
        box-shadow: 0 6px 16px rgba(140, 98, 57, 0.1);
    }
    .card-forecast {
        background: linear-gradient(135deg, #F7F5F8 0%, #E6E1E8 100%);
        border-left: 6px solid #786D7D;
        box-shadow: 0 6px 16px rgba(120, 109, 125, 0.1);
    }

    .card-label {
        font-size: 0.88rem;
        font-weight: 700;
        color: #634832;
        margin-bottom: 8px;
    }
    .card-num {
        font-size: 2.2rem;
        font-weight: 900;
        color: #2B1810;
        line-height: 1.1;
    }
    .card-unit {
        font-size: 1rem;
        font-weight: 600;
        color: #7D6B5D;
    }
    .card-footer {
        font-size: 0.8rem;
        margin-top: 10px;
        color: #8C7565;
        font-weight: 500;
    }
    
    .pill-green {
        background: #E8F5E9;
        color: #2E7D32;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .pill-red {
        background: #FFEBEE;
        color: #C62828;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.75rem;
    }

    /* 解決死白切換：分頁條改為暖調深淺融合 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #EAE1D7 !important;
        padding: 6px;
        border-radius: 16px;
        border: 1px solid #DDCFC2;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 9px 20px;
        font-weight: 700;
        color: #6C5547 !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.25s ease-in-out !important;
    }
    /* 選中分頁時：厚奶泡米白，帶柔和陰影 */
    .stTabs [aria-selected="true"] {
        background-color: #FAF6F0 !important;
        color: #3C2A21 !important;
        box-shadow: 0 4px 12px rgba(60, 42, 33, 0.08) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* 表單容器外觀：溫暖厚奶泡白，銜接自然 */
    [data-testid="stForm"] {
        background: #FAF6F0 !important;
        border: 1.5px solid #E5D9CC !important;
        border-radius: 20px !important;
        padding: 24px 28px !important;
        box-shadow: 0 8px 24px rgba(74, 52, 40, 0.04) !important;
    }

    /* 單選項目（豆款按鈕）：膠囊卡片化微調 */
    div[data-testid="stRadio"] > div {
        gap: 12px;
    }
    div[data-testid="stRadio"] label {
        background: #F2EAE0;
        padding: 6px 14px;
        border-radius: 10px;
        border: 1px solid #E0D3C4;
        transition: all 0.2s ease;
    }
    div[data-testid="stRadio"] label:hover {
        background: #E8DCCF;
    }

    /* 主要按鈕：深焙拿鐵漸層 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7A4930 0%, #4A2818 100%) !important;
        color: #FFF6EE !important;
        border: none !important;
        padding: 12px 24px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 15px rgba(74, 40, 24, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(74, 40, 24, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. 連線 Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ 請確認 Streamlit Secrets 已正確設定 SUPABASE_URL 與 SUPABASE_KEY")
    st.stop()

def fetch_data():
    res = supabase.table("coffee_records").select("*").order("event_date", desc=True).order("created_at", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    return df

df = fetch_data()

# 頂部質感 Header
st.markdown("""
<div class="header-box">
    <div class="header-title">☕ 辦公室咖啡續命站</div>
    <div class="header-desc">喝咖啡是基本人權！掌握消耗節奏、精準推算斷糧日，缺豆前準時補貨～</div>
</div>
""", unsafe_allow_html=True)

# 分流資料
unpack_df = df[df["event_type"] == "UNPACK"].copy() if not df.empty else pd.DataFrame()
restock_df = df[df["event_type"] == "RESTOCK"].copy() if not df.empty else pd.DataFrame()

# 3. 核心數據計算
total_restocked = len(restock_df)
total_unpacked = len(unpack_df)
current_stock = max(0, total_restocked - total_unpacked)

royal_stock = max(0, len(restock_df[restock_df["bean_name"] == "皇家義大利"]) - len(unpack_df[unpack_df["bean_name"] == "皇家義大利"]))
marco_stock = max(0, len(restock_df[restock_df["bean_name"] == "聖馬可綜合"]) - len(unpack_df[unpack_df["bean_name"] == "聖馬可綜合"]))

avg_days = None
days_left = None
estimated_finish_date = None
current_opened_days = 0

if len(unpack_df) >= 2:
    sorted_unpacks = unpack_df.sort_values("event_date").reset_index(drop=True)
    first_date = sorted_unpacks["event_date"].iloc[0]
    latest_date = sorted_unpacks["event_date"].iloc[-1]
    span_days = (latest_date - first_date).days
    
    if span_days > 0 and len(sorted_unpacks) > 1:
        recent_unpacks = sorted_unpacks.tail(6)
        r_span = (recent_unpacks["event_date"].iloc[-1] - recent_unpacks["event_date"].iloc[0]).days
        if r_span > 0:
            avg_days = round(r_span / (len(recent_unpacks) - 1), 1)
        else:
            avg_days = round(span_days / (len(sorted_unpacks) - 1), 1)
            
        today = datetime.now().date()
        current_opened_days = (today - latest_date).days
        
        latest_batch_count = len(sorted_unpacks[sorted_unpacks["event_date"] == latest_date])
        total_batch_expected_days = avg_days * latest_batch_count
        
        days_left = max(0, int(total_batch_expected_days - current_opened_days))
        estimated_finish_date = latest_date + timedelta(days=int(total_batch_expected_days))
elif len(unpack_df) >= 1:
    today = datetime.now().date()
    current_opened_days = (today - unpack_df["event_date"].iloc[-1]).days

# 4. 四張專屬漸層卡片
c1, c2, c3, c4 = st.columns(4)

with c1:
    pill_class = "pill-red" if current_stock <= 2 else "pill-green"
    pill_label = "🚨 庫存告急！" if current_stock <= 2 else "✨ 儲備充裕"
    st.markdown(f"""
    <div class="card-base card-stock">
        <div class="card-label">📦 櫃子裡還剩幾包？</div>
        <div class="card-num">{current_stock} <span class="card-unit">包未拆</span></div>
        <div class="card-footer">
            <span class="{pill_class}">{pill_label}</span>
            <div style="margin-top: 6px; font-weight:600; color:#5D4037;">
                👑 皇家: {royal_stock} 包 ｜ ☕ 聖馬可: {marco_stock} 包
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    v_speed = f"{avg_days}" if avg_days else "抓數據中"
    u_speed = "<span class='card-unit'>天 / 包</span>" if avg_days else ""
    sub_speed = "大約這速度消滅一包" if avg_days else "開過不同天的豆子會自動算出"
    st.markdown(f"""
    <div class="card-base card-speed">
        <div class="card-label">⚡ 大家喝有多快？</div>
        <div class="card-num">{v_speed} {u_speed}</div>
        <div class="card-footer">{sub_speed}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    if days_left is not None:
        v_left = f"{days_left}"
        u_left = "<span class='card-unit'>天</span>"
        sub_left = f"現有這批已開喝第 {current_opened_days} 天"
    elif len(unpack_df) >= 1:
        v_left = f"{current_opened_days}"
        u_left = "<span class='card-unit'>天</span>"
        sub_left = "累積下一批開豆就會開始倒數！"
    else:
        v_left = "尚未開"
        u_left = ""
        sub_left = "快去茶水間拆第一包～"
        
    st.markdown(f"""
    <div class="card-base card-days">
        <div class="card-label">⏳ 正在喝的能撐多久？</div>
        <div class="card-num">{v_left} {u_left}</div>
        <div class="card-footer">{sub_left}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    v_date = f"{estimated_finish_date}" if estimated_finish_date else "推算中"
    sub_date = "提前叫貨才不會斷糧！" if estimated_finish_date else "資料齊全後自動預測"
    st.markdown(f"""
    <div class="card-base card-forecast">
        <div class="card-label">📅 預估哪天見底？</div>
        <div class="card-num" style="font-size: 1.8rem; font-weight:800;">{v_date}</div>
        <div class="card-footer">{sub_date}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 預警小提醒
if current_stock == 0:
    st.error("😱 **重大斷糧警報**：櫃子裡已經完全**沒有庫存**了！這包喝完就真的沒了，快去叫貨！")
elif current_stock <= 2:
    st.warning(f"⚠️ **咖啡告急**：只剩最後 {current_stock} 包存貨！建議現在就可以準備下單囉～")

# 5. 操作分頁
tab1, tab2, tab3 = st.tabs(["☕ 我拆了新豆子！", "📦 咖啡豆到貨了！", "📊 飲用紀錄與趨勢"])

with tab1:
    st.markdown("### ✨ 拆了新豆子？選一下就搞定（免打字）")
    st.caption("隨手點選兩下，系統幫你全自動計算辦公室飲用頻率～")
    with st.form("unpack_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            bean_choice = st.radio(
                "這次拆的是哪一款？", 
                ["皇家義大利", "聖馬可綜合", "其他豆款"],
                horizontal=True
            )
            custom_bean = ""
            if bean_choice == "其他豆款":
                custom_bean = st.text_input("請輸入自訂豆款名稱")
        with c2:
            unpack_qty = st.number_input("這次一次開了幾包？", min_value=1, max_value=10, value=1, step=1)
            event_d = st.date_input("拆封日期", value=datetime.now().date())
            
        flavor = st.text_input("心得或風味備註（選填）", placeholder="例如：一次倒兩包進大咖啡機、今天這包香氣很棒！")
        
        btn_open = st.form_submit_button("🚀 開喝！登記拆封", use_container_width=True, type="primary")
        if btn_open:
            actual_bean = custom_bean if bean_choice == "其他豆款" else bean_choice
            if not actual_bean:
                st.error("請確認豆款名稱喔！")
            else:
                records = [{
                    "event_type": "UNPACK",
                    "bean_name": actual_bean,
                    "weight_g": 454,
                    "operator": "善心同事",
                    "event_date": str(event_d),
                    "note": f"{flavor} (一次開 {unpack_qty} 包之 #{i+1})" if unpack_qty > 1 and flavor else (f"一次開 {unpack_qty} 包之第 {i+1} 包" if unpack_qty > 1 else flavor)
                } for i in range(unpack_qty)]
                
                supabase.table("coffee_records").insert(records).execute()
                st.toast(f"🎉 成功登記拆封 {unpack_qty} 包「{actual_bean}」！續命泉源已補充 ✨")
                st.rerun()

with tab2:
    st.markdown("### 📦 買新豆子送到了？選一下就入庫")
    st.caption("採購到貨時點一下，立刻為辦公室補充未拆封庫存！")
    with st.form("restock_form", clear_on_submit=True):
        r1, r2 = st.columns(2)
        with r1:
            r_bean_choice = st.radio(
                "這次送來的是哪一款？", 
                ["皇家義大利", "聖馬可綜合", "其他豆款"],
                horizontal=True
            )
            r_custom = ""
            if r_bean_choice == "其他豆款":
                r_custom = st.text_input("請輸入自訂豆款名稱")
        with r2:
            r_qty = st.number_input("這次來了幾包？", min_value=1, value=2, step=1)
            r_date = st.date_input("到貨日期", value=datetime.now().date())
            
        r_memo = st.text_input("備註說明（選填）", placeholder="例如：特價購入、單價 450 元")
        
        btn_stock = st.form_submit_button("📦 把豆子放進櫃子（入庫）", use_container_width=True, type="primary")
        if btn_stock:
            actual_r_bean = r_custom if r_bean_choice == "其他豆款" else r_bean_choice
            if not actual_r_bean:
                st.error("請確認到貨的豆款名稱！")
            else:
                records = [{
                    "event_type": "RESTOCK",
                    "bean_name": actual_r_bean,
                    "weight_g": 454,
                    "operator": "公司採購",
                    "event_date": str(r_date),
                    "note": f"{r_memo} (第 {i+1} 包)" if r_qty > 1 and r_memo else (f"批次入庫第 {i+1} 包" if r_qty > 1 else r_memo)
                } for i in range(r_qty)]
                supabase.table("coffee_records").insert(records).execute()
                st.toast(f"📦 已將 {r_qty} 包「{actual_r_bean}」放入庫存！")
                st.rerun()

with tab3:
    st.markdown("### 📈 開豆歷史與消耗節奏")
    if len(unpack_df) >= 2:
        daily_unpacks = unpack_df.groupby(["event_date", "bean_name"]).size().reset_index(name="拆封包數")
        
        fig = px.bar(
            daily_unpacks, 
            x="event_date", 
            y="拆封包數", 
            text="拆封包數",
            color="bean_name",
            labels={"event_date": "拆封日期", "拆封包數": "開了幾包", "bean_name": "咖啡豆"},
            color_discrete_map={"皇家義大利": "#5C382A", "聖馬可綜合": "#C87D55"}
        )
        fig.update_traces(texttemplate='%{text} 包', textposition='outside')
        fig.update_layout(
            plot_bgcolor="rgba(255,255,255,0.7)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#3C2A21"),
            xaxis=dict(showgrid=False, title="開豆日期"),
            yaxis=dict(showgrid=True, gridcolor="#EFE6DC", title="拆封數量 (包)"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 目前開豆紀錄還不到 2 筆，等大家多登記幾次，這裡就會呈現各豆款的開豆歷史圖表囉！")

    st.markdown("### 📋 過去所有的開豆與補貨紀錄")
    if not df.empty:
        display_df = df.copy()
        display_df["動作"] = display_df["event_type"].map({"UNPACK": "☕ 拆封開喝", "RESTOCK": "📦 進貨補庫存"})
        display_df = display_df.rename(columns={
            "id": "編號",
            "event_date": "日期",
            "bean_name": "咖啡豆款",
            "weight_g": "克數",
            "note": "備註說明"
        })
        st.dataframe(
            display_df[["編號", "日期", "動作", "咖啡豆款", "克數", "備註說明"]],
            use_container_width=True,
            hide_index=True
        )
        
        with st.expander("🗑️ 手滑填錯了？按這裡刪除"):
            del_id = st.number_input("輸入要刪除的編號 (ID)", step=1, value=0)
            if st.button("確認刪掉這筆", type="secondary"):
                if del_id > 0:
                    supabase.table("coffee_records").delete().eq("id", del_id).execute()
                    st.success(f"已刪除編號 {del_id} 紀錄！")
                    st.rerun()
    else:
        st.caption("目前空空如也，快去登記第一筆吧！")
