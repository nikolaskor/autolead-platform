"""
Script to sync a Clerk user to the database.
This creates the dealership and user records for a Clerk account.

Usage:
    python scripts/sync_clerk_user.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.dealership import Dealership
from app.models.user import User
import uuid


def get_clerk_ids_from_jwt():
    """
    Extract Clerk user ID and org ID from a JWT token.
    
    Returns:
        tuple: (clerk_user_id, clerk_org_id, email)
    """
    print("\n" + "="*60)
    print("CLERK USER SYNC - Extract IDs from JWT")
    print("="*60)
    print("\n1. Open your dashboard in the browser")
    print("2. Open browser console (F12 or Cmd+Option+I)")
    print("3. Run this JavaScript code:\n")
    print("   const token = await window.Clerk.session.getToken();")
    print("   const parts = token.split('.');")
    print("   const payload = JSON.parse(atob(parts[1]));")
    print("   console.log('User ID:', payload.sub);")
    print("   console.log('Org ID:', payload.org_id);")
    print("   console.log('Email:', payload.email);\n")
    
    print("4. Copy the values and paste them below:\n")
    
    clerk_user_id = input("Clerk User ID (starts with 'user_'): ").strip()
    clerk_org_id = input("Clerk Org ID (starts with 'org_'): ").strip()
    email = input("Your Email: ").strip()
    name = input("Your Name: ").strip()
    
    if not clerk_user_id.startswith("user_"):
        print("❌ Error: User ID should start with 'user_'")
        sys.exit(1)
    
    if not clerk_org_id.startswith("org_"):
        print("❌ Error: Org ID should start with 'org_'")
        sys.exit(1)
    
    if not email or "@" not in email:
        print("❌ Error: Invalid email")
        sys.exit(1)
    
    return clerk_user_id, clerk_org_id, email, name


def sync_user_to_database(
    clerk_user_id: str,
    clerk_org_id: str,
    email: str,
    name: str,
    db: Session
):
    """
    Create dealership and user records in the database.
    
    Args:
        clerk_user_id: Clerk user ID
        clerk_org_id: Clerk organization ID
        email: User email
        name: User name
        db: Database session
    """
    print("\n" + "="*60)
    print("SYNCING TO DATABASE")
    print("="*60)
    
    # Check if dealership already exists
    dealership = db.query(Dealership).filter(
        Dealership.clerk_org_id == clerk_org_id
    ).first()
    
    if dealership:
        print(f"\n✅ Dealership already exists: {dealership.name}")
    else:
        # Create dealership
        dealership_name = input("\nDealership Name (e.g., 'Tesla Oslo'): ").strip() or "My Dealership"
        
        dealership = Dealership(
            id=uuid.uuid4(),
            clerk_org_id=clerk_org_id,
            name=dealership_name,
            email=email,
            subscription_status="active",
            subscription_tier="starter"
        )
        db.add(dealership)
        db.flush()
        print(f"✅ Created dealership: {dealership.name}")
    
    # Check if user already exists
    user = db.query(User).filter(
        User.clerk_user_id == clerk_user_id
    ).first()
    
    if user:
        print(f"✅ User already exists: {user.name}")
        # Update dealership if needed
        if user.dealership_id != dealership.id:
            user.dealership_id = dealership.id
            print(f"   Updated user's dealership")
    else:
        # Create user
        user = User(
            id=uuid.uuid4(),
            clerk_user_id=clerk_user_id,
            dealership_id=dealership.id,
            email=email,
            name=name,
            role="admin"  # First user is admin
        )
        db.add(user)
        print(f"✅ Created user: {user.name} (admin)")
    
    # Commit changes
    db.commit()
    
    print("\n" + "="*60)
    print("✅ SYNC COMPLETE!")
    print("="*60)
    print(f"\nDealership: {dealership.name}")
    print(f"User: {user.name} ({user.email})")
    print(f"Role: {user.role}")
    print("\n🎉 You can now refresh your dashboard and see your leads!")


def main():
    """Main function."""
    print("\n" + "="*60)
    print("NORVALT - CLERK USER SYNC SCRIPT")
    print("="*60)
    print("\nThis script will:")
    print("1. Create a dealership record for your Clerk organization")
    print("2. Create a user record for your Clerk account")
    print("3. Link them together")
    print("\nAfter running this, you'll be able to access the dashboard!\n")
    
    # Get Clerk IDs
    clerk_user_id, clerk_org_id, email, name = get_clerk_ids_from_jwt()
    
    # Confirm
    print("\n" + "-"*60)
    print("CONFIRM DETAILS:")
    print("-"*60)
    print(f"Clerk User ID: {clerk_user_id}")
    print(f"Clerk Org ID:  {clerk_org_id}")
    print(f"Email:         {email}")
    print(f"Name:          {name}")
    print("-"*60)
    
    confirm = input("\nProceed with sync? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("❌ Cancelled")
        sys.exit(0)
    
    # Create database session
    db = SessionLocal()
    
    try:
        sync_user_to_database(clerk_user_id, clerk_org_id, email, name, db)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

