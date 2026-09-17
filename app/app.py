from pathlib import Path
import random

import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="AI 彩票生产级分析大屏", page_icon="📊", layout="wide")
DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"
FEATURES = ["number", "total_count", "recent_3", "recent_5", "recent_10", "recent_20", "gap"]

st.markdown("""
<style>
.stApp { background:#050b14; color:#e8f1ff; }
[data-testid="stSidebar"] { background:#091522; }
.block-container { max-width:1800px; padding-top:1rem; }
.hero { padding:1.4rem 1.6rem; border:1px solid #1f5b83; border-radius:18px; background:linear-gradient(135deg,#103553,#071322); box-shadow:0 0 30px #0ea5e933; }
.hero h1 { margin:0; color:#7ee7ff; letter-spacing:.08em; }
.hero p { color:#aec6e4; margin:.4rem 0 0; }
.card { padding:1rem; border:1px solid #214766; border-radius:14px; background:#0b1929; }
.card-label { color:#91aac8; font-size:.8rem; }
.card-value { color:#7ee7ff; font-size:1.8rem; font-weight:800; }
.section { color:#8fe8ff; font-weight:800; border-left:3px solid #22d3ee; padding-left:.6rem; margin:1rem 0 .7rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>AI 彩票生产级分析大屏</h1><p>可复现数据处理 · 时间切分评估 · 模型评分 · 历史统计</p></div>', unsafe_allow_html=True)
st.warning("彩票结果具有随机性。模型分数不是中奖概率，也不构成投注建议。")


def find_columns(frame):
    selected = []
    for col in frame.columns:
        name = str(col).lower()
        if "date" not in name and (name.startswith("n") or any(x in name for x in ("ball", "num", "number", "red", "blue"))):
            selected.append(col)
    return selected or [c for c in frame.columns if "date" not in str(c).lower()]


def read_draws(frame):
    columns = find_columns(frame)
    draws = []
    for _, row in frame.iterrows():
        draw = []
        for col in columns:
            value = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(value):
                draw.append(int(value))
        if draw:
            draws.append(sorted(set(draw)))
    if not draws:
        raise ValueError("没有识别到有效号码。请使用 date,n1,n2,n3,n4,n5,n6 格式。")
    return columns, draws


def feature_row(number, draws, index):
    before = draws[:index]
    total = sum(number in draw for draw in before)
    gap = index + 1
    for distance, draw in enumerate(reversed(before), 1):
        if number in draw:
            gap = distance
            break
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
        for number in range(1, max_number + 1):
            rows.append(feature_row(number, draws, index))
            labels.append(int(number in draw))
    return pd.DataFrame(rows), pd.Series(labels, name="label")


def score_numbers(draws, max_number):
    rows = [feature_row(n, draws, len(draws)) for n in range(1, max_number + 1)]
    return pd.DataFrame(rows)


def fit_model(draws, max_number):
    training, labels = make_training_set(draws, max_number)
    if len(training) < 20 or labels.nunique() < 2:
        return None, None, "样本太少，使用统计评分"
    split = max(1, int(len(training) * .8))
    model = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, class_weight="balanced")
    model.fit(training[FEATURES].iloc[:split], labels.iloc[:split])
    prediction = model.predict(training[FEATURES].iloc[split:])
    score = accuracy_score(labels.iloc[split:], prediction) if len(prediction) else None
    return model, score, "时间切分随机森林"


def frequency_frame(draws):
    values = [number for draw in draws for number in draw]
    result = pd.Series(values).value_counts().sort_index().rename_axis("号码").reset_index(name="出现次数")
    result["出现频率%"] = (result["出现次数"] / len(values) * 100).round(2)
    return result


with st.sidebar:
    st.header("控制中心")
    uploaded = st.file_uploader("上传历史 CSV", type=["csv"])
    recent_window = st.slider("近期窗口", 5, 100, 30)
    combo_size = st.slider("每组号码数量", 3, 10, 6)
    combo_count = st.slider("生成组合数量", 1, 10, 5)

try:
    frame = pd.read_csv(uploaded) if uploaded else pd.read_csv(DATA_FILE)
    columns, draws = read_draws(frame)
    max_number = max(max(draw) for draw in draws)
except Exception as error:
    st.error(f"数据读取失败：{error}")
    st.stop()

frequency = frequency_frame(draws)
model, validation_score, model_name = fit_model(draws, max_number)
probe = score_numbers(draws, max_number)

if model is not None:
    probe["模型分数"] = model.predict_proba(probe[FEATURES])[:, 1]
else:
    probe["模型分数"] = (probe["total_count"] + 1.5 * probe["recent_5"] + probe["recent_10"]) / max(1, len(draws))
probe["模型分数"] = probe["模型分数"].round(4)
ranked = probe.sort_values(["模型分数", "total_count"], ascending=False)

metrics = st.columns(5)
for box, label, value in zip(metrics, ["开奖记录", "号码字段", "最大号码", "样本总数", "模型"], [len(draws), len(columns), max_number, sum(map(len, draws)), model_name]):
    box.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section">模型与数据质量</div>', unsafe_allow_html=True)
quality_left, quality_right = st.columns(2)
with quality_left:
    st.info(f"模型：{model_name}")
with quality_right:
    st.info("验证指标仅反映历史样本，不能代表未来表现。" if validation_score is None else f"时间切分回测准确率：{validation_score:.2%}（仅供参考）")

chart_left, chart_right = st.columns([1.5, 1])
with chart_left:
    st.markdown('<div class="section">号码频率</div>', unsafe_allow_html=True)
    st.bar_chart(frequency.set_index("号码")["出现次数"], use_container_width=True)
with chart_right:
    st.markdown('<div class="section">模型关注号码</div>', unsafe_allow_html=True)
    st.dataframe(ranked.head(10)[["number", "模型分数", "total_count", "recent_5", "gap"]].rename(columns={"number":"号码", "total_count":"历史次数", "recent_5":"近5期", "gap":"距离上次"}), use_container_width=True, hide_index=True)

hot, cold = st.columns(2)
with hot:
    st.markdown('<div class="section">热号</div>', unsafe_allow_html=True)
    st.dataframe(frequency.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold:
    st.markdown('<div class="section">冷号</div>', unsafe_allow_html=True)
    st.dataframe(frequency.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

st.markdown('<div class="section">近期走势</div>', unsafe_allow_html=True)
recent_values = [n for draw in draws[-recent_window:] for n in draw]
recent = pd.Series(recent_values).value_counts().rename_axis("号码").reset_index(name="近期次数")
st.bar_chart(recent.set_index("号码")["近期次数"], use_container_width=True)

st.markdown('<div class="section">生产级模型输出</div>', unsafe_allow_html=True)
st.dataframe(ranked.head(20).rename(columns={"number":"号码", "total_count":"历史次数", "recent_3":"近3期", "recent_5":"近5期", "recent_10":"近10期", "recent_20":"近20期", "gap":"距离上次", "模型分数":"模型分数"}), use_container_width=True, hide_index=True)

st.markdown('<div class="section">组合演示</div>', unsafe_allow_html=True)
seed = ranked.head(min(combo_size, len(ranked)))["number"].tolist()
for index in range(combo_count):
    selected = seed[:]
    candidates = [n for n in range(1, max_number + 1) if n not in selected]
    if len(selected) < combo_size:
        selected += random.sample(candidates, min(combo_size - len(selected), len(candidates)))
    st.write(f"组合 {index + 1}：{' · '.join(map(str, sorted(selected[:combo_size])))}")

st.caption("生产说明：本版本增加了输入校验、时间切分回测、可复现随机森林和数据质量提示；仍不能改变彩票的随机性。")
