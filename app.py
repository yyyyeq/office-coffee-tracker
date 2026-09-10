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

# 溫暖又親切的樣式設計
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
        color: #a89f91;
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

# 2. Supabase 連線
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

# 頁面大標題
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("☕ 辦公室咖啡續命站")
    st.caption("喝咖啡是基本人權！即時算出喝多快、哪天斷糧，缺豆前趕快補貨～")
with col_btn:
    if st.button("🔄 重新載入", use_container_width=True):
        st.rerun()

# 拆分開豆與到貨
unpack_df = df[df["event_type"] == "UNPACK"].copy() if not df.empty else pd.DataFrame()
restock_df = df[df["event_type"] == "RESTOCK"].copy() if not df.empty else pd.DataFrame()

# 3. 核心數據計算
total_restocked = len(restock_df)
total_unpacked = len(unpack_df)
current_stock = max(0, total_restocked - total_unpacked)

avg_days = None
days_left = None
estimated_finish_date = None
current_opened_days = 0

if len(unpack_df) >= 2:
    sorted_unpacks = unpack_df.sort_values("event_date").reset_index(drop=True)
    sorted_unpacks["prev_date"] = sorted_unpacks["event_date"].shift(1)
    sorted_unpacks["duration_days"] = (pd.to_datetime(sorted_unpacks["event_date"]) - pd.to_datetime(sorted_unpacks["prev_date"])).dt.days
    
    recent = sorted_unpacks["duration_days"].dropna().tail(5)
    if not recent.empty and recent.mean() > 0:
        avg_days = round(recent.mean(), 1)
        latest_date = sorted_unpacks["event_date"].iloc[-1]
        today = datetime.now().date()
        current_opened_days = (today - latest_date).days
        days_left = max(0, int(avg_days - current_opened_days))
        estimated_finish_date = latest_date + timedelta(days=int(avg_days))
