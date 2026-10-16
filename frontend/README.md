# RepoMedic Frontend

The professional security audit dashboard for RepoMedic, built with Next.js App Router, React 19, TypeScript, and Tailwind CSS.

## Features
- **Security Dashboard**: Visual overview of recent scans, scanner health status, and live benchmark indicators.
- **New Audit Submission**: Validated repository URL input, optional Git history scanning toggle, SSRF guardrails.
- **Live Audit Progress**: Polling with cleanup, backoff, cancellation support, and individual scanner diagnostics.
- **Audit Results View**: Prominent **Partial Audit Warning** when required scanners fail, finding filters (severity, source, category, search), and risk scoring.
- **Finding Detail Modal**: Clear distinction between deterministic evidence (`deterministic`) and LLM advice (`ai_interpretation`), sanitized code snippets, and remediation.
- **Report Downloads**: Direct server download of JSON, HTML, and SARIF 2.1.0 files.
- **Benchmark Dashboard**: Precision, recall, false positive rates, and scan timing loaded directly from reproducible benchmark output.
- **Secure BFF Architecture**: Next.js route handlers proxy backend requests with `REPMEDIC_API_KEY` on the server; zero API keys or credentials exposed to the browser.

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create `.env.local` if needed (defaults to `http://127.0.0.1:8000`):
```env
REPMEDIC_BACKEND_URL=http://127.0.0.1:8000
REPMEDIC_API_KEY=your_optional_dev_key
```

### 3. Run Development Server
```bash
npm run dev
# Dashboard opens on http://localhost:3000
```

### 4. Quality Commands
```bash
# Type checking
npx tsc --noEmit

# Unit and integration tests
npm test

# Production build
npm run build
```
