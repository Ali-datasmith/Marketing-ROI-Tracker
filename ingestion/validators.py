"""
Data Validators for MarketingROITracker.

This module validates that normalized DataFrames conform to the unified schema 
before being loaded into the analytical database. It performs structural checks, 
safe type coercion, and strict row-level validation using Pydantic.
"""

import logging
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

from config.settings import REQUIRED_COLUMNS, ChannelName

logger = logging.getLogger(__name__)


class UnifiedRecordModel(BaseModel):
    """Pydantic model for strict row-level validation of the unified schema."""
    date: Any
    channel: ChannelName
    campaign_name: str
    spend: float = Field(ge=0.0)
    clicks: int = Field(ge=0)
    impressions: int = Field(ge=0)
    conversions: int = Field(ge=0)
    revenue: float = Field(ge=0.0)

    @field_validator('date', mode='before')
    @classmethod
    def validate_date(cls, v: Any) -> Any:
        if pd.isna(v):
            raise ValueError("Date is missing")
        try:
            return pd.to_datetime(v)
        except Exception:
            raise ValueError(f"Invalid date format: {v}")


def validate_schema(df: pd.DataFrame) -> list[str]:
    """
    Checks that all REQUIRED_COLUMNS are present and correctly typed.
    Returns a list of human-readable error message strings.
    """
    errors: list[str] = []
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(sorted(missing_cols))}")
        return errors  # Cannot check types if columns are missing
    
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        errors.append("Column 'date' is not a valid datetime type.")
        
    if not (pd.api.types.is_string_dtype(df['channel']) or pd.api.types.is_object_dtype(df['channel'])):
        errors.append("Column 'channel' is not a valid string type.")
        
    if not (pd.api.types.is_string_dtype(df['campaign_name']) or pd.api.types.is_object_dtype(df['campaign_name'])):
        errors.append("Column 'campaign_name' is not a valid string type.")
        
    for col in ['spend', 'revenue']:
        if not pd.api.types.is_float_dtype(df[col]):
            errors.append(f"Column '{col}' is not a valid float type.")
            
    for col in ['clicks', 'impressions', 'conversions']:
        if not pd.api.types.is_integer_dtype(df[col]):
            errors.append(f"Column '{col}' is not a valid integer type.")
            
    return errors


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempts a final safe type coercion pass. If a row can't be coerced, 
    it is logged and filled with a safe default rather than dropped.
    """
    df = df.copy()
    
    # Date coercion
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        original_nat_count = df['date'].isna().sum()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        new_nat_count = df['date'].isna().sum()
        if new_nat_count > original_nat_count:
            coerced_count = new_nat_count - original_nat_count
            logger.warning(
                f"Coerced 'date' column: {coerced_count} invalid dates were set to NaT."
            )
            
    # String coercion
    for col in ['channel', 'campaign_name']:
        df[col] = df[col].astype(str)
        
    # Float coercion
    for col in ['spend', 'revenue']:
        if not pd.api.types.is_float_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            logger.info(f"Coerced '{col}' to float, filling uncoercible values with 0.0.")
            
    # Integer coercion
    for col in ['clicks', 'impressions', 'conversions']:
        if not pd.api.types.is_integer_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            logger.info(f"Coerced '{col}' to integer, filling uncoercible values with 0.")
            
    return df


def validate_row_level(
    df: pd.DataFrame, 
    pydantic_model: type[BaseModel]
) -> tuple[pd.DataFrame, list[str]]:
    """
    Runs the pydantic model over each row, separating valid rows from invalid ones.
    Returns a tuple of (valid_rows_df, list_of_error_strings_with_row_numbers).
    """
    valid_indices = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            pydantic_model.model_validate(row.to_dict())
            valid_indices.append(idx)
        except ValidationError as e:
            err_msgs = [err['msg'] for err in e.errors()]
            err_str = "; ".join(err_msgs)
            errors.append(
                f"Row {idx}: Some values did not meet validation criteria ({err_str}). "
                f"This row has been excluded from the final dataset."
            )
            
    return df.loc[valid_indices], errors


def run_full_validation(
    df: pd.DataFrame
) -> tuple[bool, pd.DataFrame, list[str]]:
    """
    Top-level convenience function that runs the full validation pipeline:
    1. Schema validation
    2. Type coercion
    3. Row-level validation
    
    Returns (is_valid_overall, cleaned_df, all_error_messages).
    """
    all_errors = []
    
    # 1. Structural schema validation
    schema_errors = validate_schema(df)
    if schema_errors:
        return False, df, schema_errors
        
    # 2. Safe type coercion
    coerced_df = coerce_types(df)
    
    # 3. Strict row-level validation
    valid_df, row_errors = validate_row_level(coerced_df, UnifiedRecordModel)
    all_errors.extend(row_errors)
    
    is_valid_overall = len(all_errors) == 0
    
    return is_valid_overall, valid_df, all_errors
