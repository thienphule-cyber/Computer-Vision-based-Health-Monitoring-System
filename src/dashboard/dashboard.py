import time

import streamlit as st
import pandas as pd

from config import settings
from storage.storage import get_latest_records, get_record_count


st.set_page_config(
    page_title="Biomedical Data Analytics Dashboard",
    page_icon="🩺",
    layout="wide",
)


def load_data():
    latest_records = get_latest_records(limit=settings.DASHBOARD_HISTORY_POINTS)
    return latest_records


def render_current_values(latest: dict):
    col1, col2, col3 = st.columns(3)

    col1.metric("Heart Rate", f"{latest.get('heartRate', '--')} BPM")

    respiratory_rate = latest.get("respiratoryRate")
    col2.metric("Respiratory Rate", f"{respiratory_rate} breaths/min" if respiratory_rate is not None else "N/A")

    status = latest.get("status", "Unknown")
    status_color = _get_status_color(status)
    col3.markdown(
        f"<div style='padding:10px; border-radius:8px; background-color:{status_color}; "
        f"text-align:center; color:white; font-weight:bold;'>{status}</div>",
        unsafe_allow_html=True
    )

    st.write("")
    col4, col5 = st.columns(2)

    health_score = latest.get("health_score", None)
    if health_score is not None:
        col4.metric("Health Score", f"{health_score}/100")
    else:
        col4.metric("Health Score", "N/A")

    risk_level = latest.get("risk_level", "N/A")
    risk_color = _get_risk_color(risk_level)
    col5.markdown(
        f"**Risk Level:** <span style='color:{risk_color}; font-weight:bold;'>{risk_level}</span>",
        unsafe_allow_html=True
    )


def _get_status_color(status: str) -> str:
    mapping = {
        "NORMAL": "#27AE60",
        "ELEVATED HEART RATE": "#F1C40F",
        "CHECK REQUIRED": "#E67E22",
        "HIGH HEART RATE": "#C0392B",
    }
    return mapping.get(status, "#7F8C8D")


def _get_risk_color(risk_level: str) -> str:
    mapping = {
        "Normal": "#27AE60",
        "Elevated Heart Rate": "#F1C40F",
        "Abnormal Trend": "#E67E22",
        "High Risk": "#C0392B",
    }
    return mapping.get(risk_level, "#7F8C8D")


def render_realtime_charts(df: pd.DataFrame):
    st.subheader("Real-Time Trends")

    if df.empty:
        st.info("No data available yet. Waiting for readings...")
        return

    df_chart = df.copy()
    df_chart["received_at"] = pd.to_datetime(df_chart["received_at"])
    df_chart = df_chart.set_index("received_at")

    has_respiratory = "respiratoryRate" in df_chart.columns and df_chart["respiratoryRate"].notna().any()

    if has_respiratory:
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Heart Rate (BPM)")
            st.line_chart(df_chart["heartRate"])
        with col2:
            st.caption("Respiratory Rate (breaths/min)")
            st.line_chart(df_chart["respiratoryRate"])
    else:
        st.caption("Heart Rate (BPM)")
        st.line_chart(df_chart["heartRate"])


def render_history_table(df: pd.DataFrame):
    st.subheader("Recent History")
    if df.empty:
        st.info("No historical data available.")
        return

    display_columns = ["received_at", "heartRate", "respiratoryRate", "status", "health_score", "risk_level"]
    available_columns = [c for c in display_columns if c in df.columns]
    st.dataframe(
        df[available_columns].sort_values("received_at", ascending=False),
        use_container_width=True,
        height=300
    )


def render_sidebar():
    st.sidebar.title("System Info")
    total_records = get_record_count()
    st.sidebar.metric("Total Records Stored", total_records)
    st.sidebar.markdown(f"**MQTT Broker:** `{settings.MQTT_BROKER}`")
    st.sidebar.markdown(f"**MQTT Subscribe Topic:** `{settings.MQTT_TOPIC_SUBSCRIBE}`")
    st.sidebar.markdown(f"**MQTT Publish Topic:** `{settings.MQTT_TOPIC_PUBLISH}`")
    st.sidebar.markdown(f"**Refresh Interval:** {settings.DASHBOARD_REFRESH_INTERVAL}s")
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "This dashboard provides technical health-related analytics for "
        "educational/demonstration purposes and does not constitute medical diagnosis."
    )


def main():
    st.title("🩺 Biomedical Data Analytics Dashboard")
    st.caption("Computer Vision-Based Health Monitoring System — Analytics Layer")

    render_sidebar()

    records = load_data()

    if not records:
        st.warning("No data received yet. Make sure the CV Layer and main.py are running.")
        time.sleep(settings.DASHBOARD_REFRESH_INTERVAL)
        st.rerun()
        return

    df = pd.DataFrame(records)
    latest = records[-1]

    render_current_values(latest)
    st.markdown("---")
    render_realtime_charts(df)
    st.markdown("---")
    render_history_table(df)

    time.sleep(settings.DASHBOARD_REFRESH_INTERVAL)
    st.rerun()


if __name__ == "__main__":
    main()