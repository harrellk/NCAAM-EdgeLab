import pandas as pd
from pathlib import Path

print(">>> load_kenpom STARTED (UNIFIED FINAL VERSION)")


# ----------------------------
# Normalize team names
# ----------------------------
def normalize_team(s):
    if not isinstance(s, str):
        return ""
    return (
        s.lower()
        .replace("&", "and")
        .replace(".", "")
        .replace("st ", "state ")
        .replace("'", "")
        .replace("-", " ")
        .replace("  ", " ")
        .strip()
    )


# ----------------------------
# Load CSV (standardize Team)
# ----------------------------
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"❌ Missing KP file: {path}")

    df = pd.read_csv(path)

    rename_map = {"School": "Team", "TeamName": "Team", "team": "Team", "Name": "Team"}
    for s, t in rename_map.items():
        if s in df.columns:
            df = df.rename(columns={s: t})

    if "Team" not in df.columns:
        raise ValueError(f"❌ No Team column in {path}")

    return df


# ----------------------------
# Detect summary file
# ----------------------------
def detect_index_file(folder: Path):
    candidates = sorted(folder.glob("summary*.csv"))
    if candidates:
        print(f"📘 Using {candidates[-1].name}")
        return candidates[-1]

    idx = folder / "index.csv"
    if idx.exists():
        print("📘 Using index.csv")
        return idx

    raise FileNotFoundError("❌ No summaryXX.csv or index.csv found.")


# ----------------------------
# Main loader
# ----------------------------
def load_kenpom(folder: Path) -> pd.DataFrame:
    idx_path = detect_index_file(folder)
    off_path = next(folder.glob("offense*.csv"))
    def_path = next(folder.glob("defense*.csv"))
    misc_path = next(folder.glob("misc*.csv"))
    ht_path = next(folder.glob("height*.csv"))
    hca_path = next(folder.glob("homecourt*.csv"))

    print("📂 Loading KP tables...")

    idx = load_csv(idx_path)
    off = load_csv(off_path)
    dfm = load_csv(def_path)
    misc = load_csv(misc_path)
    ht = load_csv(ht_path)
    hca = load_csv(hca_path)

    # Validate Season
    for name, df in [
        ("index", idx),
        ("offense", off),
        ("defense", dfm),
        ("misc", misc),
        ("height", ht),
    ]:
        if "Season" not in df.columns:
            raise ValueError(f"❌ Missing Season column in {name}")

    # Merge KP components
    df = (
        idx.merge(off, on=["Season", "Team"], how="left")
        .merge(dfm, on=["Season", "Team"], how="left")
        .merge(misc, on=["Season", "Team"], how="left")
        .merge(ht, on=["Season", "Team"], how="left")
    )

    # Latest season only
    latest = df["Season"].max()
    df = df[df["Season"] == latest].copy()

    # Build team_norm
    df["Team_norm"] = df["Team"].apply(normalize_team)
    hca["Team_norm"] = hca["Team"].apply(normalize_team)

    # Merge HCA
    df = df.merge(hca[["Team_norm", "HomeCourtAdv"]], on="Team_norm", how="left")

    # Clean HCA
    df["HomeCourtAdv"] = pd.to_numeric(df["HomeCourtAdv"], errors="coerce")
    df["HomeCourtAdv"].fillna(df["HomeCourtAdv"].mean(), inplace=True)

    essential = ["Team", "AdjOE", "AdjDE", "AdjEM", "AdjTempo", "HomeCourtAdv"]
    for col in essential:
        if col not in df.columns:
            raise ValueError(f"❌ Missing KP column: {col}")

    clean = df[essential].copy()

    out = Path("data/processed/kenpom")
    out.mkdir(parents=True, exist_ok=True)
    clean.to_csv(out / "kenpom_master.csv", index=False)

    print("💾 Saved → data/processed/kenpom/kenpom_master.csv")
    print(">>> load_kenpom FINISHED\n")

    return clean
