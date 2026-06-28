#!/usr/bin/env python3
"""
PCRbase version diff monitor.
- Compares current harvested PCR versions against a saved snapshot.
- Detects: new PCRs, updated versions (new valid_from/content_hash), expired PCRs.
- Sends email to NOTIFY_EMAIL if changes found.
- Writes a diff report and creates a GitHub PR with the diff summary.

Usage:
  python src/monitor_versions.py [--snapshot data/snapshots/latest.json] [--email]
"""
import sys, os, json, hashlib, smtplib, subprocess, argparse, datetime
sys.path.insert(0, os.path.dirname(__file__))
from schema import get_con
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "snapshots", "latest.json")
NOTIFY_EMAIL = os.environ.get("PCRBASE_NOTIFY_EMAIL", "nickgogerty@gmail.com")
SMTP_FROM = os.environ.get("PCRBASE_SMTP_FROM", "nickgogerty@gmail.com")
# Uses Gmail App Password or SMTP relay. Set SMTP_PASS env var.
SMTP_HOST = os.environ.get("PCRBASE_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("PCRBASE_SMTP_PORT", "587"))
SMTP_PASS = os.environ.get("PCRBASE_SMTP_PASS", "")

REPO_DIR = os.path.join(os.path.dirname(__file__), "..")


def get_current_snapshot():
    """Pull current PCR version state from DuckDB."""
    c = get_con()
    rows = c.execute("""
        SELECT p.pcr_id, p.operator_id, p.title, p.method_family,
               v.version_id, v.version_label, v.valid_from, v.valid_until,
               v.content_hash, v.source_url, v.access_status,
               v.retrieved_at::VARCHAR as retrieved_at
        FROM pcr p
        JOIN pcr_version v ON v.pcr_id = p.pcr_id
        ORDER BY p.operator_id, p.pcr_id, v.version_label
    """).fetchall()
    cols = ['pcr_id','operator_id','title','method_family','version_id',
            'version_label','valid_from','valid_until','content_hash',
            'source_url','access_status','retrieved_at']
    c.close()
    snapshot = {}
    for row in rows:
        d = dict(zip(cols, [str(x) if x is not None else None for x in row]))
        snapshot[d['version_id']] = d
    return snapshot


def load_previous_snapshot():
    if not os.path.exists(SNAPSHOT_PATH):
        return None
    with open(SNAPSHOT_PATH) as f:
        return json.load(f)


def save_snapshot(snapshot):
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    with open(SNAPSHOT_PATH, 'w') as f:
        json.dump(snapshot, f, indent=2, default=str)


def diff_snapshots(prev, curr):
    if prev is None:
        return {'new_versions': list(curr.values()), 'changed': [], 'removed': []}
    prev_ids = set(prev.keys())
    curr_ids = set(curr.keys())
    new_versions = [curr[vid] for vid in curr_ids - prev_ids]
    removed = [prev[vid] for vid in prev_ids - curr_ids]
    changed = []
    for vid in curr_ids & prev_ids:
        p, c = prev[vid], curr[vid]
        diffs = {}
        for k in ['content_hash', 'valid_until', 'valid_from', 'access_status']:
            if p.get(k) != c.get(k):
                diffs[k] = {'from': p.get(k), 'to': c.get(k)}
        if diffs:
            changed.append({'version': c, 'changes': diffs})
    return {'new_versions': new_versions, 'changed': changed, 'removed': removed}


def format_report(diff, as_markdown=False):
    ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    total = len(diff['new_versions']) + len(diff['changed']) + len(diff['removed'])
    sep = '\n' if not as_markdown else '\n'

    lines = [f"# PCRbase Version Diff Report — {ts}",
             f"**{total} change(s) detected**{sep}"]

    if diff['new_versions']:
        lines.append(f"## ➕ New PCR Versions ({len(diff['new_versions'])})")
        for v in diff['new_versions'][:20]:
            lines.append(f"- [{v['operator_id']}] **{v['title']}** — version `{v['version_label']}` (valid until {v['valid_until']})")
        if len(diff['new_versions']) > 20:
            lines.append(f"  ... and {len(diff['new_versions'])-20} more")

    if diff['changed']:
        lines.append(f"\n## ✏️ Changed Versions ({len(diff['changed'])})")
        for item in diff['changed'][:20]:
            v = item['version']
            chg = ', '.join(f"{k}: {c['from']} → {c['to']}" for k, c in item['changes'].items())
            lines.append(f"- [{v['operator_id']}] **{v['title']}** — {chg}")

    if diff['removed']:
        lines.append(f"\n## ➖ Removed Versions ({len(diff['removed'])})")
        for v in diff['removed'][:20]:
            lines.append(f"- [{v['operator_id']}] {v['title']} v{v['version_label']}")

    return '\n'.join(lines)


def send_email(subject, body):
    if not SMTP_PASS:
        print(f"[monitor] SMTP_PASS not set — skipping email. Subject would be: {subject}")
        return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = NOTIFY_EMAIL
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(SMTP_FROM, SMTP_PASS)
            s.sendmail(SMTP_FROM, [NOTIFY_EMAIL], msg.as_string())
        print(f"[monitor] Email sent to {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"[monitor] Email failed: {e}")


def create_pr(report_md, diff):
    """Create a GitHub branch + PR with the diff report."""
    ts = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M')
    branch = f"pcr-diff/{ts}"
    report_path = os.path.join(REPO_DIR, f"data/snapshots/diff-{ts}.md")

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report_md)

    cmds = [
        ['git', '-C', REPO_DIR, 'checkout', '-b', branch],
        ['git', '-C', REPO_DIR, 'add', report_path, SNAPSHOT_PATH],
        ['git', '-C', REPO_DIR, 'commit', '-m', f'chore: PCR version diff {ts}'],
        ['git', '-C', REPO_DIR, 'push', 'origin', branch],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[monitor] git cmd failed: {' '.join(cmd)}\n{result.stderr}")
            return None

    total = len(diff['new_versions']) + len(diff['changed']) + len(diff['removed'])
    pr_title = f"PCR version diff {ts}: {total} change(s)"
    pr_body = report_md[:3000]
    gh_result = subprocess.run(
        ['gh', 'pr', 'create', '--title', pr_title, '--body', pr_body,
         '--base', 'main', '--head', branch, '--repo', 'nickgogerty/pcrbase'],
        capture_output=True, text=True, cwd=REPO_DIR
    )
    if gh_result.returncode == 0:
        pr_url = gh_result.stdout.strip()
        print(f"[monitor] PR created: {pr_url}")
        return pr_url
    else:
        print(f"[monitor] PR creation failed: {gh_result.stderr}")
        return None


def main():
    parser = argparse.ArgumentParser(description='PCRbase version diff monitor')
    parser.add_argument('--email', action='store_true', help='Send email if changes found')
    parser.add_argument('--pr', action='store_true', help='Create GitHub PR if changes found')
    parser.add_argument('--save', action='store_true', default=True, help='Save new snapshot (default: True)')
    args = parser.parse_args()

    print("[monitor] Loading current DB state…")
    curr = get_current_snapshot()
    prev = load_previous_snapshot()

    if prev is None:
        print("[monitor] No previous snapshot found — saving baseline. No diff to report.")
        save_snapshot(curr)
        return

    diff = diff_snapshots(prev, curr)
    total = len(diff['new_versions']) + len(diff['changed']) + len(diff['removed'])

    if total == 0:
        print("[monitor] No changes detected.")
        return

    print(f"[monitor] {total} change(s) detected:")
    print(f"  New versions: {len(diff['new_versions'])}")
    print(f"  Changed: {len(diff['changed'])}")
    print(f"  Removed: {len(diff['removed'])}")

    report = format_report(diff, as_markdown=True)
    print("\n" + report)

    if args.email or SMTP_PASS:
        send_email(f"PCRbase: {total} PCR version change(s) detected", report)

    if args.pr:
        create_pr(report, diff)

    if args.save:
        save_snapshot(curr)
        print(f"[monitor] Snapshot saved to {SNAPSHOT_PATH}")


if __name__ == '__main__':
    main()
