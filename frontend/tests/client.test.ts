import test from "node:test";
import assert from "node:assert/strict";
import {
  formatDuration,
  formatDurationMs,
  getRiskColor,
  getSecurityScoreColor,
  getSeverityBadgeClass,
  validateGitRepoUrl,
  redactSensitiveString,
  formatRelativeTimestamp,
} from "../src/lib/formatters.ts";
import type {
  Finding,
  ScannerHealth,
  SecurityScore,
  AIDiagnosis,
} from "../src/types/repomedic.ts";

// 1. Duration Formatting
test("formatDuration formats seconds accurately", () => {
  assert.equal(formatDuration(0.45), "0.45s");
  assert.equal(formatDuration(12.345), "12.35s");
  assert.equal(formatDuration(65), "1m 5s");
  assert.equal(formatDuration(125.4), "2m 5s");
  assert.equal(formatDuration(undefined), "N/A");
  assert.equal(formatDurationMs(450), "450ms");
  assert.equal(formatDurationMs(1500), "1.50s");
});

// 2. Severity Badge Classes
test("getSeverityBadgeClass provides distinct styling for each severity level", () => {
  assert.match(getSeverityBadgeClass("critical"), /red/);
  assert.match(getSeverityBadgeClass("high"), /orange/);
  assert.match(getSeverityBadgeClass("medium"), /amber/);
  assert.match(getSeverityBadgeClass("low"), /blue/);
  assert.match(getSeverityBadgeClass("info"), /slate/);
});

// 3. Risk Color
test("getRiskColor assigns appropriate visual levels based on score", () => {
  assert.match(getRiskColor(90), /red/);
  assert.match(getRiskColor(75), /orange/);
  assert.match(getRiskColor(50), /amber/);
  assert.match(getRiskColor(25), /blue/);
  assert.match(getRiskColor(10), /emerald/);
});

// 4. Security Score Color (100 = best, 0 = worst)
test("getSecurityScoreColor properly maps letter grades and colors", () => {
  const gradeA = getSecurityScoreColor(95);
  assert.equal(gradeA.grade, "A");
  assert.match(gradeA.text, /emerald/);

  const gradeB = getSecurityScoreColor(75);
  assert.equal(gradeB.grade, "B");
  assert.match(gradeB.text, /blue/);

  const gradeC = getSecurityScoreColor(60);
  assert.equal(gradeC.grade, "C");
  assert.match(gradeC.text, /amber/);

  const gradeD = getSecurityScoreColor(45);
  assert.equal(gradeD.grade, "D");
  assert.match(gradeD.text, /orange/);

  const gradeF = getSecurityScoreColor(20);
  assert.equal(gradeF.grade, "F");
  assert.match(gradeF.text, /red/);
});

// 5. Partial Audit Evaluation
test("Partial audit evaluation correctly detects failed required scanners", () => {
  const scanners: Record<string, ScannerHealth> = {
    custom_rules: {
      status: "failed",
      required: true,
      duration_ms: 120,
      finding_count: 0,
      error_message: "Syntax error in AST parser",
    },
    semgrep: {
      status: "completed",
      required: false,
      duration_ms: 350,
      finding_count: 2,
    },
  };

  const hasFailedRequired = Object.values(scanners).some(
    (s) => s.required && (s.status === "failed" || s.status === "unavailable")
  );
  assert.equal(hasFailedRequired, true);

  // If only optional fails:
  const scanners2: Record<string, ScannerHealth> = {
    custom_rules: {
      status: "completed",
      required: true,
      duration_ms: 150,
      finding_count: 3,
    },
    semgrep: {
      status: "failed",
      required: false,
      duration_ms: 10,
      finding_count: 0,
      error_message: "Semgrep binary not found in PATH",
    },
  };
  const hasFailedRequired2 = Object.values(scanners2).some(
    (s) => s.required && (s.status === "failed" || s.status === "unavailable")
  );
  assert.equal(hasFailedRequired2, false);
});

// 6. Missing Score versus Zero Score Handling
test("Distinguishes valid zero score from missing or undefined score", () => {
  const zeroScore: SecurityScore = {
    score: 0,
    grade: "F",
    penalty: 500,
    severity_counts: { critical: 10 },
  };

  function evaluateScoreDisplay(s?: SecurityScore | null): string {
    if (s === undefined || s === null || s.score === undefined || s.score === null) {
      return "Unavailable";
    }
    return `${s.score}/100`;
  }

  assert.equal(evaluateScoreDisplay(zeroScore), "0/100");
  assert.equal(evaluateScoreDisplay(null), "Unavailable");
  assert.equal(evaluateScoreDisplay(undefined), "Unavailable");
});

