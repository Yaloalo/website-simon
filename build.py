from __future__ import annotations

import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


ROOT = Path(__file__).resolve().parent
CONTENT_FILE = ROOT / "content" / "site.json"
SRC_DIR = ROOT / "src"
TEMPLATES_DIR = SRC_DIR / "templates"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"

SECTION_MAP = [
    ("approach", "arbeitsweise"),
    ("about", "ueber-mich"),
    ("qualifications", "werdegang"),
    ("offer", "angebot"),
    ("practice", "praxis"),
    ("contact", "kontakt"),
]


class BuildError(RuntimeError):
    pass


def get_base_path() -> str:
    raw = os.environ.get("SITE_BASE_PATH", "").strip()
    if raw in {"", "/"}:
        return ""
    if not raw.startswith("/"):
        raise BuildError("SITE_BASE_PATH muss leer sein oder mit '/' beginnen.")
    return raw.rstrip("/")


BASE_PATH = get_base_path()


def public_url(public_path: str) -> str:
    if not public_path:
        return ""
    if not public_path.startswith("/"):
        raise BuildError(f"Pfad '{public_path}' muss mit '/' beginnen.")
    return f"{BASE_PATH}{public_path}" if BASE_PATH else public_path


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"Inhaltsdatei fehlt: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(
            f"Ungültiges JSON in {path} (Zeile {exc.lineno}, Spalte {exc.colno}): {exc.msg}"
        ) from exc


def require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BuildError(f"{path} muss ein Objekt sein.")
    return value


def require_list(value: Any, path: str, minimum: int = 0) -> list[Any]:
    if not isinstance(value, list):
        raise BuildError(f"{path} muss eine Liste sein.")
    if len(value) < minimum:
        raise BuildError(f"{path} muss mindestens {minimum} Einträge enthalten.")
    return value


