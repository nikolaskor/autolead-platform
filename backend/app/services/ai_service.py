"""
AI Service for generating Norwegian car sales responses using Claude API.

Features:
- Norwegian language responses
- Contextual responses based on lead data
- Professional dealership tone
- Vehicle interest awareness
- Error handling and retries
"""
import logging
from typing import Optional
from anthropic import Anthropic
from ..core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for generating AI responses to customer inquiries."""

    def __init__(self):
        """Initialize Claude API client."""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Please provide a valid API key in your configuration."
            )
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude 3.5 Sonnet

    def generate_initial_response(
        self,
        customer_name: str,
        vehicle_interest: Optional[str],
        customer_message: str,
        dealership_name: str,
        dealership_phone: Optional[str] = None,
        dealership_email: Optional[str] = None,
        available_vehicles: Optional[list] = None
    ) -> dict:
        """
        Generate initial AI response to a new lead inquiry.

        Args:
            customer_name: Name of the customer
            vehicle_interest: Vehicle they're interested in
            customer_message: Their inquiry message
            dealership_name: Name of the dealership
            dealership_phone: Dealership phone number
            dealership_email: Dealership email
            available_vehicles: List of vehicles in stock (optional)

        Returns:
            dict with the following keys:
                - response (str): The generated response text.
                - confidence (float): Confidence score for the response (0.9 for successful AI generation, 0.3 for fallback).
                - model (str): The model used to generate the response ("claude-3-5-sonnet-20241022" on success, "fallback" on failure).
                - tokens_used (int): Number of tokens used in the API call (present only on success).
                - error (str): Error message (present only on failure).
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(
                dealership_name=dealership_name,
                dealership_phone=dealership_phone,
                dealership_email=dealership_email,
                available_vehicles=available_vehicles
            )

            # Build user prompt
            user_prompt = self._build_initial_response_prompt(
                customer_name=customer_name,
                vehicle_interest=vehicle_interest,
                customer_message=customer_message
            )

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,  # Keep responses concise
                temperature=0.7,  # Balanced creativity
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract response
            response_text = message.content[0].text

            logger.info(
                f"AI response generated for {customer_name}",
                extra={
                    "customer_name": customer_name,
                    "vehicle_interest": vehicle_interest,
                    "tokens_used": message.usage.input_tokens + message.usage.output_tokens
                }
            )

            return {
                "response": response_text,
                "confidence": 0.9,  # High confidence for Claude 3.5
                "model": self.model,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}")
            # Return fallback response
            return {
                "response": self._get_fallback_response(
                    customer_name=customer_name,
                    dealership_name=dealership_name
                ),
                "confidence": 0.3,  # Low confidence (fallback)
                "model": "fallback",
                "error": str(e)
            }

    def generate_follow_up_response(
        self,
        customer_name: str,
        vehicle_interest: Optional[str],
        previous_conversation: list[dict],
        dealership_name: str,
        follow_up_number: int = 1
    ) -> dict:
        """
        Generate follow-up message for a lead that hasn't responded.

        Args:
            customer_name: Name of the customer
            vehicle_interest: Vehicle they're interested in
            previous_conversation: List of previous messages
            dealership_name: Name of the dealership
            follow_up_number: Which follow-up this is (1, 2, 3...)

        Returns:
            dict with the following keys:
                - response (str): The generated follow-up message.
                - confidence (float): Confidence score for the response (0.85 for successful AI generation, 0.3 for fallback).
                - model (str): The model used to generate the response ("claude-3-5-sonnet-20241022" on success, "fallback" on failure).
                - tokens_used (int): Number of tokens used in the response (present only on success).
                - error (str): Error message if response generation failed (present only on failure).
        """
        try:
            system_prompt = f"""Du er en hjelpsom kundeservicerepresentant for {dealership_name},
en bilforhandler i Norge. Du følger opp en kunde som ikke har svart på den opprinnelige henvendelsen.

Regler for oppfølging:
- Vær kort og uformell (1-2 setninger)
- Vis interesse uten å være påtrengende
- Tilby hjelp eller spør om de fortsatt er interessert
- Ikke gjenta det du allerede har sagt
- Hold en vennlig og profesjonell tone
- Svar alltid på norsk
"""

            # Build conversation context
            conversation_context = "\n".join([
                f"{'Kunde' if msg['sender_type'] == 'customer' else 'Oss'}: {msg['message']}"
                for msg in previous_conversation
            ])

            user_prompt = f"""Kunde: {customer_name}
Interessert i: {vehicle_interest or 'Ikke spesifisert'}
Oppfølging nr: {follow_up_number}

Tidligere samtale:
{conversation_context}

Generer en kort oppfølgingsmelding som:
1. Er venlig og ikke påtrengende
2. Spør om de fortsatt er interessert
3. Tilbyr hjelp
4. Er maks 2-3 setninger
"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.8,  # Slightly more creative for variety
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = message.content[0].text

            return {
                "response": response_text,
                "confidence": 0.85,
                "model": self.model,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Follow-up generation failed: {str(e)}")
            return {
                "response": self._get_fallback_followup(customer_name),
                "confidence": 0.3,
                "model": "fallback",
                "error": str(e)
            }

    def _build_system_prompt(
        self,
        dealership_name: str,
        dealership_phone: Optional[str],
        dealership_email: Optional[str],
        available_vehicles: Optional[list]
    ) -> str:
        """Build the system prompt for Claude."""
        base_prompt = f"""Du er en hjelpsom kundeservicerepresentant for {dealership_name},
