import random
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="彩票展示版大屏", page_icon="📊", layout="wide")
DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.markdown(
    """
    <style>
    .stApp { background: #050d18; color: #edf6ff; }
    [data-testid="stSidebar"] { background: #091827; }
    .block-container { max-width: 1800px; padding-top: 1rem; }
    .hero { background: linear-gradient(135deg,#0c233c,#071521); border:1px solid #1e4d76; border-radius:18px; padding:1.5rem 1.6rem; box-shadow:0 0 30px rgba(34,211,238,.07); }
    .hero h1 { margin:0; color:#8fe9ff; letter-spacing:.08em; font-size:2.4rem; }
    .hero p { color:#c3d5efff; margin:.55rem 0 0; }
    .card { background:linear-gradient(180deg,#0d1d2f,#0a1827); border:1px solid #224e76; border-radius:14px; padding:1rem; }
    .label { color:#92aac7; font-size:.8rem; }
    .value { color:#7fe8ff; font-size:1.8rem; font-weight:800; }
    .panel { background:linear-gradient(180deg,#0d1d2f,#0a1623); border:1px solid #214d73; border-radius:16px; padding:1rem; margin-bottom:1rem; }
    .section { color:#94ebff; font-weight:800; border-left:3px solid #22d3ee; padding-left:.6rem; margin:1rem 0 .6rem; }
    .badge { display:inline-block; padding: .2rem .7rem; border-radius:999px; background:rgba(34,211,238,.08); border:1px solid rgba(34,211,238,.4); color:#def9ff; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><h1>彩票展示版大屏</h1><p>历史数据 · 热号分析 · 冷号观察 · 近期走势 · 组合推荐</p></div>', unsafe_allow_html=True)
st.warning("仅用于展示与学习，不代表中奖预测。")


def detect_columns(frame):
    cols = []
    for col in frame.columns:
        name = str(col).lower()
        if "date" in name:
            continue
        if any(part in name for part in ["ball", "num", "number", "red", "blue"]) or name.startswith("n"):
            cols.append(col)
    return cols or [c for c in frame.columns if "date" not in str(c).lower()]


def read_numbers(frame):
    cols = detect_columns(frame)
    draws = []
    for _, row in frame.iterrows():
        numbers = []
        for col in cols:
            val = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(val):
                numbers.append(int(val))
        if numbers:
            draws.append(sorted(set(numbers)))
    if not draws:
        raise ValueError("没有识别到有效号码数据。请使用 date,n1,... 格式。")
    return cols, draws


def frequency_table(draws):
    values = [n for draw in draws for n in draw]
    freq = pd.Series(values).value_counts().sort_index().rename_axis("号码").reset_index(name="出现次数")
    freq["出现频率%"] = (freq["出现次数"] / len(values) * 100).round(2)
    return freq


def recent_table(draws, window=30):
    values = [n for draw in draws[-window:] for n in draw]
    recent = pd.Series(values).value_counts().rename_axis("号码").reset_index(name="近期次数")
    recent = recent.sort_values("近期次数", ascending=False).head(20)
    return recent


def combo_candidates(freq, count=6, total=5):
    hot = freq.sort_values("出现次数", ascending=False).head(20)["号码"].tolist()
    combos = []
    for _ in range(total):
        pool = hot[:]
        if len(pool) < count:
            pool += list(range(1, 51))
        combo = sorted(random.sample(pool, count))
        combos.append(combo)
    return combos


with st.sidebar:
    st.header("控制中心")
    uploaded = st.file_uploader("上传 CSV", type=["csv"])
    recent_window = st.slider("近期窗口", 10, 100, 30)
    combo_size = st.slider("每组号码数量", 3, 10, 6)
    combo_total = st.slider("展示组合数", 1, 10, 5)

try:
    frame = pd.read_csv(uploaded) if uploaded else pd.read_csv(DATA_FILE)
    columns, draws = read_numbers(frame)
except Exception as exc:
    st.error(f"读取失败：{exc}")
    st.stop()

freq = frequency_table(draws)
recent = recent_table(draws, recent_window)
combos = combo_candidates(freq, count=combo_size, total=combo_total)

metrics = st.columns(5)
for col, (label, value) in zip(metrics, [("数据条数", len(draws)), ("号码字段", len(columns)), ("样本总数", sum(len(d) for d in draws)), ("不同号码", freq.shape[0]), ("窗口", recent_window)]):
    col.markdown(f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

left, right = st.columns([1.7, 1])
with left:
    st.markdown('<div class="section">号码频率</div>', unsafe_allow_html=True)
    st.bar_chart(freq.set_index("号码")["出现次数"], use_container_width=True)
with right:
    st.markdown('<div class="section">聚焦号码</div>', unsafe_allow_html=True)
    top = freq.sort_values("出现次数", ascending=False).head(8)
    for _, row in top.iterrows():
        st.markdown(f'<span class="badge">号码 {int(row["号码"])} · {int(row["出现次数"])} 次</span>', unsafe_allow_html=True)

hot_col, cold_col = st.columns(2)
with hot_col:
    st.markdown('<div class="section">热号 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold_col:
    st.markdown('<div class="section">冷号 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

trend_col, suggest_col = st.columns([1.2, 1.2])
with trend_col:
    st.markdown('<div class="section">近期走势</div>', unsafe_allow_html=True)
    st.bar_chart(recent.set_index("号码")["近期次数"], use_container_width=True)
    st.dataframe(recent, use_container_width=True, hide_index=True)
with suggest_col:
    st.markdown('<div class="section">推荐建议</div>', unsafe_allow_html=True)
    hot_nums = freq.sort_values("出现次数", ascending=False).head(5)["号码"].astype(int).tolist()
    cold_nums = freq.sort_values("出现次数", ascending=True).head(5)["号码"].astype(int).tolist()
    st.info(f"热号重点：{', '.join(map(str, hot_nums))}")
    st.info(f"冷号观察：{', '.join(map(str, cold_nums))}")
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(12), use_container_width=True, hide_index=True)

st.markdown('<div class="section">组合演示</div>', unsafe_allow_html=True)
for i, combo in enumerate(combos, 1):
    st.write(f"组合 {i}: {combo}")

st.caption("说明：仅用于展示与分析，不构成中奖预测，也不作为投注建议。")
