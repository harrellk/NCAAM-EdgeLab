import sys
import pandas as pd
from pathlib import Path
from utils import normalize
from fetch_odds import load_draftkings_odds  # <-- correct loader

# Add project /src folder to import path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# ============================================================
# CONFIG
# ============================================================

ODDS_FILE = Path("data/raw/daily_odds.json")
ALIAS_FILE = Path("data/mappings/team_aliases.csv")
KP_FILE = Path("data/processed/kenpom/kenpom_master.csv")


# ============================================================
# LOADER HELPERS
# ============================================================


def load_aliases(path: Path) -> dict:
    print(f"📂 Loading alias file → {path}")
    df = pd.read_csv(path)
    df["Alias_norm"] = df["Alias"].apply(normalize)
    df["Team_norm"] = df["Team"].apply(normalize)
    alias_map = dict(zip(df["Alias_norm"], df["Team"]))
    print(f"   Loaded {len(alias_map)} alias mappings")
    return alias_map


def load_kenpom(path: Path) -> pd.DataFrame:
    print(f"📘 Loading KenPom master → {path}")
    df = pd.read_csv(path)
    df["Team_norm"] = df["Team"].apply(normalize)
    print(f"   Loaded {len(df)} KP teams")
    return df


# ============================================================
# MAIN CHECK
# ============================================================


def run_check():
    # ---------------------------------------------------------
    # 1. Load DK odds *with your official loader*
    # ---------------------------------------------------------
    print(f"📂 Loading DK odds → {ODDS_FILE}")
    odds = load_draftkings_odds(ODDS_FILE, ALIAS_FILE)

    print(f"   Loaded {len(odds)} processed matchups")
    print("   Columns:", odds.columns.tolist())

    # Ensure expected processed columns exist
    required = {"HomeTeam", "AwayTeam"}
    if not required.issubset(odds.columns):
        raise ValueError(
            f"ERROR: Expected columns {required}, but found {set(odds.columns)}.\n"
            f"Looks like raw JSON was loaded instead of processed DK odds."
        )

    # ---------------------------------------------------------
    # 2. Load alias + KenPom
    # ---------------------------------------------------------
    alias_map = load_aliases(ALIAS_FILE)
    kp = load_kenpom(KP_FILE)

    # ---------------------------------------------------------
    # 3. Normalize names from DK
    # ---------------------------------------------------------
    odds["Home_norm"] = odds["HomeTeam"].apply(normalize)
    odds["Away_norm"] = odds["AwayTeam"].apply(normalize)

    # ---------------------------------------------------------
    # 4. Resolve each team using alias → direct KP match
    # ---------------------------------------------------------
    def resolve(norm_name: str):
        # Alias match?
        if norm_name in alias_map:
            return alias_map[norm_name]

        # Direct KenPom match?
        match = kp[kp["Team_norm"] == norm_name]
        if len(match) == 1:
            return match["Team"].values[0]

        # No match found
        return None

    odds["Home_resolved"] = odds["Home_norm"].apply(resolve)
    odds["Away_resolved"] = odds["Away_norm"].apply(resolve)

    # ---------------------------------------------------------
    # 5. Detect unmatched teams
    # ---------------------------------------------------------
    unmatched = odds[odds["Home_resolved"].isna() | odds["Away_resolved"].isna()]

    if len(unmatched):
        print("\n❌ UNMATCHED TEAMS FOUND:")
        print(
            unmatched[
                [
                    "HomeTeam",
                    "AwayTeam",
                    "Home_norm",
                    "Away_norm",
                    "Home_resolved",
                    "Away_resolved",
                ]
            ].to_string(index=False)
        )

        unmatched.to_csv("output/diagnostics_unmatched.csv", index=False)
        print("❌ Saved → output/diagnostics_unmatched.csv")

    else:
        print("\n✅ All teams successfully mapped to KenPom!")

    # ---------------------------------------------------------
    # 6. Save full audit report
    # ---------------------------------------------------------
    audit_cols = [
        "HomeTeam",
        "AwayTeam",
        "Home_norm",
        "Away_norm",
        "Home_resolved",
        "Away_resolved",
    ]

    audit_path = Path("output/diagnostics_team_mapping_audit.csv")
    odds[audit_cols].to_csv(audit_path, index=False)
    print(f"\n💾 Audit saved → {audit_path}")


if __name__ == "__main__":
    run_check()
