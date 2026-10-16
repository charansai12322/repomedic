"""API endpoints for retrieving reproducible security benchmark results."""

import json
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from repomedic.api.dependencies import verify_api_key

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"], dependencies=[Depends(verify_api_key)])

BENCHMARK_RESULTS_FILE = (
    Path(__file__).resolve().parent.parent.parent / "benchmarks" / "results" / "benchmark_latest.json"
)


class BenchmarkSummaryResponse(BaseModel):
    """High-level summary of the latest reproducible benchmark run."""

    timestamp_utc: str = Field(description="ISO-8601 UTC timestamp of the benchmark execution")
    total_fixtures: int = Field(description="Total synthetic fixtures evaluated")
    true_positives: int = Field(description="Total verified true positive findings")
    false_positives: int = Field(description="Total false positive findings")
    false_negatives: int = Field(description="Total missed expected findings")
    true_negatives: int = Field(description="Total clean control fixtures correctly passed")
    precision: float = Field(description="Precision: TP / (TP + FP)")
    recall: float = Field(description="Recall: TP / (TP + FN)")
    false_positive_rate: float = Field(description="False positive rate: FP / (FP + TN)")
    f1_score: float = Field(description="Harmonic mean of precision and recall")
    ai_citation_validity: float = Field(description="Percentage of AI citations with valid finding IDs")
    average_scan_duration_ms: float = Field(description="Average scan latency per fixture in ms")
    median_scan_duration_ms: float = Field(description="Median scan latency per fixture in ms")
    scanner_availability_rate: float = Field(description="Proportion of scanners available and completed")
    scanner_failure_rate: float = Field(description="Proportion of scanners failed")
    partial_audit_rate: float = Field(description="Proportion of fixtures resulting in partial audit")


@router.get(
    "/latest",
    summary="Get full latest benchmark report",
)
async def get_latest_benchmark() -> Dict[str, Any]:
    """
    Returns the complete latest security benchmark report including per-fixture breakdowns.
    If no benchmark has been executed yet, returns HTTP 404.
    """
    if not BENCHMARK_RESULTS_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No benchmark results available. Run `python -m benchmarks.runner` to generate results.",
        )
    try:
        with open(BENCHMARK_RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read benchmark results: {str(e)}",
        )


@router.get(
    "/summary",
    response_model=BenchmarkSummaryResponse,
    summary="Get high-level benchmark scorecard",
)
async def get_benchmark_summary() -> BenchmarkSummaryResponse:
    """
    Returns the high-level benchmark scorecard metrics for dashboard display.
    If no benchmark has been executed yet, returns HTTP 404.
    """
    data = await get_latest_benchmark()
    return BenchmarkSummaryResponse(
        timestamp_utc=data.get("timestamp_utc", ""),
        total_fixtures=data.get("total_fixtures", 0),
        true_positives=data.get("true_positives", 0),
        false_positives=data.get("false_positives", 0),
        false_negatives=data.get("false_negatives", 0),
        true_negatives=data.get("true_negatives", 0),
        precision=data.get("precision") or 0.0,
        recall=data.get("recall") or 0.0,
        false_positive_rate=data.get("false_positive_rate") or 0.0,
        f1_score=data.get("f1_score") or 0.0,
        ai_citation_validity=data.get("ai_citation_validity") or 1.0,
        average_scan_duration_ms=data.get("average_scan_duration_ms") or 0.0,
        median_scan_duration_ms=data.get("median_scan_duration_ms") or 0.0,
        scanner_availability_rate=data.get("scanner_availability_rate") or 1.0,
        scanner_failure_rate=data.get("scanner_failure_rate") or 0.0,
        partial_audit_rate=data.get("partial_audit_rate") or 0.0,
    )
