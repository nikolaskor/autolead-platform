"""
Embed code generation endpoints.
Provides API to generate HTML/JavaScript embed codes for dealership websites.
"""
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional

from ....core.config import settings
from ....api.deps import get_current_user, get_current_dealership
from ....models.user import User
from ....models.dealership import Dealership
from ....utils.embed_code import (
    generate_html_form,
    generate_javascript_snippet,
    generate_embed_code_docs,
)

router = APIRouter()


@router.get("/embed/form-html")
def get_html_form_code(
    custom_css: Optional[str] = Query(None, description="Custom CSS to style the form"),
    redirect_url: Optional[str] = Query(None, description="URL to redirect after submission"),
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
) -> Dict[str, str]:
    """
    Generate standalone HTML form code for embedding on dealership website.

    Returns complete HTML code including styling and JavaScript to handle
    form submissions to the Norvalt webhook.

    - **custom_css**: Optional custom CSS to override default styling
    - **redirect_url**: Optional URL to redirect users after successful submission

    Returns:
        Dictionary with HTML code and instructions
    """

    # Use configured API URL
    api_base_url = settings.API_URL

    code = generate_html_form(
        dealership_id=str(dealership.id),
        api_base_url=api_base_url,
        custom_css=custom_css,
        redirect_url=redirect_url,
    )

    return {
        "code": code,
        "dealership_id": str(dealership.id),
        "dealership_name": dealership.name,
        "instructions": [
            "Copy the HTML code below",
            "Paste it into your website where you want the form to appear",
            "The form is fully styled and functional",
            "Test by submitting the form - you'll see the lead in your dashboard"
        ]
    }


@router.get("/embed/javascript")
def get_javascript_snippet(
    form_selector: str = Query("#contact-form", description="CSS selector for your existing form"),
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
) -> Dict[str, str]:
    """
    Generate JavaScript snippet to enhance existing form on dealership website.

    This script intercepts form submissions and sends data to Norvalt webhook
    while maintaining your existing form's look and feel.

    - **form_selector**: CSS selector for your form (e.g., "#contact-form", ".lead-form")

    Returns:
        Dictionary with JavaScript code and instructions
    """

    api_base_url = settings.API_URL

    code = generate_javascript_snippet(
        dealership_id=str(dealership.id),
        api_base_url=api_base_url,
        form_selector=form_selector,
    )

    return {
        "code": code,
        "dealership_id": str(dealership.id),
        "dealership_name": dealership.name,
        "form_selector": form_selector,
        "instructions": [
            "Copy the JavaScript code below",
            "Paste it before the closing </body> tag in your HTML",
            "Update the form_selector if your form has a different ID/class",
            "Ensure your form has fields: name, email, message",
            "Test by submitting your form"
        ]
    }


@router.get("/embed/docs")
def get_embed_documentation(
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
) -> Dict[str, Any]:
    """
    Get complete embed code documentation with all integration options.

    Returns documentation for:
    - Standalone HTML form
    - JavaScript snippet for existing forms
    - Direct API integration details

    Useful for displaying in dashboard or sending to technical contacts.

    Returns:
        Complete documentation with all embed options and instructions
    """

    api_base_url = settings.API_URL

    docs = generate_embed_code_docs(
        dealership_id=str(dealership.id),
        api_base_url=api_base_url,
    )

    docs["dealership_name"] = dealership.name

    return docs
