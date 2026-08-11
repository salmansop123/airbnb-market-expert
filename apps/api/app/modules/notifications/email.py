import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _wrap(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#F7F3EC;padding:24px;color:#0B1220">
  <div style="max-width:560px;margin:0 auto;background:#fff;padding:32px;border-radius:16px">
    <p style="color:#1F6B5A;letter-spacing:0.12em;text-transform:uppercase;font-size:12px">StayPrice AI</p>
    <h1 style="font-size:28px;margin:8px 0 16px">{title}</h1>
    {body}
    <p style="margin-top:32px;font-size:12px;color:#5B6B7C">© StayPrice AI · Revenue clarity for hosts</p>
  </div>
</body></html>"""


async def send_email(to: str, subject: str, html: str) -> None:
    if settings.RESEND_API_KEY:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={"from": settings.EMAIL_FROM, "to": [to], "subject": subject, "html": html},
                timeout=30,
            )
            resp.raise_for_status()
        return
    logger.info("EMAIL to=%s subject=%s body=%s", to, subject, html[:500])


async def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify?token={token}"
    html = _wrap(
        "Verify your email",
        f"<p>Welcome to StayPrice. Confirm your email to start pricing with AI.</p>"
        f"<p><a href='{link}' style='display:inline-block;background:#E85D4C;color:#fff;padding:12px 20px;"
        f"border-radius:999px;text-decoration:none'>Verify email</a></p>"
        f"<p style='font-size:13px;color:#5B6B7C'>Or use token: <code>{token}</code></p>",
    )
    await send_email(to, "Verify your StayPrice AI email", html)


async def send_password_reset_email(to: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/forgot-password?token={token}"
    html = _wrap(
        "Reset your password",
        f"<p>We received a request to reset your password.</p>"
        f"<p><a href='{link}' style='display:inline-block;background:#0B1220;color:#F7F3EC;padding:12px 20px;"
        f"border-radius:999px;text-decoration:none'>Reset password</a></p>"
        f"<p style='font-size:13px;color:#5B6B7C'>Token: <code>{token}</code></p>",
    )
    await send_email(to, "Reset your StayPrice AI password", html)


async def send_analysis_complete_email(to: str, property_title: str, price: float, link: str) -> None:
    html = _wrap(
        "Your price recommendation is ready",
        f"<p><strong>{property_title}</strong> suggested nightly rate:</p>"
        f"<p style='font-size:36px;margin:8px 0'>${price:.0f}<span style='font-size:16px'>/night</span></p>"
        f"<p><a href='{link}' style='display:inline-block;background:#1F6B5A;color:#fff;padding:12px 20px;"
        f"border-radius:999px;text-decoration:none'>View full analysis</a></p>",
    )
    await send_email(to, f"Analysis ready — {property_title}", html)
