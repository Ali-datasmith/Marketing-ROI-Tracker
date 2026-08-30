import logging
import os

import httpx
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class BudgetRecommendation(BaseModel):
    channel: str = Field(..., description="Target marketing channel")
    action: str = Field(..., description="'INCREASE', 'DECREASE', or 'MAINTAIN'")
    percentage_change: float = Field(..., description="Recommended percentage change in budget allocation")
    rationale: str = Field(..., description="Data-driven reason for the recommendation")


class RiskFactor(BaseModel):
    category: str = Field(..., description="Risk category, e.g. 'Saturation', 'Low ROAS', 'High CAC'")
    channel: str = Field(..., description="Channel associated with risk")
    severity: str = Field(..., description="'HIGH', 'MEDIUM', 'LOW'")
    description: str = Field(..., description="Detailed description of identified risk factor")


class MarketingInsightsReport(BaseModel):
    """Pydantic schema for structured C-suite AI Marketing Insights."""

    executive_summary: str = Field(..., description="High-level channel performance and blended metrics summary.")
    blended_roas_assessment: str = Field(..., description="Assessment of overall blended ROAS and efficiency.")
    budget_recommendations: list[BudgetRecommendation] = Field(..., description="Actionable spend reallocations across channels.")
    risk_factors: list[RiskFactor] = Field(..., description="Identified channel saturation points or low-ROAS flags.")


class AISynthesisError(Exception):
    """Base exception class with status-code-first error taxonomy."""
    def __init__(self, code: str, message: str, original_error: Exception | None = None):
        self.code = code  # CAT_QUOTA, CAT_AUTH, CAT_TIMEOUT, CAT_SCHEMA, CAT_API_KEY_MISSING
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{code}] {message}")


def _is_transient_error(exception: BaseException) -> bool:
    """Identify transient network, timeout, 429 rate limit, or 5xx server errors for retry."""
    if isinstance(exception, (httpx.RequestError, httpx.HTTPStatusError)):
        if isinstance(exception, httpx.HTTPStatusError):
            return exception.response.status_code in (429, 500, 502, 503, 504)
        return True

    err_str = str(exception).lower()
    transient_keywords = ["429", "quota", "resourceexhausted", "500", "502", "503", "504", "timeout", "deadline", "rate limit"]
    return any(keyword in err_str for keyword in transient_keywords)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(_is_transient_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_gemini_api_with_retry(
    client: "genai.Client",
    prompt: str,
) -> MarketingInsightsReport:
    """Execute Gemini API content generation with resilience exponential backoff."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=MarketingInsightsReport,
        temperature=0.2,
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=config,
    )

    if response.parsed and isinstance(response.parsed, MarketingInsightsReport):
        logger.info("Successfully received structured MarketingInsightsReport from Gemini 3.5 Flash.")
        return response.parsed
    elif response.text:
        logger.info("Parsing raw JSON string into MarketingInsightsReport schema...")
        return MarketingInsightsReport.model_validate_json(response.text)
    else:
        raise AISynthesisError("CAT_SCHEMA", "Gemini response returned empty content.")


def generate_insights_report(
    summary_data: str,
    attribution_data: str,
    api_key: str | None = None
) -> MarketingInsightsReport:
    """
    Generate structured marketing insights using Gemini 3.5 Flash and Pydantic schema
    with httpx + tenacity resilience layer.
    """
    effective_api_key = api_key or os.getenv("GEMINI_API_KEY")

    if not effective_api_key:
        logger.warning("No Gemini API key supplied. Utilizing mock fallback insights report.")
        return get_mock_insights_report()

    if not GENAI_AVAILABLE:
        logger.error("google-genai library not installed.")
        raise AISynthesisError("CAT_SCHEMA", "google-genai SDK is not available in environment.")

    prompt = f"""
You are an expert B2B Marketing Analytics & Revenue Architect.
Analyze the following marketing performance and multi-touch attribution data:

--- BLENDED CHANNEL METRICS ---
{summary_data}

--- MULTI-TOUCH ATTRIBUTION MODELS ---
{attribution_data}

Provide an executive C-suite report in structured JSON format adhering strictly to the schema.
Highlight top performing channels, recommend optimal budget reallocations based on multi-touch attribution,
and flag saturation or efficiency risks.
"""

    try:
        logger.info("Initializing Google GenAI client targeting gemini-3.5-flash with httpx timeouts...")
        http_options = types.HttpOptions(timeout=15000)
        client = genai.Client(api_key=effective_api_key, http_options=http_options)

        return _call_gemini_api_with_retry(client, prompt)

    except AISynthesisError:
        raise
    except Exception as e:
        err_str = str(e).lower()
        logger.error(f"Gemini API call failed after retries: {e}")

        if "quota" in err_str or "429" in err_str or "resourceexhausted" in err_str:
            raise AISynthesisError("CAT_QUOTA", "API quota exhausted or rate limit exceeded.", original_error=e)
        elif "auth" in err_str or "unauthorized" in err_str or "401" in err_str or "403" in err_str or "api_key" in err_str:
            raise AISynthesisError("CAT_AUTH", "Authentication or API Key validation failed.", original_error=e)
        elif "timeout" in err_str or "deadline" in err_str:
            raise AISynthesisError("CAT_TIMEOUT", "Request to Gemini API timed out.", original_error=e)
        else:
            raise AISynthesisError("CAT_SCHEMA", f"Unexpected error during AI synthesis: {e}", original_error=e)


def get_mock_insights_report() -> MarketingInsightsReport:
    """Generate realistic mock report for testing or when API key is missing."""
    return MarketingInsightsReport(
        executive_summary="Overall marketing campaigns delivered strong results with a blended ROAS of 3.4x. Organic SEO and Email Marketing demonstrated the highest capital efficiency, while Meta Ads drove high top-of-funnel conversion volume.",
        blended_roas_assessment="Blended CAC stands at $28.40 across all channels. Search and organic channels heavily assist late-stage conversions, making linear attribution the most balanced evaluation model.",
        budget_recommendations=[
            BudgetRecommendation(
                channel="Organic SEO",
                action="INCREASE",
                percentage_change=15.0,
                rationale="Exceptional assisted conversion value with minimal incremental spend required."
            ),
            BudgetRecommendation(
                channel="Google Ads",
                action="INCREASE",
                percentage_change=10.0,
                rationale="High buyer intent with a solid 4.1x linear attribution ROAS."
            ),
            BudgetRecommendation(
                channel="Meta Ads",
                action="DECREASE",
                percentage_change=10.0,
                rationale="Reaching saturation point on retargeting audiences with rising CPA."
            ),
        ],
        risk_factors=[
            RiskFactor(
                category="Saturation",
                channel="Meta Ads",
                severity="MEDIUM",
                description="Frequency metrics indicate audience fatigue in core retargeting campaign."
            ),
            RiskFactor(
                category="Low ROAS",
                channel="Generic Channel",
                severity="LOW",
                description="Uncategorized spend requires tighter campaign tagging to evaluate ROI accurately."
            ),
        ]
    )
