# infra/github/kpi_score.py
import json, sys, pathlib, re

def dummy_metrics(spec_text: str):
    # Heuristics: count "Premise", "Inference", "Contradiction"
    prem = len(re.findall(r"\bPremise\b|\bPremissas?\b", spec_text, re.I))
    infr = len(re.findall(r"\bInference\b|\bInfer(ê|e)ncias?\b", spec_text, re.I))
    contra = len(re.findall(r"\bContradiction\b|\bContradiç(ões|ao|ão)\b", spec_text, re.I))
    # Toy scoring
    faithfulness = 0.90 + min(prem, 5)*0.01
    contradiction = 0.85 + min(contra, 5)*0.01
    return round(min(faithfulness, 0.99), 3), round(min(contradiction, 0.99), 3)

def main():
    args = sys.argv[1:]
    if "--spec_dir" not in args or "--out" not in args:
        print("Usage: kpi_score.py --spec_dir lsa/spec --out infra/github/kpi_report.json")
        sys.exit(2)
    spec_dir = pathlib.Path(args[args.index("--spec_dir")+1])
    out_path = pathlib.Path(args[args.index("--out")+1])

    buf = []
    for p in spec_dir.rglob("*.md"):
        buf.append(p.read_text(encoding="utf-8"))
    joined = "\n\n".join(buf) if buf else ""
    fscore, cscore = dummy_metrics(joined)

    report = {"Faithfulness@Premise": fscore, "ContradictionCoverage": cscore}
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
