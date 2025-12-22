import pandas as pd
import numpy as np
from pathlib import Path

MODEL_OUTPUT = Path("output/model/Model_Batch_Output_Calibrated.csv")
TEAM_PERF_FILE = Path("output/reports/team_performance_report_v2.xlsx")
OUTPUT_FILE = Path("output/matchup_scorer/today_matchup_scores.xlsx")


def norm_positive_rate(rate):
    if np.isnan(rate):
        return 0.5
    return float(np.clip((rate - 0.40) / 0.20, 0, 1))


def norm_error(mae, bias):
    if np.isnan(mae):
        return 0.5
    combo = 0.7 * mae + 0.3 * abs(bias if not np.isnan(bias) else 0)
    return float(np.clip((20 - combo) / 15, 0, 1))


def norm_edge_strength(edge_points):
    if np.isnan(edge_points):
        return 0
    return float(np.clip(abs(edge_points) / 10, 0, 1))


def load_inputs():
    if not MODEL_OUTPUT.exists():
        raise FileNotFoundError(f"Missing model output: {MODEL_OUTPUT}")

    if not TEAM_PERF_FILE.exists():
        raise FileNotFoundError(f"Missing team performance file: {TEAM_PERF_FILE}")

    df = pd.read_csv(MODEL_OUTPUT)
    ats = pd.read_excel(TEAM_PERF_FILE, sheet_name="Team_Wide_ATS")
    acc = pd.read_excel(TEAM_PERF_FILE, sheet_name="Model_Accuracy")
    edge = pd.read_excel(TEAM_PERF_FILE, sheet_name="Edge_Performance")

    return df, ats, acc, edge


def build_lookups(ats, acc, edge):
    ats_lookup = ats.set_index("Team").to_dict(orient="index")
    acc_lookup = acc.set_index("Team").to_dict(orient="index")
    edge_lookup = edge.set_index("EdgeTeam").to_dict(orient="index")
    return ats_lookup, acc_lookup, edge_lookup


def get_team_ats(team, ats_lookup):
    d = ats_lookup.get(team)
    if not d:
        return np.nan, np.nan
    return d["ATS_HitRate"], d["Games"]


def get_team_acc(team, acc_lookup):
    d = acc_lookup.get(team)
    if not d:
        return np.nan, np.nan, np.nan
    return d["MAE"], d["RMSE"], d["Bias"]


def get_edge_perf(team, edge_lookup):
    d = edge_lookup.get(team)
    if not d:
        return np.nan, np.nan, np.nan
    return d["ATS_HitRate"], d["Games"], d["AvgEdgePoints"]


def build_scorer(df, ats_lookup, acc_lookup, edge_lookup):
    rows = []

    for _, row in df.iterrows():
        edge_team = row["EdgeTeam"]
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        opp = away if edge_team == home else home

        edge_pts = row["EdgePoints"]

        team_ats_rate, team_ats_games = get_team_ats(edge_team, ats_lookup)
        opp_ats_rate, opp_ats_games = get_team_ats(opp, ats_lookup)

        mae, rmse, bias = get_team_acc(edge_team, acc_lookup)
        edge_hit_rate, edge_games, hist_avg_edge = get_edge_perf(edge_team, edge_lookup)

        edge_strength_score = norm_edge_strength(edge_pts)
        team_ats_score = norm_positive_rate(team_ats_rate)
        edge_perf_score = norm_positive_rate(edge_hit_rate)
        model_acc_score = norm_error(mae, bias)
        opp_penalty = norm_positive_rate(opp_ats_rate)
        opp_factor = 1 - 0.3 * opp_penalty

        base_score = (
            0.30 * edge_strength_score
            + 0.25 * team_ats_score
            + 0.25 * edge_perf_score
            + 0.20 * model_acc_score
        )

        final_score = float(np.clip(base_score * 100 * opp_factor, 0, 100))

        if final_score >= 75:
            tier = "GREEN"
        elif final_score >= 60:
            tier = "YELLOW"
        elif final_score >= 45:
            tier = "ORANGE"
        else:
            tier = "RED"

        rows.append(
            {
                "Date": row["Date"],
                "Matchup": f"{home} vs {away}",
                "EdgeTeam": edge_team,
                "EdgePoints_Today": edge_pts,
                "ConfidenceScore": final_score,
                "Tier": tier,
            }
        )

    return pd.DataFrame(rows)


def write_output(df):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"🔥 Matchup Scorer written to: {OUTPUT_FILE}")


def main():
    df, ats, acc, edge = load_inputs()
    ats_lookup, acc_lookup, edge_lookup = build_lookups(ats, acc, edge)
    scorer = build_scorer(df, ats_lookup, acc_lookup, edge_lookup)
    write_output(scorer)


if __name__ == "__main__":
    main()
