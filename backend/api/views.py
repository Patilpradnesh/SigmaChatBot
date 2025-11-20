# backend/api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
import os
import re

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/api -> backend
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
EXCEL_PATH = os.path.join(DATASET_DIR, "realestate.xlsx")  # put your file here

def load_dataset():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Dataset not found at {EXCEL_PATH}. Put the excel file there.")
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    # Normalize column names: strip and lower for comparison, but keep originals too
    df.columns = [c.strip() for c in df.columns]
    return df

# Attempt to load on import
try:
    df = load_dataset()
    load_error = None
except Exception as e:
    df = None
    load_error = str(e)


def find_location_rows(area_query):
    """Case-insensitive contains on 'final location' or sensible fallbacks."""
    if df is None:
        return pd.DataFrame()
    # prefer exact column names we've seen
    candidates = [c for c in df.columns if c.strip().lower() in ("final location", "final_location", "location", "area", "area name")]
    if candidates:
        col = candidates[0]
        return df[df[col].astype(str).str.contains(area_query, case=False, na=False)]
    # fallback: search all string columns
    str_cols = [c for c in df.columns if df[c].dtype == object]
    if not str_cols:
        return pd.DataFrame()
    mask = False
    for c in str_cols:
        mask = mask | df[c].astype(str).str.contains(area_query, case=False, na=False)
    return df[mask]


def make_json_safe_series(series):
    """Return list converting NaN -> None and numeric to native Python types."""
    out = []
    for v in series.tolist():
        if pd.isna(v):
            out.append(None)
        else:
            # convert numpy types to Python scalars
            if isinstance(v, (pd.Timestamp,)):
                out.append(str(v))
            else:
                try:
                    if isinstance(v, (float, int)):
                        out.append(float(v) if pd.notna(v) else None)
                    else:
                        out.append(v)
                except Exception:
                    out.append(v)
    return out


