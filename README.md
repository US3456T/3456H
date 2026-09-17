import random
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI 彩票大数据中心", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.markdown(
    """
    <style>
    .stApp { background: #050d18; color: #edf4ff; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] { background: #091827; border-right: 1px solid #16314d; }
    .block-container { max-width: 1800px; padding-top: 1.2rem; }
    .hero {
        background: linear-gradient(135deg, rgba(13, 50, 86, 0.95), rgba(7, 21, 38, 0.95));
        border: 1px solid #1d4f75;
        border-radius: 18px;
        padding: 1.3rem 1.5rem;
        box-shadow: 0 0 26px rgba(34, 211, 238, 0.12);
        margin-bottom: 1.2rem;
    }
    .hero h1 {
        color: #7ee7ff;
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        margin: 0;
    }
    .hero p {
        color: #b8d1ef;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }
    .metric-card {
        background: linear-gradient(180deg, #0d1d2f, #0b1728);
        border: 1px solid #1e4467;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: inset 0 0 20px rgba(34, 211, 238, 0.03);
    }
    .metric-label { color: #8ca7c9; font-size: 0.8rem; }
    .metric-value { color: #7ee7ff; font-size: 2rem; font-weight: 800; margin-top: 0.4rem; }
    .panel {
        background: linear-gradient(145deg, #0d1c2d, #0a1524);
        border: 1px solid #1d4165;
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .panel-title {
        color: #8fe8ff;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0.8rem;
        padding-left: 0.6rem;
        border-left: 3px solid #22d3ee;
    }
    .badge-hot { color: #ff8c8c; background: rgba(190, 24, 93, 0.14); border: 1px solid rgba(248, 113, 113, 0.4); padding: 0.2rem 0.6rem; border-radius: 999px; }
    .badge-cold { color: #9ad3ff; background: rgba(59, 130, 246, 0.14); border: 1px solid rgba(96, 165, 250, 0.4); padding: 0.2rem 0.6rem; border-radius: 999px; }
    .small-note { color: #9db2ce; font-size: 0.84rem; }
    div[data-testid="stDataFrame"] { border-radius: 12px; border: 1px solid #224a74; }
    div.stButton > button { background: linear-gradient(180deg, #0ea5e9, #0369a1); border: 1px solid #67e8f9; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><h1>AI 彩票大数据中心</h1><p>历史数据统计 · 热冷监测 · 近期走势 · 智能推荐 · 组合演示</p></div>', unsafe_allow_html=True)
st.warning("仅用于历史数据分析与演示，不保证中奖，结果仍然具有随机性。")


def detect_columns(df):
    cols = []
    for c in df.columns:
        name = str(c).lower()
        if "date" in name:
            continue
        if any(token in name for token in ["ball", "num", "number", "red", "blue"]) or name.startswith("n"):
            cols.append(c)
    return cols or [c for c in df.columns if str(c).lower() != "date"]


def normalize_numbers(df):
    cols = detect_columns(df)
    if not cols:
        raise ValueError("CSV 中没有找到可用号码列。请至少提供 n1,n2,n3,n4,n5,n6 或 ball1,ball2,... 这类格式。")
    frames = [pd.to_numeric(df[c], errors="coerce") for c in cols]
    values = pd.concat(frames, ignore_index=True).dropna().astype(int)
    return cols, values


def frequency_table(numbers):
    res = numbers.value_counts().sort_index().rename("出现次数").reset_index()
    res.columns = ["号码", "出现次数"]
    res["出现频率%"] = (res["出现次数"] / res["出现次数"].sum() * 100).round(2)
    return res


def recent_table(numbers, window):
    res = numbers.tail(window).value_counts().rename("近期次数").reset_index()
    res.columns = ["号码", "近期次数"]
    return res.sort_values("近期次数", ascending=False).head(20)


def recommendation_table(freq, recent):
    score = freq.copy()
    recent_map = dict(zip(recent["号码"], recent["近期次数"]))
    score["近期次数"] = score["号码"].map(recent_map).fillna(0).astype(int)
    score["综合指数"] = (score["出现次数"] + score["近期次数"] * 1.5).round(2)
    score["状态"] = score["近期次数"].apply(lambda x: "近期活跃" if x else "偏冷观察")
    return score.sort_values("综合指数", ascending=False).head(15)


def generate_random_combo(count, max_num, total):
    combos = []
    for _ in range(total):
        combos.append(sorted(random.sample(range(1, max_num + 1), count)))
    return combos


with st.sidebar:
    st.markdown("### 控制中心")
    uploaded = st.file_uploader("上传历史数据 CSV", type=["csv"]) 
    st.markdown("---")
    st.slider("近期窗口", 10, 100, 30, key="recent_window")
    st.slider("演示组合数量", 1, 10, 5, key="combo_count")
    st.slider("每组号码数量", 3, 10, 6, key="combo_size")
    st.caption("支持列名：date, n1-n6, ball1-ball6")

if uploaded is not None:
    try:
        data = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"读取上传文件失败：{exc}")
        st.stop()
else:
    try:
        data = pd.read_csv(DATA_FILE)
    except Exception as exc:
        st.error(f"读取演示数据失败：{exc}")
        st.stop()

try:
    columns, numbers = normalize_numbers(data)
except Exception as exc:
    st.error(f"数据识别失败：{exc}")
    st.stop()

freq = frequency_table(numbers)
recent = recent_table(numbers, st.session_state.recent_window)
recommend = recommendation_table(freq, recent)

metric_cols = st.columns(5)
metrics = [
    ("数据条数", len(data)),
    ("号码字段", len(columns)),
    ("号码样本", len(numbers)),
    ("不同号码", freq.shape[0]),
    ("近期窗口", st.session_state.recent_window),
]
for c, (label, value) in zip(metric_cols, metrics):
    c.markdown(f'''<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>''', unsafe_allow_html=True)

left, right = st.columns([1.9, 1])
with left:
    st.markdown('<div class="panel"><div class="panel-title">总览：号码频率图</div></div>', unsafe_allow_html=True)
    st.bar_chart(freq.set_index("号码")["出现次数"], use_container_width=True)
with right:
    st.markdown('<div class="panel"><div class="panel-title">智能关注</div></div>', unsafe_allow_html=True)
    for _, row in recommend.head(6).iterrows():
        label = 'badge-hot' if row['近期次数'] else 'badge-cold'
        st.markdown(f'<div class="small-note"><span class="{label}">号码 {int(row["号码"])}</span> 综合指数 {row["综合指数"]} · 近期 {int(row["近期次数"])} 次</div>', unsafe_allow_html=True)

hot_col, cold_col = st.columns(2)
with hot_col:
    st.markdown('<div class="panel"><div class="panel-title">热号 Top 10</div></div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold_col:
    st.markdown('<div class="panel"><div class="panel-title">冷号 Top 10</div></div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

recent_col, ai_col = st.columns([1.2, 1.2])
with recent_col:
    st.markdown('<div class="panel"><div class="panel-title">近期走势</div></div>', unsafe_allow_html=True)
    st.dataframe(recent, use_container_width=True, hide_index=True)
    st.bar_chart(recent.set_index("号码")["近期次数"], use_container_width=True)
with ai_col:
    st.markdown('<div class="panel"><div class="panel-title">AI 风格建议</div></div>', unsafe_allow_html=True)
    top_nums = recommend["号码"].head(5).astype(int).tolist()
    hot_nums = freq.sort_values("出现次数", ascending=False).head(5)["号码"].astype(int).tolist()
    cold_nums = freq.sort_values("出现次数", ascending=True).head(5)["号码"].astype(int).tolist()
    st.info(f"优先观察：{', '.join(map(str, top_nums))}")
    st.info(f"热号区：{', '.join(map(str, hot_nums))}")
    st.info(f"冷号观察：{', '.join(map(str, cold_nums))}")
    st.dataframe(recommend, use_container_width=True, hide_index=True)

st.markdown('<div class="panel"><div class="panel-title">随机演示组合</div></div>', unsafe_allow_html=True)
max_num = int(numbers.max()) if not numbers.empty else 49
for idx, combo in enumerate(generate_random_combo(st.session_state.combo_size, max_num, st.session_state.combo_count), 1):
    st.write(f"组合 {idx}: {combo}")

st.caption("说明：本页面通过历史统计和启发式评分展示数据趋势，不保证中奖，也不构成投注建议。")
