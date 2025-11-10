"""
Email processing service for classifying and extracting lead data from emails.

This service handles:
1. Pre-filtering (spam detection)
2. AI classification (Claude API)
3. Lead extraction (for sales inquiries)
"""
import json
import re
from typing import Optional, Dict, Any, Tuple
from anthropic import Anthropic
from sqlalchemy.orm import Session

from ..models.email import Email
from ..models.lead import Lead
from ..schemas.email import EmailClassificationResult, EmailLeadExtraction
from ..core.config import settings


# Known spam domains (basic list - expand as needed)
SPAM_DOMAINS = {
    "spam.com",
    "test.com",
    "example.com",
    # Add more spam domains
}

# Spam indicators in subject/body
SPAM_KEYWORDS = [
    "unsubscribe",
    "click here to opt out",
    "this is an advertisement",
    "viagra",
    "cialis",
    "casino",
    "lottery",
    "congratulations you've won",
]


class EmailProcessor:
    """Service for processing incoming emails."""

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize with Anthropic API client."""
        # Use provided key or get from settings
        api_key = anthropic_api_key or getattr(settings, 'ANTHROPIC_API_KEY', None)
        self.anthropic_client = Anthropic(api_key=api_key) if api_key else None

    def pre_filter_spam(self, email: Email) -> Tuple[bool, Optional[str]]:
        """
        Pre-filter obvious spam before AI classification.

        Args:
            email: Email model instance

        Returns:
            Tuple of (is_spam, reason)
        """
        # Check sender domain
        if email.from_email:
            domain = email.from_email.split('@')[-1].lower()
            if domain in SPAM_DOMAINS:
                return True, f"Sender domain '{domain}' is blacklisted"

        # Check for spam keywords in subject
        if email.subject:
            subject_lower = email.subject.lower()
            for keyword in SPAM_KEYWORDS:
                if keyword in subject_lower:
                    return True, f"Subject contains spam keyword: '{keyword}'"

        # Check for spam keywords in body
        body = email.body_text or email.body_html or ""
        body_lower = body.lower()
        for keyword in SPAM_KEYWORDS:
            if keyword in body_lower:
                return True, f"Body contains spam keyword: '{keyword}'"

        # Check for excessive links (newsletters often have many links)
        if email.body_html:
            link_count = len(re.findall(r'<a\s+href=', email.body_html, re.IGNORECASE))
            if link_count > 10:
                return True, f"Email contains {link_count} links (likely newsletter/marketing)"

        # Check for unsubscribe links (marketing emails)
        if email.body_html and 'unsubscribe' in body_lower:
            return True, "Email contains unsubscribe link (likely newsletter)"

        return False, None

    def classify_email(self, email: Email) -> EmailClassificationResult:
        """
        Classify email using Claude API.

        Args:
            email: Email model instance

        Returns:
            EmailClassificationResult with classification, confidence, and reasoning
        """
        if not self.anthropic_client:
            # Fallback if no API key configured
            return EmailClassificationResult(
                classification="uncertain",
                confidence=0.0,
                reasoning="No Anthropic API key configured for classification"
            )

        # Build email content for analysis
        email_content = f"""
Email Metadata:
- From: {email.from_name or ''} <{email.from_email}>
- To: {email.to_email}
- Subject: {email.subject or '(no subject)'}

Email Body:
{email.body_text or email.body_html or '(empty)'}
""".strip()

        prompt = f"""Analyze this email and classify it into one of these categories:

1. **sales_inquiry**: Customer is interested in buying, test driving, or learning more about a car
2. **spam**: Marketing emails, scams, irrelevant automated messages
3. **other**: Internal communication, vendor emails, general inquiries not related to car sales
4. **uncertain**: Cannot determine with confidence (needs human review)

