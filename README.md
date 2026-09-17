# 3456H 企业级看板版

这是一个适合展示的中文企业级看板版分析页面，包含：

- CSV 读取和输入检查
- 热号/冷号分析
- 近期走势
- AI 启发式排序
- 组合候选生成
- 生产级看板布局

## 运行

```bash
docker compose up --build
```

浏览器访问：

```text
http://localhost:8501
```

本地运行：

```bash
cd app
python -m pip install -r requirements.txt
streamlit run app.py
```

## 说明

该项目仅用于历史数据展示，不保证中奖，不构成投资或投注建议。
