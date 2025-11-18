import numpy as np
import pandas as pd

def compute_model(df, default_hca=3.4):
    """
    Compute model projections using KenPom efficiency metrics,
    with home-court advantage and calibration applied.
    """

    # ----------------------------------------------------------
    # 1) Home-court advantage
    # ----------------------------------------------------------
    if "HomeCourtAdv_A" in df.columns:
        HCA = df["HomeCourtAdv_A"].fillna(default_hca)
    else:
        HCA = default_hca

    # ----------------------------------------------------------
    # 2) Raw model margin (positive = home stronger)
    # ----------------------------------------------------------
    raw_margin = df["AdjEM_A"] - df["AdjEM_B"] + HCA

    # ----------------------------------------------------------
    # 3) Convert to sportsbook convention before calibration
    #    Negative = home favorite
    # ----------------------------------------------------------
    df["HomeModelSpread"] = -raw_margin
    df["AwayModelSpread"] = raw_margin

    # ----------------------------------------------------------
    # 4) Raw model total
    # ----------------------------------------------------------
    tempo_factor = (df["AdjTempo_A"] + df["AdjTempo_B"]) / 2
    raw_total = (df["AdjOE_A"] + df["AdjOE_B"]) * (tempo_factor / 100)

    df["ModelTotal"] = raw_total

    # ----------------------------------------------------------
    # 5) Calibration factors
    # ----------------------------------------------------------
    SPREAD_SCALE = 1.22    # adjust later with data
    TOTAL_SCALE  = 1.08    # adjust later with data

    df["HomeModelSpread"] *= SPREAD_SCALE
    df["AwayModelSpread"] *= SPREAD_SCALE
    df["ModelTotal"]      *= TOTAL_SCALE

    # Clean rounding
    df["HomeModelSpread"] = df["HomeModelSpread"].round(2)
    df["AwayModelSpread"] = df["AwayModelSpread"].round(2)
    df["ModelTotal"]      = df["ModelTotal"].round(1)

    # ----------------------------------------------------------
    # 6) Nonlinear blowout compression
    # ----------------------------------------------------------

    def compress_spread(x, cap=18, shrink=0.50):
        """
        Compress extreme spreads to prevent unrealistic blowout margins.
        
        cap = threshold where compression starts
        shrink = percentage to compress excess margin
        """
        ax = abs(x)
        if ax <= cap:
            return x
        excess = ax - cap
        compressed = cap + excess * shrink
        return np.sign(x) * compressed

    # commented out for now due to drastically reducing the spreads of anticipated blowouts; need more data
    #df["HomeModelSpread"] = df["HomeModelSpread"].apply(compress_spread)
    #df["AwayModelSpread"] = df["AwayModelSpread"].apply(compress_spread)

    # ----------------------------------------------------------
    # 7) Win probability (using calibrated spread)
    # ----------------------------------------------------------
    # ----- WIN PROBABILITY -----
    # Use RAW (unscaled) margin, not sportsbook-style spread.
    raw_margin = df["AdjEM_A"] - df["AdjEM_B"] + HCA

    df["WinProb_A_pct"] = 100 / (1 + np.exp(-raw_margin / 6))
    df["WinProb_A_pct"] = df["WinProb_A_pct"].clip(1, 99).round(3)

    return df

