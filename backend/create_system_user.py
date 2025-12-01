import sys
import os
from sqlalchemy import select

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import models, database
from app.auth import get_password_hash

def create_system_user():
    db = database.SessionLocal()
    try:
        # Check if exists
        existing = db.scalars(select(models.User).where(models.User.username == 'system')).first()
        if existing:
            print(f"User 'system' already exists with ID: {existing.id}")
            return

        print("Creating 'system' user...")
        system_user = models.User(
            username='system',
            password_hash=get_password_hash('system_password_complex_123'), # Random password
            full_name='System Automation',
            role='admin', # Give admin role to be safe
            department='System'
        )
        db.add(system_user)
        db.commit()
        db.refresh(system_user)
        print(f"✅ User 'system' created successfully with ID: {system_user.id}")

    except Exception as e:
        print(f"❌ Error creating system user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_system_user()
