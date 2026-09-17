import random
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI 彩票黑色大屏", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.markdown("""
<style>
.stApp { background: #07111f; color: #e6edf7; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
[data-testid="stSidebar"] { background: #0b1728; border-right: 1px solid #1d3553; }
.block-container { max-width: 1800px; padding-top: 1.5rem; }
.dashboard-title { color: #66e3ff; font-size: 2.2rem; font-weight: 800; letter-spacing: .08em; text-shadow: 0 0 18px #0ea5e9; }
.dashboard-subtitle { color: #8da8c5; margin-bottom: 1.2rem; }
.panel { background: linear-gradient(145deg, #0c1b30, #0a1525); border: 1px solid #1c4165; border-radius: 14px; padding: 18px; box-shadow: 0 0 24px rgba(14,165,233,.08); margin-bottom: 18px; }
.panel-title { color: #8cecff; font-size: 1.1rem; font-weight: 700; border-left: 3px solid #22d3ee; padding-left: 10px; margin-bottom: 12px; }
.metric-card { background: #0d2037; border: 1px solid #1f5276; border-radius: 12px; padding: 16px; text-align: center; }
.metric-label { color: #8da8c5; font-size: .85rem; }
.metric-value { color: #66e3ff; font-size: 1.8rem; font-weight: 800; margin-top: 5px; }
.badge-hot { color: #ff8a8a; background: #3b1c2b; padding: 4px 9px; border-radius: 999px; }
.badge-cold { color: #8cc8ff; background: #102c4b; padding: 4px 9px; border-radius: 999px; }
div[data-testid="stDataFrame"] { border: 1px solid #20496c; }
div.stButton > button { background: #0e7490; color: white; border: 1px solid #38bdf8; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dashboard-title">◈ AI 彩票数据分析中心</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">实时统计 · 热冷监测 · 近期走势 · 智能观察 · 随机演示</div>', unsafe_allow_html=True)
st.warning("这是历史数据分析演示，不代表中奖预测；彩票结果具有随机性。")


def detect_number_columns(df):
    selected = []
    for col in df.columns:
        name = str(col).lower()
        if "date" in name:
            continue
        if any(token in name for token in ["ball", "num", "number", "red", "blue"]) or name.startswith("n"):
            selected.append(col)
    return selected or [c for c in df.columns if str(c).lower() != "date"]


def load_numbers(df):
    columns = detect_number_columns(df)
    values = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in columns], ignore_index=True)
    return columns, values.dropna().astype(int)


def frequency_table(numbers):
    result = numbers.value_counts().sort_index().rename("出现次数").reset_index()
    result.columns = ["号码", "出现次数"]
    result["出现频率%"] = (result["出现次数"] / len(numbers) * 100).round(2)
    return result


def recent_table(numbers, window):
    result = numbers.tail(window).value_counts().rename("近期次数").reset_index()
    result.columns = ["号码", "近期次数"]
    return result.sort_values("近期次数", ascending=False).head(20)


def recommendation_table(freq, recent):
    result = freq.copy()
    recent_map = dict(zip(recent["号码"], recent["近期次数"]))
    result["近期次数"] = result["号码"].map(recent_map).fillna(0).astype(int)
    result["综合指数"] = (result["出现次数"] + result["近期次数"] * 1.5).round(2)
    result["分类"] = result["近期次数"].apply(lambda x: "近期活跃" if x else "偏冷观察")
    return result.sort_values("综合指数", ascending=False).head(15)


with st.sidebar:
    st.markdown("### ⚙ 控制中心")
    uploaded = st.file_uploader("上传历史数据 CSV", type=["csv"])
    window = st.slider("近期分析窗口", 10, 100, 30)
    combo_count = st.slider("演示组合数量", 1, 10, 5)
    combo_size = st.slider("每组号码数量", 3, 10, 6)
    st.markdown("---")
    st.caption("支持列名：date、n1-n6、ball1-ball6 等。")

try:
    data = pd.read_csv(uploaded) if uploaded else pd.read_csv(DATA_FILE)
    columns, numbers = load_numbers(data)
except Exception as exc:
    st.error(f"数据读取失败：{exc}")
    st.stop()

if numbers.empty:
    st.error("没有可以分析的数字数据。")
    st.stop()

freq = frequency_table(numbers)
recent = recent_table(numbers, window)
recommend = recommendation_table(freq, recent)

st.markdown('<div class="panel-title">▣ 核心运行指标</div>', unsafe_allow_html=True)
metrics = st.columns(5)
metric_values = [("数据记录", len(data)), ("号码字段", len(columns)), ("号码样本", len(numbers)), ("不同号码", freq.shape[0]), ("近期窗口", window)]
for box, (label, value) in zip(metrics, metric_values):
    box.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

left, right = st.columns([1.65, 1])
with left:
    st.markdown('<div class="panel-title">▣ 全量号码频率雷达</div>', unsafe_allow_html=True)
    st.bar_chart(freq.set_index("号码")["出现次数"], color="#22d3ee")
with right:
    st.markdown('<div class="panel-title">▣ 智能关注清单</div>', unsafe_allow_html=True)
    for _, row in recommend.head(6).iterrows():
        color = "badge-hot" if row["近期次数"] else "badge-cold"
        st.markdown(f'<p><span class="{color}">号码 {int(row["号码"])}</span>　综合指数 <b>{row["综合指数"]}</b><br><small>总计 {int(row["出现次数"])} 次 · 近期 {int(row["近期次数"])} 次</small></p>', unsafe_allow_html=True)

hot_col, cold_col = st.columns(2)
with hot_col:
    st.markdown('<div class="panel-title">▲ 热号监测 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold_col:
    st.markdown('<div class="panel-title">▼ 冷号监测 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

recent_col, ai_col = st.columns([1, 1])
with recent_col:
    st.markdown('<div class="panel-title">◷ 近期走势</div>', unsafe_allow_html=True)
    st.bar_chart(recent.set_index("号码")["近期次数"], color="#a78bfa")
    st.dataframe(recent, use_container_width=True, hide_index=True)
with ai_col:
    st.markdown('<div class="panel-title">✦ AI 风格研判</div>', unsafe_allow_html=True)
    top = recommend.head(5)["号码"].tolist()
    hot = freq.sort_values("出现次数", ascending=False).head(5)["号码"].tolist()
    cold = freq.sort_values("出现次数").head(5)["号码"].tolist()
    st.info(f"综合关注：{', '.join(map(str, top))}")
    st.info(f"高频观察：{', '.join(map(str, hot))}")
    st.info(f"低频观察：{', '.join(map(str, cold))}")
    st.dataframe(recommend, use_container_width=True, hide_index=True)

st.markdown('<div class="panel-title">✧ 随机演示组合</div>', unsafe_allow_html=True)
max_number = int(numbers.max())
for index in range(combo_count):
    combo = sorted(random.sample(range(1, max_number + 1), min(combo_size, max_number)))
    st.write(f"演示组合 {index + 1}：{' · '.join(map(str, combo))}")

st.caption("系统说明：所有指数均为基于历史频率的启发式展示，不是科学中奖概率，也不构成投注建议。")
