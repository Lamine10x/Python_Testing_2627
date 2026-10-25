"""Genere un rapport HTML a partir de l'analyse Flake8 du projet."""

import html
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGETS = [
    'server.py',
    'tests',
    'locustfile.py',
    'generate_flake8_report.py',
]
REPORT_PATH = ROOT / 'rapport_flake8.html'

ERROR_PATTERN = re.compile(
    r'^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+): '
    r'(?P<code>[A-Z]\d+) (?P<message>.*)$'
)


def run_flake8(arguments):
    """Execute Flake8 et retourne le resultat de la commande."""
    return subprocess.run(
        [sys.executable, '-m', 'flake8'] + arguments,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def parse_errors(output):
    """Transforme la sortie Flake8 en liste d'erreurs structurees."""
    errors = []
    for line in output.splitlines():
        match = ERROR_PATTERN.match(line)
        if match:
            errors.append(match.groupdict())
    return errors


def build_rows(errors):
    """Construit les lignes HTML du tableau des violations."""
    rows = []
    for error in errors:
        rows.append(
            '<tr>'
            f'<td>{html.escape(error["file"])}</td>'
            f'<td>{error["line"]}</td>'
            f'<td>{error["col"]}</td>'
            f'<td><span class="code">{html.escape(error["code"])}</span></td>'
            f'<td>{html.escape(error["message"])}</td>'
            '</tr>'
        )
    return '\n'.join(rows)


def build_report(errors, version, command, output, exit_code):
    """Construit le contenu HTML complet du rapport."""
    success = exit_code == 0 and not errors
    status_label = 'Succès' if success else 'Échec'
    status_class = 'success' if success else 'failure'
    rows = build_rows(errors)

    if errors:
        violations = (
            '<table>'
            '<thead><tr>'
            '<th>Fichier</th><th>Ligne</th><th>Colonne</th>'
            '<th>Code</th><th>Message</th>'
            '</tr></thead>'
            f'<tbody>{rows}</tbody>'
            '</table>'
        )
    else:
        violations = (
            '<p class="empty">Aucune violation PEP8 / Flake8 détectée.</p>'
        )

    raw_output = html.escape(output) if output else (
        '(aucune sortie : aucune violation)'
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rapport Flake8 — GUDLFT</title>
  <style>
    :root {{
      --bg: #f8f9fb;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #64748b;
      --success: #16a34a;
      --success-bg: #f0fdf4;
      --success-border: #bbf7d0;
      --danger: #dc2626;
      --danger-bg: #fef2f2;
      --danger-border: #fecaca;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      padding: 36px 20px;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, Segoe UI, system-ui, sans-serif;
      line-height: 1.6;
    }}

    .container {{ max-width: 1040px; margin: 0 auto; }}

    header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 24px;
    }}

    .eyebrow {{
      margin: 0 0 4px;
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }}

    h1 {{
      margin: 0 0 4px;
      font-size: 2rem;
      letter-spacing: -0.03em;
    }}

    .subtitle {{ margin: 0; color: var(--muted); }}

    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border: 1px solid;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 700;
      white-space: nowrap;
    }}

    .badge.success {{
      color: var(--success);
      background: var(--success-bg);
      border-color: var(--success-border);
    }}

    .badge.failure {{
      color: var(--danger);
      background: var(--danger-bg);
      border-color: var(--danger-border);
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-bottom: 22px;
    }}

    .card, .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }}

    .card {{ padding: 16px 18px; }}

    .card-label {{
      margin-bottom: 4px;
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }}

    .card-value {{ font-size: 1.45rem; font-weight: 700; }}

    .panel {{ padding: 22px; margin-bottom: 18px; }}

    .panel h2 {{
      margin: 0 0 12px;
      font-size: 1rem;
      letter-spacing: -0.01em;
    }}

    pre {{
      margin: 0;
      padding: 16px;
      overflow-x: auto;
      border-radius: 8px;
      background: #0f172a;
      color: #e2e8f0;
      font-family: Consolas, monospace;
      font-size: 0.84rem;
      line-height: 1.55;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
    }}

    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}

    th {{
      color: var(--muted);
      font-size: 0.7rem;
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }}

    tr:last-child td {{ border-bottom: none; }}

    .code {{
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      background: var(--danger-bg);
      color: var(--danger);
      font-family: Consolas, monospace;
      font-size: 0.78rem;
      font-weight: 700;
    }}

    .empty {{
      margin: 0;
      padding: 18px;
      border: 1px dashed var(--success-border);
      border-radius: 8px;
      background: var(--success-bg);
      color: var(--success);
      font-weight: 600;
      text-align: center;
    }}

    footer {{
      padding-top: 8px;
      color: var(--muted);
      font-size: 0.78rem;
      text-align: right;
    }}

    @media (max-width: 760px) {{
      .cards {{ grid-template-columns: 1fr; }}
      header {{ flex-direction: column; }}
      body {{ padding: 22px 14px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <p class="eyebrow">Qualité du code</p>
        <h1>Rapport Flake8</h1>
        <p class="subtitle">GUDLFT — analyse PEP8 du projet</p>
      </div>
      <span class="badge {status_class}">{status_label}</span>
    </header>

    <section class="cards">
      <div class="card">
        <div class="card-label">Violations</div>
        <div class="card-value">{len(errors)}</div>
      </div>
      <div class="card">
        <div class="card-label">Code de sortie</div>
        <div class="card-value">{exit_code}</div>
      </div>
      <div class="card">
        <div class="card-label">Version Flake8</div>
        <div class="card-value" style="font-size: 0.95rem;">
          {html.escape(version.split(' ')[0])}
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>Commande exécutée</h2>
      <pre>{html.escape(command)}</pre>
    </section>

    <section class="panel">
      <h2>Violations détectées</h2>
      {violations}
    </section>

    <section class="panel">
      <h2>Sortie complète</h2>
      <pre>{raw_output}</pre>
    </section>

    <footer>
      Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
      — Flake8 {html.escape(version)}
    </footer>
  </div>
</body>
</html>
"""


def main():
    """Execute Flake8 et écrit le rapport HTML."""
    version_result = run_flake8(['--version'])
    version = version_result.stdout.strip().replace('\n', ' ')

    errors_result = run_flake8(TARGETS)
    output = (errors_result.stdout + errors_result.stderr).strip()
    errors = parse_errors(output)

    command = 'python -m flake8 ' + ' '.join(TARGETS)
    report = build_report(
        errors=errors,
        version=version,
        command=command,
        output=output,
        exit_code=errors_result.returncode,
    )
    REPORT_PATH.write_text(report, encoding='utf-8')

    print(f'Rapport HTML généré : {REPORT_PATH}')
    print(f'Violations détectées : {len(errors)}')


if __name__ == '__main__':
    main()
