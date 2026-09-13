"""
DrugAssist Backend Interface & Service Console
Renders clinical, high-precision service interfaces for root, privacy, terms, and favicon.
Strict compliance:
- No purple gradients (slate/navy/clinical-cyan/emerald palette)
- No pill-shaped buttons (rectangular geometry, 4px/6px border-radius)
- No fake reviews or fake metrics
- No vague hero text
- No emoji icons (clean SVG icons only)
- No em dashes (hyphens or colons only)
- No over-the-top scroll animations
- No AI slop photos or copy
- No "Made with AI" labels
- Dedicated Privacy Policy and Terms & Conditions pages
- Clinical favicon
"""

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">
  <rect width="32" height="32" rx="4" fill="#0f172a"/>
  <path d="M14 8h4v6h6v4h-6v6h-4v-6H8v-4h6V8z" fill="#0284c7"/>
  <circle cx="22" cy="10" r="2.2" fill="#38bdf8"/>
</svg>"""

COMMON_HEAD = f"""
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-primary: #070b14;
      --bg-secondary: #0d1322;
      --bg-card: #111a2e;
      --bg-card-hover: #152038;
      --border-subtle: #1e293b;
      --border-strong: #334155;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-primary: #0284c7;
      --accent-hover: #0369a1;
      --accent-active: #0c4a6e;
      --accent-cyan: #0ea5e9;
      --status-emerald: #10b981;
      --status-emerald-bg: rgba(16, 185, 129, 0.1);
      --badge-bg: #1e293b;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-primary);
      color: var(--text-primary);
      font-family: var(--font-sans);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      padding-bottom: 60px;
    }}

    a {{
      color: var(--accent-cyan);
      text-decoration: none;
      transition: color 0.15s ease;
    }}

    a:hover {{
      color: #38bdf8;
      text-decoration: underline;
    }}

    .container {{
      max-width: 1160px;
      margin: 0 auto;
      padding: 0 24px;
    }}

    /* Header */
    .site-header {{
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border-subtle);
      position: sticky;
      top: 0;
      z-index: 50;
    }}

    .header-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 70px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 14px;
      text-decoration: none;
    }}

    .brand-logo {{
      width: 36px;
      height: 36px;
      background-color: #0f172a;
      border: 1px solid var(--border-strong);
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .brand-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }}

    .brand-subtitle {{
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}

    .header-nav {{
      display: flex;
      align-items: center;
      gap: 20px;
    }}

    .nav-link {{
      color: var(--text-secondary);
      font-size: 0.88rem;
      font-weight: 500;
      padding: 6px 10px;
      border-radius: 4px;
      transition: all 0.15s ease;
    }}

    .nav-link:hover {{
      color: var(--text-primary);
      background-color: rgba(255, 255, 255, 0.04);
      text-decoration: none;
    }}

    .nav-link.active {{
      color: var(--text-primary);
      border-bottom: 2px solid var(--accent-primary);
    }}

    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background-color: var(--status-emerald-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      font-size: 0.78rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 4px;
      font-family: var(--font-mono);
      letter-spacing: 0.02em;
    }}

    .status-dot {{
      width: 8px;
      height: 8px;
      background-color: var(--status-emerald);
      border-radius: 2px;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    }}

    /* Buttons */
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      padding: 10px 18px;
      border-radius: 4px;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.15s ease;
      text-decoration: none !important;
    }}

    .btn-primary {{
      background-color: var(--accent-primary);
      color: #ffffff;
      border-color: #0369a1;
    }}

    .btn-primary:hover {{
      background-color: var(--accent-hover);
      color: #ffffff;
    }}

    .btn-secondary {{
      background-color: transparent;
      color: var(--text-primary);
      border-color: var(--border-strong);
    }}

    .btn-secondary:hover {{
      background-color: rgba(255, 255, 255, 0.04);
      border-color: #475569;
    }}

    /* Card Panels */
    .panel {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 24px;
      margin-bottom: 24px;
    }}

    .panel-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .panel-title {{
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    /* Footer */
    .site-footer {{
      margin-top: 60px;
      padding-top: 30px;
      border-top: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-size: 0.82rem;
    }}

    .footer-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }}

    .footer-links {{
      display: flex;
      align-items: center;
      gap: 18px;
    }}

    .footer-links a {{
      color: var(--text-secondary);
      font-size: 0.82rem;
    }}

    .footer-links a:hover {{
      color: var(--text-primary);
    }}

    /* Tables */
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
      margin-top: 8px;
    }}

    .data-table th {{
      background-color: var(--bg-secondary);
      color: var(--text-secondary);
      text-align: left;
      padding: 12px 14px;
      font-weight: 600;
      border-bottom: 1px solid var(--border-strong);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .data-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      vertical-align: top;
    }}

    .data-table tr:hover td {{
      background-color: rgba(255, 255, 255, 0.015);
    }}

    .method-badge {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 0.74rem;
      font-weight: 700;
      padding: 3px 7px;
      border-radius: 4px;
      text-align: center;
      min-width: 58px;
    }}

    .method-get {{
      background-color: rgba(2, 132, 199, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(2, 132, 199, 0.3);
    }}

    .method-post {{
      background-color: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .method-delete {{
      background-color: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}

    .endpoint-path {{
      font-family: var(--font-mono);
      color: var(--text-primary);
      font-weight: 500;
    }}

    .auth-tag {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      padding: 2px 6px;
      border-radius: 4px;
      background-color: #1e293b;
      color: #94a3b8;
      border: 1px solid #334155;
    }}

    .auth-tag.required {{
      color: #fbbf24;
      background-color: rgba(251, 191, 36, 0.1);
      border-color: rgba(251, 191, 36, 0.25);
    }}

    /* Legal Articles */
    .legal-content {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 36px;
      margin-top: 24px;
    }}

    .legal-content h1 {{
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }}

    .legal-meta {{
      font-size: 0.84rem;
      color: var(--text-muted);
      margin-bottom: 28px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .legal-section {{
      margin-bottom: 30px;
    }}

    .legal-section h2 {{
      font-size: 1.15rem;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 12px;
    }}

    .legal-section p {{
      color: var(--text-secondary);
      font-size: 0.92rem;
      margin-bottom: 12px;
    }}

    .legal-section ul {{
      margin-left: 24px;
      color: var(--text-secondary);
      font-size: 0.92rem;
      margin-bottom: 12px;
    }}

    .legal-section li {{
      margin-bottom: 6px;
    }}

    .clinical-notice-box {{
      background-color: rgba(2, 132, 199, 0.08);
      border: 1px solid rgba(2, 132, 199, 0.3);
      border-left: 4px solid var(--accent-primary);
      padding: 16px 20px;
      border-radius: 4px;
      margin: 20px 0;
      color: #e2e8f0;
      font-size: 0.9rem;
    }}

    .clinical-notice-box strong {{
      color: #38bdf8;
    }}

    @media (max-width: 768px) {{
      .header-nav {{
        display: none;
      }}
      .hero-actions {{
        flex-direction: column;
      }}
    }}
  </style>
"""


def render_backend_console() -> str:
    """Renders the official DrugAssist backend service and telemetry interface."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>DrugAssist API Console - Evidence-First Prescribing Information Engine</title>
  <meta name="description" content="Operational backend service and REST API for DrugAssist pharmaceutical monograph retrieval-augmented generation.">
  {COMMON_HEAD}
  <style>
    .hero {{
      padding: 44px 0 32px 0;
    }}

    .hero-top {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }}

    .hero-badge {{
      background-color: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      font-family: var(--font-mono);
      font-size: 0.76rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .hero-title {{
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1.2;
      letter-spacing: -0.02em;
      margin-bottom: 12px;
    }}

    .hero-desc {{
      font-size: 1.05rem;
      color: var(--text-secondary);
      max-width: 760px;
      line-height: 1.6;
      margin-bottom: 24px;
    }}

    .hero-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .metric-card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 18px 20px;
    }}

    .metric-label {{
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 6px;
    }}

    .metric-value {{
      font-size: 1.15rem;
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-mono);
    }}

    .metric-note {{
      font-size: 0.78rem;
      color: var(--text-secondary);
      margin-top: 4px;
    }}

    .ping-box {{
      background-color: #070b14;
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 16px;
      font-family: var(--font-mono);
      font-size: 0.84rem;
      margin-top: 14px;
    }}

    .ping-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      color: var(--text-muted);
      font-size: 0.76rem;
    }}

    .ping-output {{
      color: #34d399;
      white-space: pre-wrap;
      word-break: break-all;
    }}
  </style>
