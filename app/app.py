import json
import random
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="AI 彩票最终生产版", page_icon="📊", layout="wide")
DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"
FEATURES = ["number", "total_count", "recent_3", "recent_5", "recent_10", "recent_20", "gap"]

st.markdown(
    """
    <style>
    .stApp { background:#050d18; color:#ebf4ff; }
    [data-testid="stSidebar"] { background:#091827; }
    .block-container { max-width:1800px; }
    .hero { background: linear-gradient(135deg,#112d45,#071521); border:1px solid #1c4d79; border-radius:18px; padding:1.4rem 1.6rem; box-shadow:0 0 30px rgba(34,211,238,.09); }
    .hero h1 { margin:0; color:#8cecff; letter-spacing:.08em; }
    .hero p { margin:.45rem 0 0; color:#c2d5ee; }
    .card { background:linear-gradient(180deg,#0d1d2f,#0b1829); border:1px solid #1f4b75; border-radius:14px; padding:1rem; }
    .label { color:#90a9c7; font-size:.78rem; }
    .value { color:#7fe8ff; font-size:1.9rem; font-weight:800; }
    .panel { background:linear-gradient(180deg,#0d1d2e,#0a1423); border:1px solid #204c74; border-radius:16px; padding:1rem; margin-bottom:1rem; }
    .section { color:#8fe8ff; font-weight:800; border-left:3px solid #22d3ee; padding-left:.6rem; margin:1rem 0 .7rem; }
    .small { color:#abc2d9; font-size:.8rem; }
    .badge { display:inline-block; padding:.2rem .7rem; border-radius:999px; background:rgba(34,211,238,.1); border:1px solid rgba(34,211,238,.4); color:#dffbff; }
    .stTabs [role="tablist"] { gap:10px; }
    .stTabs [role="tab"] { background:#0a1b2d; border:1px solid #214b72; border-radius:10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><h1>AI 彩票最终生产版</h1><p>企业级数据看板 · 机器学习启发式 · 热冷监测 · 组合推荐</p></div>', unsafe_allow_html=True)
st.warning("仅用于历史数据分析与演示，不保证中奖，彩票结果仍具有随机性。")


def detect_columns(frame):
    cols = []
    for col in frame.columns:
        name = str(col).lower()
        if "date" not in name and (name.startswith("n") or any(x in name for x in ["ball", "num", "number", "red", "blue"])):
            cols.append(col)
    return cols or [c for c in frame.columns if "date" not in str(c).lower()]


def read_draws(frame):
    cols = detect_columns(frame)
    draws = []
    for _, row in frame.iterrows():
        draw = []
        for col in cols:
            val = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(val):
                draw.append(int(val))
        if draw:
            draws.append(sorted(set(draw)))
    if not draws:
        raise ValueError("未识别到有效号码，请使用 date,n1,n2,n3,n4,n5,n6 这样的格式。")
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
    return pd.DataFrame(rows), pd.Series(labels)


def frequency_table(draws):
    values = [n for d in draws for n in d]
    freq = pd.Series(values).value_counts().sort_index().rename_axis("号码").reset_index(name="出现次数")
    freq["出现频率%"] = (freq["出现次数"] / len(values) * 100).round(2)
    return freq


def recent_table(draws, window=30):
    values = [n for d in draws[-window:] for n in d]
    recent = pd.Series(values).value_counts().rename_axis("号码").reset_index(name="近期次数")
    recent = recent.sort_values("近期次数", ascending=False).head(20)
    return recent


def score_numbers(draws, max_number):
    return pd.DataFrame([feature_row(num, draws, len(draws)) for num in range(1, max_number + 1)])


def fit_model(draws, max_number):
    X, y = make_training_set(draws, max_number)
    if len(X) < 50 or y.nunique() < 2:
        return None, None, "样本不足，回退统计评分"
    feature_frame = X[FEATURES]
    X_train, X_test, y_train, y_test = train_test_split(feature_frame, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    target_pred = model.predict(X_test)
    metric = accuracy_score(y_test, target_pred)
    return model, metric, "随机森林（时间切分）"


with st.sidebar:
    st.header("控制中心")
    uploaded = st.file_uploader("上传历史 CSV", type=["csv"])
    recent_window = st.slider("近期窗口", 10, 100, 30)
    combo_size = st.slider("每组号码数量", 3, 10, 6)
    combo_count = st.slider("生成组合数", 1, 10, 5)

try:
    frame = pd.read_csv(uploaded) if uploaded else pd.read_csv(DATA_FILE)
    columns, draws = read_draws(frame)
    max_number = max(max(draw) for draw in draws)
except Exception as exc:
    st.error(f"数据读取失败：{exc}")
    st.stop()

freq = frequency_table(draws)
recent = recent_table(draws, recent_window)
model, acc, model_name = fit_model(draws, max_number)
score_frame = score_numbers(draws, max_number)
if model is not None:
    score_frame["模型分数"] = model.predict_proba(score_frame[FEATURES])[:, 1]
else:
    score_frame["模型分数"] = (score_frame["total_count"] + 1.5 * score_frame["recent_5"] + 0.6 * score_frame["recent_10"]) / max(1, len(draws))
score_frame["模型分数"] = score_frame["模型分数"].round(4)
ranked = score_frame.rename(columns={"number": "号码"}).sort_values("模型分数", ascending=False)

metrics = st.columns(5)
vals = [("数据条数", len(draws)), ("号码字段", len(columns)), ("最大号码", max_number), ("样本总数", sum(len(draw) for draw in draws)), ("模型", model_name)]
for col, (label, value) in zip(metrics, vals):
    col.markdown(f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

if acc is not None:
    st.info(f"时间切分回测准确率：{acc:.2%}")

main_left, main_right = st.columns([1.7, 1.2])
with main_left:
    st.markdown('<div class="section">号码频率</div>', unsafe_allow_html=True)
    st.bar_chart(freq.set_index("号码")["出现次数"], use_container_width=True)
with main_right:
    st.markdown('<div class="section">模型关注</div>', unsafe_allow_html=True)
    top10 = ranked.head(10)[["号码", "模型分数", "total_count", "recent_5", "gap"]].rename(columns={"total_count":"历史次数", "recent_5":"近5期", "gap":"距离上次"})
    st.dataframe(top10, use_container_width=True, hide_index=True)

hot_col, cold_col = st.columns(2)
with hot_col:
    st.markdown('<div class="section">热号 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold_col:
    st.markdown('<div class="section">冷号 Top 10</div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

past, ai = st.columns([1.2, 1.2])
with past:
    st.markdown('<div class="section">近期走势</div>', unsafe_allow_html=True)
    recent_chart = recent.set_index("号码")["近期次数"]
    st.bar_chart(recent_chart, use_container_width=True)
    st.dataframe(recent, use_container_width=True, hide_index=True)
with ai:
    st.markdown('<div class="section">AI 预测结果</div>', unsafe_allow_html=True)
    top = ranked.head(15)[["号码", "模型分数", "total_count", "recent_3", "recent_5", "recent_10"]].rename(columns={"total_count":"历史次数", "recent_3":"近3期", "recent_5":"近5期", "recent_10":"近10期"})
    st.dataframe(top, use_container_width=True, hide_index=True)

st.markdown('<div class="section">组合演示</div>', unsafe_allow_html=True)
seed = ranked.head(combo_size)["号码"].tolist()
for i in range(1, combo_count + 1):
    selected = seed[:]
    if len(selected) < combo_size:
        extras = [n for n in range(1, max_number + 1) if n not in selected]
        selected += random.sample(extras, min(combo_size - len(selected), len(extras)))
    combo = sorted(selected[:combo_size])
    st.write(f"组合 {i}: {combo}")

st.caption("说明：该版本使用历史样本进行启发式建模和推荐排序，不能保证中奖，也不构成投注建议。）")
