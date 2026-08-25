import React, { useMemo, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const demoReports = [
  { report_id:'RPT-001', text:'Date: 12/08/25 Site: Zone B - Scaffolding area. Worker Rajesh noted guard rail missing near tower 3. Potential fall hazard. No injury.' },
  { report_id:'RPT-002', text:'Tower 3 scaffolding loose hai, gir sakta hai - 2nd time this week. Rajesh bola guard rail missing hai. Zone B' },
  { report_id:'RPT-003', text:'INSPECTION LOG #4421 | LOTO not followed during maintenance of conveyor belt C-12. Worker fatigue - 12hr shift. Zone B.' },
  { report_id:'RPT-004', text:'Near miss: chemical spill - HCl drum leaked in storage S1. No PPE kit available. Worker exposed, minor irritation.' },
  { report_id:'RPT-005', text:'Tower 3 scaffolding wobbling again!!! 3rd complaint. Bolt missing. Zone B. If someone falls?? @safety' },
  { report_id:'RPT-006', text:'Electrical panel E-7 open, live wires exposed. Zone A. Night shift. Risk of electrocution.' },
  { report_id:'RPT-007', text:'Fall arrest harness expired - checked date 2023. Still in use at height work in Zone B tower 3. LOTO tag missing also.' },
  { report_id:'RPT-008', text:'fire extingusher missing near welding station WS-2, sparks flying, oil rags nearby. Zone C. Immediate risk.' }
];

function levelClass(level='MEDIUM') { return level.toLowerCase(); }

export default function App() {
  const [mode, setMode] = useState('cluster');
  const [selected, setSelected] = useState(demoReports.map(r => r.report_id));
  const [result, setResult] = useState(null);
  const [text, setText] = useState('Tower 3 scaffolding wobbling again. Bolt missing. Zone B. No injury.');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('Ready for demo');
  const chosen = useMemo(() => demoReports.filter(r => selected.includes(r.report_id)), [selected]);

  async function analyzeCluster() {
    setBusy(true); setStatus('Running NLP extraction and precursor detection…');
    try {
      const r = await fetch(`${API}/cluster`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({reports:chosen}) });
      if (!r.ok) throw new Error(`Backend returned ${r.status}`);
      setResult(await r.json()); setStatus('Analysis complete');
    } catch (e) {
      setStatus('Backend unavailable — use the Streamlit/local demo or configure VITE_API_URL.');
    } finally { setBusy(false); }
  }

  async function analyzeOne() {
    setBusy(true); setStatus('Extracting structured safety signals…');
    try {
      const r = await fetch(`${API}/analyze`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({report_id:'LIVE-WEB-001', text}) });
      if (!r.ok) throw new Error(`Backend returned ${r.status}`);
      setResult({signals:[await r.json()], clusters:[]}); setStatus('Report analyzed');
    } catch (e) { setStatus('Backend unavailable — configure VITE_API_URL for the published frontend.'); }
    finally { setBusy(false); }
  }

  const critical = result?.clusters?.find(c => c.risk_level === 'CRITICAL');
  return <div className="app">
    <header className="topbar">
      <div><div className="brand">🛡️ SafeSense <span>AI</span></div><div className="tagline">Safety intelligence before incidents escalate</div></div>
      <div className="status">● {status}</div>
    </header>

    <main>
      <section className="hero">
        <div><div className="eyebrow">AI / NLP EARLY-WARNING ENGINE</div><h1>Turn messy safety reports into <em>early warnings.</em></h1><p>Connects hazards, locations, assets and repeated precursor language across reports — so small signals don't stay buried.</p></div>
        <div className="hero-card"><div className="big">4</div><div>linked reports</div><strong>Zone B · Tower 3</strong><small>Fall/scaffolding precursor cluster</small></div>
      </section>

      <div className="tabs"><button className={mode==='cluster'?'active':''} onClick={()=>setMode('cluster')}>🚨 Precursor cluster demo</button><button className={mode==='live'?'active':''} onClick={()=>setMode('live')}>🔎 Live report</button></div>

      {mode==='cluster' ? <section className="panel">
        <div className="panel-head"><div><h2>Cross-report intelligence</h2><p>These reports come from different channels and look minor individually.</p></div><button className="primary" disabled={busy || !chosen.length} onClick={analyzeCluster}>{busy?'Analyzing…':'Detect Emerging Safety Risks'}</button></div>
        <div className="selection">{demoReports.map(r => <label key={r.report_id} className="check"><input type="checkbox" checked={selected.includes(r.report_id)} onChange={e=>setSelected(e.target.checked?[...selected,r.report_id]:selected.filter(x=>x!==r.report_id))}/><span>{r.report_id}</span></label>)}</div>
        {critical && <div className="alert"><div className="alert-title">🚨 CRITICAL EMERGING PRECURSOR</div><h2>{critical.label}</h2><p>{critical.explanation}</p><div className="action"><strong>Recommended action</strong><br/>{critical.recommendation}</div><div className="linked">Linked reports: {critical.report_ids.join(' · ')}</div></div>}
      </section> : <section className="panel"><div className="panel-head"><div><h2>Analyze a new safety report</h2><p>Paste a raw, typo-filled or mixed-language report.</p></div><button className="primary" disabled={busy} onClick={analyzeOne}>{busy?'Analyzing…':'Analyze Report'}</button></div><textarea value={text} onChange={e=>setText(e.target.value)} /><div className="hint">Example: “Tower 3 scaffolding loose hai, gir sakta hai… Zone B.”</div></section>}

      {result?.signals?.length > 0 && <section className="panel"><div className="metrics">{[['Reports',result.signals.length],['High+ signals',result.signals.filter(s=>s.risk_score>=55).length],['Clusters',result.clusters?.length||0],['Max risk',Math.max(...result.signals.map(s=>s.risk_score))]].map(([k,v])=><div className="metric" key={k}><small>{k}</small><strong>{v}</strong></div>)}</div><h2>Extracted safety signals</h2><div className="table-wrap"><table><thead><tr><th>Report</th><th>Hazard</th><th>Location</th><th>Severity</th><th>Risk</th><th>Urgency</th></tr></thead><tbody>{result.signals.map(s=><tr key={s.report_id}><td>{s.report_id}</td><td>{s.hazard_type}</td><td>{s.location}</td><td>{s.severity}</td><td><b>{s.risk_score}</b></td><td><span className={`pill ${levelClass(s.urgency)}`}>{s.urgency}</span></td></tr>)}</tbody></table></div></section>}

      <section className="aha"><div className="aha-icon">💡</div><div><strong>The SIH “aha” moment</strong><p>A single report can look like a routine near-miss. SafeSense looks across reports and asks: <b>is the same hazard recurring around the same place or asset?</b> When the pattern crosses a threshold, the team gets an early warning.</p></div></section>
    </main>
    <footer>SafeSense AI · Prototype for safety decision support · Human verification remains mandatory</footer>
  </div>;
}
