// Minimal app.js for 3456H demo: load sample-data.csv, parse CSV, render simple table and SVG line chart, wire buttons
(function () {
  // Helpers
  function qs(sel) { return document.querySelector(sel); }
  function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

  // CSV parser (very small, assumes header and comma-separated)
  function parseCSV(text) {
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#'));
    if (lines.length === 0) return [];
    const header = lines[0].split(/,\s*/).map(h => h.trim());
    return lines.slice(1).map(line => {
      const cols = line.split(/,\s*/);
      const obj = {};
      for (let i=0;i<header.length;i++) obj[header[i]] = cols[i] === undefined ? '' : cols[i];
      return obj;
    }).filter(r => r[header[0]]);
  }

  // Simple numeric conversion
  function toNumber(v){ if (v===undefined || v==='') return NaN; return Number(String(v).replace(/[^0-9.+-]/g,'')); }

  // Render table
  function renderTable(rows) {
    const body = qs('#dataTableBody');
    body.innerHTML = '';
    rows.forEach(r => {
      const tr = document.createElement('tr');
      const date = document.createElement('td'); date.textContent = r.date || r[Object.keys(r)[0]] || '';
      const val = document.createElement('td'); val.textContent = r.value || r.value === 0 ? r.value : toNumber(r[Object.keys(r)[1]] || '');
      const change = document.createElement('td'); change.textContent = '-';
      const status = document.createElement('td'); status.textContent = '-';
      tr.appendChild(date); tr.appendChild(val); tr.appendChild(change); tr.appendChild(status);
      body.appendChild(tr);
    });
  }

  // Compute stats and simple chart points
  function analyze(rows) {
    const nums = rows.map(r => toNumber(r.value)).filter(n => !isNaN(n));
    const total = nums.length;
    const avg = nums.length ? (nums.reduce((a,b)=>a+b,0)/nums.length) : 0;
    const sorted = nums.slice().sort((a,b)=>a-b);
    const median = sorted.length ? sorted[Math.floor(sorted.length/2)] : 0;
    const peak = nums.length ? Math.max(...nums) : 0;
    const volatility = nums.length ? (nums.reduce((a,b)=>a+Math.abs(b-avg),0)/nums.length).toFixed(2) : 0;
    const growthRate = nums.length > 1 ? (((nums[nums.length-1]-nums[0])/Math.abs(nums[0]||1))*100).toFixed(1) : 0;
    return { total, avg: avg.toFixed(2), median, peak, volatility, growthRate };
  }

  function renderStats(s) {
    qs('#totalRows').textContent = s.total;
    qs('#avgValue').textContent = s.avg;
    qs('#medianValue').textContent = s.median;
    qs('#peakValue').textContent = s.peak;
    qs('#volatility').textContent = s.volatility;
    qs('#growthRate').textContent = s.growthRate + '%';
  }

  // Draw simple SVG line chart
  function drawChart(rows) {
    const svg = qs('#trendChart');
    const nums = rows.map(r => toNumber(r.value)).filter(n=>!isNaN(n));
    if (nums.length === 0) { svg.innerHTML = '' ; return; }
    const w = svg.viewBox.baseVal.width || 760;
    const h = svg.viewBox.baseVal.height || 300;
    const max = Math.max(...nums);
    const min = Math.min(...nums);
    const range = max - min || 1;
    const pts = nums.map((v,i)=>{
      const x = (i/(nums.length-1))*(w-40)+20;
      const y = h - 20 - ((v-min)/range)*(h-40);
      return `${x},${y}`;
    });
    svg.innerHTML = `\n      <polyline fill="none" stroke="#7fc9ff" stroke-width="3" points="${pts.join(' ')}" />\n      <rect x="0" y="0" width="100%" height="100%" fill="transparent" />`;
  }

  // Load text file (sample csv)
  function loadText(url, cb) {
    fetch(url).then(r=>r.text()).then(cb).catch(e=>{ console.error(e); });
  }

  // Wire up
  function updateFromCSVText(text) {
    const rows = parseCSV(text);
    if (!rows || rows.length===0) {
      qs('#aiReport').innerHTML = '<p>示例数据为空或格式不被识别。</p>';
      renderTable([]); renderStats({total:0,avg:0,median:0,peak:0,volatility:0,growthRate:0}); drawChart([]);
      return;
    }
    renderTable(rows);
    const s = analyze(rows);
    renderStats(s);
    drawChart(rows);
    qs('#aiReport').innerHTML = '<h4>AI 智能分析（占位）</h4><p>自动生成的简单分析供演示使用。</p>';
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    const demoBtn = qs('#demoBtn');
    const fileInput = qs('#fileInput');

    demoBtn.addEventListener('click', ()=>{
      loadText('sample-data.csv', updateFromCSVText);
    });

    fileInput.addEventListener('change', (ev)=>{
      const f = ev.target.files && ev.target.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = ()=> updateFromCSVText(reader.result);
      reader.readAsText(f);
    });

    // Try to auto-load sample on first open
    loadText('sample-data.csv', updateFromCSVText);
  });
})();
