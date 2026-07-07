import csv
import logging
import os
from datetime import datetime, timedelta

from config import settings
from storage.storage import get_records_by_time_range

logger = logging.getLogger(__name__)

def generate_report(start_time: datetime = None, end_time: datetime = None, output_format: str = None) -> str:
    if end_time is None:
        end_time = datetime.now()
    if start_time is None:
        start_time = end_time - timedelta(seconds=settings.REPORT_INTERVAL)
    if output_format is None:
        output_format = settings.REPORT_FORMAT

    records = get_records_by_time_range(
        start_time.isoformat(timespec="seconds"),
        end_time.isoformat(timespec="seconds"),
    )

    if not records:
        logger.warning(f"No records found between {start_time} and {end_time}. Report will be empty.")

    summary = _summarize(records)

    os.makedirs(settings.REPORTS_OUTPUT_DIR, exist_ok=True)
    filename_base = f"report_{start_time.strftime('%Y%m%d_%H%M')}_{end_time.strftime('%Y%m%d_%H%M')}"

    if output_format == "csv":
        return _export_csv(records, summary, filename_base)
    elif output_format == "pdf":
        return _export_pdf(records, summary, filename_base, start_time, end_time)
    else:
        raise ValueError(f"Unsupported report format: {output_format}")
    
def _summarize(records: list) -> dict:
    if not records:
        return {
            "count": 0,
            "avg_heart_rate": None,
            "avg_spo2": None,
            "avg_temperature": None,
            "abnormal_count": 0,
        }
    
    heart_rates = [r["heartRate"] for r in records if r.get("heartRate") is not None]
    spo2_values = [r["spo2"] for r in records if r.get("spo2") is not None]
    temperatures = [r["temperature"] for r in records if r.get("temperature") is not None]

    abnormal_count = sum(1 for r in records if r.get("status") not in ("NORMAL", None))

    return {
        "count": len(records),
        "avg_heart_rate": round(sum(heart_rates) / len(heart_rates), 1) if heart_rates else None,
        "avg_spo2": round(sum(spo2_values) / len(spo2_values), 1) if spo2_values else None,
        "avg_temperature": round(sum(temperatures) / len(temperatures), 1) if temperatures else None,
        "abnormal_count": abnormal_count,
    }

def _export_csv(records: list, summary: dict, filename_base: str) -> str:
    filepath = os.path.join(settings.REPORTS_OUTPUT_DIR, f"{filename_base}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["SUMMARY"])
        writer.writerow(["Total Records", summary["count"]])
        writer.writerow(["Average Heart Rate (BPM)", summary["avg_heart_rate"]])
        writer.writerow(["Average SpO2 (%)", summary["avg_spo2"]])
        writer.writerow(["Average Temperature (C)", summary["avg_temperature"]])
        writer.writerow(["Abnormal Readings Count", summary["abnormal_count"]])
        writer.writerow([])

        writer.writerow(["received_at", "heartRate", "spo2", "temperature", "status", "health_score", "risk_level"])
        for r in records:
            writer.writerow([
                r.get("received_at"),
                r.get("heartRate"),
                r.get("spo2"),
                r.get("temperature"),
                r.get("status"),
                r.get("health_score"),
                r.get("risk_level"),
            ])

    logger.info(f"CSV report generated: {filepath}")
    return filepath

def _export_pdf(records: list, summary: dict, filename_base: str, start_time: datetime, end_time: datetime) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        logger.error("reportlab is not installed. Falling back to CSV export. Run: pip install reportlab")
        return _export_csv(records, summary, filename_base)
    
    filepath = os.path.join(settings.REPORTS_OUTPUT_DIR, f"{filename_base}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Biomedical Data Analytics Report", styles["Title"]))
    elements.append(Paragraph(
        f"Period: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    summary_data = [
        ["Metric", "Value"],
        ["Total Records", str(summary["count"])],
        ["Average Heart Rate (BPM)", str(summary["avg_heart_rate"])],
        ["Average SpO2 (%)", str(summary["avg_spo2"])],
        ["Average Temperature (C)", str(summary["avg_temperature"])],
        ["Abnormal Readings Count", str(summary["abnormal_count"])],
    ]

    summary_table = Table(summary_data, hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Detailed Records (most recent 100)", styles["Heading2"]))
    detail_header = ["Time", "HR (BPM)", "SpO2 (%)", "Temp (C)", "Status", "Risk Level"]
    detail_rows = [detail_header]
    for r in records[-100:]:
        detail_rows.append([
            str(r.get("received_at", "")),
            str(r.get("heartRate", "")),
            str(r.get("spo2", "")),
            str(r.get("temperature", "")),
            str(r.get("status", "")),
            str(r.get("risk_level", "")),
        ])

    detail_table = Table(detail_rows, hAlign="LEFT")
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    logger.info(f"PDF report generated: {filepath}")
    return filepath

if __name__ == "__main__":
    logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    path = generate_report(output_format="csv")
    print(f"Report generated at: {path}")