en bilforhandler i Norge. Din oppgave er å svare raskt og profesjonelt på
kundehenvendelser om biler.

Regler for svar:
- Svar alltid på norsk (bokmål)
- Vær høflig, vennlig og profesjonell
- Bekreft kundens interesse
- Fortell at en selger vil ta kontakt snart
- IKKE forhandle priser eller love noe som ikke er bekreftet
- IKKE oppgi kontaktinformasjon (den kommer i signaturen)
- Hold svar kort og konsist (2-4 setninger)
- Bruk et varmt og imøtekommende språk

"""

        # Add contact info if available
        if dealership_phone or dealership_email:
            base_prompt += f"\nForhandlerens kontaktinformasjon:\n"
            if dealership_phone:
                base_prompt += f"- Telefon: {dealership_phone}\n"
            if dealership_email:
                base_prompt += f"- E-post: {dealership_email}\n"

        # Add inventory context if available
        if available_vehicles:
            inventory_str = "\n".join([
                f"- {v.get('make')} {v.get('model')} ({v.get('year')})"
                for v in available_vehicles[:5]  # Show max 5
            ])
            base_prompt += f"\nBiler på lager:\n{inventory_str}\n"
            base_prompt += "\nHvis kunden spør om en bil på lager, sjekk listen og gi relevant informasjon.\n"

        return base_prompt

    def _build_initial_response_prompt(
        self,
        customer_name: str,
        vehicle_interest: Optional[str],
        customer_message: str
    ) -> str:
        """Build the user prompt for initial response."""
        return f"""Kunde: {customer_name}
Interessert i: {vehicle_interest or 'Ikke spesifisert'}
Melding: {customer_message}

Generer et venlig svar som:
1. Takker kunden for henvendelsen
2. Bekrefter interesse i kjøretøyet (hvis spesifisert)
3. Forteller at en selger vil kontakte dem snart (innen 24 timer)
4. Er varmt og inviterende

Maks 3-4 setninger. Ikke inkluder signatur eller kontaktinfo."""

    def _get_fallback_response(
        self,
        customer_name: str,
        dealership_name: str
    ) -> str:
        """Get fallback response if AI fails."""
        return f"""Hei {customer_name}!

Takk for din henvendelse til {dealership_name}. Vi setter stor pris på din interesse.

En av våre selgere vil ta kontakt med deg så snart som mulig, normalt innen 24 timer, for å hjelpe deg videre.

Med vennlig hilsen,
{dealership_name}"""

    def _get_fallback_followup(self, customer_name: str) -> str:
        """Get fallback follow-up message."""
        return f"""Hei {customer_name}!

Vi håper du fortsatt er interessert. Ta gjerne kontakt hvis du har spørsmål.

Vennlig hilsen"""


# Global AI service instance
ai_service = AIService()
