"""
============================================================================
 SHARED HELPER: idempotent section writer for results/results.md
============================================================================
 Every experiment script (Tasks 1-4) funnels its headline table into a
 SINGLE file, results/results.md, as a section "## Task N: ...". Because the
 four scripts are run independently and in any order (and may be re-run),
 each section is delimited by HTML-comment markers

     <!-- BEGIN Task N -->
     ...
     <!-- END Task N -->

 so update_section() can REPLACE a task's block in place without duplicating
 it, and always re-emits the sections in numeric order under a stable
 preamble. This is pure file I/O -- no simulation, no Aer.

 Usage (from an experiment script):
     import results_md
     results_md.update_section(1, "E91 resource cost & SKR under S*", body_md)
============================================================================
"""

import os
import re
from datetime import datetime

RESULTS_DIR = "results"
RESULTS_MD = os.path.join(RESULTS_DIR, "results.md")

_PREAMBLE = (
    "# Simulation Results\n\n"
    "Consolidated tables for the manuscript revision. Each section is written\n"
    "by its own experiment script (Tasks 1-4); re-running a script replaces\n"
    "only its own section. Numbers are produced locally by the reader -- see\n"
    "the README RUN INSTRUCTIONS.\n"
)

_BEGIN = "<!-- BEGIN Task {n} -->"
_END = "<!-- END Task {n} -->"


def _parse_sections(text):
    """Return {task_number: full_block_text} parsed from existing results.md."""
    sections = {}
    pattern = re.compile(
        r"<!-- BEGIN Task (\d+) -->\n(.*?)\n<!-- END Task \1 -->",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        sections[int(match.group(1))] = match.group(2)
    return sections


def update_section(task_number, title, body_md, results_dir=RESULTS_DIR):
    """Insert or replace the '## Task N' block in results/results.md.

    task_number : int          e.g. 1
    title       : str          short section title
    body_md     : str          markdown body (tables etc.), no leading '## '
    """
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, "results.md")

    existing = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()

    sections = _parse_sections(existing)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = (
        f"## Task {task_number}: {title}\n\n"
        f"_Last written: {stamp}._\n\n"
        f"{body_md.rstrip()}\n"
    )
    sections[task_number] = block

    parts = [_PREAMBLE]
    for n in sorted(sections):
        parts.append(
            _BEGIN.format(n=n) + "\n"
            + sections[n].rstrip() + "\n"
            + _END.format(n=n)
        )
    out = "\n\n".join(parts).rstrip() + "\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(out)

    return path


def md_table(header, rows):
    """Build a GitHub-flavoured markdown table from a header list and row lists."""
    def fmt(x):
        if isinstance(x, float):
            return f"{x:.6g}"
        return str(x)

    lines = ["| " + " | ".join(str(h) for h in header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(fmt(c) for c in r) + " |")
    return "\n".join(lines)
