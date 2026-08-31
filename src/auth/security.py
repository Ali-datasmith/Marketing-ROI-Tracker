import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from loguru import logger

ph = PasswordHasher()

# Read admin password from environment or use enterprise default credential
ENTERPRISE_DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "MTA_Enterprise_2026!Secured#")
DEFAULT_ADMIN_HASH = ph.hash(ENTERPRISE_DEFAULT_ADMIN_PASS)


def get_admin_password() -> str:
    """Return effective admin password."""
    return ENTERPRISE_DEFAULT_ADMIN_PASS


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return ph.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    """Verify password against Argon2 hash."""
    try:
        return ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


class UserSession:
    """Class representing active user session permissions."""
    def __init__(self, username: str, is_authenticated: bool, is_demo_sandbox: bool = False):
        self.username = username
        self.is_authenticated = is_authenticated
        self.is_demo_sandbox = is_demo_sandbox

    @classmethod
    def demo_user(cls) -> "UserSession":
        """Factory for 1-click Recruiter Demo user."""
        return cls(username="Recruiter Sandbox Demo", is_authenticated=True, is_demo_sandbox=True)

    @classmethod
    def admin_user(cls) -> "UserSession":
        """Factory for authenticated Admin user."""
        return cls(username="Executive Admin", is_authenticated=True, is_demo_sandbox=False)
