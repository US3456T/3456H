# 3456H 最终生产版

这是一个中文企业级数据看板，集成：

- 号码频率统计
- 热号/冷号分析
- 近期走势观察
- AI 启发式排序
- 模型回测指标
- 生成组合建议
- CSV 上传支持

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

该项目仅用于历史数据分析和演示，不保证中奖，不构成投注建议。
