import pandas as pd

noc = pd.read_csv("./data/noc_regions.csv")

FOLD_MAP = {
    # Germany family
    "EUA": "GER",  # United Team of Germany (1956/60/64)
    # Russia / USSR variants
    "EUN": "RUS",  # Unified Team (1992)
    "ROC": "RUS",  # Russian Olympic Committee (2020)
    "EUN": "RUS",
    # Australasia (AUS+NZ combined)
    "ANZ": "AUS",
    # Yugoslavia
    "YUG": "SRB",
    "SCG": "SRB",  # Serbia and Montenegro (2003–06)
    # Czechoslovakia
    "TCH": "CZE",
    # Mixed / neutral / refugees — drop these from country totals
    "ZZX": None,  # Mixed team
    "IOA": None,  # Independent Olympic Athletes (various years)
    "ROT": None,  # Refugee Olympic Team (2016)
    "EOR": None,  # Refugee Olympic Team (2020)
    # Other
    "SGP": "SIN",
    "TUV": "TUV",
}


def normalize_noc(
    df, noc_regions, fold_map=FOLD_MAP, attach_country=True, drop_none=True
):
    """
    df: athlete_events DataFrame
    noc_regions: DataFrame with columns ["NOC", "region"] from noc_regions.csv
    fold_map: dict mapping old/odd NOCs -> modern NOC or None (drop)
    attach_country: if True, add a 'Country' column from noc_regions (post-fold)
    drop_none: drop rows whose folded NOC is None (Mixed, Refugees, etc.)
    """
    out = df.copy()
    out["NOC_folded"] = out["NOC"].map(fold_map).fillna(out["NOC"])

    if drop_none:
        out = out[out["NOC_folded"].notna()]

    if attach_country:
        # build a lookup AFTER folding
        # if multiple original NOCs fold to one, dedupe mapping by the folded key
        base_map = noc_regions[["NOC", "region"]].drop_duplicates()
        # use the *folded* code to join to country name via another map step
        name_map = dict(zip(base_map["NOC"], base_map["region"]))
        out["Country"] = out["NOC_folded"].map(name_map)

    # warn about any codes we still don’t have a name for
    if attach_country:
        unknown = out.loc[out["Country"].isna(), "NOC_folded"].dropna().unique()
        if len(unknown):
            print(
                "⚠️ Unmapped NOCs (add to FOLD_MAP or noc_regions):",
                sorted(unknown.tolist()),
            )

    return out
