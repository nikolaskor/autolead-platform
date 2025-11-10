"""
Utility functions for generating embed code for dealership websites.

This module provides functions to generate HTML/JavaScript code that dealerships
can embed on their websites to capture leads via the form webhook.
"""

from typing import Dict, Any, Optional


def generate_html_form(
    dealership_id: str,
    api_base_url: str,
    custom_css: Optional[str] = None,
    redirect_url: Optional[str] = None,
) -> str:
    """
    Generate a standalone HTML form that posts to the webhook endpoint.

    Args:
        dealership_id: UUID of the dealership
        api_base_url: Base URL of the API (e.g., https://api.norvalt.no)
        custom_css: Optional custom CSS to style the form
        redirect_url: Optional URL to redirect after successful submission

    Returns:
        HTML code as a string
    """

    default_css = """
        <style>
            .norvalt-lead-form {
                max-width: 500px;
                margin: 0 auto;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 8px;
                font-family: Arial, sans-serif;
            }
            .norvalt-lead-form h2 {
                margin-top: 0;
                color: #333;
            }
            .norvalt-form-group {
                margin-bottom: 15px;
            }
            .norvalt-form-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: bold;
            }
            .norvalt-form-group input,
            .norvalt-form-group textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                box-sizing: border-box;
            }
            .norvalt-form-group textarea {
                min-height: 100px;
                resize: vertical;
            }
            .norvalt-submit-btn {
                background: #1a73e8;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }
            .norvalt-submit-btn:hover {
                background: #1557b0;
            }
            .norvalt-submit-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .norvalt-success-message {
                background: #d4edda;
                color: #155724;
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 15px;
                display: none;
            }
            .norvalt-error-message {
                background: #f8d7da;
                color: #721c24;
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 15px;
                display: none;
            }
        </style>
    """

    css = custom_css if custom_css else default_css

    redirect_js = f"""
        setTimeout(() => {{
            window.location.href = '{redirect_url}';
        }}, 2000);
    """ if redirect_url else ""

    html = f"""
<!-- Norvalt Lead Capture Form -->
<!-- Dealership ID: {dealership_id} -->
{css}

<div class="norvalt-lead-form">
    <h2>Kontakt oss</h2>

    <div class="norvalt-success-message" id="norvaltSuccessMessage">
        Takk for din henvendelse! Vi tar kontakt med deg snart.
    </div>

    <div class="norvalt-error-message" id="norvaltErrorMessage">
        Noe gikk galt. Vennligst prøv igjen.
    </div>

    <form id="norvaltLeadForm">
        <div class="norvalt-form-group">
            <label for="norvalt-name">Navn *</label>
            <input type="text" id="norvalt-name" name="name" required>
        </div>

        <div class="norvalt-form-group">
            <label for="norvalt-email">E-post *</label>
            <input type="email" id="norvalt-email" name="email" required>
        </div>

        <div class="norvalt-form-group">
            <label for="norvalt-phone">Telefon</label>
            <input type="tel" id="norvalt-phone" name="phone">
        </div>

        <div class="norvalt-form-group">
            <label for="norvalt-vehicle">Interessert i kjøretøy</label>
            <input type="text" id="norvalt-vehicle" name="vehicle_interest" placeholder="F.eks. Tesla Model 3">
        </div>

        <div class="norvalt-form-group">
            <label for="norvalt-message">Melding *</label>
            <textarea id="norvalt-message" name="message" required placeholder="Skriv din melding her..."></textarea>
        </div>

        <button type="submit" class="norvalt-submit-btn" id="norvaltSubmitBtn">
            Send henvendelse
        </button>
    </form>
</div>

<script>
(function() {{
    const form = document.getElementById('norvaltLeadForm');
    const submitBtn = document.getElementById('norvaltSubmitBtn');
    const successMsg = document.getElementById('norvaltSuccessMessage');
    const errorMsg = document.getElementById('norvaltErrorMessage');

    form.addEventListener('submit', async function(e) {{
        e.preventDefault();

        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sender...';

        // Hide previous messages
        successMsg.style.display = 'none';
        errorMsg.style.display = 'none';

        // Collect form data
        const formData = {{
            name: document.getElementById('norvalt-name').value,
            email: document.getElementById('norvalt-email').value,
            phone: document.getElementById('norvalt-phone').value || null,
            vehicle_interest: document.getElementById('norvalt-vehicle').value || null,
            message: document.getElementById('norvalt-message').value,
            source_url: window.location.href
        }};

        try {{
            const response = await fetch('{api_base_url}/webhooks/form/{dealership_id}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(formData)
            }});

            if (response.ok) {{
                // Show success message
                successMsg.style.display = 'block';
                form.reset();
                {redirect_js}
            }} else {{
                // Show error message
                errorMsg.style.display = 'block';
            }}
        }} catch (error) {{
            console.error('Error:', error);
            errorMsg.style.display = 'block';
        }} finally {{
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send henvendelse';
        }}
    }});
}})();
</script>
<!-- End Norvalt Lead Capture Form -->
"""

    return html


