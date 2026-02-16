"""Service for generating HTML email templates."""
import ast
import html as html_module
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Resolve the storage root once (backend/storage/)
_STORAGE_ROOT = str(Path(__file__).resolve().parents[2] / "storage")

# Image serving API prefix
_IMAGE_API_PREFIX = "/api/v1/images"


class HTMLTemplateService:
    """Service for generating HTML email templates."""

    @staticmethod
    def storage_path_to_url(path: str) -> str:
        """Convert a filesystem storage path to an API-servable URL.

        If the path is already a URL (http/https) or a relative API path, return as-is.
        Otherwise, strip the storage root prefix and return an API image URL.
        """
        if not path:
            return path
        if path.startswith(("http://", "https://", _IMAGE_API_PREFIX)):
            return path

        # Try to find the storage/ portion of the path
        storage_idx = path.find("/storage/")
        if storage_idx != -1:
            relative = path[storage_idx + len("/storage/"):]
            return f"{_IMAGE_API_PREFIX}/{relative}"

        # If it's already a relative path (e.g. "generated_images/hero.png"), use directly
        if not path.startswith("/"):
            return f"{_IMAGE_API_PREFIX}/{path}"

        return path

    def generate_email_template(
        self,
        subject_line: str,
        preview_text: Optional[str],
        greeting: str,
        body: str,
        call_to_action: str,
        closing: str,
        footer: Optional[str],
        hero_image_url: Optional[str] = None,
        product_image_urls: Optional[List[str]] = None,
        color_scheme: Optional[Dict[str, str]] = None,
        tone: str = "professional",
    ) -> str:
        """
        Generate a complete HTML email template.
        
        Args:
            subject_line: Email subject line
            preview_text: Preview text
            greeting: Greeting text
            body: Main body content
            call_to_action: CTA text
            closing: Closing text
            footer: Footer content
            hero_image_url: URL/path to hero image
            product_image_urls: List of product image URLs
            color_scheme: Color scheme dictionary (primary, secondary, background, text)
            tone: Email tone
            
        Returns:
            Complete HTML email template
        """
        # Convert filesystem paths to API URLs
        if hero_image_url:
            hero_image_url = self.storage_path_to_url(hero_image_url)
        if product_image_urls:
            product_image_urls = [self.storage_path_to_url(u) for u in product_image_urls]

        if not color_scheme:
            color_scheme = self._get_color_scheme_for_tone(tone)

        # Parse structured content from LLM output
        body_parsed = self._parse_text_parts(body)
        body_html = self._body_to_html(body_parsed)
        cta = self._parse_cta(call_to_action)
        cta_button_color = cta.get("button_color") or color_scheme["secondary"]
        cta_hover_color = self._darken_color(cta_button_color)

        greeting_parsed = self._parse_text_parts(greeting) if greeting else ""
        greeting_text = " ".join(greeting_parsed) if isinstance(greeting_parsed, list) else greeting_parsed
        closing_parsed = self._parse_text_parts(closing) if closing else ""
        closing_text = " ".join(closing_parsed) if isinstance(closing_parsed, list) else closing_parsed
        footer_parsed = self._parse_footer(footer)

        escaped_subject = html_module.escape(subject_line)

        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>{escaped_subject}</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
        /* Reset */
        body, table, td, p, a {{
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        table, td {{
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }}
        img {{
            -ms-interpolation-mode: bicubic;
            border: 0;
            height: auto;
            line-height: 100%;
            outline: none;
            text-decoration: none;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.7;
            color: {color_scheme['text']};
            background-color: {color_scheme['background']};
        }}

        .email-wrapper {{
            width: 100%;
            background-color: {color_scheme['background']};
        }}

        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        .header {{
            background: linear-gradient(135deg, {color_scheme['primary']}, {self._lighten_color(color_scheme['primary'], 0.2)});
            padding: 32px 24px;
            text-align: center;
        }}

        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            line-height: 1.3;
            letter-spacing: -0.3px;
        }}

        .preview-text {{
            display: none;
            font-size: 1px;
            color: {color_scheme['background']};
            line-height: 1px;
            max-height: 0px;
            max-width: 0px;
            opacity: 0;
            overflow: hidden;
        }}

        .hero-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            display: block;
        }}

        .content {{
            padding: 36px 32px;
        }}

        .greeting {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 24px;
            color: {color_scheme['primary']};
        }}

        .body-text {{
            margin-bottom: 24px;
            color: {color_scheme['text']};
            font-size: 15px;
            line-height: 1.7;
        }}

        .body-text p {{
            margin: 0 0 16px 0;
        }}

        .body-text p:last-child {{
            margin-bottom: 0;
        }}

        .cta-wrapper {{
            text-align: center;
            padding: 12px 0 8px;
        }}

        .cta-button {{
            display: inline-block;
            padding: 16px 36px;
            background-color: {cta_button_color};
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 700;
            font-size: 16px;
            letter-spacing: 0.3px;
            transition: background-color 0.2s ease;
        }}

        .cta-button:hover {{
            background-color: {cta_hover_color};
        }}

        .cta-subtext {{
            text-align: center;
            font-size: 12px;
            color: #888888;
            margin-top: 8px;
        }}

        .divider {{
            border: none;
            border-top: 1px solid #eeeeee;
            margin: 28px 0;
        }}

        .products-section {{
            margin: 8px 0 0;
            padding: 24px 0 0;
            border-top: 1px solid #eeeeee;
        }}

        .products-section h2 {{
            text-align: center;
            margin: 0 0 20px;
            font-size: 18px;
            font-weight: 600;
            color: {color_scheme['primary']};
        }}

        .product-grid {{
            text-align: center;
        }}

        .product-item {{
            display: inline-block;
            width: 45%;
            max-width: 200px;
            vertical-align: top;
            padding: 8px;
            box-sizing: border-box;
        }}

        .product-image {{
            width: 100%;
            max-width: 180px;
            height: auto;
            border-radius: 8px;
            border: 1px solid #f0f0f0;
        }}

        .closing {{
            margin-top: 28px;
            color: {color_scheme['text']};
            font-size: 15px;
            line-height: 1.6;
        }}

        .footer {{
            background-color: #f8f9fa;
            padding: 24px 32px;
            text-align: center;
            font-size: 12px;
            color: #888888;
            line-height: 1.6;
            border-top: 1px solid #eeeeee;
        }}

        .footer a {{
            color: {color_scheme['primary']};
            text-decoration: underline;
        }}

        .footer a:hover {{
            text-decoration: none;
        }}

        /* Mobile responsive */
        @media only screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
                border-radius: 0 !important;
            }}
            .content {{
                padding: 24px 20px !important;
            }}
            .header {{
                padding: 24px 16px !important;
            }}
            .header h1 {{
                font-size: 20px !important;
            }}
            .product-item {{
                width: 100% !important;
                max-width: 250px !important;
                display: block !important;
                margin: 0 auto 16px !important;
            }}
            .cta-button {{
                padding: 14px 28px !important;
                font-size: 15px !important;
            }}
            .footer {{
                padding: 20px 16px !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="preview-text">{html_module.escape(preview_text or '')}</div>
    <table role="presentation" class="email-wrapper" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center" style="padding: 24px 16px;">
                <table role="presentation" class="email-container" width="600" cellpadding="0" cellspacing="0" border="0">
                    <!-- Header -->
                    <tr>
                        <td class="header">
                            <h1>{escaped_subject}</h1>
                        </td>
                    </tr>
"""

        if hero_image_url:
            template += f"""                    <!-- Hero Image -->
                    <tr>
                        <td>
                            <img src="{hero_image_url}" alt="{escaped_subject}" class="hero-image" />
                        </td>
                    </tr>
"""

        template += f"""                    <!-- Content -->
                    <tr>
                        <td class="content">
                            <div class="greeting">{html_module.escape(greeting_text)}</div>

                            <div class="body-text">
                                {body_html}
                            </div>

                            <div class="cta-wrapper">
                                <a href="{cta['url']}" class="cta-button">{html_module.escape(cta['text'])}</a>
                            </div>
"""

        if cta.get("style"):
            template += f"""                            <div class="cta-subtext">{html_module.escape(cta['style'])}</div>
"""

        if product_image_urls:
            template += """                            <div class="products-section">
                                <h2>Featured Products</h2>
                                <div class="product-grid">
"""
            for i, img_url in enumerate(product_image_urls):
                template += f"""                                    <div class="product-item">
                                        <img src="{img_url}" alt="Product {i + 1}" class="product-image" />
                                    </div>
"""
            template += """                                </div>
                            </div>
"""

        template += f"""
                            <hr class="divider" />
                            <div class="closing">
                                {html_module.escape(closing_text)}
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td class="footer">
"""

        template += self._render_footer_html(footer_parsed, color_scheme)

        template += """                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        return template

    def _get_color_scheme_for_tone(self, tone: str) -> Dict[str, str]:
        """Get color scheme based on tone."""
        schemes = {
            "professional": {
                "primary": "#2c3e50",
                "secondary": "#3498db",
                "background": "#f4f4f7",
                "text": "#333333",
            },
            "casual": {
                "primary": "#e74c3c",
                "secondary": "#f39c12",
                "background": "#fdf6f0",
                "text": "#2c3e50",
            },
            "urgent": {
                "primary": "#c0392b",
                "secondary": "#e74c3c",
                "background": "#fdf2f2",
                "text": "#333333",
            },
            "friendly": {
                "primary": "#27ae60",
                "secondary": "#2ecc71",
                "background": "#f0faf4",
                "text": "#2c3e50",
            },
        }
        return schemes.get(tone.lower(), schemes["professional"])

    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color by a factor."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "#333333"
        try:
            r = int(int(hex_color[0:2], 16) * factor)
            g = int(int(hex_color[2:4], 16) * factor)
            b = int(int(hex_color[4:6], 16) * factor)
            return f"#{min(r, 255):02x}{min(g, 255):02x}{min(b, 255):02x}"
        except ValueError:
            return "#333333"

    def _lighten_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Lighten a hex color by blending toward white."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "#666666"
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            return f"#{min(r, 255):02x}{min(g, 255):02x}{min(b, 255):02x}"
        except ValueError:
            return "#666666"

    def _safe_parse_literal(self, value: str) -> Any:
        """Safely parse a Python literal (handles single-quoted dicts/lists from LLM output)."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, (dict, list)):
                return parsed
        except (ValueError, SyntaxError):
            pass
        return None

    def _parse_text_parts(self, value: Any) -> Union[str, List[str]]:
        """
        Parse text_parts: handles JSON arrays, Python-style dicts, and
        newline-separated dict strings from LLM output.
        Returns List[str] when value is/parses to that array; otherwise returns str.
        """
        if value is None:
            return ""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ""

            # First, check for newline-separated dicts — this must come before
            # the single-dict check because multi-line strings starting with '{'
            # would otherwise be misrouted to the single-dict branch.
            lines = [l.strip() for l in value.split("\n") if l.strip()]
            if len(lines) > 1 and all(l.startswith("{") for l in lines):
                parts = []
                for line in lines:
                    parsed = self._safe_parse_literal(line)
                    if isinstance(parsed, dict) and "text" in parsed:
                        parts.append(str(parsed["text"]).strip())
                    else:
                        parts.append(line)
                return parts if parts else value

            # Try parsing as a JSON/Python array
            if value.startswith("["):
                parsed = self._safe_parse_literal(value)
                if isinstance(parsed, list):
                    value = parsed
                else:
                    return value
            # Try parsing as a single dict
            elif value.startswith("{"):
                parsed = self._safe_parse_literal(value)
                if isinstance(parsed, dict) and "text" in parsed:
                    return [str(parsed["text"]).strip()]
                return value
            else:
                return value

        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]).strip())
                elif isinstance(item, str):
                    parsed = self._safe_parse_literal(item)
                    if isinstance(parsed, dict) and "text" in parsed:
                        parts.append(str(parsed["text"]).strip())
                    else:
                        parts.append(item.strip())
                elif item is not None:
                    parts.append(str(item).strip())
            return parts if parts else ""
        if isinstance(value, dict) and "text" in value:
            return [str(value["text"]).strip()]
        return str(value)

    def _body_to_html(self, body_parsed: Union[str, List[str]]) -> str:
        """Render body as HTML paragraphs."""
        if isinstance(body_parsed, list):
            paragraphs = "".join(
                f"<p>{html_module.escape(part)}</p>\n" for part in body_parsed if part
            )
            return paragraphs if paragraphs else ""
        return self._format_body_text(body_parsed)

    # Style values that are layout hints, not descriptive text for the user
    _CTA_STYLE_IGNORE = {"button", "link", "text", "primary", "secondary", "default"}

    def _parse_cta(self, value: Any) -> Dict[str, Optional[str]]:
        """
        Parse call_to_action: dict with text, url, style, button_color/color.
        Handles both JSON and Python-style dict strings.
        """
        default: Dict[str, Optional[str]] = {"text": "Learn More", "url": "#", "style": None, "button_color": None}
        if value is None or (isinstance(value, str) and not value.strip()):
            return default
        if isinstance(value, str):
            value_stripped = value.strip()
            if value_stripped.startswith("{"):
                parsed = self._safe_parse_literal(value_stripped)
                if isinstance(parsed, dict):
                    value = parsed
                else:
                    return {"text": value_stripped, "url": "#", "style": None, "button_color": None}
            else:
                return {"text": value_stripped, "url": "#", "style": None, "button_color": None}
        if isinstance(value, dict):
            # Extract style — ignore values that are just layout hints (e.g. "button")
            raw_style = str(value["style"]).strip() if value.get("style") else None
            if raw_style and raw_style.lower() in self._CTA_STYLE_IGNORE:
                raw_style = None

            # Accept both "button_color" and "color" keys
            btn_color = value.get("button_color") or value.get("color")
            return {
                "text": str(value.get("text") or default["text"]).strip(),
                "url": str(value.get("url") or default["url"]).strip() or "#",
                "style": raw_style,
                "button_color": str(btn_color).strip() if btn_color else None,
            }
        return default

    def _parse_footer(self, value: Any) -> Dict[str, Optional[str]]:
        """Parse footer content, handling dict with text and unsubscribe_link."""
        default: Dict[str, Optional[str]] = {"text": None, "unsubscribe_link": None}
        if value is None:
            return default
        if isinstance(value, str):
            value_stripped = value.strip()
            if value_stripped.startswith("{"):
                parsed = self._safe_parse_literal(value_stripped)
                if isinstance(parsed, dict):
                    return {
                        "text": str(parsed.get("text", "")).strip() or None,
                        "unsubscribe_link": str(parsed.get("unsubscribe_link", "")).strip() or None,
                    }
            return {"text": value_stripped or None, "unsubscribe_link": None}
        if isinstance(value, dict):
            return {
                "text": str(value.get("text", "")).strip() or None,
                "unsubscribe_link": str(value.get("unsubscribe_link", "")).strip() or None,
            }
        if isinstance(value, list):
            combined = " ".join(str(v) for v in value if v)
            return self._parse_footer(combined)
        return default

    def _render_footer_html(self, footer_data: Dict[str, Optional[str]], color_scheme: Dict[str, str]) -> str:
        """Render footer as HTML with proper links."""
        text = footer_data.get("text")
        unsub_link = footer_data.get("unsubscribe_link") or "#"

        if text:
            footer_text = html_module.escape(text)
            # Replace pipe-separated links with actual anchor tags
            footer_text = re.sub(
                r"Unsubscribe",
                f'<a href="{unsub_link}">Unsubscribe</a>',
                footer_text,
                flags=re.IGNORECASE,
            )
            footer_text = re.sub(
                r"Privacy Policy",
                '<a href="#">Privacy Policy</a>',
                footer_text,
                flags=re.IGNORECASE,
            )
            footer_text = re.sub(
                r"Contact Us",
                '<a href="#">Contact Us</a>',
                footer_text,
                flags=re.IGNORECASE,
            )
            return f"                            <p>{footer_text}</p>\n"

        return f"""                            <p>Thank you for being a valued customer!</p>
                            <p><a href="{unsub_link}">Unsubscribe</a> | <a href="#">Privacy Policy</a></p>
"""

    def _format_body_text(self, body: str) -> str:
        """Format body text with proper paragraph breaks."""
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = [body] if body else [""]

        formatted = ""
        for para in paragraphs:
            formatted += f"<p>{html_module.escape(para)}</p>\n"
        return formatted






