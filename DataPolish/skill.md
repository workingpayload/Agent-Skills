---
name: datapolish
description: Cleans, normalizes, and validates raw datasets using pandas, polars, or Great Expectations. Profiles data quality, removes duplicates, coerces types, imputes nulls, and produces a quality report. Use when a user asks to clean data, fix data quality issues, or prepare data for analysis.
---

# DataPolish

## Overview

Transform raw, dirty data into analysis-ready datasets through a repeatable pipeline: profile → deduplicate → type-coerce → null-handle → validate → report. Always preserve the original data; write cleaned output to a new file or table.

## Workflow

### 1. Profile the Raw Data

Run profiling before touching anything. This reveals what cleaning is actually needed.

```python
import pandas as pd
df = pd.read_csv("raw.csv")
print(df.shape, df.dtypes, df.isnull().sum(), df.describe(include="all"), df.duplicated().sum())
# polars: df.schema, df.null_count(), df.describe()
# Full HTML report: ProfileReport(df).to_file("profile.html")  # ydata-profiling
```

For files >2 GB, switch to polars (`pl.read_csv`) or DuckDB (`duckdb.sql("SELECT ... FROM 'raw.csv'")`) for out-of-core processing, or use pandas `chunksize`: `pd.read_csv("raw.csv", chunksize=100_000)` and process iteratively.

Record: row count, null rates per column, duplicate count, cardinality of categoricals, min/max/mean of numerics.

### 2. Deduplicate

```python
# Exact duplicates
df = df.drop_duplicates()

# Business-key deduplication (keep most recent record)
df = (df.sort_values("updated_at", ascending=False)
        .drop_duplicates(subset=["customer_id"])
        .reset_index(drop=True))
```

Before deduplicating on a business key, validate it is actually unique in the source: `assert df["customer_id"].notna().all()`. Silently deduplicating on a key that contains nulls will collapse unrelated records.

Log how many rows were removed. If >5% of rows are duplicates, flag this to the user — it may indicate an upstream ingestion bug.

### 3. Coerce Types

Never trust inferred types from CSV. Cast explicitly:

```python
# pandas
df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["status"] = df["status"].astype("category")
df["user_id"] = df["user_id"].astype("Int64")  # nullable integer
```

After casting, re-check `df.isnull().sum()` — coercion errors produce new nulls (`errors="coerce"` silently nullifies unparseable values).

### 4. Handle Nulls

Choose a strategy per column based on domain knowledge:

| Strategy | When to use | Code |
|----------|-------------|------|
| Drop rows | Null in a required key field | `df.dropna(subset=["id"])` |
| Median imputation | Numeric, skewed distribution | `df["age"].fillna(df["age"].median())` |
| Mean imputation | Numeric, normal distribution | `df["score"].fillna(df["score"].mean())` |
| Mode imputation | Categorical | `df["city"].fillna(df["city"].mode()[0])` |
| Forward fill | Time series, ordered data | `df["price"].ffill(limit=N)` — set `limit` to cap how many consecutive gaps to fill; unbounded `ffill()` on sparse series can propagate stale values across long gaps |
| Sentinel value | Categorical "unknown" is meaningful | `df["country"].fillna("UNKNOWN")` |
| Flag + impute | Want to preserve missingness signal | add `df["age_was_null"] = df["age"].isnull()` then impute |

Never impute primary keys, foreign keys, or timestamps used for deduplication.

### 5. Standardize Text and Categoricals

```python
# Strip whitespace and normalize case
df["email"] = df["email"].str.strip().str.lower()
df["country_code"] = df["country_code"].str.upper().str.strip()

# Normalize inconsistent categoricals
status_map = {"active": "ACTIVE", "Active": "ACTIVE", "1": "ACTIVE",
              "inactive": "INACTIVE", "0": "INACTIVE"}
df["status"] = df["status"].map(status_map).fillna("UNKNOWN")
```

### 6. Validate with Great Expectations

```python
import great_expectations as gx

context = gx.get_context()
validator = context.sources.pandas_default.read_dataframe(df)

validator.expect_column_values_to_not_be_null("customer_id")
validator.expect_column_values_to_be_between("amount", min_value=0)
validator.expect_column_values_to_match_regex("email", r"^[^@]+@[^@]+\.[^@]+$")
validator.expect_column_values_to_be_in_set("status", ["ACTIVE", "INACTIVE", "UNKNOWN"])

results = validator.validate()
print(results["success"])  # False if any expectation fails
```

### 7. Write Output and Quality Report

```python
df.to_csv("cleaned.csv", index=False)
# or for parquet (preferred for large datasets):
df.to_parquet("cleaned.parquet", index=False)
```

## Output Format

Produce a quality report as a markdown summary:

```
## Data Quality Report

| Metric               | Before  | After   |
|----------------------|---------|---------|
| Row count            | 10,482  | 9,971   |
| Duplicate rows       | 511     | 0       |
| Null rate (amount)   | 8.3%    | 0%      |
| Null rate (email)    | 2.1%    | 2.1%*   |
| Type errors (date)   | 47      | 0       |

*Email nulls retained — legitimate opt-out records.

Imputation applied: amount → median (92.4), age → median (34)
Validation: 4/4 Great Expectations checks passed
Output: cleaned.parquet (9,971 rows × 14 columns)
```

## Edge Cases

**Mixed datetime formats in one column**: `pd.to_datetime` with `infer_datetime_format=True` handles many cases, but silently misparses ambiguous dates like `01/02/03`. Use `dayfirst` and `yearfirst` params explicitly, or parse with multiple `format` attempts in a try/except loop.

**High-cardinality categoricals with typos**: For fields like `city_name` with thousands of unique values, use fuzzy matching (`thefuzz` / `rapidfuzz`) with a known reference list rather than a manual map.

**Personally Identifiable Information (PII)**: Before profiling or reporting, check for columns containing SSNs, credit card numbers, or health data. Mask or hash PII before writing reports: `df["ssn"] = df["ssn"].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest())`.
