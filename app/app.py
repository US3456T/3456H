import random
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI 彩票分析大盘", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.title("📊 AI 彩票分析大盘")
st.caption("基于历史数据的智能统计、热号/冷号分析、近期走势和随机组合生成。")
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

    df2 = df.copy()
    frames = []
    for col in columns:
        s = pd.to_numeric(df2[col], errors="coerce")
        frames.append(s)

    series = pd.concat(frames, ignore_index=True).dropna().astype(int)
    return df2, columns, series


def build_frequency_table(series: pd.Series):
    counts = series.value_counts().sort_index()
    return counts.rename("出现次数").reset_index().rename(columns={"index": "号码", "出现次数": "出现次数"})


def get_recent_numbers(series: pd.Series, lookback: int = 20):
    # 近 lookback 个号码作为最近走势曝光
    return series.tail(lookback).value_counts().sort_values(ascending=False)


def generate_insights(freq_df: pd.DataFrame, recent_counts: pd.Series, series: pd.Series):
    all_nums = list(range(1, int(series.max()) + 1))
    seen_set = set(freq_df["号码"].tolist())
    missed = [n for n in all_nums if n not in seen_set]

    hot = freq_df.sort_values("出现次数", ascending=False).head(10)
    cold = freq_df.sort_values("出现次数", ascending=True).head(10)

    recent_top = recent_counts.head(10)
    recent_top_df = pd.DataFrame({
        "号码": recent_top.index.astype(int),
        "近期出现次数": recent_top.values.astype(int),
    })

    # 这部分是“AI 风格”启发式推理，不是概率保证
    tips = []
    if not hot.empty:
        tips.append(f"热号建议：{', '.join(map(str, hot['号码'].head(5).tolist()))} 近期频繁出现，适合观测。")
    if not cold.empty:
        tips.append(f"冷号观察：{', '.join(map(str, cold['号码'].head(5).tolist()))} 当前出现较少，可作为对照观察。")
    if len(missed) > 0:
        tips.append(f"未出现号码：{', '.join(map(str, missed[:10]))}，这些号码在当前样本中尚未出现。")
    if not recent_top_df.empty:
        tips.append(f"最近走势重点：{', '.join(map(str, recent_top_df['号码'].head(5).tolist()))} 在近段数据中更活跃。")

    return {
        "hot": hot,
        "cold": cold,
        "recent": recent_top_df,
        "tips": tips,
        "missed": missed,
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
    st.header("分析选项")
    min_draws = st.slider("最小统计样本", min_value=1, max_value=50, value=5)
    sample_count = st.slider("生成随机组合数", min_value=1, max_value=20, value=5)

if uploaded is not None:
    try:
        data = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"读取上传文件失败：{exc}")
        st.stop()
else:
    data = load_demo_data()

try:
    df, columns, numbers = normalize_draws(data)
except Exception as exc:
    st.error(f"读取数据失败：{exc}")
    st.stop()

freq_df = build_frequency_table(numbers)
insights = generate_insights(freq_df, get_recent_numbers(numbers), numbers)

col1, col2, col3, col4 = st.columns(4)
col1.metric("数据条数", len(df))
col2.metric("号码列数", len(columns))
col3.metric("号码总出现次数", len(numbers))
col4.metric("不同号码数", freq_df.shape[0])

st.subheader("历史数据")
st.dataframe(df, use_container_width=True, hide_index=True)

if not freq_df.empty:
    st.subheader("号码出现频次总览")
    st.bar_chart(freq_df.set_index("号码")["出现次数"])

    st.subheader("热号 / 冷号")
    hot, cold = st.columns(2)
    with hot:
        st.markdown("**热号 Top 10**")
        st.dataframe(insights["hot"].head(10), use_container_width=True, hide_index=True)
    with cold:
        st.markdown("**冷号 Top 10**")
        st.dataframe(insights["cold"].head(10), use_container_width=True, hide_index=True)

    st.subheader("近期走势")
    recent = insights["recent"]
    st.dataframe(recent, use_container_width=True, hide_index=True)

    st.subheader("AI 智能分析建议")
    for item in insights["tips"]:
        st.info(item)

    st.subheader("随机生成组合示例")
    max_num = int(numbers.max()) if not numbers.empty else 49
    combo_count = min(sample_count, 10)
    generated = generate_random_combo(count=min(len(columns), 6), max_num=max_num, total=combo_count)
    for i, combo in enumerate(generated, 1):
        st.write(f"组合 {i}: {combo}")

st.caption("说明：本工具基于历史频率和近期分布进行统计分析，不能保证中奖结果。")
