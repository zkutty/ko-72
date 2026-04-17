"""
Send the HTML newsletter email via the Resend API.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader

ACCENT_COLORS = {
    "Spring": "#6b8f71",
    "Summer": "#c9734a",
    "Autumn": "#d4a853",
    "Winter": "#4a7fa5",
}


def _get_subscribers(api_key: str) -> list[str]:
    """Merge Resend audience contacts with SUBSCRIBER_EMAILS env var."""
    subscribers: set[str] = set()

    audience_id = os.environ.get("RESEND_AUDIENCE_ID", "").strip()
    if audience_id:
        req = urllib.request.Request(
            f"https://api.resend.com/audiences/{audience_id}/contacts",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                for contact in data.get("data", []):
                    if not contact.get("unsubscribed", False):
                        subscribers.add(contact["email"].strip())
        except urllib.error.URLError as e:
            print(f"Warning: could not fetch Resend audience contacts: {e}")

    subscriber_str = os.environ.get("SUBSCRIBER_EMAILS", "").strip()
    for addr in subscriber_str.split(","):
        addr = addr.strip()
        if addr:
            subscribers.add(addr)

    return sorted(subscribers)


def send_email(season: dict, content: dict, worker_url: str = "https://subscribe.ko-72.com") -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]

    recipients = _get_subscribers(resend.api_key)
    if not recipients:
        raise ValueError("No subscribers found. Set SUBSCRIBER_EMAILS or RESEND_AUDIENCE_ID.")

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("email.html")

    today = date.today()
    accent_color = ACCENT_COLORS.get(season["major_season"].capitalize(), "#888780")
    archive_url = f"https://ko-72.com/archive/{season['id']:02d}-{season['slug']}.html"
    signup_url = f"{worker_url}/subscribe"
    unsubscribe_url = f"https://ko-72.com/unsubscribe.html"

    html = template.render(
        season=season,
        content=content,
        today=today,
        accent_color=accent_color,
        archive_url=archive_url,
        signup_url=signup_url,
        unsubscribe_url=unsubscribe_url,
    )

    subject = f"Kō · {season['name_en']} ({season['name_romaji']})"

    params: resend.Emails.SendParams = {
        "from": "Kō <seasons@ko-72.com>",
        "to": recipients,
        "subject": subject,
        "html": html,
    }

    response = resend.Emails.send(params)
    print(f"Email sent to {len(recipients)} subscriber(s). Resend ID: {response['id']}")
