# PM_Bond_Correlation_Study

This repository contains a Python script for comparing US/Japan sovereign yields and precious metals, then visualizing and ranking their relationships.

## Script included

- `us_jp_gold_silver_compare.py`

The script compares monthly-aligned series for:

1. US 10Y bond yield
2. Japan 10Y bond yield
3. 10Y yield spread (US - Japan)
4. US 30Y bond yield
5. Japan 30Y bond yield
6. 30Y yield spread (US - Japan)
7. Cross-maturity spread (US10Y - JP30Y)
8. Cross-maturity spread (US30Y - JP10Y)
9. Gold
10. Silver

## Data sources

- **FRED** (via `pandas_datareader`)
  - US 10Y: `DGS10`
  - US 30Y: `DGS30`
  - Japan 10Y: `IRLTLT01JPM156N`
- **Stooq** (via `pandas_datareader`)
  - Japan 30Y: `30YJPY.B`
- **Yahoo Finance** (via `yfinance`)
  - Gold: `GC=F`
  - Silver: `SI=F`

## Outputs

When run, the script:

- Prints a data caveat for US 30Y discontinuity history.
- Builds a month-end aligned dataset.
- Prints the tail of the aligned DataFrame.
- Prints the correlation matrix.
- Prints top correlated and least correlated pairs.
- Saves the aligned dataset CSV.
- Saves and displays plots:
  - raw levels
  - normalized z-score overlay
  - correlation heatmap

## Environment setup

### 1) Python version

Use **Python 3.10+** (3.11 recommended).

### 2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install --upgrade pip
pip install pandas matplotlib pandas_datareader yfinance
```

## How to run

From the repository root:

```bash
python us_jp_gold_silver_compare.py
```

### Useful arguments

- `--start` (default: `2006-02-01`)
- `--end` (default: `None`, uses latest available)
- `--csv` (default: `us_jp_10y_30y_gold_silver_monthly.csv`)
- `--out-prefix` (default: `us_jp_10y_30y_gold_silver`)

Example:

```bash
python us_jp_gold_silver_compare.py \
  --start 2010-01-01 \
  --end 2024-12-31 \
  --csv outputs/monthly_dataset.csv \
  --out-prefix outputs/us_jp_study
```

## Notes and caveats

- The US 30Y FRED series (`DGS30`) has a known historical discontinuity. Starting at or after `2006-02-01` is recommended.
- The script needs internet access to download data from FRED, Stooq, and Yahoo Finance.
- If you use custom output paths (e.g., `outputs/...`), create those directories first.

## Optional: make the script executable

```bash
chmod +x us_jp_gold_silver_compare.py
./us_jp_gold_silver_compare.py --start 2015-01-01
```
