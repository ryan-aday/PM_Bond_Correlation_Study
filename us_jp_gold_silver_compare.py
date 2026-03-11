#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare:
1) US 10Y bond yield
2) Japan 10Y bond yield
3) 10Y yield spread = US 10Y - Japan 10Y
4) US 30Y bond yield
5) Japan 30Y bond yield
6) 30Y yield spread = US 30Y - Japan 30Y
7) Gold price
8) Silver price

Outputs:
- Raw monthly plot
- Normalized overlay plot
- Correlation matrix (printed and heatmap plotted)
- Top 3 most correlated relationships
- Top 3 least correlated relationships

Notes:
- US 10Y and US 30Y are fetched from FRED
- Japan 10Y is fetched from FRED
- Japan 30Y is fetched from Stooq
- Gold and silver are fetched from Yahoo Finance
- All series are aligned to month-end before comparison
"""

import argparse
import warnings

import pandas as pd
import matplotlib.pyplot as plt
from pandas_datareader import data as pdr
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)


def print_data_warnings(start: str) -> None:
    """
    Print important dataset caveats for the user.

    The US 30Y Treasury FRED series (DGS30) has a known discontinuity:
    it was discontinued for a period and later reintroduced. If the user
    requests dates before 2006-02-01, the aligned dataset may have gaps
    or fewer valid rows once all series are combined.
    """
    print("\n[Warning] Data caveat:")
    print("The FRED US 30Y Treasury yield series (DGS30) contains a historical discontinuity.")
    print("It was discontinued for a period and later reintroduced.")
    print("For this reason, dates before 2006-02-01 may produce gaps or reduce the aligned sample size.")
    print("Using --start 2006-02-01 or later is recommended for cleaner comparisons.\n")


def fetch_fred_series(series_id: str, start: str, end: str) -> pd.Series:
    """
    Fetch a time series from FRED.
    """
    s = pdr.DataReader(series_id, "fred", start, end)
    s = s.squeeze()
    s.name = series_id
    return s


def fetch_stooq_close(symbol: str, start: str, end: str) -> pd.Series:
    """
    Fetch a series from Stooq and return its Close column.

    Stooq often returns data in reverse chronological order, so we sort it.
    """
    df = pdr.DataReader(symbol, "stooq", start, end)
    if df.empty:
        raise ValueError(f"No data returned from Stooq for {symbol}")

    df = df.sort_index()
    close = df["Close"].copy()
    close.name = symbol
    return close


def fetch_yahoo_close(ticker: str, start: str, end: str) -> pd.Series:
    """
    Fetch a Yahoo Finance ticker and return the Close column.
    """
    df = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df.empty:
        raise ValueError(f"No data returned for ticker {ticker}")

    # Handle possible MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        close = df["Close"].iloc[:, 0]
    else:
        close = df["Close"]

    close.name = ticker
    return close


def to_month_end(series: pd.Series, method: str = "last") -> pd.Series:
    """
    Convert a time series to month-end frequency.

    Parameters
    ----------
    series : pd.Series
        Input time series
    method : str
        'last' to use the last value in each month
        'mean' to use the monthly average
    """
    s = series.dropna().copy()

    if method == "last":
        return s.resample("ME").last()
    elif method == "mean":
        return s.resample("ME").mean()
    else:
        raise ValueError("method must be 'last' or 'mean'")


def zscore_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize each column to z-scores for cross-series comparison.
    """
    return (df - df.mean()) / df.std(ddof=0)


def print_top_bottom_correlations(corr: pd.DataFrame, top_n: int = 3) -> None:
    """
    Print the top N most and least correlated unique pairwise relationships.

    Self-correlations are excluded, and duplicate pairs are avoided.
    """
    pairs = []
    cols = corr.columns.tolist()

    # Build a list of unique upper-triangle correlation pairs
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], corr.iloc[i, j]))

    corr_pairs = pd.DataFrame(pairs, columns=["Series_1", "Series_2", "Correlation"])

    # Highest positive correlations
    most_corr = corr_pairs.sort_values("Correlation", ascending=False).head(top_n)

    # Lowest correlations (most negative / weakest)
    least_corr = corr_pairs.sort_values("Correlation", ascending=True).head(top_n)

    print(f"\nTop {top_n} most correlated relationships:")
    for _, row in most_corr.iterrows():
        print(f"{row['Series_1']} vs {row['Series_2']}: {row['Correlation']:.3f}")

    print(f"\nTop {top_n} least correlated relationships:")
    for _, row in least_corr.iterrows():
        print(f"{row['Series_1']} vs {row['Series_2']}: {row['Correlation']:.3f}")


