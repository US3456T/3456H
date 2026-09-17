# 3456H 彩票数据分析演示

这是一个适合初学者使用的中文演示仓库。它提供一个可以直接打开的网页，用于读取 CSV 历史数据、统计号码出现次数、查看最近记录，并生成“随机演示组合”。

> 重要：彩票开奖结果具有随机性，统计和机器学习不能保证预测中奖，也不应作为投注依据。

## 最简单的运行方法（Windows）

1. 安装 Docker Desktop 并打开它。
2. 在本仓库根目录打开 PowerShell。
3. 执行：

```powershell
docker compose up --build
```

4. 浏览器打开：`http://localhost:8501`
5. 停止运行：在 PowerShell 按 `Ctrl+C`，或执行：

```powershell
docker compose down
```

## 不安装 Docker 的方法

进入 `app` 文件夹，安装 Python 3.10 或更高版本，然后执行：

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

浏览器打开：`http://localhost:8501`

## 文件说明

- `docker-compose.yml`：一键启动网页。
- `app/app.py`：中文网页和统计逻辑。
- `app/data/demo.csv`：演示历史数据，可替换为你自己的 CSV。
- `projects/`：五个开源项目的说明和来源记录；本仓库不声称复制或验证这些项目的全部代码。

## 数据格式

CSV 至少需要一列号码。示例使用：`date,n1,n2,n3,n4,n5,n6`。网页也会尝试识别 `ball1`、`ball2` 等列。
