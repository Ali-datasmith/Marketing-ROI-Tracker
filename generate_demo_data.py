"""
generate_demo_data.py

Generates 4 realistic, messy, and distinct CSV files simulating ad platform 
exports (Google Ads, Facebook Ads, Email, SEO) for a marketing analytics demo.
"""

import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

# --- Configuration & Seeding ---
SEED: int = 42
np.random.seed(SEED)
random.seed(SEED)

fake: Faker = Faker()
Faker.seed(SEED)

DATA_DIR: Path = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATES: pd.DatetimeIndex = pd.date_range(end="2024-10-31", periods=70)
WEEKEND_FACTOR: np.ndarray = np.where(DATES.dayofweek >= 5, 0.4, 1.0)


# --- Helper Functions ---
def generate_campaign_names(count: int) -> list[str]:
    """Generate plausible campaign names using Faker."""
    prefixes = [
        "Summer", "Winter", "Flash", "Holiday", "Brand", 
        "Retargeting", "Lookalike", "Prospecting", "Q3", "Q4"
    ]
    suffixes = [
        "Sale", "Launch", "Push", "Campaign", "Promo", 
        "Drive", "Awareness", "Acquisition"
    ]
    return [
        f"{fake.random_element(prefixes)} {fake.random_element(suffixes)} - {fake.company()}" 
        for _ in range(count)
    ]

def apply_imperfections(df: pd.DataFrame, spend_col: str, clicks_col: str, impressions_col: str, conv_col: str) -> pd.DataFrame:
    """Inject realistic data messiness into the dataframe."""
    # 1. 0 clicks but >0 impressions (5% of rows)
    mask_imp = df[impressions_col] > 0
    if mask_imp.any():
        zero_click_idx = df[mask_imp].sample(frac=0.05, random_state=SEED).index
        df.loc[zero_click_idx, clicks_col] = 0

    # 2. Missing/blank conversions (3% of rows)
    conv_idx = df.sample(frac=0.03, random_state=SEED).index
    df.loc[conv_idx, conv_col] = np.nan

    # 3. Inconsistent decimal precision for spend
    df[spend_col] = df[spend_col].apply(lambda x: round(x, random.choice([2, 3, 4])))

    return df

def format_dates(df: pd.DataFrame, date_col: str, fmt: str) -> pd.DataFrame:
    """Format the date column to mimic platform-specific exports."""
    df[date_col] = df[date_col].dt.strftime(fmt)
    return df


# --- Platform Generators ---
def generate_google_ads() -> pd.DataFrame:
    campaigns = generate_campaign_names(5)
    rows = []
    
    for camp in campaigns:
        spend = np.random.uniform(100, 500, 70) * WEEKEND_FACTOR
        clicks = (spend * np.random.uniform(0.8, 2.5)).astype(int)
        impressions = (clicks * np.random.uniform(30, 100)).astype(int)
        conversions = (clicks * np.random.uniform(0.02, 0.06)).astype(int)
        conv_value = conversions * np.random.uniform(30, 80)
        
        camp_df = pd.DataFrame({
            "Day": DATES,
            "Campaign": camp,
            "Cost": spend,
            "Clicks": clicks,
            "Impressions": impressions,
            "Conversions": conversions,
            "Conv. value": conv_value
        })
        rows.append(camp_df)
        
    df = pd.concat(rows, ignore_index=True)
    df = apply_imperfections(df, "Cost", "Clicks", "Impressions", "Conversions")
    return format_dates(df, "Day", "%Y-%m-%d")

def generate_facebook_ads() -> pd.DataFrame:
    campaigns = generate_campaign_names(6)
    rows = []
    
    for camp in campaigns:
        spend = np.random.uniform(200, 800, 70) * WEEKEND_FACTOR
        link_clicks = (spend * np.random.uniform(1.0, 3.0)).astype(int)
        impressions = (link_clicks * np.random.uniform(40, 120)).astype(int)
        results = (link_clicks * np.random.uniform(0.03, 0.07)).astype(int)
        purchase_value = results * np.random.uniform(40, 90)
        
        camp_df = pd.DataFrame({
            "Reporting starts": DATES,
            "Campaign name": camp,
            "Amount spent (USD)": spend,
            "Link clicks": link_clicks,
            "Impressions": impressions,
            "Results": results,
            "Purchase value": purchase_value
        })
        rows.append(camp_df)
        
    df = pd.concat(rows, ignore_index=True)
    df = apply_imperfections(df, "Amount spent (USD)", "Link clicks", "Impressions", "Results")
    return format_dates(df, "Reporting starts", "%m/%d/%Y")

