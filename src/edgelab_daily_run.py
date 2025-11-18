#!/usr/bin/env python3
import json
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# Utility
# =============================================================================

def normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return (s.lower()
            .replace(".", "")
            .replace(",", "")
            .replace("-", " ")
            .replace("&", "and")
            .replace("st ", "state ")
            .replace("  ", " ")
            .strip())

def safe(df, col, default=0):
    return df[col] if col in df.columns else pd.Series([default] * len(df))

# =============================================================================
# Load DraftKings JSON + Build Odds DataFrame
# =============================================================================

DATE_TAG = "2025-11-13"
ODDS_FILE = f"./daily_odds_{DATE_TAG}.json"
ALIAS_FILE = "team_aliases.csv"
KP_FILE = "kenpom_team_data.csv"

print(f"📂 Loading DraftKings odds from: {ODDS_FILE}")

with open(ODDS_FILE, "r") as f:
    raw = json.load(f)

# Only DK entries
dk_games = []
for g in raw:
    for bm in g.get("bookmakers", []):
        if bm.get("key") != "draftkings":
            continue

        home = g["home_team"]
        away = g["away_team"]

        spread_home = None
        total_points = None

        for m in bm.get("markets", []):
            if m["key"] == "spreads":
                for o in m["outcomes"]:
                    # Home is negative if favored at home
                    if o["name"] == home:
                        spread_home = o.get("point", None)
            if m["key"] == "totals":
                for o in m["outcomes"]:
                    if o["name"].lower() == "over":
                        total_points = o.get("point", None)

        dk_games.append({
            "Date": g["commence_time"].split("T")[0],
            "HomeTeam_raw": home,
            "AwayTeam_raw": away,
            "MarketSpread": spread_home,
            "MarketTotal": total_points
        })

odds_df = pd.DataFrame(dk_games)
print(f"✅ Loaded {len(odds_df)} DK matchups.")
print(f"📊 Odds frame built: {len(odds_df)} games.")

# =============================================================================
# Load KenPom Data
# =============================================================================

print(f"📘 Loading KenPom master table: {KP_FILE}")
kp = pd.read_csv(KP_FILE)
kp_cols = kp.columns.tolist()
print(f"📘 KenPom columns loaded: {len(kp_cols)} fields.")

kp["Team_norm"] = kp["Team"].apply(normalize)

# =============================================================================
# Load Aliases
# =============================================================================

print("🔍 Loading team_aliases.csv...")
aliases = pd.read_csv(ALIAS_FILE)

aliases["Alias_norm"] = aliases["Alias"].apply(normalize)
aliases["Team_norm"]  = aliases["Team"].apply(normalize)

alias_map = dict(zip(aliases["Alias_norm"], aliases["Team"]))

print("✅ Applying alias + direct mappings...")

# =============================================================================
# Apply Mappings
# =============================================================================

def map_team(name_raw):
    n = normalize(name_raw)
    if n in alias_map:
        return alias_map[n]

    # Try direct match
    kp_match = kp[kp["Team_norm"] == n]
    if len(kp_match) == 1:
        return kp_match["Team"].values[0]

    # No match — fail loudly
    return None

odds_df["HomeTeam"] = odds_df["HomeTeam_raw"].apply(map_team)
odds_df["AwayTeam"] = odds_df["AwayTeam_raw"].apply(map_team)

if odds_df["HomeTeam"].isna().any() or odds_df["AwayTeam"].isna().any():
    print("❌ ERROR: Unmatched teams found:")
    print(odds_df[odds_df["HomeTeam"].isna() | odds_df["AwayTeam"].isna()])
    raise SystemExit

print("✅ All odds teams successfully mapped to KenPom.")

# =============================================================================
# Merge KenPom Data
# =============================================================================

print("🔗 Merging KenPom data...")

kp_A = kp.add_prefix("A_")
kp_A = kp_A.rename(columns={"A_Team": "Team_A", "A_Team_norm": "Team_norm_A"})

kp_B = kp.add_prefix("B_")
kp_B = kp_B.rename(columns={"B_Team": "Team_B", "B_Team_norm": "Team_norm_B"})

