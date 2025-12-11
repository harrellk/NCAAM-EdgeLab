import numpy as np


def compute_model(df, default_hca=3.4):
    """
    Hybrid scoring model:
    - PPP-based scoring for ModelScore_A / ModelScore_B / ModelTotal
    - EM-tempo-based model margin for spreads, win probabilities, and predicted margin
    """

    # ---------------------------------------------------------
    # 1) Home Court Advantage (team-specific, scaled)
    # ---------------------------------------------------------
    HCA_raw = df.get("HomeCourtAdv_A", default_hca).fillna(default_hca)

    # NEW: Zero out HCA for neutral-site games
    if "IsNeutral" in df.columns:
        HCA = np.where(df["IsNeutral"], 0, HCA_raw * 1.1)
    else:
        HCA = HCA_raw * 1.1

    # ---------------------------------------------------------
    # 2) Possession Model (harmonic mean tempo)
    # ---------------------------------------------------------
    tempo_A = df["AdjTempo_A"]
    tempo_B = df["AdjTempo_B"]

    df["PredPoss"] = 2 / ((1 / tempo_A) + (1 / tempo_B))
    df["PredPoss"] = df["PredPoss"].clip(60, 78)

    # ---------------------------------------------------------
    # 3) PPP components
    # ---------------------------------------------------------
    OE_A_pp = df["AdjOE_A"] / 100
    DE_A_pp = df["AdjDE_A"] / 100

    OE_B_pp = df["AdjOE_B"] / 100
    DE_B_pp = df["AdjDE_B"] / 100

    # ---------------------------------------------------------
    # 4) Expected PPP (smoothed matchup)
    # ---------------------------------------------------------
    A_pp = (OE_A_pp + DE_B_pp) / 2
    B_pp = (OE_B_pp + DE_A_pp) / 2

    # ---------------------------------------------------------
    # 5) PPP → Raw scoring (for scoreboard & totals)
    # ---------------------------------------------------------
    A_raw = (A_pp * df["PredPoss"]) + (HCA / 2)
    B_raw = (B_pp * df["PredPoss"]) - (HCA / 2)

    df["ModelScore_A"] = A_raw.round(1)
    df["ModelScore_B"] = B_raw.round(1)
    df["ModelTotal"] = (A_raw + B_raw).round(1)

    # ---------------------------------------------------------
    # 6) EM-based SPREAD (hybrid margin) — CALIBRATED VERSION
    # ---------------------------------------------------------
    EM_diff = df["AdjEM_A"] - df["AdjEM_B"]
    EM_term = EM_diff * (df["PredPoss"] / 100)

    # Apply calibrated multipliers from regression:
    # hybrid_margin = 1.24 * EM_term + 0.84 * HCA + 0.20
    hybrid_margin = (1.24 * EM_term) + (0.84 * HCA) + 0.20

    # sportsbook-aligned spreads
    df["HomeModelSpread"] = (-hybrid_margin).round(2)
    df["AwayModelSpread"] = (hybrid_margin).round(2)

    # ---------------------------------------------------------
    # 7) Win Probability using hybrid margin
    # ---------------------------------------------------------
    df["WinProb_A_pct"] = 100 / (1 + np.exp(-hybrid_margin / 6))
    df["WinProb_A_pct"] = df["WinProb_A_pct"].clip(1, 99).round(3)

    # ---------------------------------------------------------
    # 8) Predicted Winner & Margin (use EM-based spread)
    # ---------------------------------------------------------
    df["PredictedMargin"] = hybrid_margin.abs().round(1)

    df["PredictedWinner"] = df.apply(
        lambda r: r["HomeTeam"] if hybrid_margin.loc[r.name] > 0 else r["AwayTeam"],
        axis=1,
    )

    # ---------------------------------------------------------
    # 9) Predicted Scoreboard (PPP scores)
    #    → BUT show the EM-hybrid implied margin in text
    # ---------------------------------------------------------
    def make_scoreboard(row):
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        home_pts = round(row["ModelScore_A"])
        away_pts = round(row["ModelScore_B"])
        return f"{home} {home_pts} – {away} {away_pts}"

    df["PredictedScoreboard"] = df.apply(make_scoreboard, axis=1)

    return df
