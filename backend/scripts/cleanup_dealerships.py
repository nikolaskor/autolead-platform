#!/usr/bin/env python3
"""
Cleanup script for dealerships in Supabase database.

WARNING: This will permanently delete dealerships and all related data:
- Users (cascade delete)
- Leads (cascade delete)
- Conversations (cascade delete)

Usage:
    python backend/scripts/cleanup_dealerships.py --list          # List all dealerships
    python backend/scripts/cleanup_dealerships.py --all           # Delete all dealerships
    python backend/scripts/cleanup_dealerships.py --email <email> # Delete by email
    python backend/scripts/cleanup_dealerships.py --name <name>  # Delete by name pattern
    python backend/scripts/cleanup_dealerships.py --id <uuid>    # Delete by ID
"""

import argparse
import sys
import uuid
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.dealership import Dealership
from app.models.user import User
from app.models.lead import Lead
from app.models.conversation import Conversation


def get_dealership_stats(db: Session, dealership: Dealership) -> dict:
    """Get statistics for a dealership."""
    user_count = db.query(func.count(User.id)).filter(User.dealership_id == dealership.id).scalar()
    lead_count = db.query(func.count(Lead.id)).filter(Lead.dealership_id == dealership.id).scalar()
    conversation_count = db.query(func.count(Conversation.id)).filter(
        Conversation.dealership_id == dealership.id
    ).scalar()
    
    return {
        "users": user_count,
        "leads": lead_count,
        "conversations": conversation_count,
    }


def list_dealerships(db: Session):
    """List all dealerships with their statistics."""
    dealerships = db.query(Dealership).order_by(Dealership.created_at.desc()).all()
    
    if not dealerships:
        print("No dealerships found in database.")
        return
    
    print(f"\nFound {len(dealerships)} dealership(s):\n")
    print(f"{'ID':<38} {'Name':<30} {'Email':<35} {'Users':<8} {'Leads':<8} {'Convs':<8} {'Created':<20}")
    print("-" * 160)
    
    for dealership in dealerships:
        stats = get_dealership_stats(db, dealership)
        created_str = dealership.created_at.strftime("%Y-%m-%d %H:%M:%S") if dealership.created_at else "N/A"
        print(
            f"{str(dealership.id):<38} "
            f"{dealership.name[:29]:<30} "
            f"{dealership.email[:34]:<35} "
            f"{stats['users']:<8} "
            f"{stats['leads']:<8} "
            f"{stats['conversations']:<8} "
            f"{created_str:<20}"
        )
    
    print()


def delete_dealership(db: Session, dealership: Dealership, confirm: bool = False) -> bool:
    """Delete a dealership and all related data."""
    stats = get_dealership_stats(db, dealership)
    
    print(f"\nDealership to delete:")
    print(f"  ID: {dealership.id}")
    print(f"  Name: {dealership.name}")
    print(f"  Email: {dealership.email}")
    print(f"  Clerk Org ID: {dealership.clerk_org_id}")
    print(f"\nThis will also delete:")
    print(f"  - {stats['users']} user(s)")
    print(f"  - {stats['leads']} lead(s)")
    print(f"  - {stats['conversations']} conversation(s)")
    
    if not confirm:
        response = input("\nAre you sure you want to delete this dealership? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Deletion cancelled.")
            return False
    
    try:
        db.delete(dealership)
        db.commit()
        print(f"✓ Successfully deleted dealership '{dealership.name}' and all related data.")
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting dealership: {e}")
        return False


def delete_all(db: Session, confirm: bool = False):
    """Delete all dealerships."""
    dealerships = db.query(Dealership).all()
    
    if not dealerships:
        print("No dealerships found to delete.")
        return
    
    total_stats = {
        "users": 0,
        "leads": 0,
        "conversations": 0,
    }
    
    for dealership in dealerships:
        stats = get_dealership_stats(db, dealership)
        total_stats["users"] += stats["users"]
        total_stats["leads"] += stats["leads"]
        total_stats["conversations"] += stats["conversations"]
    
    print(f"\n⚠️  WARNING: This will delete ALL {len(dealerships)} dealership(s)!")
    print(f"\nTotal data to be deleted:")
    print(f"  - {len(dealerships)} dealership(s)")
    print(f"  - {total_stats['users']} user(s)")
    print(f"  - {total_stats['leads']} lead(s)")
    print(f"  - {total_stats['conversations']} conversation(s)")
    
    if not confirm:
        response = input("\nType 'DELETE ALL' to confirm: ")
        if response != "DELETE ALL":
            print("Deletion cancelled.")
            return
    
    deleted_count = 0
    for dealership in dealerships:
        if delete_dealership(db, dealership, confirm=True):
            deleted_count += 1
    
    print(f"\n✓ Deleted {deleted_count} out of {len(dealerships)} dealership(s).")


def delete_by_email(db: Session, email: str, confirm: bool = False):
    """Delete dealership by email."""
    dealership = db.query(Dealership).filter(Dealership.email == email).first()
    
    if not dealership:
        print(f"✗ No dealership found with email: {email}")
        return
    
    delete_dealership(db, dealership, confirm)


def delete_by_name_pattern(db: Session, pattern: str, confirm: bool = False):
    """Delete dealerships matching name pattern."""
    dealerships = db.query(Dealership).filter(Dealership.name.ilike(f"%{pattern}%")).all()
    
    if not dealerships:
        print(f"✗ No dealerships found matching pattern: {pattern}")
        return
    
    print(f"\nFound {len(dealerships)} dealership(s) matching '{pattern}':")
    for dealership in dealerships:
        print(f"  - {dealership.name} ({dealership.email})")
    
    if not confirm:
        response = input(f"\nDelete these {len(dealerships)} dealership(s)? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Deletion cancelled.")
            return
    
    deleted_count = 0
    for dealership in dealerships:
        if delete_dealership(db, dealership, confirm=True):
            deleted_count += 1
    
    print(f"\n✓ Deleted {deleted_count} out of {len(dealerships)} dealership(s).")


def delete_by_id(db: Session, dealership_id: str, confirm: bool = False):
    """Delete dealership by ID."""
    try:
        uuid_obj = uuid.UUID(dealership_id)
    except ValueError:
        print(f"✗ Invalid UUID format: {dealership_id}")
        return
    
    dealership = db.query(Dealership).filter(Dealership.id == uuid_obj).first()
    
    if not dealership:
        print(f"✗ No dealership found with ID: {dealership_id}")
        return
    
    delete_dealership(db, dealership, confirm)


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup dealerships from Supabase database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all dealerships with statistics"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Delete all dealerships (requires confirmation)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Delete dealership by email address"
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Delete dealerships matching name pattern (case-insensitive)"
    )
    parser.add_argument(
        "--id",
        type=str,
        help="Delete dealership by UUID"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (use with caution!)"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show list by default
    if not any([args.list, args.all, args.email, args.name, args.id]):
        args.list = True
    
    db: Session = SessionLocal()
    
    try:
        if args.list:
            list_dealerships(db)
        elif args.all:
            delete_all(db, confirm=args.yes)
        elif args.email:
            delete_by_email(db, args.email, confirm=args.yes)
        elif args.name:
            delete_by_name_pattern(db, args.name, confirm=args.yes)
        elif args.id:
            delete_by_id(db, args.id, confirm=args.yes)
    finally:
        db.close()


if __name__ == "__main__":
    main()

