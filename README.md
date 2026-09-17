# 3456H 黑色大屏版

当前界面采用深色数据中心风格，提供：

- 蓝黑色大屏布局
- 核心运行指标卡片
- 号码频率雷达
- 热号和冷号监测
- 近期走势柱状图
- AI 风格智能关注清单
- CSV 历史数据上传
- 随机演示组合

运行：

```powershell
docker compose up --build
```

然后打开：`http://localhost:8501`

本地运行：

```powershell
cd app
python -m pip install -r requirements.txt
streamlit run app.py
```

重要：此工具仅用于历史统计和界面演示，不保证中奖，也不构成投注建议。
