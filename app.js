// Advanced app.js for lottery analysis (feature/advanced-analyzer)
// Features:
// - Flexible CSV parser (supports `date,value` and `date,n1,n2,...` or `numbers` column)
// - Frequency (hot/cold) calculation
// - Pattern detection: odd/even ratio, sum, span
// - Candidate generation with constraints (exclude numbers, sum range, odd/even ratio)
// - Export candidates as CSV

(function () {
  function qs(s){return document.querySelector(s)}
  function qsa(s){return Array.from(document.querySelectorAll(s))}

  // --- CSV parsing ---
  function parseCSV(text){
    const lines = text.split(/\r?\n/).map(l=>l.trim()).filter(l=>l && !l.startsWith('#'));
    if(lines.length===0) return [];
    const header = lines[0].split(/,\s*/).map(h=>h.trim());
    const rows = [];
    for(let i=1;i<lines.length;i++){
      const cols = lines[i].split(/,\s*/);
      if(cols.length===1) continue;
      const obj = {};
      for(let j=0;j<header.length;j++) obj[header[j]] = cols[j]===undefined? '': cols[j];
      // Normalize numbers array
      let numbers = [];
      // If there are many numeric columns besides first, treat as numbers
      const numericCols = header.slice(1).filter((h,idx)=> !isNaN(Number(obj[h])));
      if(numericCols.length >= 1){
        numbers = header.slice(1).map(h=>obj[h]).filter(x=>x!=='').map(x=>Number(String(x).replace(/[^0-9]/g,''))).filter(n=>!isNaN(n));
      } else if(obj.numbers){
        // parse numbers field like "1 2 3 4 5 6" or "1,2,3,4,5,6"
        numbers = String(obj.numbers).split(/[\s,;|]+/).map(x=>Number(x)).filter(n=>!isNaN(n));
      } else if(obj.value && !isNaN(Number(obj.value))){
        // fallback: single numeric value
        numbers = [Number(obj.value)];
      }
      obj._numbers = numbers;
      rows.push(obj);
    }
    return rows;
  }

  // --- Utilities ---
  function toNumber(v){ if (v===undefined || v==='') return NaN; return Number(String(v).replace(/[^0-9.+-]/g,'')); }
  function range(a,b){ const r=[]; for(let i=a;i<=b;i++) r.push(i); return r }
  function shuffle(arr){ const a = arr.slice(); for(let i=a.length-1;i>0;i--){ const j = Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]] } return a }

  // --- Analysis ---
  function computeFrequency(rows){
    const freq = {};
    let maxNum = 0;
    rows.forEach(r => { (r._numbers||[]).forEach(n=>{ if(!n) return; freq[n]=(freq[n]||0)+1; if(n>maxNum) maxNum=n; }) });
    return { freq, maxNum };
  }

  function computePatterns(rows){
    const stats = { totalRows: rows.length };
    const sums = rows.map(r=> (r._numbers && r._numbers.length)? r._numbers.reduce((a,b)=>a+b,0): toNumber(r.value) ).filter(x=>!isNaN(x));
    if(sums.length){
      const avg = sums.reduce((a,b)=>a+b,0)/sums.length;
      const median = sums.slice().sort((a,b)=>a-b)[Math.floor(sums.length/2)] || 0;
      stats.avg = Number(avg.toFixed(2));
      stats.median = median;
      stats.peak = Math.max(...sums);
      stats.volatility = Number((sums.reduce((a,b)=>a+Math.abs(b-avg),0)/sums.length).toFixed(2));
      stats.growthRate = sums.length>1? Number((((sums[sums.length-1]-sums[0])/(Math.abs(sums[0])||1))*100).toFixed(1)) : 0;
    }
    // odd/even distribution overall
    let odd=0, even=0, count=0;
    rows.forEach(r=>{ (r._numbers||[]).forEach(n=>{ if(!n) return; if(n%2===0) even++; else odd++; count++; }) });
    stats.odd = odd; stats.even = even; stats.oddEvenRatio = count? (odd+":"+even): "0:0";
    return stats;
  }

  // --- Candidate generation ---
  function generateCandidates(opts, rows){
    // opts: candidateSize, candidateCount, excludeNumbers (array), sumRange [min,max], oddEven (e.g. "3:3")
    const freqInfo = computeFrequency(rows);
    const maxNum = Math.max( (freqInfo.maxNum||0), 49 ); // fallback to 49
    const pool = range(1, maxNum).filter(n => !opts.excludeNumbers.includes(n));
    const candidates = [];
    let attempts = 0;
    while(candidates.length < opts.candidateCount && attempts < opts.candidateCount * 500){
      attempts++;
      const cand = shuffle(pool).slice(0, opts.candidateSize).sort((a,b)=>a-b);
      const sum = cand.reduce((a,b)=>a+b,0);
      if(opts.sumRange){ if(sum < opts.sumRange[0] || sum > opts.sumRange[1]) continue; }
      if(opts.oddEven){
        const [oddReq, evenReq] = opts.oddEven.split(':').map(x=>Number(x));
        const odd = cand.filter(n=>n%2===1).length;
        const even = cand.length - odd;
        if((!isNaN(oddReq) && odd !== oddReq) || (!isNaN(evenReq) && even !== evenReq)) continue;
      }
      // dedupe
      const key = cand.join(',');
      if(!candidates.some(c=>c.join(',')===key)) candidates.push(cand);
    }
    return candidates;
  }

  // --- Export CSV ---
  function exportCandidatesCSV(candidates){
    const rows = candidates.map(c=>c.join(','));
    const csv = 'numbers\n' + rows.join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'candidates.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  // --- Rendering ---
  function renderTable(rows){
    const body = qs('#dataTableBody'); body.innerHTML = '';
    rows.forEach(r=>{
      const tr = document.createElement('tr');
      const date = document.createElement('td'); date.textContent = r.date || r.Date || '';
      const val = document.createElement('td'); val.textContent = (r._numbers && r._numbers.length)? r._numbers.join(' ') : (r.value||'');
      const change = document.createElement('td'); change.textContent = '-';
      const status = document.createElement('td'); status.textContent = '-';
      tr.appendChild(date); tr.appendChild(val); tr.appendChild(change); tr.appendChild(status); body.appendChild(tr);
    });
  }

  function renderStats(stats){
    qs('#totalRows').textContent = stats.totalRows || 0;
    if(stats.avg!==undefined) qs('#avgValue').textContent = stats.avg;
    if(stats.median!==undefined) qs('#medianValue').textContent = stats.median;
    if(stats.peak!==undefined) qs('#peakValue').textContent = stats.peak;
    if(stats.volatility!==undefined) qs('#volatility').textContent = stats.volatility;
    if(stats.growthRate!==undefined) qs('#growthRate').textContent = stats.growthRate + '%';
    qs('#aiReport').querySelector('p') && (qs('#aiReport').querySelector('p').textContent='');
  }

  function drawChart(rows){
    const svg = qs('#trendChart');
    const nums = rows.map(r=> (r._numbers && r._numbers.length)? r._numbers.reduce((a,b)=>a+b,0): toNumber(r.value)).filter(n=>!isNaN(n));
    if(nums.length===0){ svg.innerHTML=''; return; }
    const w = svg.viewBox.baseVal.width || 760; const h = svg.viewBox.baseVal.height || 300;
    const max = Math.max(...nums); const min = Math.min(...nums); const rangeV = max-min||1;
    const pts = nums.map((v,i)=>{ const x = (i/(nums.length-1))*(w-40)+20; const y = h - 20 - ((v-min)/rangeV)*(h-40); return `${x},${y}` });
    svg.innerHTML = `<polyline fill="none" stroke="#7fc9ff" stroke-width="3" points="${pts.join(' ')}" />`;
  }

  // --- Glue ---
  function updateFromCSVText(text){
    const rows = parseCSV(text);
    renderTable(rows);
    const stats = computePatterns(rows);
    renderStats(stats);
    drawChart(rows);
    // frequency
    const f = computeFrequency(rows);
    // create a simple hot list
    const entries = Object.keys(f.freq).map(k=>({n:Number(k),c:f.freq[k]})).sort((a,b)=>b.c-a.c).slice(0,10);
    const hotHtml = ['<h4>热门号码（前 10）</h4>','<div>'+ entries.map(e=>`${e.n}(${e.c})`).join(', ') +'</div>'].join('');
    qs('#candidatesArea').innerHTML = hotHtml + '<div style="margin-top:8px;color:var(--muted);">生成候选请配置右侧参数并点击“生成候选组合”。</div>';
    // store rows for generation
    window.__LA_ROWS = rows;
  }

  // --- Event wiring ---
  document.addEventListener('DOMContentLoaded', ()=>{
    const demoBtn = qs('#demoBtn'); const fileInput = qs('#fileInput');
    const genBtn = qs('#genCandidatesBtn'); const exportBtn = qs('#exportCandidatesBtn');

    demoBtn.addEventListener('click', ()=>{ fetch('sample-data.csv').then(r=>r.text()).then(updateFromCSVText).catch(()=>alert('示例加载失败，请启用 HTTP 服务或手动上传 sample-data.csv')) });

    fileInput.addEventListener('change', ev=>{ const f = ev.target.files && ev.target.files[0]; if(!f) return; const reader = new FileReader(); reader.onload = ()=> updateFromCSVText(reader.result); reader.readAsText(f); });

    genBtn.addEventListener('click', ()=>{
      const rows = window.__LA_ROWS || [];
      const candidateSize = Number(qs('#candidateSize').value) || 6;
      const candidateCount = Number(qs('#candidateCount').value) || 10;
      const excludeNumbers = qs('#excludeNumbers').value.split(/[\s,;]+/).map(x=>Number(x)).filter(n=>!isNaN(n));
      const sumRangeStr = qs('#sumRange').value.trim();
      const sumRange = sumRangeStr && sumRangeStr.includes('-')? sumRangeStr.split('-').map(x=>Number(x.trim())) : null;
      const opts = { candidateSize, candidateCount, excludeNumbers, sumRange };
      const oddEvenText = ''; // could extend parsing
      opts.oddEven = null;
      const candidates = generateCandidates(opts, rows);
      // render candidates
      const area = qs('#candidatesArea');
      if(candidates.length===0) area.innerHTML += '<div style="color:#ffbaba;margin-top:8px">未能生成满足约束的候选，请放宽限制或增加尝试次数。</div>';
      else{
        const html = ['<h4>候选组合（共 '+candidates.length+'）</h4>','<ol>'+ candidates.map(c=>'<li>'+c.join(', ')+'</li>').join('\n') +'</ol>'].join('');
        area.innerHTML = html + '<div style="margin-top:8px;"><button id="_export_inline" class="btn btn-light">导出当前候选为 CSV</button></div>';
        qs('#_export_inline').addEventListener('click', ()=> exportCandidatesCSV(candidates));
        // store for export button
        window.__LA_CANDIDATES = candidates;
      }
    });

    exportBtn.addEventListener('click', ()=>{ const c = window.__LA_CANDIDATES || []; if(c.length===0){ alert('当前没有候选，请先生成'); return } exportCandidatesCSV(c); });

    // auto load sample if available
    fetch('sample-data.csv').then(r=>r.text()).then(updateFromCSVText).catch(()=>{/* ignore */});
  });
})();
