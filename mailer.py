import os
import time
import httpx
import logging

def send_email_resend(to_email: str, subject: str, html_body: str):
    """Send email via Resend API with retry logic and exponential backoff."""
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
    
    # Retry configuration: 3 attempts with exponential backoff (0.5s, 1s, 2s)
    max_retries = 3
    retry_delays = [0.5, 1.0, 2.0]
    
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=15) as client:
                res = client.post("https://api.resend.com/emails", json=payload, headers=headers)
                
                # Success case
                if res.status_code < 400:
                    return res.json()
                
                # Retry on 429 (rate limit) or 5xx (server errors)
                if res.status_code == 429 or res.status_code >= 500:
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logging.warning(f"[RESEND] Retry {attempt + 1}/{max_retries} after {res.status_code}, waiting {delay}s")
                        time.sleep(delay)
                        continue
                
                # Non-retryable error
                raise RuntimeError(f"Resend error {res.status_code}: {res.text}")
                
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            # Network errors - retry
            if attempt < max_retries - 1:
                delay = retry_delays[attempt]
                logging.warning(f"[RESEND] Network error, retry {attempt + 1}/{max_retries} after {delay}s: {str(e)}")
                time.sleep(delay)
                continue
            raise RuntimeError(f"Resend network error after {max_retries} attempts: {str(e)}")
    
    raise RuntimeError(f"Resend failed after {max_retries} attempts")
