import random
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

st.set_page_config(
    page_title="AI 彩票预测中心",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).resolve().parent / "data" / "demo.csv"

st.markdown(
    """
    <style>
    .stApp { background: #050d18; color: #edf4ff; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] { background: #091827; border-right: 1px solid #16314d; }
    .block-container { max-width: 1800px; padding-top: 1.2rem; }
    .hero {
        background: linear-gradient(135deg, rgba(13, 50, 86, 0.95), rgba(7, 21, 38, 0.95));
        border: 1px solid #1d4f75;
        border-radius: 18px;
        padding: 1.3rem 1.5rem;
        box-shadow: 0 0 26px rgba(34, 211, 238, 0.12);
        margin-bottom: 1.2rem;
    }
    .hero h1 {
        color: #7ee7ff;
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        margin: 0;
    }
    .hero p {
        color: #b8d1ef;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }
    .metric-card {
        background: linear-gradient(180deg, #0d1d2f, #0b1728);
        border: 1px solid #1e4467;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: inset 0 0 20px rgba(34, 211, 238, 0.03);
    }
    .metric-label { color: #8ca7c9; font-size: 0.8rem; }
    .metric-value { color: #7ee7ff; font-size: 2rem; font-weight: 800; margin-top: 0.4rem; }
    .panel {
        background: linear-gradient(145deg, #0d1c2d, #0a1524);
        border: 1px solid #1d4165;
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .panel-title {
        color: #8fe8ff;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0.8rem;
        border-left: 3px solid #22d3ee;
        padding-left: 0.6rem;
    }
    .badge-hot { color: #ff8c8c; background: rgba(190, 24, 93, 0.14); border: 1px solid rgba(248, 113, 113, 0.4); padding: 0.2rem 0.6rem; border-radius: 999px; }
    .badge-cold { color: #9ad3ff; background: rgba(59, 130, 246, 0.14); border: 1px solid rgba(96, 165, 250, 0.4); padding: 0.2rem 0.6rem; border-radius: 999px; }
    .small-note { color: #9db2ce; font-size: 0.84rem; }
    div[data-testid="stDataFrame"] { border-radius: 12px; border: 1px solid #224a74; }
    div.stButton > button { background: linear-gradient(180deg, #0ea5e9, #0369a1); border: 1px solid #67e8f9; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>AI 彩票预测中心</h1><p>AI 评分 · 热冷排序 · 近期走势 · 历史建模 · 组合生成</p></div>',
    unsafe_allow_html=True,
)
st.warning("该工具基于历史数据建模，提供启发式分析建议，不保证中奖，彩票结果仍随机。")


def detect_number_columns(df):
    selected = []
    for col in df.columns:
        name = str(col).lower()
        if "date" in name:
            continue
        if any(token in name for token in ["ball", "num", "number", "red", "blue"]) or name.startswith("n"):
            selected.append(col)
    if selected:
        return selected
    return [c for c in df.columns if str(c).lower() != "date"]


def normalize_draws(df):
    columns = detect_number_columns(df)
    if not columns:
        raise ValueError("CSV 中没有找到可用号码列。请至少提供 n1,n2,n3,n4,n5,n6 或 ball1,ball2,... 这类格式。")

    frames = [pd.to_numeric(df[col], errors="coerce") for col in columns]
    series = pd.concat(frames, ignore_index=True).dropna().astype(int)
    return columns, series


def build_draw_matrix(df):
    cols, numbers = normalize_draws(df)
    draw_rows = []
    for _, row in df.iterrows():
        draw = []
        for col in cols:
            val = row[col]
            if pd.notna(val):
                try:
                    draw.append(int(float(val)))
                except Exception:
                    pass
        if draw:
            draw_rows.append(sorted(draw))
    return draw_rows


def build_training_data(draws, max_num=49):
    features = []
    labels = []
    history_counts = {n: 0 for n in range(1, max_num + 1)}
    last_seen = {n: None for n in range(1, max_num + 1)}

    for idx, draw in enumerate(draws):
        current_set = set(draw)
        for num in range(1, max_num + 1):
            recent_3 = 0
            recent_5 = 0
            recent_10 = 0
            recent_20 = 0
            for j in range(max(0, idx - 20), idx):
                if num in set(draws[j]):
                    recent_20 += 1
                if j >= max(0, idx - 10):
                    if num in set(draws[j]):
                        recent_10 += 1
                if j >= max(0, idx - 5):
                    if num in set(draws[j]):
                        recent_5 += 1
                if j >= max(0, idx - 3):
                    if num in set(draws[j]):
                        recent_3 += 1

            gap = 999
            if last_seen[num] is not None:
                gap = idx - last_seen[num]

            row = {
                "num": num,
                "history_total": history_counts[num],
                "recent_3": recent_3,
                "recent_5": recent_5,
                "recent_10": recent_10,
                "recent_20": recent_20,
                "last_gap": gap,
                "hot_score": history_counts[num] + recent_3 * 2 + recent_5,
            }
            features.append(row)
            labels.append(1 if num in current_set else 0)

        for num in current_set:
            history_counts[num] += 1
            last_seen[num] = idx

    feature_df = pd.DataFrame(features)
    feature_df["label"] = labels
    return feature_df


def build_predict_row_for_number(num, history_counts, last_seen, draws, max_num=49):
    idx = len(draws) - 1
    recent_3 = 0
    recent_5 = 0
    recent_10 = 0
    recent_20 = 0

    for j in range(max(0, idx - 20), idx):
        if num in set(draws[j]):
            recent_20 += 1
        if j >= max(0, idx - 10):
            if num in set(draws[j]):
                recent_10 += 1
        if j >= max(0, idx - 5):
            if num in set(draws[j]):
                recent_5 += 1
        if j >= max(0, idx - 3):
            if num in set(draws[j]):
                recent_3 += 1

    gap = 999
    if last_seen[num] is not None:
        gap = idx - last_seen[num]

    return {
        "num": num,
        "history_total": history_counts[num],
        "recent_3": recent_3,
        "recent_5": recent_5,
        "recent_10": recent_10,
        "recent_20": recent_20,
        "last_gap": gap,
        "hot_score": history_counts[num] + recent_3 * 2 + recent_5,
    }


def build_frequency_table(numbers):
    result = numbers.value_counts().sort_index().rename("出现次数").reset_index()
    result.columns = ["号码", "出现次数"]
    result["出现频率%"] = (result["出现次数"] / result["出现次数"].sum() * 100).round(2)
    return result


def build_recent_table(numbers, window):
    recent = numbers.tail(window).value_counts().sort_values(ascending=False)
    df = recent.rename("近期次数").reset_index()
    df.columns = ["号码", "近期次数"]
    df["号码"] = df["号码"].astype(int)
    return df.head(20)


with st.sidebar:
    st.header("数据源")
    uploaded = st.file_uploader("上传历史 CSV", type=["csv"]) 
    st.markdown("---")
    st.header("预测参数")
    recent_window = st.slider("近期窗口", 10, 100, 30)
    combo_count = st.slider("推荐组合数", 1, 10, 5)
    combo_size = st.slider("每组号码数量", 3, 10, 6)

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"读取上传文件失败：{exc}")
        st.stop()
else:
    try:
        df = pd.read_csv(DATA_FILE)
    except Exception as exc:
        st.error(f"读取演示文件失败：{exc}")
        st.stop()

try:
    draws = build_draw_matrix(df)
    if not draws:
        raise ValueError("CSV 中没有任何有效号码记录。")
    max_num = max(max(draw) for draw in draws)
except Exception as exc:
    st.error(f"无法解析数据：{exc}")
    st.stop()

training_df = build_training_data(draws, max_num=max_num)
feature_cols = ["num", "history_total", "recent_3", "recent_5", "recent_10", "recent_20", "last_gap", "hot_score"]
X = training_df[feature_cols]
y = training_df["label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=250, max_depth=8, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

numbers = pd.concat([pd.Series(d) for d in draws], ignore_index=True).dropna().astype(int)
freq = build_frequency_table(numbers)
recent = build_recent_table(numbers, recent_window)

st.markdown('<div class="hero"><h1>AI 彩票预测中心</h1><p>基于历史数据训练的启发式模型，输出“下一期可能关注号码”</p></div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("数据条数", len(draws))
m2.metric("最大号码", max_num)
m3.metric("模型准确率", f"{accuracy * 100:.2f}%")
m4.metric("不同号码", freq.shape[0])

left, right = st.columns([1.7, 1.2])
with left:
    st.markdown('<div class="panel"><div class="panel-title">历史出现频率</div></div>', unsafe_allow_html=True)
    st.bar_chart(freq.set_index("号码")["出现次数"], use_container_width=True)
with right:
    st.markdown('<div class="panel"><div class="panel-title">AI 推荐中位数</div></div>', unsafe_allow_html=True)
    history_counts = {n: sum(1 for draw in draws if n in draw) for n in range(1, max_num + 1)}
    last_seen = {n: None for n in range(1, max_num + 1)}
    for idx, draw in enumerate(draws):
        for n in draw:
            last_seen[n] = idx
    rows = []
    for num in range(1, max_num + 1):
        row = build_predict_row_for_number(num, history_counts, last_seen, draws, max_num=max_num)
        rows.append(row)
    probe = pd.DataFrame(rows)
    prob = model.predict_proba(probe[feature_cols])[:, 1]
    probe["prob"] = prob
    top = probe.sort_values("prob", ascending=False).head(10)
    for _, row in top.iterrows():
        st.markdown(f'<div class="small-note"><span class="badge-hot">号码 {int(row["num"])}</span> 预测概率 {row["prob"]:.3f}</div>', unsafe_allow_html=True)

hot, cold = st.columns(2)
with hot:
    st.markdown('<div class="panel"><div class="panel-title">热号 Top 10</div></div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=False).head(10), use_container_width=True, hide_index=True)
with cold:
    st.markdown('<div class="panel"><div class="panel-title">冷号 Top 10</div></div>', unsafe_allow_html=True)
    st.dataframe(freq.sort_values("出现次数", ascending=True).head(10), use_container_width=True, hide_index=True)

recent_col, ai_col = st.columns([1.1, 1.1])
with recent_col:
    st.markdown('<div class="panel"><div class="panel-title">近期走势</div></div>', unsafe_allow_html=True)
    st.bar_chart(recent.set_index("号码")["近期次数"], use_container_width=True)
    st.dataframe(recent, use_container_width=True, hide_index=True)
with ai_col:
    st.markdown('<div class="panel"><div class="panel-title">AI 预测结果</div></div>', unsafe_allow_html=True)
    final_scores = probe.sort_values("prob", ascending=False).head(12)
    final_scores = final_scores[["num", "prob", "history_total", "recent_3", "recent_5", "recent_10"]].rename(columns={"num": "号码", "prob": "预测概率"})
    st.dataframe(final_scores, use_container_width=True, hide_index=True)

st.markdown('<div class="panel"><div class="panel-title">生成组合建议</div></div>', unsafe_allow_html=True)
max_number = int(max_num)
final_top = final_scores["号码"].head(combo_size).tolist()
selected = sorted(final_top)
for i in range(1, combo_count + 1):
    if len(selected) < combo_size:
        extras = random.sample([n for n in range(1, max_number + 1) if n not in selected], combo_size - len(selected))
        combo = sorted(selected + extras)
    else:
        combo = sorted(selected[:combo_size])
    st.write(f"组合 {i}: {combo}")

st.caption("说明：这是基于历史数据训练的启发式预测模型，不保证中奖，彩票结果仍为随机事件。")

