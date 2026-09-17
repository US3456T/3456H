import random
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="AI 彩票企业级看板", page_icon="📊", layout="wide")
DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"
FEATURES = ["number", "total_count", "recent_3", "recent_5", "recent_10", "recent_20", "gap"]

st.markdown(
    """
    <style>
    .stApp { background: #07121d; color: #edf6ff; }
    [data-testid="stSidebar"] { background: #0a1c2b; }
    .block-container { max-width: 1800px; padding-top: 1rem; }
    .hero { background: linear-gradient(135deg, #102b43, #081521); border:1px solid #1b4d73; border-radius:18px; padding:1.4rem 1.5rem; margin-bottom:1rem; }
    .hero h1 { margin:0; color:#89efff; letter-spacing:.08em; }
    .hero p { margin:.4rem 0 0; color:#b8d4ee; }
    .card { background:#0d1d2f; border:1px solid #1d4c74; padding:1rem; border-radius:14px; }
    .label { color:#8fa9c9; font-size:.78rem; }
    .value { color:#80ebff; font-size:2rem; font-weight:800; }
    .section { color:#8fe9ff; font-weight:800; border-left:3px solid #22d3ee; padding-left:.6rem; margin:1rem 0 .6rem; }
    .badge { display:inline-block; padding:0.2rem 0.7rem; border-radius:999px; background:#123857; border:1px solid #2aa7d8; color:#dff7ff; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><h1>AI 彩票企业级看板</h1><p>生产级分析 · 历史建模 · 热冷分布 · 组合推荐</p></div>', unsafe_allow_html=True)
st.warning("仅用于历史数据分析与演示，不保证中奖。")


def detect_columns(frame):
    selected = []
    for col in frame.columns:
        name = str(col).lower()
        if "date" not in name and (name.startswith("n") or any(x in name for x in ["ball", "num", "number", "red", "blue"])):
            selected.append(col)
    return selected or [c for c in frame.columns if "date" not in str(c).lower()]


def read_draws(frame):
    cols = detect_columns(frame)
    draws = []
    for _, row in frame.iterrows():
        draw = []
        for col in cols:
            value = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(value):
                draw.append(int(value))
        if draw:
            draws.append(sorted(set(draw)))
    if not draws:
        raise ValueError("未识别到有效号码，请使用 date,n1,n2,n3,n4,n5,n6 这类格式。")
    return cols, draws


def feature_row(number, draws, index):
    before = draws[:index]
    total = sum(number in draw for draw in before)
    gap = index
    for d in range(1, len(before) + 1):
        if number in before[-d]:
            gap = d
            break
    if number not in {n for d in before for n in d}:
        gap = index + 1
    return {
        "number": number,
        "total_count": total,
        "recent_3": sum(number in d for d in before[-3:]),
        "recent_5": sum(number in d for d in before[-5:]),
        "recent_10": sum(number in d for d in before[-10:]),
        "recent_20": sum(number in d for d in before[-20:]),
        "gap": gap,
    }


def make_training_set(draws, max_number):
    rows, labels = [], []
    for index, draw in enumerate(draws):
        if index == 0:
            continue
        for num in range(1, max_number + 1):
            rows.append(feature_row(num, draws, index))
            labels.append(1 if num in draw else 0)
    return pd.DataFrame(rows), pd.Series(labels, name="label")


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


def score_numbers(draws, max_number):
    rows = []
    for num in range(1, max_number + 1):
        rows.append(feature_row(num, draws, len(draws)))
    return pd.DataFrame(rows)


def fit_model(draws, max_number):
    X, y = make_training_set(draws, max_number)
    if len(X) < 50 or y.nunique() < 2:
        return None, None, "样本不足，使用统计评分"
    feature_frame = X[FEATURES]
    X_train, X_test, y_train, y_test = train_test_split(feature_frame, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    return model, acc, "随机森林（时间切分）"


with st.sidebar:
    st.header("看板参数")
    uploaded = st.file_uploader("上传 CSV 历史数据", type=["csv"])
    recent_window = st.slider("近期窗口", 10, 100, 30)
    combo_size = st.slider("每组推荐数", 3, 10, 6)
    combo_count = st.slider("生成组合数", 1, 10, 5)

try:
    frame = pd.read_csv(uploaded) if uploaded else pd.read_csv(DATA_FILE)
    columns, draws = read_draws(frame)
    max_number = max(max(draw) for draw in draws)
except Exception as exc:
    st.error(f"数据加载失败：{exc}")
    st.stop()

freq = frequency_table(draws)
recent = recent_table(draws, recent_window)
model, acc, model_label = fit_model(draws, max_number)
score_frame = score_numbers(draws, max_number)

if model is not None:
    score_frame["模型分数"] = model.predict_proba(score_frame[FEATURES])[:, 1]
else:
    score_frame["模型分数"] = (score_frame["total_count"] + 1.5 * score_frame["recent_5"] + 0.5 * score_frame["recent_10"]) / max(1, len(draws))
score_frame["模型分数"] = score_frame["模型分数"].round(4)
ranked = score_frame.rename(columns={"number":"号码"}).sort_values("模型分数", ascending=False)

metrics = st.columns(5)
values = [
    ("数据条数", len(draws)),
    ("号码字段", len(columns)),
    ("最大号码", max_number),
    ("样本总数", sum(len(draw) for draw in draws)),
    ("模型", model_label),
]
for col, (label, value) in zip(metrics, values):
    col.markdown(f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

if acc is not None:
    st.info(f"时间切分回测准确率：{acc:.2%}")

left, right = st.columns([1.6, 1])
with left:
    st.markdown('<div class="section">号码频率</div>', unsafe_allow_html=True)
    st.bar_chart(freq.set_index("号码")["出现次数"], use_container_width=True)
with right:
    st.markdown('<div class="section">模型优先级</div>', unsafe_allow_html=True)
    top = ranked.head(10)[["号码", "模型分数", "total_count", "recent_5", "gap"]]
    st.dataframe(top.rename(columns={"total_count":"历史次数", "recent_5":"近5期", "gap":"距离上次"}), use_container_width=True, hide_index=True)

hot_col, cold_col = st.columns(2)
with hot_col:
    st.markdown('<div class="section">热号 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold_col:
    st.markdown('<div class="section">冷号 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

recent_col, insight_col = st.columns([1.2, 1.2])
with recent_col:
    st.markdown('<div class="section">近期走势</div>', unsafe_allow_html=True)
    st.bar_chart(recent.set_index("号码")["近期次数"], use_container_width=True)
    st.dataframe(recent, use_container_width=True, hide_index=True)
with insight_col:
    st.markdown('<div class="section">AI 建议</div>', unsafe_allow_html=True)
    top_numbers = ranked.head(5)["号码"].tolist()
    hot_numbers = freq.sort_values("出现次数", ascending=False).head(5)["号码"].tolist()
    cold_numbers = freq.sort_values("出现次数", ascending=True).head(5)["号码"].tolist()
    st.info(f"优先观察：{', '.join(map(str, top_numbers))}")
    st.info(f"热号区：{', '.join(map(str, hot_numbers))}")
    st.info(f"冷号观察：{', '.join(map(str, cold_numbers))}")
    st.dataframe(ranked.head(15)[["号码", "模型分数", "total_count", "recent_5", "recent_10"]].rename(columns={"recent_5":"近5期", "recent_10":"近10期", "total_count":"历史次数"}), use_container_width=True, hide_index=True)

st.markdown('<div class="section">组合演示</div>', unsafe_allow_html=True)
selected = ranked.head(combo_size)["号码"].tolist()
for i in range(1, combo_count + 1):
    combo = sorted(selected[:combo_size])
    if len(combo) < combo_size:
        extras = [n for n in range(1, max_number + 1) if n not in combo]
        combo += random.sample(extras, combo_size - len(combo))
    st.write(f"组合 {i}: {sorted(combo)[:combo_size]}")

st.caption("说明：这是时间序列评估下的历史启发式分析，不保证中奖，也不构成投注建议。")
