import random
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="彩票数据分析演示", page_icon="📊", layout="wide")

st.title("📊 彩票数据分析演示")
st.warning("统计结果只反映历史数据，不能预测随机开奖结果，也不保证中奖。")

DATA_FILE = Path(__file__).parent / "data" / "demo.csv"

uploaded = st.file_uploader("上传 CSV 历史数据（可选）", type=["csv"])
try:
    data = pd.read_csv(uploaded) if uploaded else pd.read_csv(DATA_FILE)
except Exception as exc:
    st.error(f"读取数据失败：{exc}")
    st.stop()

st.subheader("历史数据")
st.dataframe(data, use_container_width=True, hide_index=True)

number_columns = [
    column for column in data.columns
    if column.lower().startswith(("n", "ball", "red", "blue"))
]
if not number_columns:
    number_columns = [column for column in data.columns if column != "date"]

numbers = pd.to_numeric(data[number_columns].stack(), errors="coerce").dropna().astype(int)
counts = numbers.value_counts().sort_index()

left, right = st.columns(2)
with left:
    st.metric("记录条数", len(data))
    st.metric("号码列数", len(number_columns))
with right:
    st.metric("不同号码数", counts.size)
    st.metric("参与统计的号码总数", len(numbers))

st.subheader("号码出现次数")
chart = counts.rename("出现次数")
st.bar_chart(chart)

st.subheader("随机演示组合")
max_number = int(numbers.max()) if not numbers.empty else 49
pick_count = min(len(number_columns), max_number)
if st.button("生成一组随机演示号码"):
    result = sorted(random.sample(range(1, max_number + 1), pick_count))
    st.success("、".join(map(str, result)))

st.caption("数据来源：仓库中的演示 CSV 或你上传的 CSV。")
