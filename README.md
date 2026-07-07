# Biomedical Analytics Layer

The **Analytics Layer** of the Intelligent Contactless Health Monitoring System with Voice-Controlled Embedded Interface. This service ingests heart rate readings from the Computer Vision Layer via MQTT, validates them, stores them, performs statistical and trend analysis, classifies health status, and distributes results to both the Arduino Embedded Notification Controller and any other subscriber.

> **Disclaimer:** This system provides technical, rule-based health analytics for educational and demonstration purposes only. It does not constitute medical diagnosis.

---

## Role in the Overall System
Computer Vision Layer (separate project)
│  MQTT publish -> topic: vitals/raw
│  {"heartRate": 72, "confidence": 91}
▼
Biomedical Analytics Layer  (this repository)
MQTT Subscribe → Validate → Store → Analyze → Classify → Alert
│  MQTT publish -> topic: vitals/result
│  {"heartRate": 72, "status": "NORMAL", "confidence": 91}
├──────────────────────┬─────────────────────────┐
▼                      ▼                          ▼
Arduino (LED, LCD     Mobile / MQTT Dashboard    Local Streamlit Dashboard
notification)          (any subscriber app)        (reads from SQLite)

This layer performs the "understanding" and "communication" stages of the pipeline. It has no knowledge of how the heart rate was obtained (camera, voice activation, etc.) or how the Arduino was triggered — it only consumes `vitals/raw` and produces `vitals/result`.

---

## Features

- **MQTT ingestion** — subscribes to `vitals/raw`, published by the Computer Vision Layer
- **Data validation** — checks required fields, data types, and value ranges (`heartRate`, optional `confidence`, `respiratoryRate`)
- **Persistent storage** — SQLite database with indexed timestamp queries
- **Statistical analysis** — mean, min, max, standard deviation, variance, rate of change
- **Trend detection** — identifies sustained increasing/decreasing heart rate patterns
- **Health classification** — `NORMAL` / `ELEVATED` / `LOW` / `HIGH_RISK` / `REPOSITION_REQUIRED`, based on both instantaneous values and trend stability
- **Health score** — a single 0–100 composite score
- **MQTT publishing** — sends `{"heartRate", "status", "confidence"}` to `vitals/result`
- **Alerting** — triggers alerts only after sustained abnormal readings, with anti-spam de-duplication
- **Automated reporting** — periodic CSV/PDF summaries
- **Live dashboard** — Streamlit-based real-time view
- **Centralized logging**

---

## Health Classification Table

| Condition | Status |
|---|---|
| 60–100 BPM | `NORMAL` |
| > 100 BPM | `ELEVATED` |
| < 60 BPM | `LOW` |
| Erratic/unstable trend | `REPOSITION_REQUIRED` |
| Multiple compounding risk factors | `HIGH_RISK` |

`REPOSITION_REQUIRED` reflects a **measurement quality issue** (unstable rPPG signal, likely due to subject movement or camera angle) rather than a clinical concern — the Arduino displays this distinctly from health-related statuses.

---

## Project Structure
BiomedicalAnalyticsPlatform/
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── mqtt/
│   │   ├── mqtt_listener.py     # Subscribes to vitals/raw
│   │   └── mqtt_publisher.py    # Publishes to vitals/result
│   ├── validation/
│   │   └── validator.py
│   ├── storage/
│   │   ├── database.py
│   │   └── storage.py
│   ├── analytics/
│   │   ├── statistics.py
│   │   ├── trend_analysis.py
│   │   ├── risk_assessment.py   # Health classification logic
│   │   └── health_score.py
│   ├── alerts/
│   │   └── alert_manager.py
│   ├── reports/
│   │   └── report_generator.py
│   ├── dashboard/
│   │   └── dashboard.py
│   ├── utils/
│   │   └── logger.py
│   └── main.py
├── data/
│   ├── raw/
│   └── processed/
├── reports_output/
├── logs/
├── tests/
├── requirements.txt
└── README.md

---

## Requirements

- Python 3.9+
- A running MQTT broker reachable by this service, the Computer Vision Layer, and the Arduino (e.g. local Mosquitto)
- The Computer Vision Layer running and publishing to `vitals/raw`

```bash
pip install -r requirements.txt
```

---

## Configuration

Key settings in `src/config/settings.py`:

- **MQTT** — broker address, `vitals/raw` subscribe topic, `vitals/result` publish topic
- **Heart rate thresholds** — `HEART_RATE_MIN_NORMAL`, `HEART_RATE_MAX_NORMAL`, `HEART_RATE_ELEVATED_THRESHOLD`, `HEART_RATE_LOW_THRESHOLD`, `HEART_RATE_HIGH_THRESHOLD`
- **Trend analysis** — sliding window size, consecutive-reading significance threshold
- **Health score weights** — relative importance of heart rate vs. data stability
- **Alerting** — consecutive trigger count, repeat notification behavior
- **Reporting / Dashboard** — output format, refresh interval

---

## Running the System

```bash
cd src
python main.py                          # Terminal 1: pipeline
streamlit run dashboard/dashboard.py     # Terminal 2: dashboard
pytest tests/ -v                         # Tests
```

### Testing without the Computer Vision Layer

```bash
mosquitto_pub -h localhost -t vitals/raw -m '{"heartRate": 78, "confidence": 90}'
```

---

## Data Flow

1. Computer Vision Layer publishes `{"heartRate": ..., "confidence": ...}` to `vitals/raw`.
2. Listener validates, stores, and triggers analytics (statistics, trend, classification, health score).
3. Storage is updated with the computed `health_score` and `status`.
4. Publisher sends `{"heartRate", "status", "confidence"}` to `vitals/result`.
5. Arduino and any other subscriber receive the result in real time.
6. Alert Manager checks for sustained abnormal conditions.
7. Dashboard and reports read from storage independently.

---

## Example Payloads

**Received (`vitals/raw`):**
```json
{ "heartRate": 118, "confidence": 91 }
```

**Published (`vitals/result`):**
```json
{ "heartRate": 118, "status": "HIGH_RISK", "confidence": 91 }
```

---

## Extending the System

- **New alert channels** — extend `alert_manager.py`'s `_dispatch()` method
- **New storage backend** — modify `database.py` only; `storage.py`'s function signatures stay the same
- **Additional vital signs** (e.g. respiratory rate) — extend `validator.py`'s field lists and the corresponding analytics functions
- **Machine learning-based classification** — replace the rule-based logic in `risk_assessment.py` with a trained model, keeping the same input/output contract

---

## Technical Concepts Demonstrated

MQTT publish/subscribe with multiple concurrent subscribers, real-time data validation, time-series statistical analysis, rule-based health classification, SQLite persistence, modular testable architecture, automated reporting, live dashboards — as the analytics stage of a voice-controlled, camera-based contactless health monitoring system.