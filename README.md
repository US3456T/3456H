# 3456H 展示版大屏

这是一个用于演示的中文大屏展示页面，包含：

- 历史数据分析
- 热号与冷号查看
- 近期走势统计
- 组合演示
- 可上传 CSV

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

仅用于展示和学习分析，不能保证中奖。
