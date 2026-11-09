"""Pencarian koin untuk ChainScope ID."""

import pandas as pd

POPULAR_COIN_IDS = (
    "bitcoin",
    "ethereum",
    "tether",
    "binancecoin",
    "solana",
    "ripple",
    "usd-coin",
    "dogecoin",
    "tron",
    "cardano",
)


def filter_coins(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter DataFrame koin berdasarkan kata kunci.

    Pencarian case-insensitive pada kolom `name`, `symbol`, dan `id`.
    - Query kosong / whitespace → kembalikan DataFrame asli.
    - Query dengan beberapa kata → semua kata harus cocok (AND).
    - Jika kolom `name`/`symbol` tidak ada, kembalikan DataFrame asli.
    """
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()

    if query is None:
        return df

    q = str(query).strip().lower()
    if not q:
        return df

    searchable_columns = [
        column for column in ("name", "symbol", "id") if column in df.columns
    ]
    if not searchable_columns:
        return df

    tokens = [t for t in q.split() if t]
    if not tokens:
        return df

    columns = {
        column: df[column].astype(str).str.lower()
        for column in searchable_columns
    }

    mask = pd.Series([True] * len(df), index=df.index)
    for token in tokens:
        token_mask = pd.Series([False] * len(df), index=df.index)
        for values in columns.values():
            token_mask = token_mask | values.str.contains(token, regex=False)
        mask = mask & token_mask

    return df[mask]


def coin_selector_options(
    df: pd.DataFrame,
    query: str,
    *,
    selected_ids: tuple[str, ...] | list[str] = (),
    limit: int = 50,
) -> list[str]:
    """Return bounded, relevant coin IDs for high-cardinality selectors."""
    if limit < 1:
        raise ValueError("Batas hasil pencarian harus lebih besar dari nol.")
    if df is None or df.empty or "id" not in df.columns:
        return []

    catalog = df.drop_duplicates("id", keep="first").copy()
    catalog["id"] = catalog["id"].astype(str)
    available_ids = set(catalog["id"])
    selected = list(dict.fromkeys(
        str(coin_id) for coin_id in selected_ids if str(coin_id) in available_ids
    ))
    normalized_query = str(query or "").strip().casefold()

    if not normalized_query:
        popular = [coin_id for coin_id in POPULAR_COIN_IDS if coin_id in available_ids]
        remaining = catalog.loc[~catalog["id"].isin(popular)]
        if "label" in remaining.columns:
            remaining = remaining.sort_values("label", key=lambda values: values.str.casefold())
        candidates = popular + remaining["id"].tolist()
    else:
        matches = filter_coins(catalog, normalized_query)
        if matches.empty:
            candidates = []
        else:
            query = normalized_query
            ids = matches["id"].astype(str).str.casefold()
            symbols = (
                matches["symbol"].astype(str).str.casefold()
                if "symbol" in matches.columns
                else pd.Series("", index=matches.index)
            )
            names = (
                matches["name"].astype(str).str.casefold()
                if "name" in matches.columns
                else pd.Series("", index=matches.index)
            )
            labels = (
                matches["label"].astype(str).str.casefold()
                if "label" in matches.columns
                else names
            )
            exact_rank = pd.Series(3, index=matches.index)
            exact_rank = exact_rank.mask(names == query, 2)
            exact_rank = exact_rank.mask(symbols == query, 1)
            exact_rank = exact_rank.mask(ids == query, 0)
            prefix_rank = (
                (~ids.str.startswith(query)).astype(int)
                + (~symbols.str.startswith(query)).astype(int)
                + (~names.str.startswith(query)).astype(int)
            )
            ranked = matches.assign(
                _exact_rank=exact_rank,
                _prefix_rank=prefix_rank,
                _label=labels,
            ).sort_values(
                ["_exact_rank", "_prefix_rank", "_label"], kind="stable"
            )
            candidates = ranked["id"].tolist()

    ordered = list(dict.fromkeys(selected + candidates))
    return ordered[:max(limit, len(selected))]