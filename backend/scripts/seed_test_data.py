"""
Seed test data for development and testing.

Creates:
- 2 test dealerships
- 2 users per dealership (1 admin, 1 sales rep)
- 10 leads per dealership (mix of sources and statuses)
- Sample conversations for some leads

Usage:
    python backend/scripts/seed_test_data.py
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models import Base, Dealership, User, Lead, Conversation


def seed_data():
    """Seed the database with test data."""
    
    # Create database session
    db = SessionLocal()
    
    try:
        print("Starting database seeding...")
        
        # Check if data already exists
        existing_dealerships = db.query(Dealership).count()
        if existing_dealerships > 0:
            print(f"Database already has {existing_dealerships} dealerships. Skipping seed.")
            print("To reseed, drop all tables and run migrations again.")
            return
        
        # Create test dealerships
        dealership1 = Dealership(
            id=uuid4(),
            name="Tesla Oslo",
            email="contact@teslaoslo.no",
            phone="+47 22 33 44 55",
            address="Drammensveien 123, 0273 Oslo",
            clerk_org_id="org_test_tesla_oslo_001",
            subscription_status="active",
            subscription_tier="professional",
        )
        
        dealership2 = Dealership(
            id=uuid4(),
            name="VW Bergen",
            email="post@vwbergen.no",
            phone="+47 55 66 77 88",
            address="Nygårdsgaten 45, 5008 Bergen",
            clerk_org_id="org_test_vw_bergen_001",
            subscription_status="active",
            subscription_tier="starter",
        )
        
        db.add(dealership1)
        db.add(dealership2)
        db.flush()
        print(f"✓ Created 2 dealerships")
        
        # Create users for dealership 1
        user1_admin = User(
            id=uuid4(),
            dealership_id=dealership1.id,
            clerk_user_id="user_test_admin_tesla_001",
            email="admin@teslaoslo.no",
            name="Kari Nordmann",
            role="admin",
            notification_preferences={"sms": True, "email": True},
        )
        
        user1_sales = User(
            id=uuid4(),
            dealership_id=dealership1.id,
            clerk_user_id="user_test_sales_tesla_001",
            email="sales@teslaoslo.no",
            name="Ola Hansen",
            role="sales_rep",
            notification_preferences={"sms": True, "email": True},
        )
        
        # Create users for dealership 2
        user2_admin = User(
            id=uuid4(),
            dealership_id=dealership2.id,
            clerk_user_id="user_test_admin_vw_001",
            email="admin@vwbergen.no",
            name="Lars Johansen",
            role="admin",
            notification_preferences={"sms": True, "email": False},
        )
        
        user2_sales = User(
            id=uuid4(),
            dealership_id=dealership2.id,
            clerk_user_id="user_test_sales_vw_001",
            email="sales@vwbergen.no",
            name="Maria Olsen",
            role="sales_rep",
            notification_preferences={"sms": True, "email": True},
        )
        
        db.add_all([user1_admin, user1_sales, user2_admin, user2_sales])
        db.flush()
        print(f"✓ Created 4 users (2 per dealership)")
        
        # Create leads for dealership 1 (Tesla Oslo)
        tesla_leads = [
            Lead(
                dealership_id=dealership1.id,
                source="website",
                customer_name="Per Andersen",
                customer_email="per.andersen@example.no",
                customer_phone="+47 900 11 222",
                vehicle_interest="Tesla Model 3",
                initial_message="Interested in test drive this weekend",
                status="new",
                lead_score=80,
                created_at=datetime.now() - timedelta(minutes=10),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="website",
                customer_name="Ingrid Larsen",
                customer_email="ingrid.larsen@example.no",
                customer_phone="+47 900 22 333",
                vehicle_interest="Tesla Model Y",
                initial_message="Looking for family SUV with long range",
                status="contacted",
                assigned_to=user1_sales.id,
                lead_score=75,
                created_at=datetime.now() - timedelta(hours=2),
                last_contact_at=datetime.now() - timedelta(hours=1),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="email",
                customer_name="Erik Johansen",
                customer_email="erik.johansen@example.no",
                customer_phone="+47 900 33 444",
                vehicle_interest="Tesla Model S",
                initial_message="Interested in trading in my current car",
                status="contacted",
                assigned_to=user1_sales.id,
                lead_score=70,
                created_at=datetime.now() - timedelta(hours=5),
                last_contact_at=datetime.now() - timedelta(hours=4),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="email",
                customer_name="Sofie Berg",
                customer_email="sofie.berg@example.no",
                vehicle_interest="Tesla Model 3",
                initial_message="Want to know about financing options",
                status="qualified",
                assigned_to=user1_sales.id,
                lead_score=85,
                created_at=datetime.now() - timedelta(days=1),
                last_contact_at=datetime.now() - timedelta(hours=12),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="facebook",
                customer_name="Thomas Nielsen",
                customer_email="thomas.nielsen@example.no",
                customer_phone="+47 900 44 555",
                vehicle_interest="Tesla Model Y",
                initial_message="Saw your ad, interested in prices",
                status="new",
                lead_score=60,
                created_at=datetime.now() - timedelta(hours=3),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="facebook",
                customer_name="Emma Pedersen",
                customer_email="emma.pedersen@example.no",
                vehicle_interest="Tesla Model 3",
                initial_message="Is this available for immediate delivery?",
                status="new",
                lead_score=65,
                created_at=datetime.now() - timedelta(hours=6),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="website",
                customer_name="Håkon Kristiansen",
                customer_email="hakon.kristiansen@example.no",
                customer_phone="+47 900 55 666",
                vehicle_interest="Tesla Model S",
                initial_message="Interested in business leasing",
                status="contacted",
                assigned_to=user1_admin.id,
                lead_score=90,
                created_at=datetime.now() - timedelta(days=2),
                last_contact_at=datetime.now() - timedelta(days=1),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="website",
                customer_name="Lise Hermansen",
                customer_email="lise.hermansen@example.no",
                vehicle_interest="Tesla Model Y",
                initial_message="Need car seat installation info",
                status="new",
                lead_score=55,
                created_at=datetime.now() - timedelta(hours=8),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="email",
                customer_name="Martin Solberg",
                customer_email="martin.solberg@example.no",
                customer_phone="+47 900 66 777",
                vehicle_interest="Tesla Model 3",
                initial_message="What colors are available?",
                status="new",
                lead_score=50,
                created_at=datetime.now() - timedelta(hours=12),
            ),
            Lead(
                dealership_id=dealership1.id,
                source="website",
                customer_name="Hanna Eriksen",
                customer_email="hanna.eriksen@example.no",
                vehicle_interest="Tesla Model Y",
                initial_message="Interested in winter tires package",
                status="contacted",
                assigned_to=user1_sales.id,
                lead_score=70,
                created_at=datetime.now() - timedelta(days=3),
                last_contact_at=datetime.now() - timedelta(days=2),
            ),
        ]
        
        # Create leads for dealership 2 (VW Bergen)
        vw_leads = [
            Lead(
                dealership_id=dealership2.id,
                source="website",
                customer_name="Jonas Bakke",
                customer_email="jonas.bakke@example.no",
                customer_phone="+47 900 77 888",
                vehicle_interest="VW ID.4",
                initial_message="Looking for electric SUV",
                status="new",
                lead_score=75,
                created_at=datetime.now() - timedelta(minutes=30),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="website",
                customer_name="Silje Moen",
                customer_email="silje.moen@example.no",
                vehicle_interest="VW ID.3",
                initial_message="Need compact electric car for city driving",
                status="contacted",
                assigned_to=user2_sales.id,
                lead_score=80,
                created_at=datetime.now() - timedelta(hours=4),
                last_contact_at=datetime.now() - timedelta(hours=2),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="email",
                customer_name="Andreas Lund",
                customer_email="andreas.lund@example.no",
                customer_phone="+47 900 88 999",
                vehicle_interest="VW Golf",
                initial_message="Interested in hybrid version",
                status="contacted",
                assigned_to=user2_sales.id,
                lead_score=70,
                created_at=datetime.now() - timedelta(hours=6),
                last_contact_at=datetime.now() - timedelta(hours=5),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="email",
                customer_name="Camilla Strand",
                customer_email="camilla.strand@example.no",
                vehicle_interest="VW ID.4",
                initial_message="What is the delivery time?",
                status="new",
                lead_score=65,
                created_at=datetime.now() - timedelta(hours=8),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="facebook",
                customer_name="Fredrik Svendsen",
                customer_email="fredrik.svendsen@example.no",
                customer_phone="+47 900 99 000",
                vehicle_interest="VW ID.Buzz",
                initial_message="Interested in the electric van",
                status="qualified",
                assigned_to=user2_sales.id,
                lead_score=85,
                created_at=datetime.now() - timedelta(days=1),
                last_contact_at=datetime.now() - timedelta(hours=18),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="facebook",
                customer_name="Marte Haugen",
                customer_email="marte.haugen@example.no",
                vehicle_interest="VW ID.3",
                initial_message="Can I get a test drive next week?",
                status="new",
                lead_score=70,
                created_at=datetime.now() - timedelta(hours=10),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="website",
                customer_name="Øyvind Dahl",
                customer_email="oyvind.dahl@example.no",
                customer_phone="+47 911 11 222",
                vehicle_interest="VW Tiguan",
                initial_message="Looking for SUV with 7 seats",
                status="contacted",
                assigned_to=user2_admin.id,
                lead_score=75,
                created_at=datetime.now() - timedelta(days=2),
                last_contact_at=datetime.now() - timedelta(days=1),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="website",
                customer_name="Kristine Holm",
                customer_email="kristine.holm@example.no",
                vehicle_interest="VW ID.4",
                initial_message="What colors are in stock?",
                status="new",
                lead_score=60,
                created_at=datetime.now() - timedelta(hours=15),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="email",
                customer_name="Daniel Aas",
                customer_email="daniel.aas@example.no",
                customer_phone="+47 911 22 333",
                vehicle_interest="VW Golf",
                initial_message="Interested in business lease",
                status="contacted",
                assigned_to=user2_sales.id,
                lead_score=80,
                created_at=datetime.now() - timedelta(days=1),
                last_contact_at=datetime.now() - timedelta(hours=20),
            ),
            Lead(
                dealership_id=dealership2.id,
                source="website",
                customer_name="Linda Eide",
                customer_email="linda.eide@example.no",
                vehicle_interest="VW ID.3",
                initial_message="Is there a winter promotion?",
                status="new",
                lead_score=55,
                created_at=datetime.now() - timedelta(hours=20),
            ),
        ]
        
        db.add_all(tesla_leads + vw_leads)
        db.flush()
        print(f"✓ Created 20 leads (10 per dealership)")
        
        # Create sample conversations for some leads
        conversations = [
            # Conversation for second Tesla lead (contacted)
            Conversation(
                lead_id=tesla_leads[1].id,
                dealership_id=dealership1.id,
                channel="email",
                direction="inbound",
                sender=tesla_leads[1].customer_name,
                sender_type="customer",
                message_content=tesla_leads[1].initial_message,
                created_at=tesla_leads[1].created_at,
            ),
            Conversation(
                lead_id=tesla_leads[1].id,
                dealership_id=dealership1.id,
                channel="email",
                direction="outbound",
                sender="AI",
                sender_type="ai",
                message_content="Hei Ingrid! Takk for din interesse i Tesla Model Y. Vi har den på lager og kan tilby en prøvekjøring. En selger vil kontakte deg i dag.",
                created_at=tesla_leads[1].created_at + timedelta(minutes=2),
            ),
            # Conversation for second VW lead (contacted)
            Conversation(
                lead_id=vw_leads[1].id,
                dealership_id=dealership2.id,
                channel="email",
                direction="inbound",
                sender=vw_leads[1].customer_name,
                sender_type="customer",
                message_content=vw_leads[1].initial_message,
                created_at=vw_leads[1].created_at,
            ),
            Conversation(
                lead_id=vw_leads[1].id,
                dealership_id=dealership2.id,
                channel="email",
                direction="outbound",
                sender="AI",
                sender_type="ai",
                message_content="Hei Silje! Takk for henvendelsen. VW ID.3 er perfekt for bykjøring med god rekkevidde. Vi vil gjerne vise deg bilen.",
                created_at=vw_leads[1].created_at + timedelta(minutes=1),
            ),
        ]
        
        db.add_all(conversations)
        db.flush()
        print(f"✓ Created {len(conversations)} sample conversations")
        
        # Commit all changes
        db.commit()
        print("\n✅ Database seeding completed successfully!")
        print(f"\nSummary:")
        print(f"  - 2 dealerships (Tesla Oslo, VW Bergen)")
        print(f"  - 4 users (2 per dealership)")
        print(f"  - 20 leads (10 per dealership)")
        print(f"  - {len(conversations)} conversations")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Norvalt Database Seeding Script")
    print("=" * 60)
    seed_data()

