import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

MODEL_FILE = BASE / "output" / "model" / "Model_Batch_Output_Calibrated.csv"
RESULTS_FILE = BASE / "data" / "raw" / "game_results_today.csv"
TRACKING_OUT = BASE / "output" / "reports" / "model_results_tracking.csv"


def load_or_create_tracking_file():
    if TRACKING_OUT.exists():
        return pd.read_csv(TRACKING_OUT)
    else:
        return pd.DataFrame()


def main():
    # Load model output
    model = pd.read_csv(MODEL_FILE)

    # Load actual game results
    results = pd.read_csv(RESULTS_FILE)

    # Merge
    merged = pd.merge(model, results, on=["Date", "HomeTeam", "AwayTeam"], how="inner")

    # Compute actual metrics
    merged["ActualMargin"] = merged["ActualHomeScore"] - merged["ActualAwayScore"]

    merged["ActualTotal"] = merged["ActualHomeScore"] + merged["ActualAwayScore"]

    # Model’s predicted margin (sportsbook convention)
    merged["ModelMargin"] = -merged["HomeModelSpread"]

    # Spread error
    merged["SpreadError"] = merged["ActualMargin"] - merged["ModelMargin"]

    # Total error
    merged["TotalError"] = merged["ActualTotal"] - merged["ModelTotal"]

    # Winner accuracy
    merged["WinnerHit"] = (
        (merged["ActualHomeScore"] > merged["ActualAwayScore"])
        == (merged["ModelScore_A"] > merged["ModelScore_B"])
    ).astype(int)

    # Edge accuracy (ATS result)
    def edge_hit(row):
        if row["EdgeSide"] == "HOME":
            return int(row["ActualMargin"] > -row["HomeMarketSpread"])
        else:
            return int(row["ActualMargin"] < -row["HomeMarketSpread"])

    merged["EdgeHit"] = merged.apply(edge_hit, axis=1)

    # Load or create tracking master
    tracking = load_or_create_tracking_file()

    # Append today's results
    tracking = pd.concat([tracking, merged], ignore_index=True)

    # Save
    tracking.to_csv(TRACKING_OUT, index=False)

    print("✔ Results tracked and saved.")
    print(f"→ {TRACKING_OUT}")


if __name__ == "__main__":
    main()
