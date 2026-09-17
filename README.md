import random
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI 彩票分析大盘", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.title("📊 AI 彩票分析大盘")
st.caption("整合：历史频率、热冷分析、近期分布、智能推荐与随机组合生成")
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
        if any(token in c for token in [
            "ball", "num", "number", "n1", "n2", "n3", "n4", "n5", "n6", "red", "blue"
        ]):
            preferred.append(col)
    if preferred:
        return preferred
    return [c for c in df.columns if c.lower() != "date"]


def normalize_draws(df: pd.DataFrame):
    columns = detect_number_columns(df)
    if not columns:
        raise ValueError("CSV 里没有找到可用号码列。请至少提供 n1,n2,n3,n4,n5,n6 或 ball1,ball2,... 格式。")

    frames = []
    for col in columns:
        s = pd.to_numeric(df[col], errors="coerce")
        frames.append(s)

    series = pd.concat(frames, ignore_index=True).dropna().astype(int)
    return columns, series


def build_frequency_table(series: pd.Series):
    counts = series.value_counts().sort_index()
    df = counts.rename("出现次数").reset_index().rename(columns={"index": "号码", "出现次数": "出现次数"})
    df["出现频率%"] = (df["出现次数"] / df["出现次数"].sum() * 100).round(2)
    return df


def build_recent_table(series: pd.Series, lookback: int = 30):
    recent = series.tail(lookback).value_counts().sort_values(ascending=False)
    df = recent.rename("近期出现次数").reset_index().rename(columns={"index": "号码", "近期出现次数": "近期出现次数"})
    df["号码"] = df["号码"].astype(int)
    return df.head(20)


def build_ai_recommendation(freq_df: pd.DataFrame, recent_df: pd.DataFrame, series: pd.Series):
    if freq_df.empty:
        return pd.DataFrame(columns=["号码", "综合分", "说明"])

    score_table = freq_df.copy()
    score_table["号码"] = score_table["号码"].astype(int)
    recent_map = dict(zip(recent_df["号码"].astype(int), recent_df["近期出现次数"]))
    score_table["近期出现次数"] = score_table["号码"].map(recent_map).fillna(0).astype(int)

    # 启发式评分：总出现次数 + 近期活跃度 + 排除极端冷号
    score_table["综合分"] = (
        score_table["出现次数"] * 1.0 +
        score_table["近期出现次数"] * 1.5
    ).round(2)

    score_table = score_table.sort_values(["综合分", "出现次数"], ascending=False)
    score_table["说明"] = "热号/近期活跃"
    score_table.loc[score_table["近期出现次数"] == 0, "说明"] = "偏冷号，待观察"

    return score_table[["号码", "综合分", "出现次数", "近期出现次数", "说明"]].head(15)


def generate_random_combo(count: int = 6, max_num: int = 49, total: int = 5):
    result = []
    for _ in range(total):
        combo = sorted(random.sample(range(1, max_num + 1), count))
        result.append(combo)
    return result


with st.sidebar:
    st.header("数据来源")
    uploaded = st.file_uploader("上传 CSV 历史数据", type=["csv"], help="例如：date,n1,n2,n3,n4,n5,n6")
    st.markdown("---")
    st.header("分析设置")
    combo_count = st.slider("随机组合数", min_value=1, max_value=10, value=5)
    combo_size = st.slider("每组号码数量", min_value=3, max_value=10, value=6)
    recent_window = st.slider("近期窗口", min_value=10, max_value=100, value=30)

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
    columns, numbers = normalize_draws(data)
except Exception as exc:
    st.error(f"无法识别数据：{exc}")
    st.stop()

freq_df = build_frequency_table(numbers)
recent_df = build_recent_table(numbers, lookback=recent_window)
recommend_df = build_ai_recommendation(freq_df, recent_df, numbers)

st.subheader("数据总览")
col1, col2, col3, col4 = st.columns(4)
col1.metric("数据条数", len(data))
col2.metric("号码列数", len(columns))
col3.metric("号码总出现次数", len(numbers))
col4.metric("不同号码个数", freq_df.shape[0])

st.subheader("历史数据")
st.dataframe(data, use_container_width=True, hide_index=True)

# Tabs
overview_tab, hot_tab, recent_tab, ai_tab, combo_tab = st.tabs([
    "总览",
    "热冷分析",
    "近期走势",
    "AI 推荐",
    "随机组合"
])

with overview_tab:
    st.subheader("号码频率分布")
    st.bar_chart(freq_df.set_index("号码")["出现次数"])

    hottest = freq_df.sort_values("出现次数", ascending=False).head(10)
    st.markdown("**Top 10 热号**")
    st.dataframe(hottest, use_container_width=True, hide_index=True)

with hot_tab:
    hot, cold = st.columns(2)
    with hot:
        st.markdown("### 热号 Top 10")
        st.dataframe(freq_df.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
    with cold:
        st.markdown("### 冷号 Top 10")
        st.dataframe(freq_df.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

with recent_tab:
    st.markdown("### 近期出现强度")
    st.dataframe(recent_df, use_container_width=True, hide_index=True)

    if recent_df.empty:
        st.warning("近期窗口内没有数据。")
    else:
        st.bar_chart(recent_df.set_index("号码")["近期出现次数"])

with ai_tab:
    st.markdown("### AI 风格建议")

    generated_tips = []
    if not recommend_df.empty:
        top_numbers = recommend_df["号码"].head(5).tolist()
        generated_tips.append(f"优先观察：{', '.join(map(str, top_numbers))}。它们在总频率和近窗口活跃度上整体更强。")

        hot_numbers = freq_df.sort_values("出现次数", ascending=False).head(5)["号码"].tolist()
        generated_tips.append(f"热号集中区：{', '.join(map(str, hot_numbers))}。近期出现较多，适合做观察。")

        cold_numbers = freq_df.sort_values("出现次数", ascending=True).head(5)["号码"].tolist()
        generated_tips.append(f"冷号观察：{', '.join(map(str, cold_numbers))}。当前较少出现，可作为对照窗口。")

    for item in generated_tips:
        st.info(item)

    st.markdown("### 综合推荐表")
    st.dataframe(recommend_df, use_container_width=True, hide_index=True)

with combo_tab:
    st.markdown("### 随机组合生成")
    max_num = int(numbers.max()) if not numbers.empty else 49
    combos = generate_random_combo(count=min(combo_size, 6), max_num=max_num, total=combo_count)
    for idx, combo in enumerate(combos, 1):
        st.write(f"组合 {idx}: {combo}")

st.caption("说明：该页面只做历史数据分析与统计解读，不保证中奖，所有号码仍属于随机事件。")
