#!/usr/bin/env python3
"""
Update dealership emails from placeholder to user emails.

This script finds dealerships with placeholder emails and updates them
with the email from the first admin user in that dealership.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.dealership import Dealership
from app.models.user import User


def update_placeholder_emails(db: Session, dry_run: bool = True):
    """Update dealership emails from placeholder to user emails."""
    
    # Find all dealerships with placeholder emails
    dealerships = db.query(Dealership).filter(
        Dealership.email.like("org-%@placeholder.norvalt.no")
    ).all()
    
    if not dealerships:
        print("No dealerships with placeholder emails found.")
        return
    
    print(f"Found {len(dealerships)} dealership(s) with placeholder emails:\n")
    
    updated_count = 0
    for dealership in dealerships:
        # Find the first admin user (or any user) in this dealership
        user = db.query(User).filter(
            User.dealership_id == dealership.id
        ).order_by(User.created_at.asc()).first()
        
        if not user:
            print(f"  ⚠️  {dealership.name} ({dealership.email}) - No users found, skipping")
            continue
        
        if user.email.startswith("user-") and "@placeholder.norvalt.no" in user.email:
            print(f"  ⚠️  {dealership.name} ({dealership.email}) - User also has placeholder email: {user.email}")
            continue
        
        print(f"  ✓ {dealership.name}")
        print(f"    Current: {dealership.email}")
        print(f"    Update to: {user.email} (from user: {user.name or 'N/A'})")
        
        if not dry_run:
            dealership.email = user.email
            updated_count += 1
        print()
    
    if dry_run:
        print("DRY RUN - No changes made. Run with --apply to update emails.")
    else:
        db.commit()
        print(f"✓ Updated {updated_count} dealership email(s).")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update dealership placeholder emails to user emails"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply the changes (default is dry-run)"
    )
    
    args = parser.parse_args()
    
    db: Session = SessionLocal()
    
    try:
        update_placeholder_emails(db, dry_run=not args.apply)
    finally:
        db.close()


if __name__ == "__main__":
    main()

