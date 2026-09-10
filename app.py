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

# 🎨 乾淨自然、無破版的燕麥暖奶風格
st.markdown("""
<style>
    /* 全站單一底色，上下滑動毫無色差斷層 */
    .stApp {
        background-color: #F4EFEA;
        color: #38281F;
    }
    
    .block-container {
        max-width: 960px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* 原生卡片容器風格微調 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FCFAF7 !important;
        border: 1px solid #E5DBD1 !important;
        border-radius: 14px !important;
        box-shadow: 0 2px 10px rgba(56, 40, 31, 0.03) !important;
    }

    /* 分頁導覽列自然融入 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #E8DFD5;
        padding: 4px;
        border-radius: 12px;
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 6px 16px;
        font-weight: 600;
        color: #695547;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FCFAF7 !important;
        color: #38281F !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* 表單背景融入 */
    [data-testid="stForm"] {
        background-color: #FCFAF7 !important;
        border: 1px solid #E5DBD1 !important;
        border-radius: 14px !important;
        padding: 20px !important;
    }

    /* 主按鈕沉穩深焙色 */
    div.stButton > button[kind="primary"] {
        background-color: #4A3428 !important;
        color: #FCFAF7 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #38261C !important;
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

# 頁首乾淨排版
col_h1, col_h2 = st.columns([6, 1])
with col_h1:
    st.title("☕ 辦公室咖啡續命站")
    st.caption("喝咖啡是基本人權！掌握消耗節奏、精準推算斷糧日～")
with col_h2:
    st.write("")
    if st.button("🔄 重新載入", use_container_width=True):
        st.rerun()

# 4. 原生 Container 卡片（不使用易破版的外部 HTML 容器）
c1, c2, c3, c4 = st.columns(4)

with c1:
    with st.container(border=True):
        st.caption("📦 櫃子還剩")
        st.subheader(f"{current_stock} 包未拆")
        stock_msg = "🚨 庫存告急" if current_stock <= 2 else "✨ 存量充足"
        st.caption(f"{stock_msg} (皇家 {royal_stock} ｜ 聖馬可 {marco_stock})")

with c2:
    with st.container(border=True):
        st.caption("⚡ 大家喝多快")
        if avg_days:
            st.subheader(f"{avg_days} 天/包")
            st.caption("大約這速度消滅一包")
        else:
            st.subheader("計算中")
            st.caption("開過不同天數豆子會自動算出")

with c3:
    with st.container(border=True):
        st.caption("⏳ 現有能撐多久")
        if days_left is not None:
            st.subheader(f"約 {days_left} 天")
            st.caption(f"這批已開喝第 {current_opened_days} 天")
        elif len(unpack_df) >= 1:
            st.subheader(f"第 {current_opened_days} 天")
            st.caption("累積下一批開豆開始倒數")
        else:
            st.subheader("尚未開豆")
            st.caption("快去茶水間拆第一包～")

with c4:
    with st.container(border=True):
        st.caption("📅 預估見底日")
        if estimated_finish_date:
            st.subheader(f"{estimated_finish_date}")
            st.caption("提早叫貨不斷糧！")
        else:
            st.subheader("推算中")
            st.caption("紀錄齊全後自動預測")

st.write("")

# 5. 操作分頁
tab1, tab2, tab3 = st.tabs(["☕ 我拆了新豆子！", "📦 咖啡豆到貨了！", "📊 飲用紀錄與趨勢"])

with tab1:
    st.markdown("#### 拆了新豆子？選一下就搞定（免打字）")
    with st.form("unpack_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            bean_choice = st.radio("拆哪一款？", ["皇家義大利", "聖馬可綜合", "其他豆款"], horizontal=True)
            custom_bean = ""
            if bean_choice == "其他豆款":
                custom_bean = st.text_input("輸入自訂豆款名稱")
        with f2:
            unpack_qty = st.number_input("開了幾包？", min_value=1, max_value=10, value=1, step=1)
            event_d = st.date_input("拆封日期", value=datetime.now().date())
            
        flavor = st.text_input("心得或風味備註（選填）", placeholder="例如：一次開兩包倒大機器、這批很香")
        
        btn_open = st.form_submit_button("🚀 開喝！登記拆封", use_container_width=True, type="primary")
        if btn_open:
            actual_bean = custom_bean if bean_choice == "其他豆款" else bean_choice
            if not actual_bean:
                st.error("請確認豆款名稱！")
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
    st.markdown("#### 買新豆子送到了？選一下就入庫")
    with st.form("restock_form", clear_on_submit=True):
        r1, r2 = st.columns(2)
        with r1:
            r_bean_choice = st.radio("送來哪一款？", ["皇家義大利", "聖馬可綜合", "其他豆款"], horizontal=True)
            r_custom = ""
            if r_bean_choice == "其他豆款":
                r_custom = st.text_input("輸入自訂到貨豆款")
        with r2:
            r_qty = st.number_input("來了幾包？", min_value=1, value=2, step=1)
            r_date = st.date_input("到貨日期", value=datetime.now().date())
            
        r_memo = st.text_input("備註說明（選填）", placeholder="例如：特價購入、單價 450 元")
        
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
    st.markdown("#### 📈 開豆歷史與消耗節奏")
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
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#38281F"),
            xaxis=dict(showgrid=False, title="開豆日期"),
            yaxis=dict(showgrid=True, gridcolor="#E5DBD1", title="拆封數量 (包)"),
            margin=dict(l=10, r=10, t=25, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 目前開豆紀錄還不到 2 筆，等大家多登記幾次，這裡就會呈現圖表囉！")

    st.markdown("#### 📋 歷史明細紀錄")
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
