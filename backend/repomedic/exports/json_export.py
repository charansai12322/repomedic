"""JSON report exporter for RepoMedic."""

from repomedic.models.reports import ScanReport


def export_report_to_json(report: ScanReport, indent: int = 2) -> str:
    """Serializes a ScanReport to formatted JSON text."""
    return report.model_dump_json(indent=indent)