def build_dataset(start: str, end: str) -> pd.DataFrame:
    """
    Build the aligned monthly comparison dataset.

    The final DataFrame includes:
    - US and Japan 10Y yields
    - 10Y yield spread
    - US and Japan 30Y yields
    - 30Y yield spread
    - Cross-maturity US/JP spreads
    - Gold and silver prices
    """
    # -----------------------------
    # Fetch 10Y bond yield series
    # -----------------------------
    us10 = fetch_fred_series("DGS10", start, end)
    jp10 = fetch_fred_series("IRLTLT01JPM156N", start, end)

    # -----------------------------
    # Fetch 30Y bond yield series
    # -----------------------------
    us30 = fetch_fred_series("DGS30", start, end)

    # Japan 30Y is pulled from Stooq
    # If the Stooq symbol changes in the future, replace it here
    jp30 = fetch_stooq_close("30YJPY.B", start, end)

    # -----------------------------
    # Fetch metals
    # -----------------------------
    gold = fetch_yahoo_close("GC=F", start, end)
    silver = fetch_yahoo_close("SI=F", start, end)

    # -----------------------------
    # Resample all series to month-end
    # -----------------------------
    us10_m = to_month_end(us10, method="last")
    jp10_m = to_month_end(jp10, method="last")
    us30_m = to_month_end(us30, method="last")
    jp30_m = to_month_end(jp30, method="last")
    gold_m = to_month_end(gold, method="last")
    silver_m = to_month_end(silver, method="last")

    # -----------------------------
    # Combine into one DataFrame
    # -----------------------------
    df = pd.concat(
        [
            us10_m.rename("US_10Y_Yield"),
            jp10_m.rename("JP_10Y_Yield"),
            us30_m.rename("US_30Y_Yield"),
            jp30_m.rename("JP_30Y_Yield"),
            gold_m.rename("Gold"),
            silver_m.rename("Silver"),
        ],
        axis=1,
    )

    # -----------------------------
    # Compute yield spreads
    # -----------------------------
    df["Yield_Diff_10Y_US_minus_JP"] = df["US_10Y_Yield"] - df["JP_10Y_Yield"]
    df["Yield_Diff_30Y_US_minus_JP"] = df["US_30Y_Yield"] - df["JP_30Y_Yield"]

    # Cross-maturity spreads
    df["Yield_Diff_US10Y_minus_JP30Y"] = df["US_10Y_Yield"] - df["JP_30Y_Yield"]
    df["Yield_Diff_US30Y_minus_JP10Y"] = df["US_30Y_Yield"] - df["JP_10Y_Yield"]

    # Drop rows where any required value is missing
    df = df.dropna()

    # Reorder columns for cleaner output
    df = df[
        [
            "US_10Y_Yield",
            "JP_10Y_Yield",
            "Yield_Diff_10Y_US_minus_JP",
            "US_30Y_Yield",
            "JP_30Y_Yield",
            "Yield_Diff_30Y_US_minus_JP",
            "Yield_Diff_US10Y_minus_JP30Y",
            "Yield_Diff_US30Y_minus_JP10Y",
            "Gold",
            "Silver",
        ]
    ]

    return df


