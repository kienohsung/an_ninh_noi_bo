import sys
import os
from datetime import datetime, time
import pytz
from sqlalchemy import select

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import models, database
from app.config import settings

def check_long_term_logic():
    db = database.SessionLocal()
    with open("debug_result.log", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        try:
            log(f"--- Debugging Long Term Guest Logic ---")
            log(f"Timezone: {settings.TZ}")
            tz = pytz.timezone(settings.TZ)
            now = datetime.now(tz)
            today = now.date()
            log(f"Current Time: {now}")
            log(f"Today: {today}")

            # 1. Check 'system' user - REMOVED (Logic updated to use original registrant)
            # system_user = db.scalars(select(models.User).where(models.User.username == 'system')).first()
            # if not system_user:
            #     log("❌ ERROR: User 'system' NOT FOUND in database!")
            # else:
            #     log(f"✅ User 'system' found (ID: {system_user.id})")

            # 2. Check Active Long Term Guests
            log(f"\nChecking Active Long Term Guests for date: {today}...")
            query = select(models.LongTermGuest).where(
                models.LongTermGuest.is_active == True,
                models.LongTermGuest.start_date <= today,
                models.LongTermGuest.end_date >= today
            )
            active_guests = db.scalars(query).all()
            log(f"Found {len(active_guests)} active long-term guests valid for today.")
            
            for guest in active_guests:
                log(f"  - [{guest.id}] {guest.full_name} ({guest.id_card_number}) | Registrant ID: {guest.registered_by_user_id}")

            # 3. Check Existing Daily Entries (Global check)
            log(f"\nChecking Existing Daily Entries (Global) today...")
            start_of_day = datetime.combine(today, time.min, tzinfo=tz)
            end_of_day = datetime.combine(today, time.max, tzinfo=tz)
            
            existing_guests = db.scalars(
                select(models.Guest).where(
                    models.Guest.created_at >= start_of_day,
                    models.Guest.created_at <= end_of_day,
                    models.Guest.id_card_number != ""
                )
            ).all()
            
            log(f"Found {len(existing_guests)} guests created today.")
            for g in existing_guests:
                 log(f"  - [{g.id}] {g.full_name} ({g.id_card_number}) | Status: {g.status} | Registered By: {g.registered_by_user_id}")

            # 4. Simulation
            log(f"\n--- Simulation Result ---")
            existing_ids = {g.id_card_number for g in existing_guests if g.id_card_number}
            to_create = []
            for guest in active_guests:
                if guest.id_card_number and guest.id_card_number not in existing_ids:
                    to_create.append(f"{guest.full_name} (by User {guest.registered_by_user_id})")
            
            if to_create:
                log(f"✅ Logic SHOULD create {len(to_create)} guests:")
                for item in to_create:
                    log(f"   + {item}")
            else:
                log(f"⚠️ Logic would create 0 guests (either no active guests or all already created).")

        except Exception as e:
            log(f"❌ Exception during debug: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    check_long_term_logic()
