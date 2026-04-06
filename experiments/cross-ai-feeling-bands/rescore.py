"""
Rescore existing benchmark results with the current scoring function.
Useful when the scorer is updated and we want to re-analyze without
re-running expensive API calls.
"""

import json
from pathlib import Path
from benchmark_runner import score_response


def rescore_all():
    results_dir = Path(__file__).parent / "benchmark_results"
    rescored_dir = results_dir / "rescored"
    rescored_dir.mkdir(exist_ok=True)

    for f in sorted(results_dir.glob("results_*.json")):
        with open(f, encoding="utf-8") as fp:
            runs = json.load(fp)

        changed = 0
        for r in runs:
            old_score = r.get("score")
            if "response" in r:
                new_score = score_response(r["problem_id"], r["response"])
                if new_score != old_score:
                    r["old_score"] = old_score
                    r["score"] = new_score
                    changed += 1

        out_file = rescored_dir / f.name
        with open(out_file, "w", encoding="utf-8") as fp:
            json.dump(runs, fp, indent=2, ensure_ascii=False)

        print(f"{f.name}: {changed} scores changed")

    print(f"\nRescored files written to: {rescored_dir}")


if __name__ == "__main__":
    rescore_all()
