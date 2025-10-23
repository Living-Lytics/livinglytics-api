import os
import httpx

def send_email_resend(to_email: str, subject: str, html_body: str):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("Missing RESEND_API_KEY")

    mail_from = os.getenv("MAIL_FROM")
    mail_from_name = os.getenv("MAIL_FROM_NAME", "Living Lytics")

    payload = {
        "from": f"{mail_from_name} <{mail_from}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=15) as client:
        res = client.post("https://api.resend.com/emails", json=payload, headers=headers)
        if res.status_code >= 400:
            raise RuntimeError(f"Resend error {res.status_code}: {res.text}")
        return res.json()