def generate_javascript_snippet(
    dealership_id: str,
    api_base_url: str,
    form_selector: str = "#contact-form",
) -> str:
    """
    Generate JavaScript code to enhance an existing form on the dealership website.

    This snippet can be added to a page with an existing form to capture submissions
    and send them to the Norvalt webhook.

    Args:
        dealership_id: UUID of the dealership
        api_base_url: Base URL of the API
        form_selector: CSS selector for the form (default: #contact-form)

    Returns:
        JavaScript code as a string
    """

    js = f"""
<!-- Norvalt Lead Capture Integration -->
<!-- Dealership ID: {dealership_id} -->
<script>
(function() {{
    const form = document.querySelector('{form_selector}');
    if (!form) {{
        console.error('Norvalt: Form not found with selector "{form_selector}"');
        return;
    }}

    form.addEventListener('submit', async function(e) {{
        e.preventDefault();

        // Extract form data
        const formData = new FormData(form);
        const data = {{
            name: formData.get('name') || formData.get('customer_name'),
            email: formData.get('email') || formData.get('customer_email'),
            phone: formData.get('phone') || formData.get('customer_phone') || null,
            vehicle_interest: formData.get('vehicle_interest') || formData.get('vehicle') || null,
            message: formData.get('message') || formData.get('comments') || '',
            source_url: window.location.href
        }};

        // Validate required fields
        if (!data.name || !data.email || !data.message) {{
            alert('Vennligst fyll ut alle påkrevde felt');
            return;
        }}

        try {{
            const response = await fetch('{api_base_url}/webhooks/form/{dealership_id}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(data)
            }});

            if (response.ok) {{
                // Allow form to submit normally or show custom success message
                alert('Takk for din henvendelse! Vi tar kontakt med deg snart.');
                form.reset();
            }} else {{
                console.error('Norvalt webhook error:', await response.text());
                // Allow form to submit normally as fallback
                form.submit();
            }}
        }} catch (error) {{
            console.error('Norvalt error:', error);
            // Allow form to submit normally as fallback
            form.submit();
        }}
    }});

    console.log('Norvalt lead capture initialized');
}})();
</script>
<!-- End Norvalt Integration -->
"""

    return js


def generate_embed_code_docs(dealership_id: str, api_base_url: str) -> Dict[str, Any]:
    """
    Generate complete embed code documentation for a dealership.

    Returns a dictionary with different integration options.

    Args:
        dealership_id: UUID of the dealership
        api_base_url: Base URL of the API

    Returns:
        Dictionary with embed code options and instructions
    """

    return {
        "dealership_id": dealership_id,
        "api_base_url": api_base_url,
        "options": {
            "standalone_form": {
                "title": "Standalone HTML Form",
                "description": "Complete form with styling that can be embedded anywhere on your website",
                "code": generate_html_form(dealership_id, api_base_url),
                "instructions": [
                    "Copy the entire HTML code below",
                    "Paste it into your website where you want the form to appear",
                    "Customize the CSS styles if needed",
                    "Test by submitting the form"
                ]
            },
            "existing_form": {
                "title": "Enhance Existing Form",
                "description": "JavaScript snippet to capture submissions from your existing contact form",
                "code": generate_javascript_snippet(dealership_id, api_base_url),
                "instructions": [
                    "Add this script tag before the closing </body> tag",
                    "Update the form selector if your form has a different ID/class",
                    "Ensure your form has fields: name, email, message",
                    "Optional fields: phone, vehicle_interest",
                    "Test by submitting your form"
                ]
            },
            "direct_api": {
                "title": "Direct API Integration",
                "description": "Use the webhook API directly from your backend",
                "endpoint": f"{api_base_url}/webhooks/form/{dealership_id}",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body_example": {
                    "name": "Ola Nordmann",
                    "email": "ola@example.com",
                    "phone": "+47 123 45 678",
                    "vehicle_interest": "Tesla Model 3",
                    "message": "I'm interested in a test drive",
                    "source_url": "https://yourdealership.no/contact"
                },
                "response_example": {
                    "lead_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "created"
                }
            }
        },
        "notes": [
            "All form submissions are automatically processed within 90 seconds",
            "Customers will receive an AI-generated response via email",
            "Sales reps will be notified via SMS",
            "Duplicate submissions within 5 minutes will update the existing lead",
            "Monitor webhook performance in your Norvalt dashboard"
        ]
    }
