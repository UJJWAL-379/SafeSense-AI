import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="SafeSense AI | Safety Intelligence", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.main-title {font-size: 2.4rem; font-weight: 800; margin-bottom: 0;}
.subtitle {color: #64748b; margin-top: 0; font-size: 1.05rem;}
.alert-box {padding: 18px; border-radius: 14px; border: 1px solid #fecaca; background: #fff1f2;}
.demo-box {padding: 18px; border-radius: 14px; border: 1px solid #bfdbfe; background: #eff6ff;}
.metric-label {font-size: .82rem; color: #64748b;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ SafeSense AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI/NLP early-warning engine for detecting safety precursors before incidents escalate</div>', unsafe_allow_html=True)

API_URL = st.sidebar.text_input("Backend URL", "http://localhost:8000")

@st.cache_data
def load_demo():
    return json.loads(Path("data/demo_reports.json").read_text(encoding="utf-8"))


def analyze_reports(reports):
    response = requests.post(f"{API_URL}/cluster", json={"reports": reports}, timeout=90)
    response.raise_for_status()
    return response.json()


def analyze_one(text, report_id="LIVE-001"):
    response = requests.post(f"{API_URL}/analyze", json={"report_id": report_id, "text": text}, timeout=90)
    response.raise_for_status()
    return response.json()

reports = load_demo()

with st.sidebar:
    st.header("🎛️ Demo Controls")
    mode = st.radio("Demo mode", ["Live report", "Precursor cluster demo"], index=1)
    st.divider()
    st.caption("For judges: start the backend first, then use the cluster demo to show how separate reports become one emerging risk.")

if mode == "Live report":
    st.subheader("Analyze a new safety report")
    sample = "Worker reported scaffolding wobbling again in Zone B Tower 3. Bolt missing. No injury."
    text = st.text_area("Paste a raw / messy report", sample, height=160)
    report_id = st.text_input("Report ID", "LIVE-001")
    uploaded = st.file_uploader("Or upload TXT / PDF / image", type=["txt", "pdf", "png", "jpg", "jpeg", "webp"])

    if uploaded:
        st.info(f"Uploaded: {uploaded.name}. Use the backend file endpoint to run OCR/extraction, or paste the extracted text above for the live demo.")

    if st.button("🔎 Analyze Report", type="primary", use_container_width=True):
        if not text.strip():
            st.error("Enter a report first.")
        else:
            try:
                with st.spinner("Extracting hazards, causes and risk signals..."):
                    signal = analyze_one(text, report_id)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Risk score", signal["risk_score"])
                c2.metric("Hazard", signal["hazard_type"].replace("_", " ").title())
                c3.metric("Severity", signal["severity"].upper())
                c4.metric("Urgency", signal["urgency"].upper())
                st.success("Report analyzed successfully")
                st.json(signal)
            except Exception as exc:
                st.error(f"Backend unavailable: {exc}")

else:
    st.markdown('<div class="demo-box"><b>Judge demo:</b> These reports come from different channels and look minor individually. SafeSense connects them through hazard + location + repeated precursor language.</div>', unsafe_allow_html=True)

    ids = [r["report_id"] for r in reports]
    default_ids = ids
    selected_ids = st.multiselect("Select reports to analyze", ids, default=default_ids)
    chosen = [r for r in reports if r["report_id"] in selected_ids]

    if st.button("🚨 Detect Emerging Safety Risks", type="primary", use_container_width=True):
        try:
            with st.spinner("Running NLP extraction and cross-report precursor detection..."):
                result = analyze_reports(chosen)
            st.session_state["result"] = result
        except Exception as exc:
            st.error(f"Backend unavailable: {exc}")

    result = st.session_state.get("result")
    if result:
        signals = result.get("signals", [])
        clusters = result.get("clusters", [])
        df = pd.DataFrame(signals)

        st.divider()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Reports analyzed", len(signals))
        c2.metric("High+ signals", sum(s.get("risk_score", 0) >= 55 for s in signals))
        c3.metric("Emerging clusters", len(clusters))
        c4.metric("Highest risk", max((s.get("risk_score", 0) for s in signals), default=0))
        c5.metric("Near-misses", sum(s.get("severity") == "near-miss" for s in signals))

        critical = [c for c in clusters if c.get("risk_level") == "CRITICAL"]
        high = [c for c in clusters if c.get("risk_level") == "HIGH"]
        if critical:
            c = critical[0]
            st.markdown(f'''<div class="alert-box"><h3>🚨 Emerging CRITICAL precursor cluster</h3><b>{c["label"]}</b><br>{c["explanation"]}<br><br><b>Recommended action:</b> {c["recommendation"]}<br><br><b>Linked reports:</b> {", ".join(c["report_ids"])}</div>''', unsafe_allow_html=True)
        elif high:
            c = high[0]
            st.warning(f"Emerging HIGH-risk cluster: {c['label']} — {c['explanation']}")

        st.subheader("📈 Risk by report")
        if not df.empty:
            chart_df = df[["report_id", "risk_score"]].set_index("report_id")
            st.bar_chart(chart_df)

        left, right = st.columns(2)
        with left:
            st.subheader("Hazard distribution")
            if not df.empty:
                st.bar_chart(df["hazard_type"].value_counts())
        with right:
            st.subheader("Severity distribution")
            if not df.empty:
                st.bar_chart(df["severity"].value_counts())

        st.subheader("🧠 Extracted safety signals")
        display_cols = ["report_id", "hazard_type", "location", "asset", "event_type", "severity", "risk_score", "urgency"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], use_container_width=True, hide_index=True)

        st.subheader("🚨 Precursor clusters")
        if clusters:
            for cluster in clusters:
                level = cluster.get("risk_level", "MEDIUM")
                icon = "🔴" if level == "CRITICAL" else "🟠" if level == "HIGH" else "🟡"
                with st.expander(f"{icon} {level} — {cluster['label']} — {cluster['count']} linked reports", expanded=(level == "CRITICAL")):
                    st.write(cluster["explanation"])
                    st.write(f"**Recurring signal:** {cluster.get('recurring_signal', '—')}")
                    st.write(f"**Action:** {cluster.get('recommendation', '—')}")
                    st.write(f"**Reports:** {', '.join(cluster['report_ids'])}")
        else:
            st.info("No repeated precursor cluster detected. Add more reports from the same area/hazard to demonstrate aggregation.")

        st.subheader("🎯 The SIH 'aha' moment")
        st.write("A single report can look like a routine near-miss. SafeSense looks across reports and asks: **Is the same hazard recurring at the same place or asset?** When the pattern crosses a threshold, it becomes an early-warning signal for the safety team.")

st.divider()
st.caption("Prototype for safety decision support. Human safety professionals remain responsible for verification, corrective action and emergency response.")
