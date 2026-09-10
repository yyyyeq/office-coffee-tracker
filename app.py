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

# 🎨 現代輕透咖啡館風格（告別生硬焊死感）
st.markdown("""
<style>
    /* 全站溫潤奶茶底色 */
    .stApp {
        background-color: #F8F5F0;
        color: #2D241E;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .block-container {
        max-width: 1050px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* 原生卡片容器注入輕透呼吸感 */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #EBE4DC !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(78, 52, 46, 0.04) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(78, 52, 46, 0.08) !important;
    }

    /* 指標小標籤與數值樣式 */
    .stat-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #8C7A6B;
        letter-spacing: 0.3px;
        margin-bottom: 4px;
    }
    .stat-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #2D241E;
        line-height: 1.1;
    }
    .stat-unit {
        font-size: 0.95rem;
        font-weight: 500;
        color: #8C7A6B;
        margin-left: 2px;
    }
    .stat-footer {
        font-size: 0.8rem;
        color: #A19183;
        margin-top: 6px;
    }

    /* 狀態晶片 */
    .chip {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .chip-warning { background: #FDE8E8; color: #C81E1E; }
    .chip-success { background: #EDF7EE; color: #2E7D32; }

    /* 分頁導覽列（原生膠囊質感） */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #EFE9E2;
        padding: 5px;
        border-radius: 14px;
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 18px;
        font-weight: 600;
        color: #7A695B;
        border: none !important;
        background: transparent !important;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2D241E !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* 表單邊框與輸入框柔化 */
    [data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 1px solid #EBE4DC !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 4px 16px rgba(78, 52, 46, 0.03) !important;
    }

    /* 主按鈕：優雅烘焙咖啡棕 */
    div.stButton > button[kind="primary"] {
        background-color: #4A3428 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(74, 52, 40, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #38261C !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(74, 52, 40, 0.3) !important;
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

# 原生流暢 Header
head_col1, head_col2 = st.columns([5, 1])
with head_col1:
    st.title("☕ 辦公室咖啡續命站")
    st.caption("喝咖啡是基本人權！即時算出喝多快、哪天斷糧，缺豆前準時補貨～")
with head_col2:
    if st.button("🔄 重整", use_container_width=True):
        st.rerun()

# 拆分開豆與到貨
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

# 4. 原生 Border 容器（徹底解決焊死感）
c1, c2, c3, c4 = st.columns(4)

with c1:
    with st.container(border=True):
        st.markdown('<div class="stat-label">📦 櫃子裡還剩</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{current_stock}<span class="stat-unit">包未拆</span></div>', unsafe_allow_html=True)
        chip_cls = "chip-warning" if current_stock <= 2 else "chip-success"
        chip_txt = "🚨 庫存告急" if current_stock <= 2 else "✨ 儲備充裕"
        st.markdown(f"""
        <div class="stat-footer">
            <span class="chip {chip_cls}">{chip_txt}</span>
            <div style="margin-top:5px; font-weight:600; color:#5D4037;">皇家: {royal_stock} ｜ 聖馬可: {marco_stock}</div>
        </div>
        """, unsafe_allow_html=True)

with c2:
    with st.container(border=True):
        st.markdown('<div class="stat-label">⚡ 大家喝有多快</div>', unsafe_allow_html=True)
        val = f"{avg_days}<span class='stat-unit'>天/包</span>" if avg_days else "計算中"
        sub = "約這速度喝完一包" if avg_days else "開過不同天的豆會算出"
        st.markdown(f'<div class="stat-value">{val}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-footer">{sub}</div>', unsafe_allow_html=True)

with c3:
    with st.container(border=True):
        st.markdown('<div class="stat-label">⏳ 這包還能撐多久</div>', unsafe_allow_html=True)
        if days_left is not None:
            val_l = f"約 {days_left}<span class='stat-unit'>天</span>"
            sub_l = f"現有這批已開第 {current_opened_days} 天"
        elif len(unpack_df) >= 1:
            val_l = f"第 {current_opened_days}<span class='stat-unit'>天</span>"
            sub_l = "累積下批開豆開始倒數"
        else:
            val_l = "尚未開"
            sub_l = "快去拆第一包～"
        st.markdown(f'<div class="stat-value">{val_l}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-footer">{sub_l}</div>', unsafe_allow_html=True)

with c4:
    with st.container(border=True):
        st.markdown('<div class="stat-label">📅 預估哪天見底</div>', unsafe_allow_html=True)
        val_d = f"{estimated_finish_date}" if estimated_finish_date else "推算中"
        sub_d = "提早叫貨不斷糧！" if estimated_finish_date else "資料齊全後預測"
        st.markdown(f'<div class="stat-value" style="font-size:1.75rem;">{val_d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-footer">{sub_d}</div>', unsafe_allow_html=True)

st.write("")

if current_stock == 0:
    st.error("😱 **重大斷糧警報**：櫃子裡已經完全**沒有庫存**了！這包喝完就真的沒了，快去叫貨！")
elif current_stock <= 2:
    st.warning(f"⚠️ **咖啡告急**：只剩最後 {current_stock} 包存貨！建議現在就可以準備下單囉～")

# 5. 操作分頁
tab1, tab2, tab3 = st.tabs(["☕ 我拆了新豆子！", "📦 咖啡豆到貨了！", "📊 飲用紀錄與趨勢"])

with tab1:
    st.markdown("##### 拆了新豆子？選一下就搞定（免打字）")
    with st.form("unpack_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            bean_choice = st.radio("拆哪一款？", ["皇家義大利", "聖馬可綜合", "其他豆款"], horizontal=True)
            custom_bean = st.text_input("輸入自訂豆款") if bean_choice == "其他豆款" else ""
        with c2:
            unpack_qty = st.number_input("開了幾包？", min_value=1, max_value=10, value=1, step=1)
            event_d = st.date_input("拆封日期", value=datetime.now().date())
            
        flavor = st.text_input("心得或風味備註（選填）", placeholder="例如：一次開兩包倒大機器、這批很香")
        
        btn_open = st.form_submit_button("🚀 開喝！登記拆封", use_container_width=True, type="primary")
        if btn_open:
            actual_bean = custom_bean if bean_choice == "其他豆款" else bean_choice
            if not actual_bean:
                st.error("請填寫豆款名稱！")
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
                st.toast(f"🎉 成功登記拆封 {unpack_qty} 包「{actual_bean}」！")
                st.rerun()

with tab2:
    st.markdown("##### 買新豆子送到了？選一下就入庫")
    with st.form("restock_form", clear_on_submit=True):
        r1, r2 = st.columns(2)
        with r1:
            r_bean_choice = st.radio("送來哪一款？", ["皇家義大利", "聖馬可綜合", "其他豆款"], horizontal=True)
            r_custom = st.text_input("輸入自訂到貨豆款") if r_bean_choice == "其他豆款" else ""
        with r2:
            r_qty = st.number_input("來了幾包？", min_value=1, value=2, step=1)
            r_date = st.date_input("到貨日期", value=datetime.now().date())
            
        r_memo = st.text_input("備註（選填）", placeholder="例如：特價購入、單價 450 元")
        
        btn_stock = st.form_submit_button("📦 把豆子放進櫃子（入庫）", use_container_width=True, type="primary")
        if btn_stock:
            actual_r_bean = r_custom if r_bean_choice == "其他豆款" else r_bean_choice
            if not actual_r_bean:
                st.error("請確認到貨豆款！")
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
    st.markdown("##### 📈 開豆歷史與消耗節奏")
    if len(unpack_df) >= 2:
        daily_unpacks = unpack_df.groupby(["event_date", "bean_name"]).size().reset_index(name="拆封包數")
        
        fig = px.bar(
            daily_unpacks, 
            x="event_date", 
            y="拆封包數", 
            text="拆封包數",
            color="bean_name",
            labels={"event_date": "拆封日期", "拆封包數": "開了幾包", "bean_name": "咖啡豆"},
            color_discrete_map={"皇家義大利": "#4A3428", "聖馬可綜合": "#A2704E"}
        )
        fig.update_traces(texttemplate='%{text} 包', textposition='outside')
        fig.update_layout(
            plot_bgcolor="rgba(255,255,255,0)",
            paper_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#2D241E"),
            xaxis=dict(showgrid=False, title="開豆日期"),
            yaxis=dict(showgrid=True, gridcolor="#EBE4DC", title="拆封數量 (包)"),
            margin=dict(l=10, r=10, t=25, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 目前開豆紀錄還不到 2 筆，等大家多登記幾次，這裡就會呈現圖表囉！")

    st.markdown("##### 📋 歷史明細紀錄")
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
