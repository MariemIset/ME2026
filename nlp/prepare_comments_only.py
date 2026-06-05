import os

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SURVEY_DIR = os.path.join(BASE_DIR, "Airline+Passenger+Satisfaction")
OUTPUT_FILE = os.path.join(BASE_DIR, "comments_only.csv")


def resolve_input_file():
    candidates = [
        os.path.join(BASE_DIR, "Tweets.csv"),
        os.path.join(BASE_DIR, "tweets.csv"),
        os.path.join(SURVEY_DIR, "Tweets.csv"),
        os.path.join(SURVEY_DIR, "tweets.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def prepare_comments():
    input_file = resolve_input_file()
    if input_file is None:
        # If comments_only.csv already exists, skip generation
        if os.path.exists(OUTPUT_FILE):
            print(f"✓ Using existing comments file: {OUTPUT_FILE}")
            return
        raise FileNotFoundError(
            "Input file not found. Put Tweets.csv or tweets.csv in ME2026 or Airline+Passenger+Satisfaction."
        )

    print(f"Using source file: {input_file}")
    df = pd.read_csv(input_file)
    if "text" not in df.columns:
        raise ValueError("Tweets.csv must contain a 'text' column.")

    comments = df[["text"]].copy()
    comments = comments.rename(columns={"text": "comment_text"})
    comments["comment_text"] = comments["comment_text"].astype(str).str.strip()
    comments = comments[comments["comment_text"].str.len() >= 20]
    comments = comments.drop_duplicates(subset=["comment_text"]).reset_index(drop=True)

    comments.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved {len(comments)} comments to: {OUTPUT_FILE}")


if __name__ == "prepare_comments":
    prepare_comments()
