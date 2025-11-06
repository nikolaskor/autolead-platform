"""
Script to add sample leads to your dealership.
This populates your dashboard with test data.

Usage:
    python scripts/add_sample_leads.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import random

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.dealership import Dealership
from app.models.lead import Lead
from app.models.conversation import Conversation


# Sample data for realistic leads
NORWEGIAN_NAMES = [
    "Ola Nordmann", "Kari Hansen", "Lars Olsen", "Ingrid Berg",
    "Erik Johansen", "Silje Andersen", "Magnus Kristiansen", "Anna Larsen",
    "Thomas Pedersen", "Emma Nilsen"
]

VEHICLES = [
    "Tesla Model 3", "Tesla Model Y", "VW ID.4", "VW ID.3",
    "Audi e-tron", "BMW iX", "Mercedes EQC", "Nissan Leaf",
    "Hyundai Ioniq 5", "Polestar 2"
]

INITIAL_MESSAGES = [
    "Hei! Jeg er interessert i å prøvekjøre denne bilen. Er den tilgjengelig denne helgen?",
    "Kan dere fortelle mer om prisene og finansieringsmuligheter?",
    "Jeg vil gjerne ha mer informasjon om rekkevidde og lading.",
    "Er det mulig å få tilbud på innbytte av min nåværende bil?",
    "Jeg har sett denne bilen på nettsiden deres og vil gjerne vite mer.",
    "Kan jeg bestille en prøvekjøring? Jeg er ledig på hverdager.",
    "Hva er leveringstiden på denne modellen?",
    "Jeg ønsker å diskutere leasing-alternativer for bedrift.",
    "Er det noen kampanjer eller rabatter tilgjengelig nå?",
    "Kan dere gi meg et pristilbud inkludert alle ekstrautstyr?"
]

AI_RESPONSES = [
    "Hei {name}! Takk for din interesse i {vehicle}. Vi har bilen tilgjengelig for prøvekjøring. En av våre selgere vil kontakte deg i dag for å avtale tidspunkt. Mvh Norvalt",
    "Hei {name}! Flott at du er interessert i {vehicle}. Vi sender deg et detaljert pristilbud på e-post innen kort tid. En selger vil også ringe deg for å diskutere dine ønsker. Mvh Norvalt",
    "Takk for henvendelsen {name}! Vi vil gjerne hjelpe deg med {vehicle}. En av våre eksperter vil ta kontakt i dag for å svare på alle dine spørsmål. Mvh Norvalt",
]


def create_sample_leads(dealership_id: uuid.UUID, db: Session, count: int = 10):
    """
    Create sample leads for a dealership.
    
    Args:
        dealership_id: ID of the dealership
        db: Database session
        count: Number of leads to create
    """
    print(f"\n📝 Creating {count} sample leads...")
    
    statuses = ["new", "contacted", "qualified", "won", "lost"]
    sources = ["website", "email", "facebook", "manual"]
    
    leads_created = []
    
    for i in range(count):
        # Random data
        name = random.choice(NORWEGIAN_NAMES)
        vehicle = random.choice(VEHICLES)
        status = random.choice(statuses)
        source = random.choice(sources)
        
        # Generate email from name
        email = f"{name.lower().replace(' ', '.')}.{random.randint(100, 999)}@example.no"
        
        # Random phone number (Norwegian format)
        phone = f"+47 {random.randint(400, 999)} {random.randint(10, 99)} {random.randint(100, 999)}"
        
        # Random date within last 14 days
        days_ago = random.randint(0, 14)
        created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Create lead
        lead = Lead(
            id=uuid.uuid4(),
            dealership_id=dealership_id,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            vehicle_interest=vehicle,
            initial_message=random.choice(INITIAL_MESSAGES),
            source=source,
            source_url="https://dealership.no/contact" if source == "website" else None,
            status=status,
            created_at=created_at,
            last_contact_at=created_at if status != "new" else None,
        )
        
        db.add(lead)
        db.flush()  # Get the lead ID
        
        leads_created.append(lead)
        
        # Add AI response for non-new leads
        if status != "new":
            ai_message = random.choice(AI_RESPONSES).format(name=name.split()[0], vehicle=vehicle)
            conversation = Conversation(
                id=uuid.uuid4(),
                lead_id=lead.id,
                dealership_id=dealership_id,
                channel="email",
                direction="outbound",
                sender="AI Assistant",
                sender_type="ai",
                message_content=ai_message,
                created_at=created_at + timedelta(minutes=5),
            )
            db.add(conversation)
        
        print(f"  ✓ {name} - {vehicle} ({status}, {source})")
    
    db.commit()
    print(f"\n✅ Created {count} sample leads!")
    
    return leads_created


def main():
    """Main function."""
    print("\n" + "="*60)
    print("NORVALT - ADD SAMPLE LEADS")
    print("="*60)
    print("\nThis script will add 10 sample leads to your dealership.")
    print("This will populate your dashboard with test data.\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Find the user's dealership (most recent one)
        dealership = db.query(Dealership).order_by(Dealership.created_at.desc()).first()
        
        if not dealership:
            print("❌ Error: No dealership found in database")
            print("   Run sync_clerk_user.py first!")
            sys.exit(1)
        
        print(f"📍 Adding leads to: {dealership.name}")
        print(f"   Dealership ID: {dealership.id}")
        
        # Confirm
        confirm = input("\nProceed? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("❌ Cancelled")
            sys.exit(0)
        
        # Create sample leads
        leads = create_sample_leads(dealership.id, db, count=10)
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"\n🎉 Added {len(leads)} sample leads to {dealership.name}")
        print("\n📊 Lead breakdown:")
        
        # Count by status
        status_counts = {}
        source_counts = {}
        for lead in leads:
            status_counts[lead.status] = status_counts.get(lead.status, 0) + 1
            source_counts[lead.source] = source_counts.get(lead.source, 0) + 1
        
        print("\nBy Status:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        print("\nBy Source:")
        for source, count in source_counts.items():
            print(f"  - {source}: {count}")
        
        print("\n🚀 Now refresh your dashboard to see the leads!")
        print("   http://localhost:3000/dashboard/leads")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

