import pandas as pd
import numpy as np
from pathlib import Path
import sys

# ---------------------------------------------------------
# EdgePoints bucket definitions
# ---------------------------------------------------------
EP_BINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, np.inf]
EP_LABELS = [
    "0–0.99",
    "1–1.99",
    "2–2.99",
    "3–3.99",
    "4–4.99",
    "5–5.99",
    "6–6.99",
    "7–7.99",
    "8–8.99",
    "9+",
]


def classify_group(row) -> str:
    """
    GroupCat logic:

    - "Neutral"    → IsNeutral = true
    - "AwayEdge"   → IsNeutral = false and EdgeSide = "AWAY"
    - "HomeEdge"   → IsNeutral = false and EdgeSide = "HOME"
    """
    is_neutral = str(row.get("IsNeutral", "")).lower() == "true"
    edge_side = str(row.get("EdgeSide", "")).upper()

    if is_neutral:
        return "Neutral"
    if not is_neutral and edge_side == "AWAY":
        return "AwayEdge"
    if not is_neutral and edge_side == "HOME":
        return "HomeEdge"
    return "Other"


def build_game_level_bucket_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a game-level report like:

    EP_Bucket  GroupCat  HomeTeam  AwayTeam  HomeMarketSpread  EdgeTeam  EdgePoints  EdgeSide  IsNeutral
    """
    d = df.copy()

    # EdgePoints are already positive in your model, so bucket directly
    d["EP_Bucket"] = pd.cut(
        d["EdgePoints"],
        bins=EP_BINS,
        labels=EP_LABELS,
        right=False,
    )

    # GroupCat classification (Neutral / AwayEdge / HomeEdge)
    d["GroupCat"] = d.apply(classify_group, axis=1)

    # Normalize IsNeutral to TRUE/FALSE strings for consistency
    d["IsNeutral_str"] = d["IsNeutral"].astype(str).str.upper()

    # Build final view
    out = d[
        [
            "EP_Bucket",
            "GroupCat",
            "HomeTeam",
            "AwayTeam",
            "HomeMarketSpread",
            "EdgeTeam",
            "EdgePoints",
            "EdgeSide",
            "IsNeutral_str",
        ]
    ].rename(columns={"IsNeutral_str": "IsNeutral"})

    # Sort like your example: by EP_Bucket, then GroupCat, then descending EdgePoints
    out = out.sort_values(
        by=["EP_Bucket", "GroupCat", "EdgePoints"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    return out


def main(input_csv: str, output_csv: str):
    # Load model batch output
    df = pd.read_csv(input_csv)

    # Sanity check: required columns
    required_cols = {
        "HomeTeam",
        "AwayTeam",
        "HomeMarketSpread",
        "EdgeTeam",
        "EdgePoints",
        "EdgeSide",
        "IsNeutral",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input file is missing required columns: {missing}")

    report_df = build_game_level_bucket_report(df)

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(out_path, index=False)

    print(f"✅ Game-level EdgePoints bucket report written to: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("\nUsage:")
        print(
            "  python build_edgepoint_game_report.py "
            "<Model_Batch_Output_Calibrated.csv> "
            "<output_report.csv>"
        )
        print("\nExample:")
        print(
            "  python build_edgepoint_game_report.py "
            "Model_Batch_Output_Calibrated.csv "
            "output/reports/edgepoint_game_report.csv"
        )
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    main(input_csv, output_csv)
