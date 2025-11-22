#!/usr/bin/env python3
from pathlib import Path

# === Core imports (modular architecture) ===
from fetch_odds import load_draftkings_odds
from load_kenpom import load_kenpom
from compute_model import compute_model
from generate_edges import convert_lines
from utils import normalize

# 🔥 DEBUG: identify which fetch_odds module is actually being used
import inspect
import fetch_odds

print("DEBUG: fetch_odds loaded from:", inspect.getfile(fetch_odds))

print("\n==========================================")
print("🏀 NCAAM EdgeLab — Daily Pipeline (MODULAR)")
print("==========================================\n")

# === Directory structure ===
BASE = Path(__file__).resolve().parents[1]

RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
MAP = BASE / "data" / "mappings"
OUT = BASE / "output" / "model"

ODDS_FILE = RAW / "daily_odds.json"
ALIAS_FILE = MAP / "team_aliases.csv"
KP_DIR = BASE / "data" / "processed" / "kenpom"


# =====================================================================
# STEP 1 — Load DraftKings Odds
# =====================================================================
print("📡 Loading DraftKings odds...")
odds = load_draftkings_odds(ODDS_FILE, ALIAS_FILE)
print(f"✔ Loaded {len(odds)} matchups.\n")

# =====================================================================
# STEP 2 — Load KenPom Master Table
# =====================================================================
print("📘 Loading KenPom master table...")
kp = load_kenpom(KP_DIR)

# Canonical normalization
kp["Team_norm"] = kp["Team"].apply(normalize)
print(f"✔ KP teams loaded: {len(kp)}\n")


# =====================================================================
# STEP 3 — Merge Odds ↔ KP
# =====================================================================
print("🔗 Merging DraftKings odds with KenPom data...")

# Normalize odds names
odds["Home_norm"] = odds["HomeTeam"].apply(normalize)
odds["Away_norm"] = odds["AwayTeam"].apply(normalize)

kp_lookup = kp.set_index("Team_norm")

# Validation
missing_home = odds[~odds["Home_norm"].isin(kp_lookup.index)]
missing_away = odds[~odds["Away_norm"].isin(kp_lookup.index)]

if len(missing_home) or len(missing_away):
    print("❌ Unmatched teams found!")
    if len(missing_home):
        print("❌ HOME TEAM MISMATCHES:\n", missing_home)
    if len(missing_away):
        print("❌ AWAY TEAM MISMATCHES:\n", missing_away)
    raise SystemExit("❌ Fix alias mappings and rerun.")

# Attach KP stats
kp_cols = ["Team", "AdjOE", "AdjDE", "AdjEM", "AdjTempo", "HomeCourtAdv"]
for col in kp_cols:
    odds[f"{col}_A"] = odds["Home_norm"].map(kp_lookup[col])
    odds[f"{col}_B"] = odds["Away_norm"].map(kp_lookup[col])

merged = odds.drop(columns=["Home_norm", "Away_norm"])
print("✔ Odds + KP merge complete.\n")

# =====================================================================
# STEP 3B — Neutral-Site Validation & Logging
# =====================================================================
if "IsNeutral" in merged.columns:
    neutrals = merged[merged["IsNeutral"]]
    if len(neutrals):
        print("🏟 Neutral-Site Games Detected:")
        print(neutrals[["Date", "HomeTeam", "AwayTeam", "IsNeutral"]])
        print()
    else:
        print("ℹ No neutral-site games flagged today.")
        print("   (If this is unexpected, update daily_odds.json)\n")


# =====================================================================
# STEP 4 — Model Computation
# =====================================================================
print("🧠 Applying compute_model() calibration and projections...")
merged = compute_model(merged)
print("✔ Model spreads, totals, scores, and win probabilities generated.\n")


# =====================================================================
# STEP 5 — Edge Computation
# =====================================================================
print("📊 Evaluating edges (spread + totals)...")
final = convert_lines(merged)
print("✔ Edge evaluation complete.\n")


# =====================================================================
# STEP 6 — Select Final Output Fields
# =====================================================================
COLUMNS_TO_KEEP = [
    "Date",
    "HomeTeam",
    "AwayTeam",
    "HomeMarketSpread",
    "AwayMarketSpread",
    "MarketTotal",
    "PredPoss",
    "ModelScore_A",
    "ModelScore_B",
    "ModelTotal",
    "HomeModelSpread",
    "AwayModelSpread",
    "WinProb_A_pct",
    "HomeValue",
    "AwayValue",
    "EdgeSide",
    "EdgeTeam",
    "EdgePoints",
    "TotalEdge",
    "PredictedWinner",
    "PredictedMargin",
    "PredictedScoreboard",
    "IsNeutral",  # NEW — include neutral flag in final outputs
]

final_trimmed = final[COLUMNS_TO_KEEP]


# =====================================================================
# STEP 7 — Save Results
# =====================================================================
OUT.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

final.to_csv(OUT / "Model_Batch_Output_Calibrated.csv", index=False)
final_trimmed.to_csv(PROC / "ModelInput_Today.csv", index=False)

print("💾 Output saved:")
print(f"   • {OUT / 'Model_Batch_Output_Calibrated.csv'}")
print(f"   • {PROC / 'ModelInput_Today.csv'}")

print("\n🔥 Pipeline complete.")
print("==========================================\n")
