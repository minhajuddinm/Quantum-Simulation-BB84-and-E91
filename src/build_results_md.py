"""
============================================================================
 REBUILD results/results.md FROM THE CSVs  (no simulation)
============================================================================
 Regenerates the entire results/results.md in a SINGLE process by reading the
 CSVs already written by Tasks 1-4. Because one process writes every section
 sequentially, the result is race-free -- run this after launching Tasks 1
 and 2 concurrently (in separate terminals) to guarantee results.md contains
 every section regardless of which run finished writing first.

 It reuses each experiment script's own section builder, so the tables here
 are byte-identical to what the scripts emit on their own. No Aer/Qiskit
 simulation is run: importing the modules only loads their functions (their
 main() is guarded), and this utility only reads the result CSVs. Sections
 whose input CSVs are absent are skipped (with a note), so you can rebuild
 partway through a run.

 By default results.md is rebuilt fresh (any stale sections are dropped).
 Pass --keep to preserve existing sections that are not rebuilt this time.

 Run:
   python build_results_md.py
   python build_results_md.py --keep
============================================================================
"""

import argparse
import os

import results_md


def _exists(*paths):
    return all(os.path.exists(p) for p in paths)


def rebuild(keep=False):
    md_path = results_md.RESULTS_MD
    if not keep and os.path.exists(md_path):
        os.remove(md_path)
        print(f"Removed stale {md_path} (fresh rebuild).")

    written, skipped = [], []

    # --- Task 3: config/versions (no CSV input; always available) ---
    try:
        import report_config
        report_config.write_results_md()
        written.append(3)
    except Exception as e:                       # pragma: no cover
        skipped.append(("3", f"report_config failed: {e}"))

    # --- Task 1: E91 resource cost + SKR ---
    try:
        import e91_resource_cost_sstar as t1
        if _exists(t1.RC_CSV) or _exists(t1.SKR_CSV):
            t1.write_results_md()
            written.append(1)
        else:
            skipped.append(("1", f"missing {t1.RC_CSV} / {t1.SKR_CSV} "
                                 "(run e91_resource_cost_sstar.py)"))
    except Exception as e:                        # pragma: no cover
        skipped.append(("1", f"error: {e}"))

    # --- Task 2: CI reruns / convergence / Welch ---
    try:
        import ci_reruns as t2
        if _exists(t2.SUMMARY):
            t2.write_results_md()
            written.append(2)
        else:
            skipped.append(("2", f"missing {t2.SUMMARY} (run ci_reruns.py)"))
    except Exception as e:                        # pragma: no cover
        skipped.append(("2", f"error: {e}"))

    # --- Task 4: finite-key SKR ---
    try:
        import finite_key_skr as t4
        if _exists(t4.PERTRIAL_A) or _exists(t4.PERTRIAL_B):
            rows = t4.load_all()
            groups = t4.group_by_config(rows)
            crossing_rows = t4.write_crossing(groups)
            t4.write_results_md(groups, crossing_rows)
            written.append(4)
        else:
            skipped.append(("4", f"missing {t4.PERTRIAL_A} / {t4.PERTRIAL_B} "
                                 "(run ci_reruns.py, then this)"))
    except SystemExit as e:                       # load_all aborts on old schema
        skipped.append(("4", str(e).strip() or "per-trial CSV schema issue"))
    except Exception as e:                        # pragma: no cover
        skipped.append(("4", f"error: {e}"))

    print("\n" + "=" * 60)
    print(f" Rebuilt {md_path}")
    print(f"   sections written : {sorted(written) if written else 'none'}")
    for n, why in skipped:
        print(f"   Task {n} skipped  : {why}")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true",
                    help="Preserve existing sections not rebuilt this run "
                         "(default: fresh rebuild from the CSVs present).")
    args = ap.parse_args()
    rebuild(keep=args.keep)


if __name__ == "__main__":
    main()
