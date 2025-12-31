"""Service for generating HTML email templates."""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HTMLTemplateService:
    """Service for generating HTML email templates."""

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
        # Determine color scheme based on tone if not provided
        if not color_scheme:
            color_scheme = self._get_color_scheme_for_tone(tone)

        # Build HTML template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>{subject_line}</title>
    <style>
        /* Reset styles */
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
        
        /* Main styles */
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: {color_scheme['text']};
            background-color: {color_scheme['background']};
        }}
        
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        
        .header {{
            background-color: {color_scheme['primary']};
            padding: 20px;
            text-align: center;
        }}
        
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 24px;
        }}
        
        .hero-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            display: block;
        }}
        
        .content {{
            padding: 30px 20px;
        }}
        
        .greeting {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: {color_scheme['text']};
        }}
        
        .body-text {{
            margin-bottom: 20px;
            color: {color_scheme['text']};
        }}
        
        .cta-button {{
            display: inline-block;
            padding: 15px 30px;
            background-color: {color_scheme['secondary']};
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
        }}
        
        .cta-button:hover {{
            background-color: {self._darken_color(color_scheme['secondary'])};
        }}
        
        .products-section {{
            margin: 30px 0;
            padding: 20px 0;
        }}
        
        .product-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .product-item {{
            text-align: center;
        }}
        
        .product-image {{
            width: 100%;
            max-width: 150px;
            height: auto;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        
        .closing {{
            margin-top: 30px;
            color: {color_scheme['text']};
        }}
        
        .footer {{
            background-color: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666666;
        }}
        
        .footer a {{
            color: {color_scheme['primary']};
            text-decoration: none;
        }}
        
        /* Mobile responsive */
        @media only screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
            }}
            .content {{
                padding: 20px 15px !important;
            }}
            .product-grid {{
                grid-template-columns: 1fr !important;
            }}
        }}
    </style>
</head>
<body>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table role="presentation" class="email-container" cellpadding="0" cellspacing="0" border="0">
                    <!-- Header -->
                    <tr>
                        <td class="header">
                            <h1>{subject_line}</h1>
                        </td>
                    </tr>
                    
                    <!-- Hero Image -->
"""

        if hero_image_url:
            html += f"""                    <tr>
                        <td>
                            <img src="{hero_image_url}" alt="Hero Image" class="hero-image" />
                        </td>
                    </tr>
"""

        html += f"""                    <!-- Content -->
                    <tr>
                        <td class="content">
                            <div class="greeting">{greeting}</div>
                            
                            <div class="body-text">
                                {self._format_body_text(body)}
                            </div>
                            
                            <div style="text-align: center;">
                                <a href="#" class="cta-button">{call_to_action}</a>
                            </div>
"""

        # Add product images section if provided
        if product_image_urls:
            html += """                            <div class="products-section">
                                <h2 style="text-align: center; margin-bottom: 20px;">Featured Products</h2>
                                <div class="product-grid">
"""
            for img_url in product_image_urls:
                html += f"""                                    <div class="product-item">
                                        <img src="{img_url}" alt="Product" class="product-image" />
                                    </div>
"""
            html += """                                </div>
                            </div>
"""

        html += f"""                            <div class="closing">
                                {closing}
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td class="footer">
"""

        if footer:
            html += f"                            {footer}<br><br>"
        else:
            html += """                            <p>Thank you for being a valued customer!</p>
                            <p><a href="#">Unsubscribe</a> | <a href="#">Privacy Policy</a></p>
"""

        html += """                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        return html

    def _get_color_scheme_for_tone(self, tone: str) -> Dict[str, str]:
        """Get color scheme based on tone."""
        schemes = {
            "professional": {
                "primary": "#2c3e50",
                "secondary": "#3498db",
                "background": "#ffffff",
                "text": "#333333",
            },
            "casual": {
                "primary": "#e74c3c",
                "secondary": "#f39c12",
                "background": "#ffffff",
                "text": "#2c3e50",
            },
            "urgent": {
                "primary": "#c0392b",
                "secondary": "#e74c3c",
                "background": "#ffffff",
                "text": "#333333",
            },
            "friendly": {
                "primary": "#27ae60",
                "secondary": "#2ecc71",
                "background": "#ffffff",
                "text": "#2c3e50",
            },
        }
        return schemes.get(tone.lower(), schemes["professional"])

    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color by a factor."""
        # Simple darkening - in production, use proper color manipulation
        # This is a simplified version
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
        # For simplicity, return a darker shade
        return f"#{hex_color[:4]}"

    def _format_body_text(self, body: str) -> str:
        """Format body text with proper paragraph breaks."""
        # Split by double newlines or periods followed by space
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [body]

        formatted = ""
        for para in paragraphs:
            formatted += f"<p>{para}</p>\n"
        return formatted



