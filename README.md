const DEFAULT_DATA = [
  { date: '2024-01', value: 120 },
  { date: '2024-02', value: 127 },
  { date: '2024-03', value: 131 },
  { date: '2024-04', value: 142 },
  { date: '2024-05', value: 149 },
  { date: '2024-06', value: 168 },
  { date: '2024-07', value: 174 },
  { date: '2024-08', value: 163 },
  { date: '2024-09', value: 188 },
  { date: '2024-10', value: 204 },
  { date: '2024-11', value: 216 },
  { date: '2024-12', value: 232 }
];

const elements = {
  totalRows: document.getElementById('totalRows'),
  avgValue: document.getElementById('avgValue'),
  medianValue: document.getElementById('medianValue'),
  growthRate: document.getElementById('growthRate'),
  peakValue: document.getElementById('peakValue'),
  volatility: document.getElementById('volatility'),
  aiReport: document.getElementById('aiReport'),
  dataTableBody: document.getElementById('dataTableBody'),
  demoBtn: document.getElementById('demoBtn'),
  fileInput: document.getElementById('fileInput'),
  copyBtn: document.getElementById('copyBtn')
};

function toFixedNumber(value, digits = 1) {
  return Number.isFinite(value) ? Number(value).toFixed(digits) : '0.0';
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

function parseCSV(text) {
  const rawLines = (text || '').trim();
  if (!rawLines) return [];

  const delimiter = rawLines.includes(';') && !rawLines.includes(',') ? ';' : ',';
  const lines = rawLines.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) return [];

  const headers = lines[0].split(delimiter).map((cell) => cell.trim().replace(/^"|"$/g, '').toLowerCase());
  const dateIndex = headers.findIndex((header) => ['date', 'time', 'day', 'month', '日期', '时间', '月份'].includes(header));
  const valueIndex = headers.findIndex((header) => ['value', 'num', 'count', 'amount', 'data', '值', '数量', '金额', '数值'].includes(header));

  const records = [];

  for (let i = 1; i < lines.length; i += 1) {
    const values = lines[i].split(delimiter).map((cell) => cell.trim().replace(/^"|"$/g, ''));
    if (!values.length) continue;

    const date = values[dateIndex] || `第${i}条`;
    const numeric = Number(values[valueIndex] || 0);
    if (!Number.isFinite(numeric)) continue;

    records.push({ date, value: numeric });
  }

  return records;
}

function computeStats(data) {
  const values = data.map((item) => item.value);
  const total = data.length;
  const avg = total ? values.reduce((sum, num) => sum + num, 0) / total : 0;
  const first = data[0]?.value ?? 0;
  const last = data[data.length - 1]?.value ?? 0;
  const growth = first === 0 ? 0 : ((last - first) / first) * 100;
  const peak = Math.max(...values, 0);
  const peakItem = data.reduce((maxItem, item) => {
    if (item.value > maxItem.value) return item;
    return maxItem;
  }, data[0] || { date: 'N/A', value: 0 });

  const volatility = data.length > 1
    ? data.slice(1).reduce((acc, item, idx) => acc + Math.abs(item.value - data[idx].value), 0) / (data.length - 1)
    : 0;

  return {
    total,
    avg,
    median: median(values),
    growth,
    peak,
    peakItem,
    volatility,
    first,
    last
  };
}

function generateAiReport(data, stats) {
  const trendText = stats.last >= stats.first ? '整体呈上升趋势' : '整体呈下降趋势';
  const phase = stats.growth > 10 ? '增长较强' : stats.growth > 0 ? '稳步提升' : stats.growth > -10 ? '略有回调' : '波动较大';
  const riskText = stats.volatility > 20 ? '波动较大，建议重点关注异常点' : '波动相对稳定，趋势较清晰';

  const keyInsights = [
    `当前数据共 ${stats.total} 条记录，平均值为 ${toFixedNumber(stats.avg)}，中位数为 ${toFixedNumber(stats.median)}。`,
    `${trendText}，从 ${toFixedNumber(stats.first)} 变化到 ${toFixedNumber(stats.last)}，累计增长约 ${toFixedNumber(stats.growth)}%。`,
    `峰值出现在 ${stats.peakItem.date}，最高达到 ${toFixedNumber(stats.peak)}，整体表现属于 ${phase}。`,
    `近阶段波动水平约 ${toFixedNumber(stats.volatility)}，${riskText}。`
  ];

  const actions = [
    '继续观察最近 2-3 个周期的变化趋势，确认是否持续放大。',
    '如果增长率持续高于历史均值，可重点放大增长区间并复盘成功原因。',
    '如果波动明显放大，建议关注极值与拐点，及时排查异常数据。',
    '定期更新数据并与均值、峰值对比，可更准确地判断是否进入新周期。'
  ];

  return { keyInsights, actions };
}

