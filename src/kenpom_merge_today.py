import pandas as pd

print("🏀 Starting KenPom merge and cleanup...")

# === Load all 5 KenPom component files ===
index = pd.read_csv("index.csv")
offense = pd.read_csv("offense26.csv")
defense = pd.read_csv("defense26.csv")
height = pd.read_csv("height26.csv")
misc = pd.read_csv("misc26.csv")
homecourt = pd.read_csv("homecourt.csv")

# === Clean & normalize team names ===
def clean_team(name):
    return str(name).strip().replace("&", "and").replace(".", "").replace("St", "State")

def ensure_team_column(df):
    # find the right column
    for c in df.columns:
        if "Team" in c or "Name" in c:
            df.rename(columns={c: "Team"}, inplace=True)
            break
    if "Team" not in df.columns:
        df.insert(0, "Team", "Unknown")
    df["Team"] = df["Team"].apply(clean_team)
    return df

for d in [index, offense, defense, height, misc, homecourt]:
    ensure_team_column(d)

# === Filter to most recent season if applicable ===
for d in [index, offense, defense, height, misc]:
    if "Season" in d.columns:
        latest = d["Season"].max()
        d.drop(d[d["Season"] != latest].index, inplace=True)

# === Deduplicate by team before merging ===
for d in [index, offense, defense, height, misc, homecourt]:
    d.drop_duplicates(subset=["Team"], inplace=True)

# === Merge KenPom sources safely ===
df = index.merge(offense, on="Team", how="left", suffixes=("", "_off"))
df = df.merge(defense, on="Team", how="left", suffixes=("", "_def"))
df = df.merge(height, on="Team", how="left", suffixes=("", "_ht"))
df = df.merge(misc, on="Team", how="left", suffixes=("", "_misc"))

# === Clean and merge HomeCourtAdv last ===
homecourt["HomeCourtAdv"] = pd.to_numeric(homecourt["HomeCourtAdv"], errors="coerce")
homecourt.drop_duplicates(subset=["Team"], inplace=True)
df = df.merge(homecourt[["Team", "HomeCourtAdv"]], on="Team", how="left")

# === Final numeric cleanup ===
df["HomeCourtAdv"] = pd.to_numeric(df["HomeCourtAdv"], errors="coerce")
mean_hca = df["HomeCourtAdv"].mean(skipna=True)
df["HomeCourtAdv"].fillna(mean_hca, inplace=True)

# === Derived advanced metrics ===
if "AdjOE" in df.columns and "AdjDE" in df.columns:
    df["NetEfficiency"] = df["AdjOE"] - df["AdjDE"]
if "ORPct" in df.columns and "ORPct_def" in df.columns:
    df["RebDiff"] = df["ORPct"] - df["ORPct_def"]
if "TOPct" in df.columns and "TOPct_def" in df.columns:
    df["TO_Diff"] = df["TOPct_def"] - df["TOPct"]
if "FG3Pct" in df.columns and "OppFG3Pct" in df.columns:
    df["3P_Gap"] = df["FG3Pct"] - df["OppFG3Pct"]
if "StlRate" in df.columns and "OppStlRate" in df.columns:
    df["Stl_Gap"] = df["StlRate"] - df["OppStlRate"]
if "BlockPct" in df.columns and "OppBlockPct" in df.columns:
    df["Block_Gap"] = df["BlockPct"] - df["OppBlockPct"]

# === Sanity check ===
print(f"✅ Merged {len(df)} teams, {len(df.columns)} total columns.")
print("📊 Sample HomeCourtAdv values:")
print(df[["Team", "HomeCourtAdv"]].head(10))

# === Save final file ===
df.to_csv("kenpom_team_data.csv", index=False)
print("💾 Saved as kenpom_team_data.csv")
print("🏁 Merge complete.")
