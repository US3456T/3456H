import random
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI 彩票分析大盘", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.title("📊 AI 彩票分析大盘")
st.caption("基于历史数据的智能统计、热号分析、冷号分析、走势观察和随机组合生成。")
st.warning("仅用于学习和数据分析，不能保证中奖，彩票开奖结果仍然是随机事件。")


@st.cache_data
def load_demo_data():
    return pd.read_csv(DATA_FILE)


def detect_number_columns(df: pd.DataFrame):
    preferred = []
    for col in df.columns:
        c = str(col).lower()
        if "date" in c:
            continue
        if any(token in c for token in ["ball", "num", "number", "n1", "n2", "n3", "n4", "n5", "n6", "red", "blue"]):
            preferred.append(col)
    if preferred:
        return preferred
    return [c for c in df.columns if c.lower() != "date"]


def normalize_draws(df: pd.DataFrame):
    columns = detect_number_columns(df)
    if not columns:
        raise ValueError("CSV 中没有找到可用的号码列。请至少提供像 n1,n2,n3,n4,n5,n6 或 ball1,ball2,... 这样的列。")

    frames = []
    for col in columns:
        s = pd.to_numeric(df[col], errors="coerce")
        frames.append(s)

    series = pd.concat(frames, ignore_index=True).dropna().astype(int)
    return columns, series


def build_frequency_table(series: pd.Series):
    counts = series.value_counts().sort_index()
    return counts.rename("出现次数").reset_index().rename(columns={"index": "号码", "出现次数": "出现次数"})


def get_recent_numbers(series: pd.Series, lookback: int = 30):
    return series.tail(lookback).value_counts().sort_values(ascending=False)


def get_local_trend(series: pd.Series):
    result = []
    values = series.sort_values().tolist()
    for i in range(len(values) - 1):
        if values[i + 1] > values[i]:
            result.append("上升")
        elif values[i + 1] < values[i]:
            result.append("下降")
        else:
            result.append("持平")
    return result[:10]


def build_ai_style_summary(freq_df: pd.DataFrame, recent_counts: pd.Series, series: pd.Series):
    all_nums = list(range(1, int(series.max()) + 1))
    seen = set(freq_df["号码"].tolist())
    missed = [n for n in all_nums if n not in seen]

    hot = freq_df.sort_values("出现次数", ascending=False).head(10)
    cold = freq_df.sort_values("出现次数", ascending=True).head(10)
    recent_top = recent_counts.head(10)

    tips = []
    if not hot.empty:
        tips.append(f"热号集中区：{', '.join(map(str, hot['号码'].head(5).tolist()))}。近期趋势偏活跃。")
    if not cold.empty:
        tips.append(f"冷号观察区：{', '.join(map(str, cold['号码'].head(5).tolist()))}。近期出现频次较低。")
    if missed:
        tips.append(f"当前样本未出现号码：{', '.join(map(str, missed[:10]))}。可作为对照观察。")
    if not recent_top.empty:
        tips.append(f"近期重点关注号码：{', '.join(map(str, recent_top.index[:5].astype(int).tolist()))}。短期变化较明显。")

    return {
        "hot": hot,
        "cold": cold,
        "recent": recent_top,
        "tips": tips,
    }


def generate_random_combo(count: int = 6, max_num: int = 49, total: int = 5):
    combos = []
    for _ in range(total):
        combo = sorted(random.sample(range(1, max_num + 1), count))
        combos.append(combo)
    return combos


with st.sidebar:
    st.header("数据源")
    uploaded = st.file_uploader("上传 CSV 历史数据", type=["csv"], help="例如：date,n1,n2,n3,n4,n5,n6")
    st.markdown("---")
    st.header("分析设置")
    sample_count = st.slider("随机组合数", min_value=1, max_value=10, value=5)
    combo_size = st.slider("每组号码数量", min_value=3, max_value=10, value=6)

if uploaded is not None:
    try:
        data = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"读取上传文件失败：{exc}")
        st.stop()
else:
    data = pd.read_csv(DATA_FILE)

try:
    columns, numbers = normalize_draws(data)
except Exception as exc:
    st.error(f"无法识别数据：{exc}")
    st.stop()

freq_df = build_frequency_table(numbers)
summary = build_ai_style_summary(freq_df, get_recent_numbers(numbers), numbers)
trend = get_local_trend(numbers)

st.subheader("数据总览")
col1, col2, col3, col4 = st.columns(4)
col1.metric("数据条数", len(data))
col2.metric("号码列数", len(columns))
col3.metric("出现号码总量", len(numbers))
col4.metric("不同号码个数", freq_df.shape[0])

st.subheader("历史数据")
st.dataframe(data, use_container_width=True, hide_index=True)

st.subheader("号码频率分布")
st.bar_chart(freq_df.set_index("号码")["出现次数"])

hot, cold = st.columns(2)
with hot:
    st.markdown("### 热号 Top 10")
    st.dataframe(summary["hot"].head(10), use_container_width=True, hide_index=True)
with cold:
    st.markdown("### 冷号 Top 10")
    st.dataframe(summary["cold"].head(10), use_container_width=True, hide_index=True)

st.subheader("近期走势（智能观察）")
recent_df = pd.DataFrame({
    "号码": summary["recent"].index.astype(int),
    "近期出现次数": summary["recent"].values.astype(int),
})
st.dataframe(recent_df, use_container_width=True, hide_index=True)

st.subheader("局部趋势观察")
st.write(trend)

st.subheader("AI 风格分析建议")
for tip in summary["tips"]:
    st.info(tip)

st.subheader("随机组合生成")
max_num = int(numbers.max()) if not numbers.empty else 49
combinations = generate_random_combo(count=min(combo_size, 6), max_num=max_num, total=sample_count)
for idx, combo in enumerate(combinations, 1):
    st.write(f"组合 {idx}: {combo}")

st.caption("说明：该页面仅基于历史数据做统计分析与智能解读，不代表中奖概率或预测结果。")