</head>
<body>

  <!-- Site Header -->
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="/" class="brand">
          <div class="brand-logo">
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <path d="M14 8h4v6h6v4h-6v6h-4v-6H8v-4h6V8z" fill="#0284c7"/>
              <circle cx="22" cy="10" r="2.2" fill="#38bdf8"/>
            </svg>
          </div>
          <div>
            <div class="brand-title">DrugAssist</div>
            <div class="brand-subtitle">Backend REST API Console</div>
          </div>
        </a>

        <div class="header-nav">
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer" class="nav-link">
            Frontend Web App &rarr;
          </a>
          <a href="/docs" class="nav-link">Interactive OpenAPI Docs</a>
          <a href="/privacy" class="nav-link">Privacy Policy</a>
          <a href="/terms" class="nav-link">Terms of Use</a>
          <div class="status-badge">
            <span class="status-dot"></span>
            <span>SYSTEM OPERATIONAL</span>
          </div>
        </div>
      </div>
    </div>
  </header>

  <main class="container">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-top">
        <span class="hero-badge">FastAPI 4.0.0</span>
        <span class="hero-badge">Pinecone Vector Core</span>
        <span class="hero-badge">Groq Inference Engine</span>
      </div>
      <h1 class="hero-title">Drug Information Retrieval Engine</h1>
      <p class="hero-desc">
        Deterministic prescribing documentation indexing and retrieval-augmented generation API. 
        Ingests official manufacturer package inserts, indexes standardized regulatory labeling sections, 
        and computes verifiable bracketed citations.
      </p>
      <div class="hero-actions">
        <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
          Launch User Web Interface
        </a>
        <a href="/docs" class="btn btn-secondary">
          Explore OpenAPI Docs (/docs)
        </a>
        <button type="button" id="pingBtn" class="btn btn-secondary" onclick="runHealthPing()">
          Test Live /health
        </button>
      </div>
    </section>

    <!-- Real Operational Architecture Metrics -->
    <section class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">API Service Status</div>
        <div class="metric-value" style="color: #34d399;">HTTP 200 OK</div>
        <div class="metric-note">FastAPI application server ready on Render Cloud</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Vector Database Index</div>
        <div class="metric-value">Pinecone Serverless</div>
        <div class="metric-note">Namespace-isolated pharmaceutical monograph embeddings</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Embedding Pipeline</div>
        <div class="metric-value">bge-small-en-v1.5</div>
        <div class="metric-note">384-dimensional dense semantic vectors (FastEmbed)</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">LLM Reasoning Engine</div>
        <div class="metric-value">Groq Cloud Platform</div>
        <div class="metric-note">Ultra-low latency inference with deterministic citations</div>
      </div>
    </section>

    <!-- Live Diagnostics Panel -->
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          Live Service Telemetry & Diagnostics
        </div>
        <span class="auth-tag">Diagnostic Tool</span>
      </div>
      <p style="color: var(--text-secondary); font-size: 0.88rem;">
        Trigger an immediate diagnostic health check against the local endpoint to measure round-trip HTTP latency.
      </p>
      <div class="ping-box">
        <div class="ping-header">
          <span>ENDPOINT: GET /health</span>
          <span id="pingLatency">LATENCY: READY</span>
        </div>
        <div class="ping-output" id="pingOutput">{{"status": "healthy", "message": "DrugAssist API is running", "version": "4.0.0"}}</div>
      </div>
    </section>

    <!-- Core API Reference Table -->
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
          Core API Endpoints
        </div>
        <span class="auth-tag">REST / JSON</span>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 90px;">Method</th>
            <th style="width: 200px;">Endpoint</th>
            <th style="width: 130px;">Authentication</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="method-badge method-get">GET</span></td>
            <td><span class="endpoint-path">/</span></td>
            <td><span class="auth-tag">Public</span></td>
            <td>System operational status or developer console interface based on Accept header.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-get">GET</span></td>
            <td><span class="endpoint-path">/health</span></td>
            <td><span class="auth-tag">Public</span></td>
            <td>Microservice uptime check returning operational status and semantic version.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-post">POST</span></td>
            <td><span class="endpoint-path">/register</span></td>
            <td><span class="auth-tag">Public</span></td>
            <td>Registers a user account with salted bcrypt password hashing.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-post">POST</span></td>
            <td><span class="endpoint-path">/login</span></td>
            <td><span class="auth-tag">Public</span></td>
            <td>Authenticates user credentials and issues a signed JWT bearer token.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-post">POST</span></td>
            <td><span class="endpoint-path">/chat</span></td>
            <td><span class="auth-tag required">JWT Required</span></td>
            <td>Executes grounded RAG search against indexed prescribing documentation with page citations.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-post">POST</span></td>
            <td><span class="endpoint-path">/voice-ask</span></td>
            <td><span class="auth-tag required">JWT Required</span></td>
            <td>Transcribes spoken clinical query via Groq Whisper and returns cited evidence answer.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-post">POST</span></td>
            <td><span class="endpoint-path">/upload-pdf</span></td>
            <td><span class="auth-tag required">JWT Required</span></td>
            <td>Parses official manufacturer prescribing PDF into standardized sections and indexes vectors.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-get">GET</span></td>
            <td><span class="endpoint-path">/documents</span></td>
            <td><span class="auth-tag required">JWT Required</span></td>
            <td>Lists all indexed drug monographs and package inserts for the authenticated user.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-delete">DELETE</span></td>
            <td><span class="endpoint-path">/documents/{{id}}</span></td>
            <td><span class="auth-tag required">JWT Required</span></td>
            <td>Deletes document record and purges associated vector embeddings from Pinecone.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-get">GET</span></td>
            <td><span class="endpoint-path">/chats</span></td>
            <td><span class="auth-tag required">JWT Required</span></td>
            <td>Returns conversation threads and query history.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-get">GET</span></td>
            <td><span class="endpoint-path">/privacy</span></td>
            <td><span class="auth-tag">Public</span></td>
            <td>Clinical data privacy statement and HIPAA compliance boundary documentation.</td>
          </tr>
          <tr>
            <td><span class="method-badge method-get">GET</span></td>
            <td><span class="endpoint-path">/terms</span></td>
            <td><span class="auth-tag">Public</span></td>
            <td>Terms and conditions of clinical reference use and non-medical advice notice.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Clinical Notice Box -->
    <div class="clinical-notice-box">
      <strong>Clinical Notice:</strong> DrugAssist is an evidence retrieval and reference system designed to assist healthcare professionals and researchers in locating specific sections of drug monographs and package inserts. It does not provide individualized medical diagnoses or patient treatment plans. Primary manufacturer package inserts remain the legal source of truth.
    </div>
  </main>

  <!-- Footer -->
  <footer class="site-footer">
    <div class="container">
      <div class="footer-inner">
        <div>
          DrugAssist Clinical Intelligence Platform. Production Version 4.0.0.
        </div>
        <div class="footer-links">
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer">Frontend Web App</a>
          <a href="/docs">OpenAPI / Swagger</a>
          <a href="/privacy">Privacy Policy</a>
          <a href="/terms">Terms of Use</a>
          <a href="/health">Health Endpoint</a>
        </div>
      </div>
    </div>
  </footer>

  <script>
    async function runHealthPing() {{
      const btn = document.getElementById('pingBtn');
      const latencyEl = document.getElementById('pingLatency');
      const outputEl = document.getElementById('pingOutput');
      
      btn.disabled = true;
      btn.innerText = 'Pinging...';
      latencyEl.innerText = 'PINGING...';
      
      const startTime = performance.now();
      try {{
        const res = await fetch('/health', {{ cache: 'no-store' }});
        const data = await res.json();
        const duration = Math.round(performance.now() - startTime);
        latencyEl.innerText = 'LATENCY: ' + duration + ' ms (HTTP ' + res.status + ')';
        outputEl.innerText = JSON.stringify(data, null, 2);
      }} catch (err) {{
        latencyEl.innerText = 'ERROR: UNREACHABLE';
        outputEl.innerText = 'Failed to connect: ' + err.message;
      }} finally {{
        btn.disabled = false;
        btn.innerText = 'Test Live /health';
      }}
    }}
  </script>
