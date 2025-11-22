import json
import pandas as pd
from pathlib import Path

# =========================
# Load Team Alias File
# =========================


def load_alias_map(alias_path: Path):
    if not alias_path.exists():
        return {}

    df = pd.read_csv(alias_path)
    df = df.dropna(subset=["Alias", "Team"])
    return dict(zip(df["Alias"], df["Team"]))


def normalize(name: str):
    if not isinstance(name, str):
        return ""
    return (
        name.lower()
        .replace(".", "")
        .replace("&", "and")
        .replace("(", "")
        .replace(")", "")
        .replace("'", "")
        .replace("st ", "state ")
        .replace("-", "")
        .replace(" ", "")
    )


# =========================
# DraftKings Loader
# =========================


def load_draftkings_odds(json_path, alias_path):
    """
    Loads odds, applies aliasing, and outputs clean Team_A / Team_B.
    """
    # ----------------------------
    # Load raw JSON
    # ----------------------------
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot find odds file: {json_path}")

    with open(path, "r") as f:
        data = json.load(f)

    alias_map = load_alias_map(Path(alias_path))

    rows = []

    for g in data:
        dk = next((b for b in g["bookmakers"] if b["key"] == "draftkings"), None)
        if not dk:
            continue

        spreads = next((m for m in dk["markets"] if m["key"] == "spreads"), None)
        totals = next((m for m in dk["markets"] if m["key"] == "totals"), None)
        if not spreads:
            continue

        home_raw = g["home_team"]
        away_raw = g["away_team"]

        # ------------------------------------
        # Extract BOTH team spreads properly
        # ------------------------------------
        home_mkt_spread = None
        away_mkt_spread = None

        for outcome in spreads["outcomes"]:
            team_name = outcome["name"]
            spread = outcome.get("point")

            if team_name == home_raw:
                home_mkt_spread = spread
            elif team_name == away_raw:
                away_mkt_spread = spread

        # If only one is provided (rare), infer the opposite
        if home_mkt_spread is not None and away_mkt_spread is None:
            away_mkt_spread = -home_mkt_spread

        if away_mkt_spread is not None and home_mkt_spread is None:
            home_mkt_spread = -away_mkt_spread

        # Totals
        total_point = totals["outcomes"][0]["point"] if totals else None

        # ----------------------------
        # Apply alias mapping
        # ----------------------------
        def map_team(raw):
            raw_norm = normalize(raw)
            # First try raw exact match in alias file
            for alias, canonical in alias_map.items():
                if normalize(alias) == raw_norm:
                    return canonical
            return raw  # fallback

        home_clean = map_team(home_raw)
        away_clean = map_team(away_raw)

        # These are what the model uses
        Team_A = home_clean
        Team_B = away_clean

        rows.append(
            {
                "Date": g["commence_time"][:10],
                "HomeTeam_raw": home_raw,
                "AwayTeam_raw": away_raw,
                "HomeTeam": home_clean,
                "AwayTeam": away_clean,
                "Team_A": Team_A,
                "Team_B": Team_B,
                "HomeMarketSpread": home_mkt_spread,
                "AwayMarketSpread": away_mkt_spread,
                "MarketTotal": total_point,
                # NEW — pass through neutral-site flag
                "IsNeutral": g.get("is_neutral", False),
            }
        )

    return pd.DataFrame(rows)
