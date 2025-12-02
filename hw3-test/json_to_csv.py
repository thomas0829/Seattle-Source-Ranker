import json
import pandas as pd

INPUT_PATH = "../data/seattle_projects_20251201_074039.json"
OUTPUT_PATH = "../data/repos_for_validation.csv"

# 1. Load JSON
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. Extract "projects"
if "projects" not in data:
    raise ValueError("JSON format error: top-level key 'projects' not found.")

projects = data["projects"]

# 3. Convert to DataFrame
df = pd.DataFrame(projects)

# 4. Optional: flatten owner.login and owner.type
if "owner" in df.columns:
    df["owner_login"] = df["owner"].apply(lambda x: x.get("login") if isinstance(x, dict) else None)
    df["owner_type"] = df["owner"].apply(lambda x: x.get("type") if isinstance(x, dict) else None)

# 5. Remove the nested owner column
df = df.drop(columns=["owner"], errors="ignore")

# 6. Ensure size column exists
if "size" not in df.columns:
    df["size"] = None

# 7. Save CSV
df.to_csv(OUTPUT_PATH, index=False)

print(f"Conversion completed. Output file: {OUTPUT_PATH}")