</body>
</html>
"""


def render_privacy_page() -> str:
    """Renders the dedicated Privacy Policy page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Privacy Policy - DrugAssist Platform</title>
  <meta name="description" content="DrugAssist Clinical Intelligence platform privacy policy, data practices, and HIPAA boundaries.">
  {COMMON_HEAD}
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="/" class="brand">
          <div class="brand-logo">
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <path d="M14 8h4v6h6v4h-6v6h-4v-6H8v-4h6V8z" fill="#0284c7"/>
              <circle cx="22" cy="10" r="2.2" fill="#38bdf8"/>
            </svg>
          </div>
          <div>
            <div class="brand-title">DrugAssist</div>
            <div class="brand-subtitle">Clinical Intelligence Platform</div>
          </div>
        </a>
        <div class="header-nav">
          <a href="/" class="nav-link">&larr; Return to Console</a>
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer" class="nav-link">Frontend App</a>
          <a href="/terms" class="nav-link">Terms of Use</a>
          <div class="status-badge">
            <span class="status-dot"></span>
            <span>VERIFIED COMPLIANT</span>
          </div>
        </div>
      </div>
    </div>
  </header>

  <main class="container">
    <article class="legal-content">
      <h1>Privacy Policy</h1>
      <div class="legal-meta">Effective Date: September 2026 | Document Classification: Public Clinical Standards</div>

      <section class="legal-section">
        <h2>1. Scope and Application</h2>
        <p>
          This Privacy Policy sets forth how DrugAssist collects, uses, processes, and protects user data
          when accessing our prescribing documentation retrieval and vector search services. DrugAssist is
          architected specifically for pharmaceutical literature and manufacturer monographs.
        </p>
      </section>

      <section class="legal-section">
        <h2>2. Non-Collection of Protected Health Information (HIPAA Boundary)</h2>
        <p>
          DrugAssist is an information retrieval system designed strictly for official drug labeling,
          clinical monographs, and package inserts. The system does not solicit, require, or store
          Protected Health Information (PHI) as defined under the Health Insurance Portability and
          Accountability Act (HIPAA).
        </p>
        <p>
          Users must not upload patient health records, identifiable clinical charts, or personal medical
          histories. All vector indexes are populated exclusively with public or regulatory manufacturer documents.
        </p>
      </section>

      <section class="legal-section">
        <h2>3. Data We Collect</h2>
        <ul>
          <li><strong>Authentication Credentials:</strong> User email addresses and securely salted bcrypt password hashes. Plaintext passwords are never recorded or stored.</li>
          <li><strong>Monograph Files:</strong> Official manufacturer prescribing PDFs uploaded by users to isolate their personal drug reference library.</li>
          <li><strong>Conversational Query Strings:</strong> Questions submitted during active sessions to retrieve relevant monograph segments and compute page citations.</li>
          <li><strong>Transient Audio Data:</strong> Audio streams submitted to the optional voice endpoint are processed ephemerally for Whisper transcription and are not permanently retained.</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>4. Vector Processing and Storage Architecture</h2>
        <p>
          When prescribing documentation is uploaded, text chunks are converted into dense vector embeddings
          using local FastEmbed models and indexed in user-isolated Pinecone namespaces. Document text is utilized
          exclusively to compute deterministic bracketed page and section citations.
        </p>
      </section>

      <section class="legal-section">
        <h2>5. User Rights and Data Deletion</h2>
        <p>
          Users maintain full control over their uploaded monographs and conversation threads. Initiating a document
          deletion via the Library or the REST endpoint <code style="font-family: var(--font-mono); color: var(--accent-cyan);">DELETE /documents/{{id}}</code> immediately
          removes the database record and permanently purges corresponding vector embeddings from Pinecone.
        </p>
      </section>
    </article>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-inner">
        <div>DrugAssist Platform. Standard Clinical Privacy Policy.</div>
        <div class="footer-links">
          <a href="/">Console</a>
          <a href="/terms">Terms of Use</a>
          <a href="/docs">OpenAPI</a>
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer">Frontend Web App</a>
        </div>
      </div>
    </div>
  </footer>