merged = odds_df.merge(
    kp_A, left_on="HomeTeam", right_on="Team_A", how="left"
).merge(
    kp_B, left_on="AwayTeam", right_on="Team_B", how="left"
)

merged.to_csv("ModelInput_Today.csv", index=False)
print("💾 Saved ModelInput_Today.csv")

# =============================================================================
# Build Model Projections
# =============================================================================

print("🧠 Generating model projections...")

# Model spread: A - B + HCA
HCA = 3.0

AdjEM_A = safe(merged, "A_AdjEM", 0).fillna(0)
AdjEM_B = safe(merged, "B_AdjEM", 0).fillna(0)

model_spread_raw = AdjEM_A - AdjEM_B + HCA

# Totals model
AdjOE_A = safe(merged, "A_AdjOE", 100).fillna(100)
AdjOE_B = safe(merged, "B_AdjOE", 100).fillna(100)
Tempo_A = safe(merged, "A_AdjTempo", 68).fillna(68)
Tempo_B = safe(merged, "B_AdjTempo", 68).fillna(68)

tempo_factor = (Tempo_A + Tempo_B) / 2
model_total_raw = (AdjOE_A + AdjOE_B) * (tempo_factor / 100)

# Calibration constants
SPREAD_SCALE = 1.12
TOTAL_SCALE = 0.94

model_spread = model_spread_raw * SPREAD_SCALE
model_total = model_total_raw * TOTAL_SCALE

market_spread = safe(merged, "MarketSpread").fillna(0)
market_total = safe(merged, "MarketTotal").fillna(0)

spread_edge = model_spread - market_spread
total_edge = model_total - market_total

# Win probability
win_prob = (50 + model_spread * 2.3).clip(1, 99)

# =============================================================================
# Convert to True Sportsbook Lines (Corrected)
# =============================================================================

def convert_to_true_lines(row):
    A = row["Team_A"]
    B = row["Team_B"]
    ms = float(row["ModelSpread"])
    mk = float(row["MarketSpread"])

    # --------------------------
    # Model favorite logic
    # --------------------------
    if ms > 0:
        model_fav = A
        model_dog = B
    else:
        model_fav = B
        model_dog = A

    # The model line is simply the model spread
    model_line = ms

    # --------------------------
    # Market favorite logic
    # --------------------------
    if mk < 0:    # negative = favorite
        market_fav = A
        market_dog = B
    else:
        market_fav = B
        market_dog = A

    market_line = mk

    # --------------------------
    # Edge calculation
    # --------------------------
    # If the favorite matches, use model_line directly
    if model_fav == market_fav:
        model_line_mkt = model_line
    else:
        # If favorites differ, flip sign so perspective matches the market
        model_line_mkt = -model_line

    edge = model_line_mkt - market_line

    return pd.Series({
        "Model_Favorite": model_fav,
        "Model_Underdog": model_dog,
        "Model_Line": round(model_line, 2),
        "Market_Favorite": market_fav,
        "Market_Underdog": market_dog,
        "Market_Line": market_line,
        "Edge_Side": model_dog if edge > 0 else model_fav,
        "Edge_Points": round(edge, 2)
    })

# =============================================================================
# Final Output DataFrame
# =============================================================================

out = pd.DataFrame({
    "Date": merged["Date"],
    "Team_A": merged["Team_A"],
    "Team_B": merged["Team_B"],
    "ModelSpread": model_spread.round(2),
    "MarketSpread": market_spread,
    "SpreadEdge": spread_edge.round(2),
    "ModelTotal": model_total.round(1),
    "MarketTotal": market_total,
    "TotalEdge": total_edge.round(1),
    "WinProb_A_pct": win_prob.round(3),
})

true_lines = out.apply(convert_to_true_lines, axis=1)
out = pd.concat([out, true_lines], axis=1)

out.to_csv("Model_Batch_Output_Calibrated.csv", index=False)
print("💾 Saved Model_Batch_Output_Calibrated.csv")

# =============================================================================
# Console Summary
# =============================================================================

print("\n=== Top Projected Edges (Calibrated, Home Perspective) ===")
top = out.copy().sort_values(by="SpreadEdge", key=lambda x: x.abs(), ascending=False)
print(top.head(12).to_string(index=False))

print("\n🏁 All systems go.")
