import pandas as pd
from utils import normalize


def apply_alias_mapping(df, alias_file):
    aliases = pd.read_csv(alias_file)

    aliases["Alias_norm"] = aliases["Alias"].apply(normalize)
    aliases["Team_norm"] = aliases["Team"].apply(normalize)

    alias_map = dict(zip(aliases["Alias_norm"], aliases["Team"]))
    direct_map = dict(zip(aliases["Team_norm"], aliases["Team"]))

    def resolve(name):
        n = normalize(name)
        return alias_map.get(n, direct_map.get(n, name))

    df["HomeTeam"] = df["HomeTeam_raw"].apply(resolve)
    df["AwayTeam"] = df["AwayTeam_raw"].apply(resolve)

    return df
