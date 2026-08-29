from ai.insights_engine import (
    generate_insights_report,
    get_mock_insights_report,
)
from auth.security import DEFAULT_ADMIN_HASH, UserSession, hash_password, verify_password
from reporting.pdf_generator import generate_executive_pdf


class TestSecurityAndReporting:
    def test_argon2_auth(self) -> None:
        assert verify_password(DEFAULT_ADMIN_HASH, "admin123")
        assert not verify_password(DEFAULT_ADMIN_HASH, "wrongpass")

        hashed = hash_password("secret_pass")
        assert verify_password(hashed, "secret_pass")

        demo_user = UserSession.demo_user()
        assert demo_user.is_demo_sandbox
        assert demo_user.is_authenticated

    def test_ai_insights_mock_and_fallback(self) -> None:
        mock_report = get_mock_insights_report()
        assert "3.4x" in mock_report.executive_summary
        assert len(mock_report.budget_recommendations) > 0

        report_fallback = generate_insights_report("summary", "attribution", api_key=None)
        assert report_fallback.executive_summary != ""

    def test_pdf_generation(self) -> None:
        mock_report = get_mock_insights_report()
        summary = {
            "total_spend": 1000.0,
            "total_revenue": 3500.0,
            "overall_roas": 3.5,
            "overall_cpa": 20.0,
        }
        pdf_bytes = generate_executive_pdf(summary, mock_report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
