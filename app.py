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

# 溫暖質感 CSS
st.markdown("""
<style>
    .status-card {
        background: #ffffff;
        border: 1.5px solid #f0ebe6;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 12px rgba(140, 109, 88, 0.05);
    }
    .status-title {
        font-size: 0.9rem;
        color: #8c7e75;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .status-number {
        font-size: 1.9rem;
        font-weight: 800;
        color: #3e2723;
        line-height: 1.2;
    }
    .status-sub {
        font-size: 0.8rem;
        color: #888;
        margin-top: 4px;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
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

# 頁首標題
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("☕ 辦公室咖啡續命站")
    st.caption("喝咖啡是基本人權！即時算出喝多快、哪天斷糧，缺豆前趕快補貨～")
with col_btn:
    if st.button("🔄 重新載入", use_container_width=True):
        st.rerun()

# 分流資料
unpack_df = df[df["event_type"] == "UNPACK"].copy() if not df.empty else pd.DataFrame()
restock_df = df[df["event_type"] == "RESTOCK"].copy() if not df.empty else pd.DataFrame()

# 3. 核心數據計算
total_restocked = len(restock_df)
total_unpacked = len(unpack_df)
current_stock = max(0, total_restocked - total_unpacked)

# 分豆款統計未拆封包數
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

# 4. 口語化四卡儀表板
c1, c2, c3, c4 = st.columns(4)

with c1:
    bg = "#fdeeed" if current_stock <= 1 else "#edf7ed"
    color = "#c62828" if current_stock <= 1 else "#2e7d32"
    badge_text = "🚨 庫存告急！" if current_stock <= 1 else "✨ 儲備充裕"
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">📦 櫃子裡還剩幾包？</div>
        <div class="status-number">{current_stock} <span style="font-size: 1.1rem; font-weight: normal; color: #777;">包未拆</span></div>
        <div class="status-sub">
            <span class="badge" style="background:{bg}; color:{color};">{badge_text}</span>
            <div style="margin-top: 4px; font-size: 0.75rem; color: #666;">
                👑 皇家: {royal_stock} 包 ｜ ☕ 聖馬可: {marco_stock} 包
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    v_speed = f"{avg_days} <span style='font-size: 1rem; font-weight: normal; color: #777;'>天/包</span>" if avg_days else "<span style='font-size:1.2rem; color:#aaa;'>抓數據中...</span>"
    sub_speed = "大約這速度消滅一包" if avg_days else "開過不同天數的豆子後會自動算出"
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">⚡ 大家喝有多快？</div>
        <div class="status-number">{v_speed}</div>
        <div class="status-sub">{sub_speed}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    if days_left is not None:
        v_left = f"約 {days_left} <span style='font-size: 1rem; font-weight: normal; color: #777;'>天</span>"
        sub_left = f"現有這批已開喝第 {current_opened_days} 天"
    elif len(unpack_df) >= 1:
        v_left = f"第 {current_opened_days} <span style='font-size: 1rem; font-weight: normal; color: #777;'>天</span>"
        sub_left = "累積下一批開豆就會開始倒數！"
    else:
        v_left = "<span style='font-size:1.2rem; color:#aaa;'>還沒開過</span>"
        sub_left = "趕快去拆第一包～"
        
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">⏳ 正在喝的能撐多久？</div>
        <div class="status-number">{v_left}</div>
        <div class="status-sub">{sub_left}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    v_date = f"{estimated_finish_date}" if estimated_finish_date else "<span style='font-size:1.2rem; color:#aaa;'>推算中...</span>"
    sub_date = "提前叫貨才不會斷糧！" if estimated_finish_date else "資料夠了會自動預測"
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">📅 預估哪天見底？</div>
        <div class="status-number">{v_date}</div>
        <div class="status-sub">{sub_date}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 預警提示
if current_stock == 0:
    st.error("😱 **重大警報**：櫃子裡已經**沒有半包存貨**了！喝完就真的沒了，快去叫貨！")
elif current_stock <= 2:
    st.warning(f"⚠️ **咖啡告急**：只剩最後 {current_stock} 包存貨！建議現在就可以準備下單囉～")

# 5. 操作分頁
tab1, tab2, tab3 = st.tabs(["☕ 我拆了新豆子！", "📦 咖啡豆到貨了！", "📊 飲用紀錄與趨勢"])

with tab1:
    st.markdown("#### 拆了新豆子？選一下就搞定（免打字）～")
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
                custom_bean = st.text_input("請輸入其他豆款名稱")
        with c2:
            unpack_qty = st.number_input("這次一次開了幾包？", min_value=1, max_value=10, value=1, step=1)
            event_d = st.date_input("拆封日期", value=datetime.now().date())
            
        flavor = st.text_input("心得或備註（選填）", placeholder="例如：開兩包倒大機器、這批很香")
        
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
                    "operator": "善心同事",  # 免填名字，系統自動代入
                    "event_date": str(event_d),
                    "note": f"{flavor} (一次開 {unpack_qty} 包之 #{i+1})" if unpack_qty > 1 and flavor else (f"一次開 {unpack_qty} 包之第 {i+1} 包" if unpack_qty > 1 else flavor)
                } for i in range(unpack_qty)]
                
                supabase.table("coffee_records").insert(records).execute()
                st.toast(f"🎉 成功登記拆封 {unpack_qty} 包「{actual_bean}」！續命泉源已補充 ✨")
                st.rerun()

with tab2:
    st.markdown("#### 買新豆子送到了？選一下就入庫！")
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
        
        btn_stock = st.form_submit_button("📦 把豆子放進櫃子（入庫）", use_container_width=True)
        if btn_stock:
            actual_r_bean = r_custom if r_bean_choice == "其他豆款" else r_bean_choice
            if not actual_r_bean:
                st.error("請確認到貨的豆款名稱！")
            else:
                records = [{
                    "event_type": "RESTOCK",
                    "bean_name": actual_r_bean,
                    "weight_g": 454,
                    "operator": "公司採購",  # 免填名字
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
            color_discrete_map={"皇家義大利": "#5c3d2e", "聖馬可綜合": "#8c6d58"}
        )
        fig.update_traces(texttemplate='%{text} 包', textposition='outside')
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, title="開豆日期"),
            yaxis=dict(showgrid=True, gridcolor="#eee", title="拆封數量 (包)"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 目前開豆紀錄還不到 2 筆，等大家多登記幾次，這裡就會呈現各豆款的開豆歷史圖表囉！")

    st.markdown("#### 📋 過去所有的開豆與補貨紀錄")
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