// 7. Finding Filters
test("Finding filters correctly segment by severity, evidence quality, and search terms", () => {
  const findings: Finding[] = [
    {
      id: "f-1",
      title: "Hardcoded AWS Secret Access Key",
      severity: "critical",
      confidence: "high",
      source: "custom_rules",
      evidence_quality: "deterministic",
      rule_id: "sec-01",
      file_path: "config/auth.py",
      line_start: 12,
      line_end: 12,
      evidence: "AWS_SECRET = 'AKIA****************'",
      description: "AWS key hardcoded in configuration",
      remediation: "Store keys in environment variables.",
      references: ["https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html"],
    },
    {
      id: "f-2",
      title: "Potential SQL Injection in User Lookup",
      severity: "high",
      confidence: "medium",
      source: "semgrep",
      evidence_quality: "deterministic",
      rule_id: "sqli-02",
      file_path: "db/users.py",
      line_start: 45,
      line_end: 45,
      evidence: "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
      description: "Unsanitized input in query string",
      remediation: "Use parameterized queries.",
      references: ["https://owasp.org/www-community/attacks/SQL_Injection"],
    },
    {
      id: "f-3",
      title: "AI Analysis: Logic Flaw in Rate Limiter",
      severity: "medium",
      confidence: "low",
      source: "ai_triage",
      evidence_quality: "ai_interpretation",
      rule_id: "ai-triage-logic",
      file_path: "middleware/rate_limit.py",
      line_start: 88,
      line_end: 90,
      evidence: "return True # Bypass on error",
      description: "AI identified potential fallback weakness",
      remediation: "Fail closed instead of open.",
      references: [],
    },
  ];

  // Filter by severity critical
  const criticals = findings.filter((f) => f.severity === "critical");
  assert.equal(criticals.length, 1);
  assert.equal(criticals[0].id, "f-1");

  // Filter by search query
  const sqlMatch = findings.filter(
    (f) =>
      f.title.toLowerCase().includes("sql") || f.file_path.toLowerCase().includes("sql")
  );
  assert.equal(sqlMatch.length, 1);
  assert.equal(sqlMatch[0].id, "f-2");

  // Distinguish deterministic vs AI interpretation
  const deterministicFindings = findings.filter((f) => f.evidence_quality === "deterministic");
  const aiFindings = findings.filter((f) => f.evidence_quality === "ai_interpretation");
  assert.equal(deterministicFindings.length, 2);
  assert.equal(aiFindings.length, 1);
});

// 8. Evidence Redaction Sanity Check
test("Evidence redaction sanity check prevents raw secrets in display text", () => {
  const rawSample = "ghp_1234567890abcdef1234567890abcdef123456";
  const redactedSample = redactSensitiveString(rawSample);

  assert.notEqual(rawSample, redactedSample);
  assert.equal(redactedSample.includes("abcdef"), false);
  assert.equal(redactedSample.startsWith("ghp_****"), true);

  const awsSample = "AKIAIOSFODNN7EXAMPLE";
  const redactedAws = redactSensitiveString(awsSample);
  assert.equal(redactedAws, "AKIA****************");

  const openAiSample = "sk-abcdef1234567890abcdef1234";
  const redactedOpenAi = redactSensitiveString(openAiSample);
  assert.equal(redactedOpenAi.includes("123456"), false);
});

// 9. Repository URL Validation (SSRF Prevention)
test("validateGitRepoUrl correctly validates valid Git URLs and rejects dangerous SSRF targets", () => {
  // Valid URLs
  assert.equal(validateGitRepoUrl("https://github.com/org/repo").valid, true);
  assert.equal(validateGitRepoUrl("https://gitlab.com/group/subgroup/project.git").valid, true);
  assert.equal(validateGitRepoUrl("git@github.com:org/repo.git").valid, true);

  // Prohibited SSRF and Localhost
  assert.equal(validateGitRepoUrl("http://localhost:8000").valid, false);
  assert.equal(validateGitRepoUrl("http://127.0.0.1:3000").valid, false);
  assert.equal(validateGitRepoUrl("http://169.254.169.254/latest/meta-data").valid, false);
  assert.equal(validateGitRepoUrl("file:///etc/passwd").valid, false);
  assert.equal(validateGitRepoUrl("").valid, false);
  assert.equal(validateGitRepoUrl("not-a-url").valid, false);
});

// 10. Job Terminal States for Polling
test("Terminal state detection accurately stops polling", () => {
  const terminalStates = ["completed", "partial", "failed"];
  const activeStates = ["queued", "running"];

  assert.equal(terminalStates.includes("completed"), true);
  assert.equal(terminalStates.includes("partial"), true);
  assert.equal(terminalStates.includes("failed"), true);
  assert.equal(terminalStates.includes("queued"), false);
  assert.equal(terminalStates.includes("running"), false);

  activeStates.forEach((state) => {
    assert.equal(terminalStates.includes(state), false);
  });
});

// 11. AI Diagnosis Matching
test("AI diagnoses correlate correctly with scanner finding IDs", () => {
  const diagnoses: AIDiagnosis[] = [
    {
      finding_id: "f-1",
      title: "Hardcoded Credential Exposure",
      why_it_matters: "Attackers can compromise AWS resources immediately.",
      fix: "Revoke token and inject via AWS Secrets Manager.",
      priority: 1,
      likely_false_positive: false,
    },
  ];

  const diagMap = new Map<string, AIDiagnosis>();
  diagnoses.forEach((d) => diagMap.set(d.finding_id, d));

  assert.equal(diagMap.has("f-1"), true);
  assert.equal(diagMap.has("f-nonexistent"), false);
  assert.equal(diagMap.get("f-1")?.priority, 1);
});

// 12. Relative Timestamp Formatting
test("formatRelativeTimestamp returns readable string without crashing", () => {
  const now = new Date().toISOString();
  assert.equal(formatRelativeTimestamp(now), "just now");
  assert.equal(formatRelativeTimestamp(null), "N/A");
  assert.equal(formatRelativeTimestamp(undefined), "N/A");
});