def plot_raw_levels(df: pd.DataFrame, out_prefix: str | None = None) -> None:
    """
    Plot raw monthly levels.

    Separate subplots are used because yields/spreads and metals are on different scales.
    """
    fig, axes = plt.subplots(4, 1, figsize=(15, 16), sharex=True)

    # 10Y yields and spread
    ax1 = axes[0]
    ax1.plot(df.index, df["US_10Y_Yield"], label="US 10Y Yield")
    ax1.plot(df.index, df["JP_10Y_Yield"], label="Japan 10Y Yield")
    ax1.plot(df.index, df["Yield_Diff_10Y_US_minus_JP"], label="10Y Diff (US-JP)")
    ax1.set_title("10Y Bond Yields and Spread")
    ax1.set_ylabel("Percent")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 30Y yields and spread
    ax2 = axes[1]
    ax2.plot(df.index, df["US_30Y_Yield"], label="US 30Y Yield")
    ax2.plot(df.index, df["JP_30Y_Yield"], label="Japan 30Y Yield")
    ax2.plot(df.index, df["Yield_Diff_30Y_US_minus_JP"], label="30Y Diff (US-JP)")
    ax2.set_title("30Y Bond Yields and Spread")
    ax2.set_ylabel("Percent")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Cross-maturity spreads
    ax3 = axes[2]
    ax3.plot(df.index, df["Yield_Diff_US10Y_minus_JP30Y"], label="US10Y - JP30Y")
    ax3.plot(df.index, df["Yield_Diff_US30Y_minus_JP10Y"], label="US30Y - JP10Y")
    ax3.set_title("Cross-Maturity US/Japan Yield Spreads")
    ax3.set_ylabel("Percent")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # Gold and silver
    ax4 = axes[3]
    ax4.plot(df.index, df["Gold"], label="Gold")
    ax4.plot(df.index, df["Silver"], label="Silver")
    ax4.set_title("Gold and Silver Prices")
    ax4.set_ylabel("Price (USD)")
    ax4.set_xlabel("Date")
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    plt.tight_layout()

    if out_prefix:
        fig.savefig(f"{out_prefix}_raw_levels.png", dpi=200, bbox_inches="tight")

    plt.show()


def plot_normalized_overlay(df: pd.DataFrame, out_prefix: str | None = None) -> None:
    """
    Plot all series on a normalized z-score basis so they can be visually compared.
    """
    zdf = zscore_df(df)

    fig, ax = plt.subplots(figsize=(15, 8))
    for col in zdf.columns:
        ax.plot(zdf.index, zdf[col], label=col)

    ax.set_title("Normalized Comparison of All 10 Series (Z-scores)")
    ax.set_ylabel("Z-score")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=2)
    plt.tight_layout()

    if out_prefix:
        fig.savefig(f"{out_prefix}_normalized_overlay.png", dpi=200, bbox_inches="tight")

    plt.show()


def plot_correlation_heatmap(corr: pd.DataFrame, out_prefix: str | None = None) -> None:
    """
    Plot the correlation matrix as a heatmap with annotations.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr.values, aspect="auto")

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)
    ax.set_title("Correlation Matrix")

    # Write correlation values inside each cell
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")

    plt.colorbar(im, ax=ax)
    plt.tight_layout()

    if out_prefix:
        fig.savefig(f"{out_prefix}_correlation_heatmap.png", dpi=200, bbox_inches="tight")

    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start",
        type=str,
        default="2006-02-01",
        help="Start date for the analysis. Default is 2006-02-01 to avoid the US 30Y discontinuity issue.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Optional end date for the analysis.",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="us_jp_10y_30y_gold_silver_monthly.csv",
        help="Output CSV file for the aligned monthly dataset.",
    )
    parser.add_argument(
        "--out-prefix",
        type=str,
        default="us_jp_10y_30y_gold_silver",
        help="Prefix used when saving plot images.",
    )
    args = parser.parse_args()

    # Print important data caveats before processing
    print_data_warnings(args.start)

    # Build the aligned dataset
    df = build_dataset(args.start, args.end)

    # Compute correlation matrix
    corr = df.corr(numeric_only=True)

    # Print recent rows
    print("\nAligned monthly dataset (tail):")
    print(df.tail(10))

    # Print correlation matrix
    print("\nCorrelation matrix:")
    print(corr.round(3))

    # Print strongest and weakest pairwise relationships
    print_top_bottom_correlations(corr, top_n=10)

    # Save aligned dataset
    df.to_csv(args.csv, index=True)
    print(f"\nSaved aligned dataset to: {args.csv}")

    # Generate plots
    plot_raw_levels(df, out_prefix=args.out_prefix)
    plot_normalized_overlay(df, out_prefix=args.out_prefix)
    plot_correlation_heatmap(corr, out_prefix=args.out_prefix)


if __name__ == "__main__":
    main()
