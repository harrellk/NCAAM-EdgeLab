import numpy as np


def compute_model(df, default_hca=3.4):
    """
    Possession-adjusted scoring model using OE/DE, harmonic tempo,
    and score-driven spreads (ModelSpread = PredictedMargin).
    """

    # -------------------------
    # 1) Home Court Advantage
    # -------------------------
    HCA = df.get("HomeCourtAdv_A", default_hca).fillna(default_hca)

    # -------------------------
    # 2) Possession Model
    # -------------------------
    tempo_A = df["AdjTempo_A"]
    tempo_B = df["AdjTempo_B"]

    df["PredPoss"] = 2 / ((1 / tempo_A) + (1 / tempo_B))
    df["PredPoss"] = df["PredPoss"].clip(60, 78)

    # -------------------------
    # 3) Per-possession Offensive/Defensive
    # -------------------------
    OE_A_pp = df["AdjOE_A"] / 100
    DE_A_pp = df["AdjDE_A"] / 100
    OE_B_pp = df["AdjOE_B"] / 100
    DE_B_pp = df["AdjDE_B"] / 100

    # -------------------------
    # 4) Expected PPP
    # -------------------------
    A_pp = (OE_A_pp + DE_B_pp) / 2
    B_pp = (OE_B_pp + DE_A_pp) / 2

    # -------------------------
    # 5) Apply HCA evenly across scoring
    # -------------------------
    # Half added to home, half removed from away
    A_raw = (A_pp * df["PredPoss"]) + (HCA / 2)
    B_raw = (B_pp * df["PredPoss"]) - (HCA / 2)

    df["ModelScore_A"] = A_raw.round(1)
    df["ModelScore_B"] = B_raw.round(1)

    # -------------------------
    # 6) Spread = score difference (no independent formula!)
    # -------------------------
    pred_margin = A_raw - B_raw

    df["HomeModelSpread"] = (-pred_margin).round(2)
    df["AwayModelSpread"] = (pred_margin).round(2)

    # -------------------------
    # 7) Total = sum of predicted points
    # -------------------------
    df["ModelTotal"] = (A_raw + B_raw).round(1)

    # -------------------------
    # 8) Win Probability (score-based)
    # -------------------------
    df["WinProb_A_pct"] = 100 / (1 + np.exp(-pred_margin / 6))
    df["WinProb_A_pct"] = df["WinProb_A_pct"].clip(1, 99).round(3)

    # -------------------------
    # 9) Scoreboard & Winner
    # -------------------------
    df["PredictedWinner"] = df.apply(
        lambda r: (
            r["HomeTeam"] if r["ModelScore_A"] > r["ModelScore_B"] else r["AwayTeam"]
        ),
        axis=1,
    )

    df["PredictedMargin"] = pred_margin.abs().round(1)

    df["PredictedScoreboard"] = df.apply(
        lambda r: f"{r['HomeTeam']} {round(r['ModelScore_A'])} – {r['AwayTeam']} {round(r['ModelScore_B'])}",
        axis=1,
    )

    return df