def require_string(value: Any, path: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise BuildError(f"{path} muss ein Text sein.")
    cleaned = value.strip()
    if not allow_empty and not cleaned:
        raise BuildError(f"{path} darf nicht leer sein.")
    return cleaned


def require_number(value: Any, path: str, *, minimum: float | None = None) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BuildError(f"{path} muss eine Zahl sein.")
    if minimum is not None and value < minimum:
        raise BuildError(f"{path} muss mindestens {minimum} sein.")
    return value


def require_boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise BuildError(f"{path} muss true oder false sein.")
    return value


def validate_email(value: str, path: str) -> str:
    email = require_string(value, path)
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise BuildError(f"{path} ist keine gültige E-Mail-Adresse.")
    return email


def validate_image(value: Any, path: str) -> dict[str, str]:
    image = require_dict(value, path)
    src = image.get("src", "")
    alt = image.get("alt", "")

    if src is None:
        src = ""
    if alt is None:
        alt = ""

    if not isinstance(src, str):
        raise BuildError(f"{path}.src muss ein Text sein.")
    if not isinstance(alt, str):
        raise BuildError(f"{path}.alt muss ein Text sein.")

    src = src.strip()
    alt = alt.strip()

    if src:
        validate_public_asset_path(src, f"{path}.src")

    return {"src": src, "alt": alt}


def validate_public_asset_path(public_path_value: str, path: str) -> None:
    if not public_path_value.startswith("/"):
        raise BuildError(f"{path} muss mit '/' beginnen.")
    if public_path_value.startswith("/uploads/") or public_path_value.startswith("/images/"):
        asset_path = STATIC_DIR / public_path_value.lstrip("/")
    else:
        raise BuildError(f"{path} darf nur auf '/uploads/...' oder '/images/...' verweisen.")

    if not asset_path.is_file():
        raise BuildError(
            f"{path} verweist auf '{public_path_value}', aber die Datei '{asset_path}' fehlt."
        )


def normalize_phone(number: str, path: str) -> str:
    value = require_string(number, path)
    raw_digits = re.sub(r"\D", "", value)

    if value.startswith("+"):
        digits = "+" + raw_digits
    elif value.startswith("00"):
        digits = "+" + raw_digits[2:]
    elif value.startswith("0"):
        digits = "+49" + raw_digits[1:]
    else:
        digits = "+" + raw_digits

    if len(re.sub(r"\D", "", digits)) < 6:
        raise BuildError(f"{path} muss mindestens 6 Ziffern enthalten. Aktuell: '{value}'.")
    return digits


def whatsapp_link(number: str, path: str) -> str:
    digits = normalize_phone(number, path).lstrip("+")
    return f"https://wa.me/{digits}"


def format_price(value: int | float) -> str:
    number = float(value)
    if number.is_integer():
        return f"{int(number)} €"
    return f"{number:.2f}".replace(".", ",") + " €"


def validate_site_data(data: dict[str, Any]) -> dict[str, Any]:
    site: dict[str, Any] = {}

    meta = require_dict(data.get("meta"), "meta")
    navigation = require_dict(data.get("navigation"), "navigation")
    hero = require_dict(data.get("hero"), "hero")
    approach = require_dict(data.get("approach"), "approach")
    about = require_dict(data.get("about"), "about")
    qualifications = require_dict(data.get("qualifications"), "qualifications")
    offer = require_dict(data.get("offer"), "offer")
    practice = require_dict(data.get("practice"), "practice")
    contact = require_dict(data.get("contact"), "contact")
    legal = require_dict(data.get("legal"), "legal")

    site["meta"] = {
        "site_title": require_string(meta.get("site_title"), "meta.site_title"),
        "description": require_string(meta.get("description"), "meta.description"),
    }

    site["navigation"] = {
        "brand": require_string(navigation.get("brand"), "navigation.brand"),
        "cta_label": require_string(navigation.get("cta_label"), "navigation.cta_label"),
    }

    site["hero"] = {
        "eyebrow": require_string(hero.get("eyebrow"), "hero.eyebrow"),
        "title": require_string(hero.get("title"), "hero.title"),
        "text_html": require_string(hero.get("text_html"), "hero.text_html"),
        "image": validate_image(hero.get("image", {}), "hero.image"),
    }

    site["approach"] = {
        "title": require_string(approach.get("title"), "approach.title"),
        "text_html": require_string(approach.get("text_html"), "approach.text_html"),
    }

    site["about"] = {
        "title": require_string(about.get("title"), "about.title"),
        "text_html": require_string(about.get("text_html"), "about.text_html"),
        "image": validate_image(about.get("image", {}), "about.image"),
    }

    qualification_items: list[dict[str, str]] = []
    for index, item in enumerate(
        require_list(qualifications.get("items"), "qualifications.items", minimum=1), start=1
    ):
        entry = require_dict(item, f"qualifications.items[{index}]")
        qualification_items.append(
            {
                "title": require_string(
                    entry.get("title"), f"qualifications.items[{index}].title"
                ),
                "text": require_string(entry.get("text"), f"qualifications.items[{index}].text"),
            }
        )

    site["qualifications"] = {
        "title": require_string(qualifications.get("title"), "qualifications.title"),
        "items": qualification_items,
    }

    topics = [
        require_string(topic, f"offer.topics[{index}]")
        for index, topic in enumerate(require_list(offer.get("topics"), "offer.topics", minimum=1), start=1)
    ]

    site["offer"] = {
        "title": require_string(offer.get("title"), "offer.title"),
        "intro_html": require_string(offer.get("intro_html"), "offer.intro_html"),
        "topics": topics,
        "session_duration": require_number(
            offer.get("session_duration"), "offer.session_duration", minimum=1
        ),
        "price": require_number(offer.get("price"), "offer.price", minimum=0),
        "pricing_note_html": require_string(
            offer.get("pricing_note_html"), "offer.pricing_note_html"
        ),
        "billing_note_html": require_string(
            offer.get("billing_note_html"), "offer.billing_note_html"
        ),
        "online_available": require_boolean(
            offer.get("online_available"), "offer.online_available"
        ),
        "online_note": require_string(offer.get("online_note", ""), "offer.online_note", allow_empty=True),
        "confidentiality_note_html": require_string(
            offer.get("confidentiality_note_html"), "offer.confidentiality_note_html"
        ),
    }
    site["offer"]["price_display"] = format_price(site["offer"]["price"])

    site["practice"] = {
        "title": require_string(practice.get("title"), "practice.title"),
        "name": require_string(practice.get("name"), "practice.name"),
        "street": require_string(practice.get("street"), "practice.street"),
        "city": require_string(practice.get("city"), "practice.city"),
        "additional_text_html": require_string(
            practice.get("additional_text_html", ""), "practice.additional_text_html", allow_empty=True
        ),
        "image": validate_image(practice.get("image", {}), "practice.image"),
    }

    phone = require_string(contact.get("phone"), "contact.phone")
    normalized_phone = normalize_phone(phone, "contact.phone")

    site["contact"] = {
        "title": require_string(contact.get("title"), "contact.title"),
        "text_html": require_string(contact.get("text_html"), "contact.text_html"),
        "email": validate_email(contact.get("email"), "contact.email"),
        "phone": phone,
    }
    site["contact"]["email_link"] = f"mailto:{site['contact']['email']}"
    site["contact"]["phone_link"] = f"tel:{normalized_phone}"
    site["contact"]["whatsapp_link"] = whatsapp_link(phone, "contact.phone")

    impressum = require_dict(legal.get("impressum"), "legal.impressum")
    datenschutz = require_dict(legal.get("datenschutz"), "legal.datenschutz")
    site["legal"] = {
        "impressum": {
            "title": require_string(impressum.get("title"), "legal.impressum.title"),
            "body_html": require_string(impressum.get("body_html"), "legal.impressum.body_html"),
        },
        "datenschutz": {
            "title": require_string(datenschutz.get("title"), "legal.datenschutz.title"),
            "body_html": require_string(
                datenschutz.get("body_html"), "legal.datenschutz.body_html"
            ),
        },
    }

    return site


def build_navigation_items(site: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for key, anchor in SECTION_MAP:
        items.append({"label": site[key]["title"], "href": f"#{anchor}"})
    return items


def create_environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.globals["url_for"] = public_url
    return environment


def prepare_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, destination, dirs_exist_ok=True)


def render_pages(site: dict[str, Any]) -> None:
    environment = create_environment()
    navigation_items = build_navigation_items(site)
    shared = {
        "site": site,
        "navigation_items": navigation_items,
        "current_year": date.today().year,
    }

    pages = [
        {
            "template": "index.html",
            "output": DIST_DIR / "index.html",
            "context": {
                "current_page": "home",
                "page_title": site["meta"]["site_title"],
                "page_description": site["meta"]["description"],
                "body_class": "page-home",
                "og_image": public_url(site["hero"]["image"]["src"])
                if site["hero"]["image"]["src"]
                else "",
            },
        },
        {
            "template": "impressum.html",
            "output": DIST_DIR / "impressum.html",
            "context": {
                "current_page": "impressum",
                "page_title": f"{site['legal']['impressum']['title']} | {site['meta']['site_title']}",
                "page_description": site["meta"]["description"],
                "body_class": "page-legal",
                "og_image": "",
            },
        },
        {
            "template": "datenschutz.html",
            "output": DIST_DIR / "datenschutz.html",
            "context": {
                "current_page": "datenschutz",
                "page_title": f"{site['legal']['datenschutz']['title']} | {site['meta']['site_title']}",
                "page_description": site["meta"]["description"],
                "body_class": "page-legal",
                "og_image": "",
            },
        },
    ]

    for page in pages:
        html = environment.get_template(page["template"]).render(**shared, **page["context"])
        page["output"].write_text(html, encoding="utf-8")


def copy_assets() -> None:
    copy_tree(SRC_DIR / "css", DIST_DIR / "css")
    copy_tree(SRC_DIR / "js", DIST_DIR / "js")
    copy_tree(STATIC_DIR, DIST_DIR)


def main() -> None:
    site_data = validate_site_data(read_json(CONTENT_FILE))
    prepare_dist()
    render_pages(site_data)
    copy_assets()
    print(f"Build erfolgreich: {DIST_DIR}")


if __name__ == "__main__":
    try:
        main()
    except BuildError as exc:
        raise SystemExit(f"Build fehlgeschlagen: {exc}") from exc