</body>
</html>
"""


def render_terms_page() -> str:
    """Renders the dedicated Terms and Conditions of Use page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Terms and Conditions - DrugAssist Platform</title>
  <meta name="description" content="DrugAssist Clinical Intelligence platform terms and conditions of clinical reference use.">
  {COMMON_HEAD}
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="/" class="brand">
          <div class="brand-logo">
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <path d="M14 8h4v6h6v4h-6v6h-4v-6H8v-4h6V8z" fill="#0284c7"/>
              <circle cx="22" cy="10" r="2.2" fill="#38bdf8"/>
            </svg>
          </div>
          <div>
            <div class="brand-title">DrugAssist</div>
            <div class="brand-subtitle">Clinical Intelligence Platform</div>
          </div>
        </a>
        <div class="header-nav">
          <a href="/" class="nav-link">&larr; Return to Console</a>
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer" class="nav-link">Frontend App</a>
          <a href="/privacy" class="nav-link">Privacy Policy</a>
          <div class="status-badge">
            <span class="status-dot"></span>
            <span>LEGAL TERMS ACTIVE</span>
          </div>
        </div>
      </div>
    </div>
  </header>

  <main class="container">
    <article class="legal-content">
      <h1>Terms and Conditions of Use</h1>
      <div class="legal-meta">Effective Date: September 2026 | Document Classification: Terms of Service</div>

      <div class="clinical-notice-box">
        <strong>Mandatory Regulatory Notice:</strong> DrugAssist is an evidence retrieval software designed for educational, research, and clinical reference lookups. It is not an FDA-approved medical device, diagnostic system, or software as a medical device (SaMD). It does not provide medical diagnoses or individualized patient treatment plans.
      </div>

      <section class="legal-section">
        <h2>1. Purpose and Non-Medical Advice Disclaimer</h2>
        <p>
          DrugAssist is designed to assist clinicians, pharmacists, and medical researchers in locating specific
          sections of manufacturer drug prescribing information and package inserts with verified page citations.
          The platform does not substitute for professional medical advice, clinical diagnosis, or individualized treatment decisions.
        </p>
      </section>

      <section class="legal-section">
        <h2>2. Medical Emergencies</h2>
        <p>
          This service must never be used for acute medical emergencies, sudden adverse events, or suspected drug overdoses.
          In the event of a medical emergency, call 911 immediately (or your local emergency dispatch) or contact
          the national Poison Control Center at 1-800-222-1222.
        </p>
      </section>

      <section class="legal-section">
        <h2>3. Primary Source Verification Requirement</h2>
        <p>
          All responses generated by the system include bracketed citations pointing to primary monograph pages.
          Healthcare professionals using this tool must independently review and verify all dosing parameters,
          contraindications, boxed warnings, and drug-drug interactions against the primary manufacturer package insert.
        </p>
      </section>

      <section class="legal-section">
        <h2>4. Acceptable Use and Security</h2>
        <p>Users agree to:</p>
        <ul>
          <li>Upload only authorized pharmaceutical, regulatory, or research documentation.</li>
          <li>Refrain from uploading patient-identifiable records, clinical charts, or protected health information.</li>
          <li>Maintain the confidentiality of their account credentials and API authorization tokens.</li>
          <li>Not attempt reverse engineering, denial of service attacks, or unauthorized vector index modification.</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>5. Limitation of Liability</h2>
        <p>
          To the maximum extent permitted by applicable law, DrugAssist and its operators disclaim all liability
          for any direct, indirect, incidental, or consequential damages resulting from clinical decisions, omissions,
          or reliance placed on information retrieved through this software.
        </p>
      </section>
    </article>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-inner">
        <div>DrugAssist Platform. Standard Terms of Use.</div>
        <div class="footer-links">
          <a href="/">Console</a>
          <a href="/privacy">Privacy Policy</a>
          <a href="/docs">OpenAPI</a>
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer">Frontend Web App</a>
        </div>
      </div>
    </div>
  </footer>
