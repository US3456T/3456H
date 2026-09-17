# 3456H AI 彩票大数据中心

这是一个中文满屏版的 Streamlit 彩票数据分析页面，适合展示：

- 号码分布统计
- 热号 / 冷号分析
- 近期走势观察
- AI 风格建议
- 随机组合生成
- CSV 历史数据上传

## 运行方式

### 方式一：Docker 运行

```bash
docker compose up --build
```

浏览器打开：

```text
http://localhost:8501
```

### 方式二：本地 Python 运行

```bash
cd app
python -m pip install -r requirements.txt
streamlit run app.py
```

浏览器打开：

```text
http://localhost:8501
```

## CSV 格式说明

示例：

```csv
date,n1,n2,n3,n4,n5,n6
2026-01-01,3,11,19,27,33,42
2026-01-08,5,9,18,22,30,45
```

也支持类似：

```csv
date,ball1,ball2,ball3,ball4,ball5,ball6
```

## 说明

此工具仅用于历史数据展示与学习分析，不保证中奖，也不构成投注建议。