Email to analyze:
{email_content}

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "classification": "sales_inquiry|spam|other|uncertain",
  "confidence": 0.85,
  "reasoning": "Brief explanation of why this email was classified this way"
}}"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Try to parse JSON (handle potential markdown code blocks)
            if response_text.startswith('```'):
                # Extract JSON from markdown code block
                json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            result = json.loads(response_text)

            return EmailClassificationResult(
                classification=result["classification"],
                confidence=result["confidence"],
                reasoning=result["reasoning"]
            )

        except Exception as e:
            # If API call fails, mark as uncertain
            return EmailClassificationResult(
                classification="uncertain",
                confidence=0.0,
                reasoning=f"AI classification failed: {str(e)}"
            )

    def extract_lead_data(self, email: Email) -> Optional[EmailLeadExtraction]:
        """
        Extract structured lead data from a sales inquiry email.

        Args:
            email: Email model instance (must be classified as sales_inquiry)

        Returns:
            EmailLeadExtraction with extracted data or None if extraction fails
        """
        if not self.anthropic_client:
            return None

        email_content = f"""
From: {email.from_name or ''} <{email.from_email}>
Subject: {email.subject or '(no subject)'}

Body:
{email.body_text or email.body_html or '(empty)'}
""".strip()

        prompt = f"""Extract lead information from this sales inquiry email about cars.

Email:
{email_content}

Extract the following information and respond ONLY with valid JSON (no markdown, no extra text):
{{
  "customer_name": "Full name if mentioned, otherwise null",
  "email": "Email address (use from_email if not mentioned in body)",
  "phone": "Phone number if mentioned, otherwise null",
  "car_interest": "Which car model(s) they're interested in",
  "inquiry_summary": "Brief 1-2 sentence summary of what they want",
  "urgency": "high|medium|low (based on language like 'urgent', 'asap', 'when available')",
  "source": "toyota.no|volkswagen.no|direct_email|other (infer from email content or domain)"
}}

If a field cannot be determined, use null. For email, use the sender's email address."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text.strip()

            # Extract JSON from markdown code blocks if present
            if response_text.startswith('```'):
                json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            result = json.loads(response_text)

            # Ensure email is set (fallback to sender email)
            if not result.get('email'):
                result['email'] = email.from_email

            return EmailLeadExtraction(**result)

        except Exception as e:
            # If extraction fails, return basic data
            return EmailLeadExtraction(
                customer_name=email.from_name,
                email=email.from_email,
                car_interest=None,
                inquiry_summary=email.subject or "Email inquiry",
                urgency="medium",
                source="email"
            )

    def process_email(self, db: Session, email: Email) -> Email:
        """
        Process an email: classify and extract lead data if applicable.

        Args:
            db: Database session
            email: Email model instance to process

        Returns:
            Updated Email instance
        """
        # Step 1: Pre-filter for spam
        is_spam, spam_reason = self.pre_filter_spam(email)
        if is_spam:
            email.classification = "spam"
            email.classification_confidence = 1.0
            email.classification_reasoning = spam_reason
            email.processing_status = "completed"
            db.commit()
            return email

        # Step 2: AI classification
        email.processing_status = "processing"
        db.commit()

        classification_result = self.classify_email(email)
        email.classification = classification_result.classification
        email.classification_confidence = classification_result.confidence
        email.classification_reasoning = classification_result.reasoning

        # Step 3: Extract lead data if sales inquiry
        if classification_result.classification == "sales_inquiry":
            lead_data = self.extract_lead_data(email)
            if lead_data:
                # Store extracted data
                email.extracted_data = lead_data.model_dump(mode='json')

                # Create lead in database
                try:
                    lead = Lead(
                        dealership_id=email.dealership_id,
                        source="email",
                        source_url=None,
                        source_metadata={
                            "email_id": str(email.id),
                            "from_email": email.from_email,
                            "subject": email.subject
                        },
                        status="new",
                        customer_name=lead_data.customer_name,
                        customer_email=lead_data.email,
                        customer_phone=lead_data.phone,
                        vehicle_interest=lead_data.car_interest,
                        initial_message=lead_data.inquiry_summary,
                        lead_score=70 if lead_data.urgency == "high" else 60 if lead_data.urgency == "medium" else 50
                    )
                    db.add(lead)
                    db.flush()  # Get the lead ID

                    # Link email to lead
                    email.lead_id = lead.id

                except Exception as e:
                    email.error_message = f"Failed to create lead: {str(e)}"
                    email.processing_status = "failed"
                    db.commit()
                    return email

        # Mark as completed
        email.processing_status = "completed"
        db.commit()

        return email


# Global instance (can be configured with API key from settings)
email_processor = EmailProcessor()
