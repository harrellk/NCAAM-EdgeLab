import pandas as pd

def convert_lines(df: pd.DataFrame) -> pd.DataFrame:
    """
    Correct spread + total edge calculation.

    Value = MarketSpread - ModelSpread
    Interpretation:
        • Higher value = better bet
        • Choose the side with the larger value
    """

    out = df.copy()

    # Ensure required columns exist
    required = [
        "HomeMarketSpread", "AwayMarketSpread",
        "HomeModelSpread", "AwayModelSpread",
        "ModelTotal", "MarketTotal",
        "HomeTeam", "AwayTeam"
    ]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"convert_lines missing columns: {missing}")

    # -------------------------
    # SPREAD VALUE CALCULATION
    # -------------------------

    out["HomeValue"] = out["HomeMarketSpread"] - out["HomeModelSpread"]
    out["AwayValue"] = out["AwayMarketSpread"] - out["AwayModelSpread"]

    # Pick best value side
    out["EdgeSide"] = out.apply(
        lambda r: "HOME" if r["HomeValue"] >= r["AwayValue"] else "AWAY",
        axis=1
    )

    out["EdgeTeam"] = out.apply(
        lambda r: r["HomeTeam"] if r["EdgeSide"] == "HOME" else r["AwayTeam"],
        axis=1
    )

    out["EdgePoints"] = out.apply(
        lambda r: max(r["HomeValue"], r["AwayValue"]),
        axis=1
    ).round(2)

    # -------------------------
    # TOTAL EDGE (for completeness)
    # -------------------------

    out["TotalEdge"] = (out["ModelTotal"] - out["MarketTotal"]).round(2)

    return out

