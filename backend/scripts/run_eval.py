"""
Batch RAGAS-style evaluation over a labeled question set.

Usage (from backend/ with venv active and a PDF already indexed):
  python -m scripts.run_eval --document-id <id>
  # or after upload via API, with the active store:
  python -m scripts.run_eval
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python -m scripts.run_eval` from backend/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.document_processor import store, try_restore_latest  # noqa: E402
from app.services.evaluator import compute_ragas_scores, log_evaluation  # noqa: E402
from app.services.rag_pipeline import run_rag  # noqa: E402

# 10 labeled pairs — replace expected answers after you pick a demo PDF.
EVAL_SET = [
    {
        "question": "What is the main topic of this document?",
        "ground_truth": "The primary subject introduced in the opening sections.",
    },
    {
        "question": "Summarize the introduction in two sentences.",
        "ground_truth": "A short overview of purpose and scope.",
    },
    {
        "question": "What key terms or definitions appear early in the document?",
        "ground_truth": "Named concepts defined near the start.",
    },
    {
        "question": "What methodology or approach is described?",
        "ground_truth": "The process or framework the authors outline.",
    },
    {
        "question": "What results or findings are reported?",
        "ground_truth": "Quantitative or qualitative outcomes stated in the text.",
    },
    {
        "question": "What limitations does the document mention?",
        "ground_truth": "Caveats or constraints acknowledged by the authors.",
    },
    {
        "question": "What recommendations are made?",
        "ground_truth": "Actionable suggestions in the conclusion or discussion.",
    },
    {
        "question": "What is X and how does it compare to Y?",
        "ground_truth": "Multi-part: definition of X plus comparison to Y (adapt X/Y to your PDF).",
    },
    {
        "question": "Which page discusses the conclusion?",
        "ground_truth": "Page number where concluding remarks appear.",
    },
    {
        "question": "What is the capital of Mars according to this document?",
        "ground_truth": "The answer is not in this document.",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run batch RAG evaluation")
    parser.add_argument("--document-id", default=None)
    args = parser.parse_args()

    if not store.indexed:
        try_restore_latest()
    if args.document_id and store.document_id != args.document_id:
        from app.services.document_processor import query_index

        query_index("warmup", k=1, document_id=args.document_id)

    if not store.indexed:
        print("No FAISS index found. Upload a PDF first (POST /api/upload).")
        sys.exit(1)

    rows = []
    print(f"Evaluating {len(EVAL_SET)} questions on document_id={store.document_id}\n")
    print(f"{'Q#':<4} {'Faith':>7} {'Relev':>7} {'Prec':>7}  Question")
    print("-" * 80)

    for i, item in enumerate(EVAL_SET, start=1):
        resp = run_rag(item["question"], document_id=store.document_id, run_eval=False)
        metrics = compute_ragas_scores(
            item["question"],
            resp.answer,
            [s.snippet for s in resp.sources],
            ground_truth=item.get("ground_truth"),
        )
        log_evaluation(
            item["question"],
            resp.answer,
            metrics,
            extra={"source": "batch_eval", "ground_truth": item.get("ground_truth")},
        )
        rows.append(
            {
                "n": i,
                "question": item["question"],
                "answer_preview": resp.answer[:160],
                "metrics": metrics.model_dump(),
                "route": resp.route.model_dump(),
            }
        )
        print(
            f"{i:<4} {metrics.faithfulness or 0:7.3f} "
            f"{metrics.answer_relevancy or 0:7.3f} "
            f"{metrics.context_precision or 0:7.3f}  "
            f"{item['question'][:48]}"
        )

    out = ROOT / "data" / "eval_logs" / "batch_eval_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote summary → {out}")


if __name__ == "__main__":
    main()
