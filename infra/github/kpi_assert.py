# infra/github/kpi_assert.py
import json, sys, pathlib

def main():
    args = sys.argv[1:]
    if "--report" not in args:
        print("Usage: kpi_assert.py --report infra/github/kpi_report.json --min_faithfulness 0.95 --min_contradiction 0.90")
        sys.exit(2)
    report_path = pathlib.Path(args[args.index("--report")+1])
    min_f = float(args[args.index("--min_faithfulness")+1]) if "--min_faithfulness" in args else 0.95
    min_c = float(args[args.index("--min_contradiction")+1]) if "--min_contradiction" in args else 0.90

    rep = json.loads(report_path.read_text(encoding="utf-8"))
    fscore = rep.get("Faithfulness@Premise", 0.0)
    cscore = rep.get("ContradictionCoverage", 0.0)

    ok = (fscore >= min_f) and (cscore >= min_c)
    print(json.dumps({"ok": ok, "scores": rep, "thresholds": {"faithfulness": min_f, "contradiction": min_c}}, indent=2))
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