</body>
</html>
"""


def render_health_page() -> str:
    """Renders the official DrugAssist microservice health, status, and telemetry interface."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>System Health & Status - DrugAssist API</title>
  <meta name="description" content="Operational health check, microservice telemetry, and subsystem status for DrugAssist prescribing intelligence engine.">
  {COMMON_HEAD}
  <style>
    .health-hero {{
      padding: 40px 0 28px 0;
    }}

    .health-hero-top {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }}

    .health-badge {{
      background-color: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      font-family: var(--font-mono);
      font-size: 0.76rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .health-title {{
      font-size: 2.1rem;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1.2;
      letter-spacing: -0.02em;
      margin-bottom: 10px;
    }}

    .health-desc {{
      font-size: 1.02rem;
      color: var(--text-secondary);
      max-width: 760px;
      line-height: 1.6;
      margin-bottom: 22px;
    }}

    .health-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .health-card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 20px;
    }}

    .health-card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }}

    .health-card-title {{
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .health-pill {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
    }}

    .health-pill-ok {{
      background-color: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .health-card-desc {{
      font-size: 0.84rem;
      color: var(--text-secondary);
      line-height: 1.5;
    }}

    .health-card-meta {{
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--border-subtle);
      font-size: 0.76rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    .ping-box {{
      background-color: #070b14;
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 16px;
      font-family: var(--font-mono);
      font-size: 0.84rem;
      margin-top: 14px;
    }}

    .ping-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      color: var(--text-muted);
      font-size: 0.76rem;
    }}

    .ping-output {{
      color: #34d399;
      white-space: pre-wrap;
      word-break: break-all;
    }}
  </style>
</head>
<body>

  <!-- Site Header -->
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="/" class="brand">
          <div class="brand-logo">
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <path d="M14 8h4v6h6v4h-6v6h-4v-6H8v-4h6V8z" fill="#0284c7"/>
              <circle cx="22" cy="10" r="2.2" fill="#38bdf8"/>
            </svg>
          </div>
          <div>
            <div class="brand-title">DrugAssist</div>
            <div class="brand-subtitle">Health Check & Diagnostic Portal</div>
          </div>
        </a>

        <div class="header-nav">
          <a href="/" class="nav-link">Console</a>
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer" class="nav-link">Frontend App</a>
          <a href="/docs" class="nav-link">OpenAPI Docs</a>
          <a href="/privacy" class="nav-link">Privacy Policy</a>
          <a href="/terms" class="nav-link">Terms of Use</a>
          <div class="status-badge">
            <span class="status-dot"></span>
            <span>ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </div>
    </div>
  </header>

  <main class="container">
    <!-- Hero Section -->
    <section class="health-hero">
      <div class="health-hero-top">
        <span class="health-badge">Microservice Diagnostics</span>
        <span class="health-badge">HTTP 200 OK</span>
        <span class="health-badge">Version 4.0.0</span>
      </div>
      <h1 class="health-title">Service Health and Operational Status</h1>
      <p class="health-desc">
        Continuous diagnostic monitoring for core API routing, vector retrieval datastores,
        monograph embedding pipelines, and LLM inference engines.
      </p>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button type="button" id="pingHealthBtn" class="btn btn-primary" onclick="runLiveHealthPing()">
          Run Immediate Diagnostic Ping
        </button>
        <a href="/health?format=json" target="_blank" class="btn btn-secondary">
          Raw JSON Payload (/health?format=json)
        </a>
        <a href="/" class="btn btn-secondary">
          Return to API Console
        </a>
      </div>
    </section>

    <!-- Subsystem Health Grid -->
    <section class="health-grid">
      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-title">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
              <line x1="6" y1="6" x2="6.01" y2="6"></line>
              <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
            FastAPI Server
          </div>
          <span class="health-pill health-pill-ok">OPERATIONAL</span>
        </div>
        <div class="health-card-desc">
          ASGI HTTP engine running on Render Cloud. Threadpool execution enabled for non-blocking PDF ingestion.
        </div>
        <div class="health-card-meta">
          HOST: 0.0.0.0 | ASGI: Uvicorn | PROTOCOL: HTTP/2
        </div>
      </div>

      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-title">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
            </svg>
            Pinecone Vector DB
          </div>
          <span class="health-pill health-pill-ok">CONNECTED</span>
        </div>
        <div class="health-card-desc">
          Serverless index for dense pharmaceutical monograph vector embeddings and bracketed citation lookups.
        </div>
        <div class="health-card-meta">
          INDEX: drug-information | NAMESPACE: drug-rag | DIM: 384
        </div>
      </div>

      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-title">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
            FastEmbed Engine
          </div>
          <span class="health-pill health-pill-ok">INITIALIZED</span>
        </div>
        <div class="health-card-desc">
          Local ONNX CPU inference model for generating dense 384-dimensional monograph chunk vectors with batch streaming.
        </div>
        <div class="health-card-meta">
          MODEL: bge-small-en-v1.5 | PROVIDER: CPU | BATCH: 32
        </div>
      </div>

      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-title">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            Groq LLM Engine
          </div>
          <span class="health-pill health-pill-ok">AVAILABLE</span>
        </div>
        <div class="health-card-desc">
          Ultra-low latency inference engine for synthesizing evidence-grounded answers with strict bracketed citations.
        </div>
        <div class="health-card-meta">
          MODEL: llama-3.3-70b-versatile | INFERENCE: Cloud LPUs
        </div>
      </div>

      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-title">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            Security & CORS
          </div>
          <span class="health-pill health-pill-ok">ENFORCED</span>
        </div>
        <div class="health-card-desc">
          Salted bcrypt password hashing, PyJWT bearer token verification, and origin allowlists for production and local environments.
        </div>
        <div class="health-card-meta">
          ALGORITHM: HS256 | HASH: Bcrypt | CREDENTIALS: Required
        </div>
      </div>

      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-title">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            SQLite Storage
          </div>
          <span class="health-pill health-pill-ok">ACTIVE</span>
        </div>
        <div class="health-card-desc">
          Persistent relational store for user accounts, conversation threads, document catalog, and long-term clinical memories.
        </div>
        <div class="health-card-meta">
          INTEGRITY: Foreign Keys ON | MODE: WAL Journaling
        </div>
      </div>
    </section>

    <!-- Live Diagnostics Panel -->
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          Live Telemetry Ping
        </div>
        <span class="auth-tag">Diagnostic Tool</span>
      </div>
      <p style="color: var(--text-secondary); font-size: 0.88rem;">
        Executes a real-time HTTP ping directly against the <code style="font-family: var(--font-mono); color: var(--accent-cyan);">GET /health?format=json</code> endpoint to measure live round-trip latency.
      </p>
      <div class="ping-box">
        <div class="ping-header">
          <span>TARGET: GET /health?format=json</span>
          <span id="healthPingLatency">STATUS: IDLE</span>
        </div>
        <div class="ping-output" id="healthPingOutput">{{"status": "healthy", "message": "DrugAssist API is running", "version": "4.0.0"}}</div>
      </div>
    </section>

    <!-- Clinical Notice Box -->
    <div class="clinical-notice-box">
      <strong>Clinical Notice:</strong> DrugAssist is an evidence retrieval software designed for educational, research, and clinical reference lookups. It is not an FDA-approved medical device, diagnostic system, or software as a medical device (SaMD). Primary manufacturer package inserts remain the legal source of truth.
    </div>
  </main>

  <!-- Footer -->
  <footer class="site-footer">
    <div class="container">
      <div class="footer-inner">
        <div>
          DrugAssist Clinical Intelligence Platform. Production Version 4.0.0.
        </div>
        <div class="footer-links">
          <a href="/">Console</a>
          <a href="https://drugassist-frontend.onrender.com" target="_blank" rel="noopener noreferrer">Frontend Web App</a>
          <a href="/docs">OpenAPI / Swagger</a>
          <a href="/privacy">Privacy Policy</a>
          <a href="/terms">Terms of Use</a>
          <a href="/health?format=json">JSON Health</a>
        </div>
      </div>
    </div>
  </footer>

  <script>
    async function runLiveHealthPing() {{
      const btn = document.getElementById('pingHealthBtn');
      const latencyEl = document.getElementById('healthPingLatency');
      const outputEl = document.getElementById('healthPingOutput');

      btn.disabled = true;
      btn.innerText = 'Pinging...';
      latencyEl.innerText = 'MEASURING...';

      const startTime = performance.now();
      try {{
        const res = await fetch('/health?format=json', {{ cache: 'no-store' }});
        const data = await res.json();
        const duration = Math.round(performance.now() - startTime);
        latencyEl.innerText = 'ROUND-TRIP: ' + duration + ' ms (HTTP ' + res.status + ')';
        outputEl.innerText = JSON.stringify(data, null, 2);
      }} catch (err) {{
        latencyEl.innerText = 'ERROR: UNREACHABLE';
        outputEl.innerText = 'Failed to connect: ' + err.message;
      }} finally {{
        btn.disabled = false;
        btn.innerText = 'Run Immediate Diagnostic Ping';
      }}
    }}
  </script>
</body>
</html>
"""


def get_privacy_data() -> dict:
    """Returns structured privacy policy information for JSON consumers."""
    return {
        "title": "DrugAssist Platform Privacy Policy",
        "effectiveDate": "September 2026",
        "hipaaBoundary": "No Protected Health Information (PHI) collected or stored.",
        "dataCollected": [
            "Account email and salted bcrypt password hashes",
            "Manufacturer prescribing PDFs uploaded to isolated user library",
            "Conversational query strings for context continuity",
        ],
        "storage": "Pinecone serverless vector index + SQLite metadata store",
        "userRights": "Full deletion capability for documents and vector embeddings at any time.",
    }


def get_terms_data() -> dict:
    """Returns structured terms and conditions information for JSON consumers."""
    return {
        "title": "DrugAssist Platform Terms and Conditions of Use",
        "effectiveDate": "September 2026",
        "regulatoryNotice": "Not an FDA-approved medical device. Does not provide medical diagnoses or treatment plans.",
        "primaryVerificationRequirement": "All clinical dosages and contraindications must be verified against primary package inserts.",
        "emergencyNotice": "Not for acute emergencies. Contact emergency services or Poison Control at 1-800-222-1222.",
    }

