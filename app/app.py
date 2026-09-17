import streamlit as st
import pandas as pd
import numpy as np
import random
from pathlib import Path

st.set_page_config(page_title="AI 彩票大屏分析", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.title("📊 AI 彩票大屏分析")
st.caption("大屏版：历史统计 + 热冷分析 + 近期走势 + AI 风格提示 + 随机组合")
st.warning("仅用于历史数据分析与学习展示，不能保证中奖。")

@st.cache_data
def load_demo_data():
    return pd.read_csv(DATA_FILE)


def detect_number_columns(df):
    cols = []
    for c in df.columns:
        cc = str(c).lower()
        if "date" in cc:
            continue
        if any(token in cc for token in ["ball", "num", "number", "n1", "n2", "n3", "n4", "n5", "n6", "red", "blue"]):
            cols.append(c)
    if cols:
        return cols
    return [c for c in df.columns if str(c).lower() != "date"]


def normalize(df):
    columns = detect_number_columns(df)
    if not columns:
        raise ValueError("CSV 里没有找到可用号码列。")
    frames = []
    for col in columns:
        frames.append(pd.to_numeric(df[col], errors="coerce"))
    series = pd.concat(frames, ignore_index=True).dropna().astype(int)
    return columns, series


def freq_table(series):
    counts = series.value_counts().sort_index()
    df = counts.rename("出现次数").reset_index().rename(columns={"index": "号码", "出现次数": "出现次数"})
    df["出现频率%"] = (df["出现次数"] / df["出现次数"].sum() * 100).round(2)
    return df


def recent_table(series, lookback=30):
    recent = series.tail(lookback).value_counts().sort_values(ascending=False)
    df = recent.rename("近期出现次数").reset_index().rename(columns={"index": "号码", "近期出现次数": "近期出现次数"})
    df["号码"] = df["号码"].astype(int)
    return df.head(20)


def build_recommend(freq_df, recent_df, series):
    score = freq_df.copy()
    score["号码"] = score["号码"].astype(int)
    recent_map = dict(zip(recent_df["号码"].astype(int), recent_df["近期出现次数"]))
    score["近期出现次数"] = score["号码"].map(recent_map).fillna(0).astype(int)
    score["综合分"] = (score["出现次数"] * 1.0 + score["近期出现次数"] * 1.5).round(2)
    score = score.sort_values(["综合分", "出现次数"], ascending=False)
    score["说明"] = "热号/近期活跃"
    score.loc[score["近期出现次数"] == 0, "说明"] = "偏冷号"
    return score[["号码", "综合分", "出现次数", "近期出现次数", "说明"]].head(15)


def make_combo(count=6, max_num=49, total=5):
    out = []
    for _ in range(total):
        out.append(sorted(random.sample(range(1, max_num + 1), count)))
    return out

with st.sidebar:
    st.header("数据源")
    uploaded = st.file_uploader("上传 CSV 历史数据", type=["csv"]) 
    st.markdown("---")
    st.header("大屏设置")
    combo_count = st.slider("随机组合数", 1, 10, 5)
    combo_size = st.slider("每组号码数量", 3, 10, 6)
    recent_window = st.slider("近期窗口", 10, 100, 30)

if uploaded is not None:
    try:
        data = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"读取上传数据失败：{exc}")
        st.stop()
else:
    data = load_demo_data()

try:
    cols, numbers = normalize(data)
except Exception as exc:
    st.error(f"无法识别数据：{exc}")
    st.stop()

freq_df = freq_table(numbers)
recent_df = recent_table(numbers, lookback=recent_window)
recommend_df = build_recommend(freq_df, recent_df, numbers)

# 顶部指标
st.subheader("数据总览")
col1, col2, col3, col4 = st.columns(4)
col1.metric("数据条数", len(data))
col2.metric("号码列数", len(cols))
col3.metric("号码总出现次数", len(numbers))
col4.metric("不同号码数", freq_df.shape[0])

# 大屏图片板
st.subheader("分析面板")
main_left, main_right = st.columns([2, 1])

with main_left:
    st.markdown("### 热号分布")
    st.bar_chart(freq_df.set_index("号码")["出现次数"])

with main_right:
    st.markdown("### 重点观察")
    if not recommend_df.empty:
        top5 = recommend_df.head(5)
        for _, row in top5.iterrows():
            st.info(f"号码 {int(row['号码'])}：综合分 {row['综合分']}，近期出现 {int(row['近期出现次数'])} 次")

# 第二行：热冷
hot, cold = st.columns(2)
with hot:
    st.markdown("### 热号 Top 10")
    st.dataframe(freq_df.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold:
    st.markdown("### 冷号 Top 10")
    st.dataframe(freq_df.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

# 第三行：近期走势 + AI 建议
recent_panel, ai_panel = st.columns([1.2, 1.2])
with recent_panel:
    st.markdown("### 近期走势")
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
    st.bar_chart(recent_df.set_index("号码")["近期出现次数"])

with ai_panel:
    st.markdown("### AI 风格分析建议")
    top_numbers = recommend_df["号码"].head(5).tolist()
    hot_numbers = freq_df.sort_values("出现次数", ascending=False).head(5)["号码"].tolist()
    cold_numbers = freq_df.sort_values("出现次数", ascending=True).head(5)["号码"].tolist()
    st.info(f"优先观察：{', '.join(map(str, top_numbers))}")
    st.info(f"热号集中区：{', '.join(map(str, hot_numbers))}")
    st.info(f"冷号观察区：{', '.join(map(str, cold_numbers))}")
    st.dataframe(recommend_df, use_container_width=True, hide_index=True)

# 随机组合
st.subheader("随机组合生成")
max_num = int(numbers.max()) if not numbers.empty else 49
combos = make_combo(count=min(combo_size, 6), max_num=max_num, total=combo_count)
for i, combo in enumerate(combos, 1):
    st.write(f"组合 {i}: {combo}")

st.caption("说明：本大屏仅提供历史数据统计与智能展示，不保证中奖。")