@api_view(["POST"])
def analyze(request):
    """
    POST JSON:
      { "query": "Analyze Wakad" }
    Response: JSON with summary, optional chart and table
    """
    if load_error:
        return Response({"error": f"Server dataset error: {load_error}"}, status=500)

    query_raw = request.data.get("query", "")
    if not isinstance(query_raw, str):
        return Response({"error": "Query must be a string"}, status=400)

    query = query_raw.strip().lower()
    if not query:
        return Response({"error": "Query cannot be empty"}, status=400)

    # --- Intent: list places ---
    if ("list" in query and ("places" in query or "locations" in query)) or query in ("list places", "list locations"):
        if df is None:
            return Response({"error": "Dataset not loaded."}, status=500)
        # try to find a sensible column for place names
        place_cols = [c for c in df.columns if c.strip().lower() in ("final location", "location", "area", "area name")]
        if place_cols:
            uniq = sorted(df[place_cols[0]].dropna().astype(str).unique().tolist())
        else:
            # fallback to first text column
            cols = [c for c in df.columns if df[c].dtype == object]
            uniq = sorted(df[cols[0]].dropna().astype(str).unique().tolist()) if cols else []
        return Response({"summary": f"Total {len(uniq)} locations found.", "places": uniq})

    # --- Intent: help / what else ---
    if "what else" in query or query in ("help", "options", "what can you do"):
        examples = [
            "Analyze Wakad",
            "List places",
            "Compare Ambegaon Budruk and Aundh",
            "Show price growth for Akurdi over last 3 years",
            "Show demand trend for Hinjewadi",
        ]
        return Response({"summary": "You can ask examples:", "examples": examples})

        # ------------------------------------------------------
    # DEMAND TREND: "show demand trend for <area>"
    # ------------------------------------------------------
    if ("demand" in query and "trend" in query) or ("show demand" in query):
        # Extract area name
        area = query
        for token in ["show", "demand", "trend", "for", "of"]:
            area = area.replace(token, "")
        area = area.strip()
        if not area:
            return Response({"error": "Cannot detect area for demand trend"}, status=400)

        rows = find_location_rows(area)
        if rows.empty:
            return Response({"error": f"No data found for {area}"}, status=404)

        # find demand-related column automatically
        demand_col = None
        priority_keywords = ["demand", "total units", "units", "supply", "launched"]

        # 1. look for exact keywords
        for col in rows.columns:
            lower = col.lower().strip()
            if any(k in lower for k in priority_keywords):
                if pd.api.types.is_numeric_dtype(rows[col]):
                    demand_col = col
                    break

        # 2. fallback: any numeric column with "total"
        if demand_col is None:
            for col in rows.columns:
                if "total" in col.lower() and pd.api.types.is_numeric_dtype(rows[col]):
                    demand_col = col
                    break

        # 3. last fallback: first numeric column
        if demand_col is None:
            for col in rows.columns:
                if pd.api.types.is_numeric_dtype(rows[col]):
                    demand_col = col
                    break

        if demand_col is None:
            return Response({"error": "No numeric demand-related column found"}, status=500)

        # Build trend
        if "year" not in rows.columns:
            return Response({"error": "Dataset missing 'year' column"}, status=500)

        ordered = rows.sort_values("year")
        trend = [
            {
                "year": int(r["year"]) if not pd.isna(r["year"]) else None,
                "value": None if pd.isna(r[demand_col]) else float(r[demand_col])
            }
            for _, r in ordered.iterrows()
        ]

        return Response({
            "summary": f"Demand trend for {area} using column '{demand_col}'.",
            "demand": trend
        })

    # --- Intent: compare X and Y ---
    if "compare" in query and " and " in query:
        parts = query.replace("compare", "").strip().split(" and ")
        if len(parts) >= 2:
            a = parts[0].strip()
            b = parts[1].strip()
            rows_a = find_location_rows(a)
            rows_b = find_location_rows(b)
            if rows_a.empty or rows_b.empty:
                return Response({"error": f"One or both locations not found: '{a}', '{b}'"}, status=404)

            # decide a numeric column for trend (prefer 'total units' or any 'total' column)
            def find_numeric_col(r):
                for candidate in ["total units", "total_units", "total units "]:
                    if candidate in r.columns:
                        return candidate
                for c in r.columns:
                    if "total" in c.lower() and pd.api.types.is_numeric_dtype(r[c]):
                        return c
                # fallback numeric column
                for c in r.columns:
                    if pd.api.types.is_numeric_dtype(r[c]):
                        return c
                return None

            col = find_numeric_col(rows_a)
            def trend(rows, col):
                if "year" in rows.columns and col in rows.columns:
                    tmp = rows.sort_values("year")[["year", col]]
                    return [{"year": int(r["year"]) if not pd.isna(r["year"]) else None,
                             "value": (None if pd.isna(r[col]) else float(r[col]))}
                            for _, r in tmp.iterrows()]
                else:
                    return rows.head(10).to_dict(orient="records")

            return Response({
                "summary": f"Comparison for '{a}' vs '{b}' (column used: {col})",
                "compare": {a: trend(rows_a, col), b: trend(rows_b, col)}
            })

    # --- Intent: show price growth for <area> over last N years ---
    if ("last" in query and "year" in query) or ("price growth" in query and "last" in query):
        m = re.search(r"last\s+(\d+)\s+year", query)
        years = int(m.group(1)) if m else 3

        # extract area by removing keywords and numbers
        area = query
        for token in ["show", "price", "growth", "for", "over", "last", "years", str(years)]:
            area = area.replace(token, "")
        area = area.strip()
        if not area:
            return Response({"error": "Could not determine area from query"}, status=400)

        rows = find_location_rows(area)
        if rows.empty:
            return Response({"error": f"No data found for {area}"}, status=404)
        if "year" not in rows.columns:
            return Response({"error": "Dataset has no 'year' column to compute last years"}, status=500)

        max_year = int(rows["year"].max())
        min_needed = max_year - years + 1
        recent = rows[rows["year"] >= min_needed].sort_values("year")

        # find a price column
        price_col = None
        for candidate in ["flat - weighted average rate", "flat weighted average rate", "price", "avg_price"]:
            if candidate in recent.columns:
                price_col = candidate
                break

        chart = {}
        if price_col:
            chart["years"] = make_json_safe_series(recent["year"])
            chart["prices"] = [None if pd.isna(x) else float(x) for x in recent[price_col].tolist()]
        else:
            chart["years"] = make_json_safe_series(recent["year"])
            chart["prices"] = [None] * len(chart["years"])

        return Response({
            "summary": f"Showing last {years} years price growth for {area}",
            "chart": chart,
            "table": recent.to_dict(orient="records")
        })

    # --- Default: Analyze <area> ---
    if query.startswith("analyze"):
        area = query.replace("analyze", "").strip()
    else:
        area = query.split()[-1]

    if not area:
        return Response({"error": "Could not determine area from query"}, status=400)

    rows = find_location_rows(area)
    if rows.empty:
        return Response({"error": f"No data found for {area}"}, status=404)

    # try to find price column
    price_col = None
    for candidate in ["flat - weighted average rate", "flat weighted average rate", "price", "avg_price"]:
        if candidate in rows.columns:
            price_col = candidate
            break

    chart = {}
    if "year" in rows.columns and price_col:
        ordered = rows.sort_values("year")
        chart = {
            "years": make_json_safe_series(ordered["year"]),
            "prices": [None if pd.isna(x) else float(x) for x in ordered[price_col].tolist()]
        }
    else:
        chart = {"years": make_json_safe_series(rows["year"]) if "year" in rows.columns else [], "prices": []}

    table = rows.to_dict(orient="records")

    return Response({
        "summary": f"Here is a quick analysis for {area}. Found {len(rows)} matching records.",
        "chart": chart,
        "table": table
    })
