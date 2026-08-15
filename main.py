"""
Precision Agriculture Platform - CLI entry point.

Examples:
    # Train the disease-detection CNN on your dataset (data/dataset/train, /val)
    python main.py train-disease --epochs 12

    # Run disease prediction alone
    python main.py predict-disease --image data/sample/leaf.jpg

    # Run the full multi-agent pipeline: weather + soil + disease + advisory + decisions
    python main.py full-report \\
        --crop wheat --growth-stage flowering \\
        --lat 12.97 --lon 77.59 \\
        --soil-file data/sample/soil_reading.json \\
        --image data/sample/leaf.jpg
"""

import argparse
import json
import sys

from orchestrator.orchestrator import Orchestrator
from agents.disease_agent import DiseaseAgent


def cmd_train_disease(args):
    from models.train_disease_model import train
    train(epochs=args.epochs, freeze_backbone=args.freeze, lr=args.lr)


def cmd_predict_disease(args):
    agent = DiseaseAgent()
    result = agent.safe_run({"image_path": args.image})
    print(json.dumps(result, indent=2))


def cmd_full_report(args):
    context = {
        "crop": args.crop,
        "growth_stage": args.growth_stage,
        "latitude": args.lat,
        "longitude": args.lon,
    }
    if args.soil_file:
        context["soil_file"] = args.soil_file
    if args.image:
        context["image_path"] = args.image

    orchestrator = Orchestrator()
    result = orchestrator.run(context)

    print("\n" + "=" * 70)
    print("CROP ADVISORY (generative AI)")
    print("=" * 70)
    print(result.get("crop_advisory", "[no advisory generated]"))

    print("\n" + "=" * 70)
    print("AUTONOMOUS FARM DECISIONS")
    print("=" * 70)
    for action in result.get("farm_decisions", []):
        print(f"[{action['priority'].upper():6s}] {action['action']}: {action['reason']}")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nFull structured result written to {args.json_out}")


def build_parser():
    parser = argparse.ArgumentParser(description="Multi-Agent Precision Agriculture Platform")
    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser("train-disease", help="Train the plant disease CNN")
    p_train.add_argument("--epochs", type=int, default=10)
    p_train.add_argument("--lr", type=float, default=1e-4)
    p_train.add_argument("--freeze", type=lambda x: x.lower() != "false", default=True)
    p_train.set_defaults(func=cmd_train_disease)

    p_predict = sub.add_parser("predict-disease", help="Run disease prediction on one image")
    p_predict.add_argument("--image", required=True)
    p_predict.set_defaults(func=cmd_predict_disease)

    p_report = sub.add_parser("full-report", help="Run the full multi-agent pipeline")
    p_report.add_argument("--crop", required=True)
    p_report.add_argument("--growth-stage", default="unspecified")
    p_report.add_argument("--lat", type=float, required=True)
    p_report.add_argument("--lon", type=float, required=True)
    p_report.add_argument("--soil-file", default=None)
    p_report.add_argument("--image", default=None, help="Optional leaf image for disease check")
    p_report.add_argument("--json-out", default=None, help="Optional path to save full JSON result")
    p_report.set_defaults(func=cmd_full_report)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