def generate_email() -> pd.DataFrame:
    campaigns = generate_campaign_names(4)
    rows = []
    
    for camp in campaigns:
        # Email has flat/low costs but high conversion rates
        cost = np.random.uniform(20, 50, 70) 
        opens = np.random.randint(5000, 15000, 70)
        clicks = (opens * np.random.uniform(0.05, 0.15)).astype(int)
        conversions = (clicks * np.random.uniform(0.10, 0.25)).astype(int)
        revenue = conversions * np.random.uniform(80, 150)
        
        camp_df = pd.DataFrame({
            "Send Date": DATES,
            "Campaign": camp,
            "Cost": cost,
            "Opens": opens,
            "Clicks": clicks,
            "Conversions": conversions,
            "Revenue": revenue
        })
        rows.append(camp_df)
        
    df = pd.concat(rows, ignore_index=True)
    df = apply_imperfections(df, "Cost", "Clicks", "Opens", "Conversions")
    return format_dates(df, "Send Date", "%d-%b-%Y")

def generate_seo() -> pd.DataFrame:
    campaigns = generate_campaign_names(5)
    rows = []
    
    for camp in campaigns:
        # SEO is mostly free, so cost is near 0, but revenue is real
        cost = np.random.uniform(0, 5, 70) 
        organic_clicks = (np.random.randint(1000, 5000, 70) * WEEKEND_FACTOR).astype(int)
        organic_impressions = (organic_clicks * np.random.uniform(15, 40)).astype(int)
        goal_completions = (organic_clicks * np.random.uniform(0.01, 0.04)).astype(int)
        assisted_revenue = goal_completions * np.random.uniform(50, 120)
        
        camp_df = pd.DataFrame({
            "Date": DATES,
            "Page/Campaign": camp,
            "Organic Cost": cost,
            "Organic Clicks": organic_clicks,
            "Organic Impressions": organic_impressions,
            "Goal Completions": goal_completions,
            "Assisted Revenue": assisted_revenue
        })
        rows.append(camp_df)
        
    df = pd.concat(rows, ignore_index=True)
    df = apply_imperfections(df, "Organic Cost", "Organic Clicks", "Organic Impressions", "Goal Completions")
    return format_dates(df, "Date", "%Y/%m/%d")


# --- Main Execution ---
def main() -> None:
    generators: dict[str, Any] = {
        "google_ads": (generate_google_ads, "sample_google_ads.csv", "Cost", "Conv. value"),
        "facebook": (generate_facebook_ads, "sample_facebook_ads.csv", "Amount spent (USD)", "Purchase value"),
        "email": (generate_email, "sample_email.csv", "Cost", "Revenue"),
        "seo": (generate_seo, "sample_seo.csv", "Organic Cost", "Assisted Revenue"),
    }

    print("Generating demo data...")
    print("-" * 50)

    for platform, (gen_func, filename, spend_col, rev_col) in generators.items():
        df = gen_func()
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False)

        # Calculate summary stats using walrus operator for concise checks
        if (total_spend := df[spend_col].sum()) > 0:
            total_revenue = df[rev_col].sum()
            roas = total_revenue / total_spend if total_spend > 0 else float('inf')
        else:
            total_revenue = df[rev_col].sum()
            roas = float('inf')

        # Use match/case for platform-specific summary formatting
        match platform:
            case "google_ads":
                date_col = "Day"
                date_fmt = "%Y-%m-%d"
            case "facebook":
                date_col = "Reporting starts"
                date_fmt = "%m/%d/%Y"
            case "email":
                date_col = "Send Date"
                date_fmt = "%d-%b-%Y"
            case "seo":
                date_col = "Date"
                date_fmt = "%Y/%m/%d"
            case _:
                date_col = "Date"
                date_fmt = "%Y-%m-%d"

        min_date = pd.to_datetime(df[date_col], format=date_fmt).min().strftime("%Y-%m-%d")
        max_date = pd.to_datetime(df[date_col], format=date_fmt).max().strftime("%Y-%m-%d")

        print(f"Platform: {platform.replace('_', ' ').title()}")
        print(f"  File: {filepath}")
        print(f"  Rows: {len(df)}")
        print(f"  Date Range: {min_date} to {max_date}")
        print(f"  Total Spend: ${total_spend:,.2f}")
        print(f"  Total Revenue: ${total_revenue:,.2f}")
        print(f"  Estimated ROAS: {roas:.2f}")
        print("-" * 50)

    print("Demo data generation complete.")

if __name__ == "__main__":
    main()
