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
    # Normalize column names: strip whitespace (but keep original case)
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
    # prefer known place columns
    candidates = [c for c in df.columns if c.strip().lower() in ("final location", "final_location", "location", "area", "area name", "area_name")]
    if candidates:
        col = candidates[0]
        return df[df[col].astype(str).str.contains(area_query, case=False, na=False)]
    # fallback: search all object (string) columns
    str_cols = [c for c in df.columns if df[c].dtype == object]
    if not str_cols:
        return pd.DataFrame()
    mask = pd.Series(False, index=df.index)
    for c in str_cols:
        mask = mask | df[c].astype(str).str.contains(area_query, case=False, na=False)
    return df[mask]


def make_json_safe_series(series):
    """Return list converting NaN -> None and numpy types to native Python types."""
    out = []
    for v in series.tolist():
        if pd.isna(v):
            out.append(None)
        else:
            # timestamps -> string; numpy numbers -> Python float
            if isinstance(v, (pd.Timestamp,)):
                out.append(str(v))
            else:
                try:
                    if isinstance(v, (float, int)):
                        out.append(float(v))
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
    Response: JSON with summary, optional chart, table, compare, demand, etc.
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
        place_cols = [c for c in df.columns if c.strip().lower() in ("final location", "location", "area", "area name")]
        if place_cols:
            uniq = sorted(df[place_cols[0]].dropna().astype(str).unique().tolist())
        else:
            cols = [c for c in df.columns if df[c].dtype == object]
            uniq = sorted(df[cols[0]].dropna().astype(str).unique().tolist()) if cols else []
        return Response({"summary": f"Total {len(uniq)} locations found.", "places": uniq})

    # --- Intent: help / what else ---
    if "what else" in query or query in ("help", "options", "what can you do"):
        examples = [
            "Analyze Wakad",
            "List places",
            "Compare Ambegaon Budruk and Aundh",
            "Compare Wakad and Hinjewadi demand",
            "Show price growth for Akurdi over last 3 years",
            "Show demand trend for Hinjewadi",
        ]
        return Response({"summary": "You can ask examples:", "examples": examples})

    # ---- DEMAND TREND COMPARISON: "compare X and Y demand" ----
    # place this BEFORE the generic compare to capture queries explicitly asking demand comparison
    if "compare" in query and " and " in query and "demand" in query:
        # remove 'demand' word then parse "compare X and Y"
        cleaned = query.replace("demand", "").replace("compare", "").strip()
        parts = [p.strip() for p in cleaned.split(" and ") if p.strip()]
        if len(parts) < 2:
            return Response({"error": "Could not parse the two locations to compare"}, status=400)

        loc1, loc2 = parts[0], parts[1]
        rows1 = find_location_rows(loc1)
        rows2 = find_location_rows(loc2)
        if rows1.empty or rows2.empty:
            return Response({"error": f"Cannot find data for '{loc1}' or '{loc2}'"}, status=404)

        # find demand-like numeric column
        def find_demand_col(rows):
            keywords = ["demand", "total units", "units", "supply", "launched"]
            # try columns containing keywords and numeric
            for col in rows.columns:
                lname = col.lower()
                if any(k in lname for k in keywords) and pd.api.types.is_numeric_dtype(rows[col]):
                    return col
            # fallback: any numeric column containing 'total'
            for col in rows.columns:
                if "total" in col.lower() and pd.api.types.is_numeric_dtype(rows[col]):
                    return col
            # last fallback: first numeric column
            for col in rows.columns:
                if pd.api.types.is_numeric_dtype(rows[col]):
                    return col
            return None

        col1 = find_demand_col(rows1)
        col2 = find_demand_col(rows2)
        if col1 is None or col2 is None:
            return Response({"error": "No numeric demand-like column found for one or both locations"}, status=500)

        if "year" not in rows1.columns or "year" not in rows2.columns:
            return Response({"error": "Dataset missing 'year' column for comparison"}, status=500)

        t1 = rows1.sort_values("year")[[ "year", col1 ]]
        t2 = rows2.sort_values("year")[[ "year", col2 ]]

        demand_compare = {
            loc1: [
                {"year": int(r["year"]) if not pd.isna(r["year"]) else None,
                 "value": None if pd.isna(r[col1]) else float(r[col1])}
                for _, r in t1.iterrows()
            ],
            loc2: [
                {"year": int(r["year"]) if not pd.isna(r["year"]) else None,
                 "value": None if pd.isna(r[col2]) else float(r[col2])}
                for _, r in t2.iterrows()
            ]
        }

        return Response({
            "summary": f"Demand comparison between {loc1} and {loc2}.",
            "demand_compare": demand_compare
        })

    # ---- Intent: general compare "Compare X and Y" ----
    if "compare" in query and " and " in query:
        cleaned = query.replace("compare", "").strip()
        parts = [p.strip() for p in cleaned.split(" and ") if p.strip()]
        if len(parts) >= 2:
            a, b = parts[0], parts[1]
            rows_a = find_location_rows(a)
            rows_b = find_location_rows(b)
            if rows_a.empty or rows_b.empty:
                return Response({"error": f"One or both locations not found: '{a}', '{b}'"}, status=404)

            # try find numeric column for trend
            def find_numeric_col(r):
                # prefer columns with 'total' or 'units'
                for candidate in r.columns:
                    lc = candidate.lower()
                    if ("total" in lc or "unit" in lc) and pd.api.types.is_numeric_dtype(r[candidate]):
                        return candidate
                # fallback first numeric column
                for c in r.columns:
                    if pd.api.types.is_numeric_dtype(r[c]):
                        return c
                return None

            col = find_numeric_col(rows_a)
            def make_trend(rows, colname):
                if colname and "year" in rows.columns and colname in rows.columns:
                    tmp = rows.sort_values("year")[[ "year", colname ]]
                    return [
                        {"year": int(r["year"]) if not pd.isna(r["year"]) else None,
                         "value": None if pd.isna(r[colname]) else float(r[colname])}
                        for _, r in tmp.iterrows()
                    ]
                else:
                    # fallback: head rows as records
                    return rows.head(10).to_dict(orient="records")

            return Response({
                "summary": f"Comparison for '{a}' vs '{b}' (column used: {col})",
                "compare": { a: make_trend(rows_a, col), b: make_trend(rows_b, col) }
            })

    # ------------------------------------------------------
    # DEMAND TREND: "show demand trend for <area>"
    # ------------------------------------------------------
    if ("demand" in query and "trend" in query) or ("show demand" in query):
        # Extract area name by removing keywords
        area = query
        for token in ["show", "demand", "trend", "for", "of"]:
            area = area.replace(token, "")
        area = area.strip()
        if not area:
            return Response({"error": "Cannot detect area for demand trend"}, status=400)

        rows = find_location_rows(area)
        if rows.empty:
            return Response({"error": f"No data found for {area}"}, status=404)

        # find demand-related numeric column
        demand_col = None
        keywords = ["demand", "total units", "units", "supply", "launched"]
        for col in rows.columns:
            if any(k in col.lower() for k in keywords) and pd.api.types.is_numeric_dtype(rows[col]):
                demand_col = col
                break
        if demand_col is None:
            # fallback: numeric column with 'total'
            for col in rows.columns:
                if "total" in col.lower() and pd.api.types.is_numeric_dtype(rows[col]):
                    demand_col = col
                    break
        if demand_col is None:
            # last fallback: first numeric column
            for col in rows.columns:
                if pd.api.types.is_numeric_dtype(rows[col]):
                    demand_col = col
                    break
        if demand_col is None:
            return Response({"error": "No numeric demand-related column found"}, status=500)

        if "year" not in rows.columns:
            return Response({"error": "Dataset missing 'year' column"}, status=500)

        ordered = rows.sort_values("year")
        trend = [
            {"year": int(r["year"]) if not pd.isna(r["year"]) else None,
             "value": None if pd.isna(r[demand_col]) else float(r[demand_col])}
            for _, r in ordered.iterrows()
        ]

        return Response({
            "summary": f"Demand trend for {area} using column '{demand_col}'.",
            "demand": trend
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
            for c in recent.columns:
                if c.lower().strip() == candidate:
                    price_col = c
                    break
            if price_col:
                break
        # fallback: any numeric column with 'price' or 'rate'
        if price_col is None:
            for c in recent.columns:
                if ("price" in c.lower() or "rate" in c.lower()) and pd.api.types.is_numeric_dtype(recent[c]):
                    price_col = c
                    break

        chart = {}
        chart["years"] = make_json_safe_series(recent["year"])
        if price_col:
            chart["prices"] = [None if pd.isna(x) else float(x) for x in recent[price_col].tolist()]
        else:
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
    lower_cols = [c.lower() for c in rows.columns]
    for candidate in ["flat - weighted average rate", "flat weighted average rate", "price", "avg_price"]:
        for c in rows.columns:
            if c.lower().strip() == candidate:
                price_col = c
                break
        if price_col:
            break
    if price_col is None:
        # fallback: any numeric column with 'price' or 'rate'
        for c in rows.columns:
            if ("price" in c.lower() or "rate" in c.lower()) and pd.api.types.is_numeric_dtype(rows[c]):
                price_col = c
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
 