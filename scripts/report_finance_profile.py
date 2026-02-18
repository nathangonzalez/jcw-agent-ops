#!/usr/bin/env python
"""
Generate a markdown finance profile report from finance_raw.sqlite.
"""

import argparse
import sqlite3
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to finance_raw.sqlite")
    parser.add_argument("--out", required=True, help="Output markdown path")
    parser.add_argument("--threshold", type=float, default=10000.0, help="Outlier threshold")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_path = Path(args.out)

    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM raw_transactions", conn)
    conn.close()

    if df.empty:
        out_path.write_text("# Finance Profile Report\n\nNo rows found.\n", encoding="utf-8")
        return

    # Standardize likely field names
    vendor_col = "vendor" if "vendor" in df.columns else None
    category_col = "category" if "category" in df.columns else None
    vendor_norm_col = "vendor_norm" if "vendor_norm" in df.columns else None
    category_norm_col = "category_norm" if "category_norm" in df.columns else None
    amount_col = "amount" if "amount" in df.columns else None

    md = []
    md.append("# Finance Profile Report")
    md.append("")
    md.append(f"**Database:** `{db_path}`")
    md.append("")

    # Top vendors
    md.append("## Top Vendors")
    if vendor_norm_col or vendor_col:
        col = vendor_norm_col or vendor_col
        vendors = df[col].value_counts().head(10)
        md.append("| Vendor | Count |")
        md.append("|--|--|")
        for v, cnt in vendors.items():
            md.append(f"| {v} | {cnt} |")
    else:
        md.append("_No vendor column found._")
    md.append("")

    # Top categories
    md.append("## Top Categories")
    if category_norm_col or category_col:
        col = category_norm_col or category_col
        cats = df[col].value_counts().head(10)
        md.append("| Category | Count |")
        md.append("|--|--|")
        for c, cnt in cats.items():
            md.append(f"| {c} | {cnt} |")
    else:
        md.append("_No category column found._")
    md.append("")

    # Largest debits/credits
    if amount_col:
        debits = df[df[amount_col] < 0].nsmallest(5, amount_col)
        credits = df[df[amount_col] > 0].nlargest(5, amount_col)

        md.append("## Largest Debits")
        if not debits.empty:
            md.append("| Date | Vendor | Amount |")
            md.append("|--|--|--|")
            for _, tx in debits.iterrows():
                md.append(f"| {tx.get('date','')} | {tx.get(vendor_col,'')} | {tx.get(amount_col,0):,.2f} |")
        else:
            md.append("_No debit transactions found._")
        md.append("")

        md.append("## Largest Credits")
        if not credits.empty:
            md.append("| Date | Vendor | Amount |")
            md.append("|--|--|--|")
            for _, tx in credits.iterrows():
                md.append(f"| {tx.get('date','')} | {tx.get(vendor_col,'')} | {tx.get(amount_col,0):,.2f} |")
        else:
            md.append("_No credit transactions found._")
        md.append("")

        # Outliers
        outliers = df[df[amount_col].abs() > args.threshold]
        md.append(f"## Outliers (>{args.threshold:,.0f})")
        if not outliers.empty:
            md.append("| Date | Vendor | Amount |")
            md.append("|--|--|--|")
            for _, tx in outliers.iterrows():
                md.append(f"| {tx.get('date','')} | {tx.get(vendor_col,'')} | {tx.get(amount_col,0):,.2f} |")
        else:
            md.append("_No outliers found._")
        md.append("")

    # Missing fields
    md.append("## Missing Fields")
    missing = df[df.isnull().any(axis=1)]
    md.append(f"Rows with missing fields: {len(missing)}")

    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote report: {out_path}")


if __name__ == "__main__":
    main()
