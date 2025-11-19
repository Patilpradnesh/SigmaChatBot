from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
import os

# Path to Excel file
EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.xlsx")

# Load Excel safely
df = pd.read_excel(EXCEL_PATH, engine="openpyxl")

# Normalize column names (lowercase, no spaces)
df.columns = df.columns.str.strip().str.lower()


@api_view(["POST"])
def analyze(request):
    # Get query text
    query = request.data.get("query", "")

    # Check for empty query
    if not query.strip():
        return Response({"error": "Query is required."}, status=400)

    # Extract area from query (last word)
    area = query.split()[-1].lower()

    # Use the correct column from your dataset: "final location"
    if "final location" not in df.columns:
        return Response({"error": "Column 'final location' not found in dataset"}, status=500)

    # Filter rows where final location contains the area
    filtered = df[df["final location"].str.lower().str.contains(area, na=False)]

    # If no data found
    if filtered.empty:
        return Response({"error": f"No data found for {area}"}, status=404)

    # Create summary text
    summary = f"Here is a quick analysis for {area} based on available data."

    # Prepare chart data
    chart_data = {
        "years": filtered["year"].tolist(),
        "prices": filtered["flat - weighted average rate"].tolist()
    }

    # Convert filtered table to list of dicts
    table_data = filtered.to_dict(orient="records")

    # Return response
    return Response({
        "summary": summary,
        "chart": chart_data,
        "table": table_data
    })