elif len(unpack_df) == 1:
    today = datetime.now().date()
    current_opened_days = (today - unpack_df["event_date"].iloc[0]).days

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
        <div class="status-sub"><span class="badge" style="background:{bg}; color:{color};">{badge_text}</span></div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    v_speed = f"{avg_days} <span style='font-size: 1rem; font-weight: normal; color: #777;'>天/包</span>" if avg_days else "<span style='font-size:1.2rem; color:#aaa;'>抓數據中...</span>"
    sub_speed = "大概這速度消滅一包" if avg_days else "至少要開過 2 包才算得出"
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
        sub_left = f"這包已經開喝第 {current_opened_days} 天"
    elif len(unpack_df) == 1:
        v_left = f"第 {current_opened_days} <span style='font-size: 1rem; font-weight: normal; color: #777;'>天</span>"
        sub_left = "開第 2 包時就會開始倒數！"
    else:
        v_left = "<span style='font-size:1.2rem; color:#aaa;'>還沒開過</span>"
        sub_left = "趕快去拆第一包～"
        
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">⏳ 這包還能撐多久？</div>
        <div class="status-number">{v_left}</div>
        <div class="status-sub">{sub_left}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    v_date = f"{estimated_finish_date}" if estimated_finish_date else "<span style='font-size:1.2rem; color:#aaa;'>推算中...</span>"
    sub_date = "提前幾天叫貨才不會斷糧！" if estimated_finish_date else "資料夠了會自動預測"
    st.markdown(f"""
    <div class="status-card">
        <div class="status-title">📅 預估哪天見底？</div>
        <div class="status-number">{v_date}</div>
        <div class="status-sub">{sub_date}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 俏皮警示
if current_stock == 0:
    st.error("😱 **重大警報**：櫃子裡已經**沒有半包存貨**了！這包喝完就真的沒了，快去叫貨！")
elif current_stock == 1:
    st.warning("⚠️ **咖啡告急**：只剩最後 1 包存貨！建議現在就可以準備下單囉～")

# 5. 操作分頁
tab1, tab2, tab3 = st.tabs(["☕ 我拆了一包新豆子！", "📦 咖啡豆到貨了！", "📊 飲用紀錄與趨勢"])

with tab1:
    st.markdown("#### 拆了一包新的？隨手幫大家記一下～")
    with st.form("unpack_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            bean = st.text_input("這包是什麼豆子？", placeholder="例如：耶加雪菲、深焙曼特寧、好市多黃袋")
            weight = st.radio("包裝大概多大？", [454, 227, 500, 1000], format_func=lambda x: f"{x}g (標準一磅)" if x==454 else (f"{x}g (半磅裝)" if x==227 else f"{x}g"), horizontal=True)
        with c2:
            who = st.text_input("你是哪位善心人士？（大名/暱稱）", placeholder="例如：Gary、Alice、小王")
            date = st.date_input("什麼時候拆的？", value=datetime.now().date())
            
        flavor = st.text_input("這包有什麼特色或評語嗎？（選填）", placeholder="例如：酸度很順、帶可可香、上次買太苦這次換換看")
        
        btn_open = st.form_submit_button("🚀 開喝！登記拆封", use_container_width=True, type="primary")
        if btn_open:
            if not bean or not who:
                st.error("豆子名字跟你的名字要填一下喔！大家才知道現在在喝什麼～")
            else:
                supabase.table("coffee_records").insert({
                    "event_type": "UNPACK",
                    "bean_name": bean,
                    "weight_g": weight,
                    "operator": who,
                    "event_date": str(date),
                    "note": flavor
                }).execute()
                st.toast("🎉 續命泉源已補充！今天工作也辛苦啦 ✨")
                st.rerun()

with tab2:
    st.markdown("#### 買新豆子送到了？加進庫存裡！")
    with st.form("restock_form", clear_on_submit=True):
        r1, r2 = st.columns(2)
        with r1:
            r_bean = st.text_input("這次買了什麼豆款？", placeholder="例如：湛盧 經典綜合豆、好市多星巴克")
        with r2:
            r_qty = st.number_input("這次來了幾包？", min_value=1, value=2, step=1)
            
        r3, r4 = st.columns(2)
        with r3:
            r_date = st.date_input("到貨日期", value=datetime.now().date())
        with r4:
            r_memo = st.text_input("備註說明（選填）", placeholder="例如：特價購入、單價 450 元")
        
        btn_stock = st.form_submit_button("📦 把豆子放進櫃子（入庫）", use_container_width=True)
        if btn_stock:
            if not r_bean:
                st.error("請填寫一下到貨的豆子品名喔！")
            else:
                records = [{
                    "event_type": "RESTOCK",
                    "bean_name": r_bean,
                    "weight_g": 454,
                    "operator": "公司採購",  # 免填，系統自動帶入
                    "event_date": str(r_date),
                    "note": f"{r_memo} (第 {i+1} 包)" if r_qty > 1 and r_memo else (f"批次入庫第 {i+1} 包" if r_qty > 1 else r_memo)
                } for i in range(r_qty)]
                supabase.table("coffee_records").insert(records).execute()
                st.toast(f"📦 庫存已增加 {r_qty} 包！辦公室又有精神啦～")
                st.rerun()

with tab3:
    st.markdown("#### 📈 每包喝了多久？（天數越短代表大家越愛喝或最近案子太忙）")
    if len(unpack_df) >= 2:
        sorted_unpacks = unpack_df.sort_values("event_date").reset_index(drop=True)
        sorted_unpacks["prev_date"] = sorted_unpacks["event_date"].shift(1)
        sorted_unpacks["撐了幾天"] = (pd.to_datetime(sorted_unpacks["event_date"]) - pd.to_datetime(sorted_unpacks["prev_date"])).dt.days
        chart_data = sorted_unpacks.dropna(subset=["撐了幾天"]).copy()
        
        fig = px.bar(
            chart_data, 
            x="event_date", 
            y="撐了幾天", 
            text="撐了幾天",
            hover_data={"bean_name": True, "operator": True, "event_date": True, "撐了幾天": True},
            labels={"event_date": "拆封日期", "撐了幾天": "撐了幾天 (天)"},
            color_discrete_sequence=["#8c6d58"]
        )
        fig.update_traces(texttemplate='%{text} 天喝完', textposition='outside')
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, title="開豆日期"),
            yaxis=dict(showgrid=True, gridcolor="#eee", title="天數"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 目前開豆紀錄還不到 2 筆，等大家拆到第 2 包，這裡就會長出喝咖啡的消耗趨勢圖囉！")

    st.markdown("#### 📋 過去所有的開豆與補貨紀錄")
    if not df.empty:
        display_df = df.copy()
        display_df["動作"] = display_df["event_type"].map({"UNPACK": "☕ 拆封開喝", "RESTOCK": "📦 進貨補庫存"})
        display_df = display_df.rename(columns={
            "id": "編號",
            "event_date": "日期",
            "bean_name": "咖啡豆名",
            "weight_g": "克數",
            "operator": "經手/開豆人",
            "note": "備註/評語"
        })
        st.dataframe(
            display_df[["編號", "日期", "動作", "咖啡豆名", "克數", "經手/開豆人", "備註/評語"]],
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