function renderMetrics(stats) {
  elements.totalRows.textContent = String(stats.total);
  elements.avgValue.textContent = toFixedNumber(stats.avg);
  elements.medianValue.textContent = toFixedNumber(stats.median);
  elements.growthRate.textContent = `${stats.growth >= 0 ? '+' : ''}${toFixedNumber(stats.growth)}%`;
  elements.peakValue.textContent = toFixedNumber(stats.peak);
  elements.volatility.textContent = toFixedNumber(stats.volatility);
}

function renderChart(data) {
  const svg = document.getElementById('trendChart');
  if (!data.length) {
    svg.innerHTML = '';
    return;
  }

  const width = 760;
  const height = 300;
  const padding = { top: 20, right: 18, bottom: 30, left: 42 };
  const values = data.map((item) => item.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = maxValue - minValue || 1;
  const xStep = (width - padding.left - padding.right) / Math.max(data.length - 1, 1);

  const points = data.map((item, index) => {
    const x = padding.left + index * xStep;
    const y = height - padding.bottom - ((item.value - minValue) / range) * (height - padding.top - padding.bottom);
    return { x, y, ...item };
  });

  const linePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - padding.bottom} L ${points[0].x} ${height - padding.bottom} Z`;

  const grid = Array.from({ length: 5 }, (_, i) => {
    const y = padding.top + ((height - padding.top - padding.bottom) / 4) * i;
    return `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(140,179,255,0.18)" stroke-width="1" />`;
  }).join('');

  const labels = points
    .filter((_, index) => index % Math.max(1, Math.ceil(points.length / 5)) === 0 || index === points.length - 1)
    .map((point) => `<text x="${point.x}" y="${height - 8}" text-anchor="middle" fill="#a8c0da" font-size="11">${point.date}</text>`)
    .join('');

  const circles = points.map((point) => `
    <circle cx="${point.x}" cy="${point.y}" r="4" fill="#7fc8ff" stroke="#061522" stroke-width="2" />
    <title>${point.date}: ${point.value}</title>
  `).join('');

  svg.innerHTML = `
    <defs>
      <linearGradient id="areaStroke" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="rgba(127,200,255,0.55)" />
        <stop offset="100%" stop-color="rgba(127,200,255,0.02)" />
      </linearGradient>
    </defs>
    ${grid}
    <path d="${areaPath}" fill="url(#areaStroke)" opacity="0.9"></path>
    <path d="${linePath}" fill="none" stroke="#7fc8ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
    ${circles}
    ${labels}
  `;
}

function renderTable(data) {
  elements.dataTableBody.innerHTML = '';

  data.forEach((item, index) => {
    const previousValue = data[index - 1]?.value ?? item.value;
    const delta = item.value - previousValue;
    const deltaText = `${delta >= 0 ? '+' : ''}${toFixedNumber(delta)}`;
    const statusText = delta > 0 ? '上涨' : delta < 0 ? '下跌' : '持平';
    const statusClass = delta > 0 ? 'status-up' : delta < 0 ? 'status-down' : 'status-flat';

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.date}</td>
      <td>${toFixedNumber(item.value)}</td>
      <td>${deltaText}</td>
      <td><span class="badge ${statusClass}">${statusText}</span></td>
    `;
    elements.dataTableBody.appendChild(row);
  });
}

function renderAi(data, stats) {
  const report = generateAiReport(data, stats);

  const insightHtml = report.keyInsights.map((entry) => `<li>${entry}</li>`).join('');
  const actionHtml = report.actions.map((entry) => `<li>${entry}</li>`).join('');

  elements.aiReport.innerHTML = `
    <h4>核心结论</h4>
    <ul>${insightHtml}</ul>
    <h4>建议动作</h4>
    <ul>${actionHtml}</ul>
  `;
}

function setData(data) {
  if (!data.length) {
    elements.aiReport.innerHTML = '<p>未识别到有效数据，请上传包含日期和数值列的 CSV。</p>';
    return;
  }

  const sorted = [...data].sort((a, b) => {
    if (a.date < b.date) return -1;
    if (a.date > b.date) return 1;
    return 0;
  });

  const stats = computeStats(sorted);
  renderMetrics(stats);
  renderChart(sorted);
  renderTable(sorted);
  renderAi(sorted, stats);
}

function loadDemoData() {
  setData(DEFAULT_DATA);
}

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    const content = String(reader.result || '');
    const parsed = parseCSV(content);
    if (!parsed.length) {
      elements.aiReport.innerHTML = '<p>CSV 解析失败。请检查列名是否包含日期和数值字段，例如：date,value。</p>';
      return;
    }
    setData(parsed);
  };
  reader.readAsText(file);
}

async function copyReport() {
  const text = elements.aiReport.innerText.trim();
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    elements.copyBtn.textContent = '已复制';
    setTimeout(() => {
      elements.copyBtn.textContent = '复制分析报告';
    }, 1200);
  } catch (error) {
    elements.copyBtn.textContent = '复制失败';
    setTimeout(() => {
      elements.copyBtn.textContent = '复制分析报告';
    }, 1200);
  }
}

elements.demoBtn.addEventListener('click', loadDemoData);
elements.fileInput.addEventListener('change', handleFileUpload);
elements.copyBtn.addEventListener('click', copyReport);

loadDemoData();
