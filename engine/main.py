import sys
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends, Form
*** End Patch
    app_source_scanned = bool(scan.get("scanned"))
    app_source_ok = app_source_scanned and len(scan.get("findings", [])) == 0

    def badge(text: str, passed: bool) -> str:
        color = "#10b981" if passed else "#ef4444"
        return f"<span style='background:{color};color:#fff;padding:4px 8px;border-radius:4px;font-weight:700;margin-right:8px'>{text}</span>"

    body = f"""<html><head><title>Internal Status</title><style>
            body{{font-family:Arial;margin:18px}}
            .card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06)}}
            .section{{margin-bottom:18px}}
            .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}}
            pre{{background:#f1f5f9;color:#0f172a;padding:12px;border-radius:6px}}
            ul.tests{{list-style:none;padding-left:0}}
            ul.tests li{{margin:6px 0}}
        </style></head><body>
        <div class='card'>
            <h2>Internal Status — Overall: <span style='color:{overall_color}'>{overall.upper()}</span></h2>

            <div class='section'>
                <h3>Database (Postgres)</h3>
                <ul class='tests'>
                    <li>{badge('Reachable', pg_reachable)}Postgres host: {pg_host}:{pg_port} — {pg_detail}</li>
                    <li>{badge('Latency OK', pg_reachable and (pg_lat is None or pg_lat <= AMBER_THRESHOLD))}Latency: {pg_lat if pg_lat is not None else 'n/a'}</li>
                </ul>
            </div>

            <div class='section'>
                <h3>Message Broker (Redis)</h3>
                <ul class='tests'>
                    <li>{badge('Reachable', redis_reachable)}Redis host: {redis_host}:{redis_port} — {redis_detail}</li>
                    <li>{badge('Latency OK', redis_reachable and (redis_lat is None or redis_lat <= AMBER_THRESHOLD))}Latency: {redis_lat if redis_lat is not None else 'n/a'}</li>
                </ul>
            </div>

            <div class='section'>
                <h3>LLM (Ollama)</h3>
                <ul class='tests'>
                    <li>{badge('Healthy', ollama_reachable)}Status: {ollama_detail}</li>
                </ul>
            </div>

            <div class='section'>
                <h3>App</h3>
                <ul class='tests'>
                    <li>{badge('HTTP Probe', app_probe_ok)}{app_probe_summary}</li>
                    <li>{badge('Source Scan', app_source_scanned and app_source_ok)}Source scanned: {app_source_scanned} — findings: {len(scan.get('findings', [])) if scan.get('scanned') else 'n/a'}</li>
                </ul>
            </div>

            {notes_html}

            {f"<div style='margin-top:12px'><strong>App probe snippet</strong><pre style='white-space:pre-wrap'>{app_probe_snippet_escaped}</pre></div>" if app_probe_snippet_escaped else ''}

            <div style='margin-top:12px'>
                <strong>Meaning &amp; Thresholds</strong>
                <ul>
                    <li><span style='color:#10b981;font-weight:700'>Green</span> = OK — latency &lt; 200 ms</li>
                    <li><span style='color:#f59e0b;font-weight:700'>Amber</span> = Degraded — latency 200 ms–1500 ms (review)</li>
                    <li><span style='color:#ef4444;font-weight:700'>Red</span> = Critical — latency &gt; 1500 ms or unreachable / policy violation</li>
                </ul>
            </div>
        </div>
        </body></html>"""
    return HTMLResponse(content=body)
            .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}}
            .service{{margin:8px 0}}
            pre{{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px}}
        body = f"""<html><head><title>Internal Status</title><style>
                body{{font-family:Arial;margin:18px}}
                .card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06)}}
                .section{{margin-bottom:18px}}
                .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}}
                pre{{background:#f1f5f9;color:#0f172a;padding:12px;border-radius:6px}}
                ul.tests{{list-style:none;padding-left:0}}
                ul.tests li{{margin:6px 0}}
            </style></head><body>
            <div class='card'>
                <h2>Internal Status — Overall: <span style='color:{overall_color}'>{overall.upper()}</span></h2>

                <div class='section'>
                    <h3>Database (Postgres)</h3>
                    <ul class='tests'>
                        <li>{badge('Reachable', pg_reachable)}Postgres host: {pg_host}:{pg_port} — {pg_detail}</li>
                        <li>{badge('Latency OK', pg_reachable and (pg_lat is None or pg_lat <= AMBER_THRESHOLD))}Latency: {pg_lat if pg_lat is not None else 'n/a'}</li>
                    </ul>
                </div>

                <div class='section'>
                    <h3>Message Broker (Redis)</h3>
                    <ul class='tests'>
                        <li>{badge('Reachable', redis_reachable)}Redis host: {redis_host}:{redis_port} — {redis_detail}</li>
                        <li>{badge('Latency OK', redis_reachable and (redis_lat is None or redis_lat <= AMBER_THRESHOLD))}Latency: {redis_lat if redis_lat is not None else 'n/a'}</li>
                    </ul>
                </div>

                <div class='section'>
                    <h3>LLM (Ollama)</h3>
                    <ul class='tests'>
                        <li>{badge('Healthy', ollama_reachable)}Status: {ollama_detail}</li>
                    </ul>
                </div>

                <div class='section'>
                    <h3>App</h3>
                    <ul class='tests'>
                        <li>{badge('HTTP Probe', app_probe_ok)}{app_probe_summary}</li>
                        <li>{badge('Source Scan', app_source_scanned and app_source_ok)}Source scanned: {app_source_scanned} — findings: {len(scan.get('findings', [])) if scan.get('scanned') else 'n/a'}</li>
                    </ul>
                </div>

                {notes_html}

                {f"<div style='margin-top:12px'><strong>App probe snippet</strong><pre style='white-space:pre-wrap'>{app_probe_snippet_escaped}</pre></div>" if app_probe_snippet_escaped else ''}

                <div style='margin-top:12px'>
                    <strong>Meaning &amp; Thresholds</strong>
                    <ul>
                        <li><span style='color:#10b981;font-weight:700'>Green</span> = OK — latency &lt; 200 ms</li>
                        <li><span style='color:#f59e0b;font-weight:700'>Amber</span> = Degraded — latency 200 ms–1500 ms (review)</li>
                        <li><span style='color:#ef4444;font-weight:700'>Red</span> = Critical — latency &gt; 1500 ms or unreachable / policy violation</li>
                    </ul>
                </div>
            </div>
            </body></html>"""
    uvicorn.run(app, host="0.0.0.0", port=8001)
