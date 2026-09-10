import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import plotly.express as px

# 1. 頁面基本設定
st.set_page_config(page_title="辦公室咖啡豆頻率追蹤系統", page_icon="☕", layout="wide")

# 2. 連線 Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("請確認 .streamlit/secrets.toml 已設定 SUPABASE_URL 與 SUPABASE_KEY")
    st.stop()

# 讀取資料函數
def fetch_data():
    res = supabase.table("coffee_records").select("*").order("event_date", desc=True).order("created_at", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    return df

st.title("☕ 辦公室咖啡豆消耗頻率追蹤系統")
st.caption("即時掌握開豆週期、推算喝完日期，告別缺豆斷糧！")

df = fetch_data()

# 拆分開豆紀錄與進貨紀錄
unpack_df = df[df["event_type"] == "UNPACK"].copy() if not df.empty else pd.DataFrame()
restock_df = df[df["event_type"] == "RESTOCK"].copy() if not df.empty else pd.DataFrame()

# ----------------------------------------------------
# 3. 核心指標與消耗頻率推算 (Metrics)
# ----------------------------------------------------
total_restocked = len(restock_df)
total_unpacked = len(unpack_df)
current_stock_bags = max(0, total_restocked - total_unpacked)

# 計算消耗頻率（平均每包撐幾天）
avg_days_per_bag = None
days_left = None
estimated_finish_date = None

if len(unpack_df) >= 2:
    # 按照時間由舊到新排序計算間隔
    sorted_unpacks = unpack_df.sort_values("event_date").reset_index(drop=True)
    sorted_unpacks["prev_date"] = sorted_unpacks["event_date"].shift(1)
    sorted_unpacks["duration_days"] = (pd.to_datetime(sorted_unpacks["event_date"]) - pd.to_datetime(sorted_unpacks["prev_date"])).dt.days
    
    # 計算近 5 包的滾動平均天數（排除首筆 NaN）
    recent_durations = sorted_unpacks["duration_days"].dropna().tail(5)
    if not recent_durations.empty and recent_durations.mean() > 0:
        avg_days_per_bag = round(recent_durations.mean(), 1)
        
        # 推算最新開的這包何時會喝完
        latest_open_date = sorted_unpacks["event_date"].iloc[-1]
        today = datetime.now().date()
        days_opened = (today - latest_open_date).days
        days_left = max(0, int(avg_days_per_bag - days_opened))
        estimated_finish_date = latest_open_date + timedelta(days=int(avg_days_per_bag))

# 顯示頂部儀表板卡片
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("未拆封庫存 (包)", f"{current_stock_bags} 包", delta="庫存充足" if current_stock_bags >= 2 else "-庫存吃緊", delta_color="normal" if current_stock_bags >= 2 else "inverse")
with col2:
    st.metric("平均消耗速度", f"{avg_days_per_bag} 天/包" if avg_days_per_bag else "資料積累中")
with col3:
    st.metric("當前這包預計剩餘", f"約 {days_left} 天" if days_left is not None else "計算中")
with col4:
    st.metric("建議補貨/喝完日", f"{estimated_finish_date}" if estimated_finish_date else "計算中")

# 警示提醒
if current_stock_bags <= 1:
    st.warning("⚠️ **庫存預警**：未拆封庫存剩餘不足 2 包，請記得預先安排採購！")

st.divider()

# ----------------------------------------------------
# 4. 登記區域（分頁標籤：開豆打卡 vs 進貨登記）
# ----------------------------------------------------
tab_unpack, tab_restock, tab_stats = st.tabs(["✨ 拆封新豆打卡", "📦 進貨入庫登記", "📊 頻率分析與歷史明細"])

with tab_unpack:
    st.subheader("拆封新咖啡豆")
    with st.form("unpack_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            bean_name = st.text_input("咖啡豆名稱 / 烘焙度", placeholder="例如：衣索比亞 耶加雪菲 / 中淺焙")
            weight_g = st.number_input("包裝克數 (g)", value=454, step=50, help="常見一磅約 454g，半磅約 227g")
        with c2:
            operator = st.text_input("拆封登記人", placeholder="例如：Alice")
            event_date = st.date_input("拆封日期", value=datetime.now().date())
        note = st.text_input("備註 / 風味筆記", placeholder="選填，例如：新口味試喝")
        
        submitted = st.form_submit_button("登記開豆 ☕", use_container_width=True)
        if submitted:
            if not bean_name or not operator:
                st.error("請填寫咖啡豆名稱與登記人！")
            else:
                supabase.table("coffee_records").insert({
                    "event_type": "UNPACK",
                    "bean_name": bean_name,
                    "weight_g": weight_g,
                    "operator": operator,
                    "event_date": str(event_date),
                    "note": note
                }).execute()
                st.success(f"已成功登記拆封：{bean_name}！")
                st.rerun()

with tab_restock:
    st.subheader("採購進貨入庫")
    with st.form("restock_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            r_bean_name = st.text_input("進貨豆款名稱", placeholder="例如：湛盧 經典綜合豆")
            r_qty = st.number_input("進貨包數", min_value=1, value=2, step=1)
        with c2:
            r_operator = st.text_input("採購人 / 經手人", placeholder="例如：總務組")
            r_date = st.date_input("進貨日期", value=datetime.now().date())
        r_note = st.text_input("備註 (採購管道/單價)", placeholder="選填，例如：momo 特價購入")
        
        r_submitted = st.form_submit_button("登記進貨 📦", use_container_width=True)
        if r_submitted:
            if not r_bean_name or not r_operator:
                st.error("請填寫進貨豆款與經手人！")
            else:
                # 依包數新增對應數量的進貨紀錄
                records = [{
                    "event_type": "RESTOCK",
                    "bean_name": r_bean_name,
                    "weight_g": 454,
                    "operator": r_operator,
                    "event_date": str(r_date),
                    "note": f"{r_note} (批次進貨第 {i+1} 包)" if r_qty > 1 else r_note
                } for i in range(r_qty)]
                supabase.table("coffee_records").insert(records).execute()
                st.success(f"成功入庫 {r_qty} 包咖啡豆！")
                st.rerun()

# ----------------------------------------------------
# 5. 數據分析圖表與明細管理
# ----------------------------------------------------
with tab_stats:
    st.subheader("每包咖啡豆消耗天數趨勢")
    if len(unpack_df) >= 2:
        sorted_unpacks = unpack_df.sort_values("event_date").reset_index(drop=True)
        sorted_unpacks["prev_date"] = sorted_unpacks["event_date"].shift(1)
        sorted_unpacks["消耗天數"] = (pd.to_datetime(sorted_unpacks["event_date"]) - pd.to_datetime(sorted_unpacks["prev_date"])).dt.days
        chart_data = sorted_unpacks.dropna(subset=["消耗天數"])
        
        fig = px.bar(
            chart_data, 
            x="event_date", 
            y="消耗天數", 
            text="消耗天數",
            hover_data=["bean_name", "operator"],
            labels={"event_date": "拆封日期", "消耗天數": "撐了幾天 (天)"},
            title="各包消耗週期（天數越短代表喝越快）"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("開豆紀錄累積達 2 次以上時，系統將自動繪製消耗週期趨勢圖。")

    st.subheader("完整歷史紀錄")
    if not df.empty:
        display_df = df.copy()
        display_df["類型"] = display_df["event_type"].map({"UNPACK": "☕ 拆封開豆", "RESTOCK": "📦 採購進貨"})
        display_df = display_df.rename(columns={
            "id": "編號",
            "event_date": "日期",
            "bean_name": "咖啡豆",
            "weight_g": "克數",
            "operator": "經手人",
            "note": "備註"
        })
        st.dataframe(display_df[["編號", "日期", "類型", "咖啡豆", "克數", "經手人", "備註"]], use_container_width=True)
        
        # 刪除功能
        with st.expander("🗑️ 刪除誤填紀錄"):
            del_id = st.number_input("請輸入要刪除的紀錄編號 (ID)", step=1, value=0)
            if st.button("確認刪除", type="primary"):
                if del_id > 0:
                    supabase.table("coffee_records").delete().eq("id", del_id).execute()
                    st.success(f"已刪除編號 {del_id} 紀錄！")
                    st.rerun()
    else:
        st.write("目前尚無任何紀錄。")
