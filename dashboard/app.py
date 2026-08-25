import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="SafeSense AI", page_icon="🛡️", layout="wide")
st.title("🛡️ SafeSense AI")
st.caption("AI/NLP early-warning engine for safety precursors")

API_URL = st.sidebar.text_input("Backend URL", "http://localhost:8000")

@st.cache_data
def load_demo():
    return json.loads(Path("data/demo_reports.json").read_text(encoding="utf-8"))

reports = load_demo()

with st.sidebar:
    st.subheader("Demo controls")
    use_demo = st.checkbox("Load demo reports", True)

if use_demo:
    selected = st.multiselect("Reports", [r["report_id"] for r in reports], default=[r["report_id"] for r in reports])
    chosen = [r for r in reports if r["report_id"] in selected]
else:
    chosen = []

if st.button("Analyze selected reports", type="primary"):
    with st.spinner("Analyzing reports and detecting precursor clusters..."):
        try:
            response = requests.post(f"{API_URL}/cluster", json={"reports": chosen}, timeout=90)
            response.raise_for_status()
            result = response.json()
            st.session_state["result"] = result
        except Exception as exc:
            st.error(f"Backend unavailable: {exc}")

result = st.session_state.get("result")
if result:
    signals = result["signals"]
    clusters = result["clusters"]
    df = pd.DataFrame(signals)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reports analyzed", len(signals))
    c2.metric("High+ risk", sum(s["risk_score"] >= 55 for s in signals))
    c3.metric("Emerging clusters", len(clusters))
    c4.metric("Max risk", max((s["risk_score"] for s in signals), default=0))

    st.subheader("Risk by report")
    st.bar_chart(df.set_index("report_id")["risk_score"])

    st.subheader("Extracted safety signals")
    st.dataframe(df[["report_id", "hazard_type", "location", "event_type", "severity", "risk_score", "urgency"]], use_container_width=True)

    st.subheader("🚨 Emerging precursor clusters")
    if clusters:
        for cluster in clusters:
            st.warning(f"**{cluster['label']}** — {cluster['count']} reports — {cluster['risk_level'].upper()}\n\n{cluster['explanation']}")
    else:
        st.info("No repeated precursor cluster detected in the selected reports.")

    st.subheader("Why this matters")
    st.write("The differentiator is cross-report intelligence: individually minor observations can become an actionable warning when the same hazard repeatedly appears in the same area.")
else:
    st.info("Select the demo reports and click **Analyze selected reports** to see the early-warning story.")
