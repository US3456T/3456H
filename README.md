const DEFAULT_DATA = [
  { date: '2024-01', value: 120 },
  { date: '2024-02', value: 128 },
  { date: '2024-03', value: 134 },
  { date: '2024-04', value: 140 },
  { date: '2024-05', value: 149 },
  { date: '2024-06', value: 165 },
  { date: '2024-07', value: 176 },
  { date: '2024-08', value: 170 },
  { date: '2024-09', value: 186 },
  { date: '2024-10', value: 201 },
  { date: '2024-11', value: 214 },
  { date: '2024-12', value: 228 }
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

function fmt(value, digits = 1) {
  return Number.isFinite(value) ? Number(value).toFixed(digits) : '0.0';
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2;
  }
  return sorted[middle];
}

function parseCSV(text) {
  const raw = (text || '').trim();
  if (!raw) return [];

  const delimiter = raw.includes(';') && !raw.includes(',') ? ';' : ',';
  const lines = raw.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) return [];

  const headers = lines[0].split(delimiter).map((cell) => cell.trim().replace(/^"|"$/g, '').toLowerCase());
  const dateIndex = headers.findIndex((header) => ['date', 'time', 'day', 'month', '日期', '时间', '月份'].includes(header));
  const valueIndex = headers.findIndex((header) => ['value', 'num', 'count', 'amount', 'data', '值', '数量', '金额', '数值'].includes(header));

  const records = [];
  for (let i = 1; i < lines.length; i += 1) {
    const cells = lines[i].split(delimiter).map((cell) => cell.trim().replace(/^"|"$/g, ''));
    if (!cells.length) continue;
    const date = cells[dateIndex] || `第${i}条`;
    const numeric = Number(cells[valueIndex] || 0);
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
  const last = data[total - 1]?.value ?? 0;
  const growth = first === 0 ? 0 : ((last - first) / first) * 100;
  const peak = Math.max(...values, 0);
  const peakItem = data.reduce((current, item) => (item.value > current.value ? item : current), data[0] || { date: 'N/A', value: 0 });
  const volatility = total > 1
    ? data.slice(1).reduce((acc, item, index) => acc + Math.abs(item.value - data[index].value), 0) / (total - 1)
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
  const phase = stats.growth > 12 ? '增长较强' : stats.growth > 0 ? '稳步提升' : stats.growth > -10 ? '略有回调' : '短期波动明显';
  const riskText = stats.volatility > 18 ? '波动偏大，建议重点关注异常点和拐点' : '波动相对稳定，趋势判断更可靠';

  const keyInsights = [
    `当前数据共 ${stats.total} 条记录，平均值为 ${fmt(stats.avg)}，中位数为 ${fmt(stats.median)}。`,
    `${trendText}，从 ${fmt(stats.first)} 变化到 ${fmt(stats.last)}，累计增长约 ${fmt(stats.growth)}%。`,
    `峰值出现在 ${stats.peakItem.date}，最高达到 ${fmt(stats.peak)}，整体结构属于 ${phase}。`,
    `近阶段波动水平约 ${fmt(stats.volatility)}，${riskText}。`
  ];

  const actions = [
    '继续观察最近 2-3 个周期的变化趋势，确认是否持续放大。',
    '如果增长率持续高于历史均值，可重点复盘成功原因并放大资源投入。',
    '如果波动长期偏大，建议重点关注极值、拐点和异常数据，及时修正判断。',
    '定期更新并和历史均值、峰值做对比，利用数据趋势做更稳妥的决策。'
  ];

  return { keyInsights, actions };
}

function renderMetrics(stats) {
  elements.totalRows.textContent = String(stats.total);
  elements.avgValue.textContent = fmt(stats.avg);
  elements.medianValue.textContent = fmt(stats.median);
  elements.growthRate.textContent = `${stats.growth >= 0 ? '+' : ''}${fmt(stats.growth)}%`;
  elements.peakValue.textContent = fmt(stats.peak);
  elements.volatility.textContent = fmt(stats.volatility);
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
    .map((point) => `<text x="${point.x}" y="${height - 8}" text-anchor="middle" fill="#a9c0d9" font-size="11">${point.date}</text>`)
    .join('');

  const circles = points.map((point) => `
    <circle cx="${point.x}" cy="${point.y}" r="4" fill="#7fc9ff" stroke="#061522" stroke-width="2" />
    <title>${point.date}: ${point.value}</title>
  `).join('');

  svg.innerHTML = `
    <defs>
      <linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="rgba(127,200,255,0.55)" />
        <stop offset="100%" stop-color="rgba(127,200,255,0.02)" />
      </linearGradient>
    </defs>
    ${grid}
    <path d="${areaPath}" fill="url(#areaFill)" opacity="0.9"></path>
    <path d="${linePath}" fill="none" stroke="#7fc9ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
    ${circles}
    ${labels}
  `;
}

function renderTable(data) {
  elements.dataTableBody.innerHTML = '';

  data.forEach((item, index) => {
    const previousValue = data[index - 1]?.value ?? item.value;
    const delta = item.value - previousValue;
    const deltaText = `${delta >= 0 ? '+' : ''}${fmt(delta)}`;
    const statusText = delta > 0 ? '上涨' : delta < 0 ? '下跌' : '持平';
    const statusClass = delta > 0 ? 'status-up' : delta < 0 ? 'status-down' : 'status-flat';

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.date}</td>
      <td>${fmt(item.value)}</td>
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

function applyDataset(data) {
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
  applyDataset(DEFAULT_DATA);
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
    applyDataset(parsed);
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
