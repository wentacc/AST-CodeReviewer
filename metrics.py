#!/usr/bin/env python3
"""
Compute F1 score and False Positive Rate from review predictions.

Usage:
    python metrics.py runs/valid_predictions.jsonl --expert CommentConsistencyExpert
"""

import argparse
import json
from pathlib import Path
from typing import List, Sequence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute F1/FPR from JSONL predictions.")
    parser.add_argument("jsonl_path", help="Path to JSONL with predictions (output of run_dataset_reviews.py).")
    parser.add_argument(
        "--expert",
        default="CommentConsistencyExpert",
        help="Name of the expert whose predictions should be evaluated.",
    )
    return parser.parse_args()


AFFIRMATIVE_PHRASES = [
    "The existing comment is still accurate",
    "The comment is still accurate",
    "comment remains accurate",
    "comment remains correct",
    "comment is accurate",
    "comment is still correct",
    "comment still matches",
    "no change required",
    "still accurate",
]


def contains_affirmative(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in AFFIRMATIVE_PHRASES)


def load_predictions(path: Path, expert: str):
    y_true, y_pred = [], []
    with path.open("r") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            label = record.get("label")
            outputs = record.get("model_output", {})
            pred = outputs.get(expert)
            expert_comments = record.get("expert_output", {}).get(expert, [])
            if label is None or pred is None:
                print(f"[warn] Missing label/prediction on line {line_num}, skipping.")
                continue
            prediction = int(pred)
            comments: Sequence[str] = []
            if isinstance(expert_comments, list):
                comments = [c for c in expert_comments if isinstance(c, str)]
            elif isinstance(expert_comments, str):
                comments = [expert_comments]

            if prediction == 1 and comments:
                if any(contains_affirmative(comment) for comment in comments):
                    prediction = 0

            y_true.append(int(label))
            y_pred.append(prediction)
    return y_true, y_pred


def compute_metrics(y_true, y_pred):
    tp = fp = tn = fn = 0
    for truth, pred in zip(y_true, y_pred):
        if truth == 1 and pred == 1:
            tp += 1
        elif truth == 0 and pred == 1:
            fp += 1
        elif truth == 0 and pred == 0:
            tn += 1
        elif truth == 1 and pred == 0:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
    }


def main():
    args = parse_args()
    jsonl_path = Path(args.jsonl_path)
    if not jsonl_path.exists():
        raise FileNotFoundError(f"{jsonl_path} does not exist.")

    y_true, y_pred = load_predictions(jsonl_path, args.expert)
    if not y_true:
        print("No valid predictions found.")
        return

    metrics = compute_metrics(y_true, y_pred)
    print(f"Evaluated {len(y_true)} samples using expert '{args.expert}'.")
    print(f"TP={metrics['TP']} FP={metrics['FP']} TN={metrics['TN']} FN={metrics['FN']}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1']:.4f}")
    print(f"FPR:       {metrics['fpr']:.4f}")


if __name__ == "__main__":
    main()