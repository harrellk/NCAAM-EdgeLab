#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

# === Core imports (modular architecture) ===
from fetch_odds import load_draftkings_odds
from load_kenpom import load_kenpom
from compute_model import compute_model
from generate_edges import convert_lines
from utils import normalize

print("\n==========================================")
print("🏀 NCAAM EdgeLab — Daily Pipeline (MODULAR)")
print("==========================================\n")

# === Directory structure ===
BASE = Path(__file__).resolve().parents[1]

RAW   = BASE / "data" / "raw"
PROC  = BASE / "data" / "processed"
MAP   = BASE / "data" / "mappings"
OUT   = BASE / "output" / "model"

ODDS_FILE  = RAW / "daily_odds.json"
ALIAS_FILE = MAP / "team_aliases.csv"
KP_DIR     = RAW


# =====================================================================
# STEP 1 — Load DraftKings Odds
# =====================================================================
print("📡 Loading DraftKings odds...")
odds = load_draftkings_odds(ODDS_FILE, ALIAS_FILE)

print(f"✔ Loaded {len(odds)} matchups.\n")


# =====================================================================
# STEP 2 — Load KenPom Master
# =====================================================================
print("📘 Loading KenPom master table...")
kp = load_kenpom(KP_DIR)

# Canonical normalization
kp["Team_norm"] = kp["Team"].apply(normalize)

print(f"✔ KP teams loaded: {len(kp)}\n")


# =====================================================================
# STEP 3 — Merge Odds ↔ KP (Home and Away)
# =====================================================================
print("🔗 Merging DraftKings odds with KenPom data...")

# Normalize odds team names using same canonical function
odds["Home_norm"] = odds["HomeTeam"].apply(normalize)
odds["Away_norm"] = odds["AwayTeam"].apply(normalize)

# Create lookup table
kp_lookup = kp.set_index("Team_norm")

# Validate every team is recognized
missing_home = odds[~ odds["Home_norm"].isin(kp_lookup.index)]
missing_away = odds[~ odds["Away_norm"].isin(kp_lookup.index)]

if len(missing_home) or len(missing_away):
    print("\n❌ Unmatched teams found!")
    if len(missing_home):
        print("❌ HOME TEAM MISMATCHES:\n", missing_home)
    if len(missing_away):
        print("❌ AWAY TEAM MISMATCHES:\n", missing_away)
    raise SystemExit("\n❌ Fix alias mappings (team_aliases.csv) and rerun.\n")

print("✔ All teams matched successfully.\n")


# Attach KP advanced metrics for A (home) and B (away)
kp_cols = ["Team", "AdjOE", "AdjDE", "AdjEM", "AdjTempo", "HomeCourtAdv"]

for col in kp_cols:
    odds[f"{col}_A"] = odds["Home_norm"].map(kp_lookup[col])
    odds[f"{col}_B"] = odds["Away_norm"].map(kp_lookup[col])

merged = odds.drop(columns=["Home_norm", "Away_norm"])

print("✔ Odds + KP merge complete.\n")


# =====================================================================
# STEP 4 — Apply the Model (compute_model)
# =====================================================================
print("🧠 Applying compute_model() calibration and projections...")

merged = compute_model(merged)

print("✔ Model spreads, totals, and win probabilities generated.\n")


# =====================================================================
# STEP 5 — Compute Edges (convert_lines)
# =====================================================================
print("📊 Evaluating edges (spread + totals)...")

final = convert_lines(merged)

print("✔ Edge evaluation complete.\n")


# =====================================================================
# STEP 6 — Save Results
# =====================================================================
OUT.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

final.to_csv(OUT / "Model_Batch_Output_Calibrated.csv", index=False)
merged.to_csv(PROC / "ModelInput_Today.csv", index=False)

print("💾 Output saved:")
print(f"   • {OUT/'Model_Batch_Output_Calibrated.csv'}")
print(f"   • {PROC/'ModelInput_Today.csv'}")

print("\n🔥 Pipeline complete.")
print("==========================================\n")

