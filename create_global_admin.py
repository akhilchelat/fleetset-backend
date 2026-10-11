import getpass

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.security.authentication import hash_password


ROLE_NAMES = [
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
    "DRIVER",
]


def main():
    db: Session = SessionLocal()

    try:
        print("\n=== FleetSet Global Admin Bootstrap ===\n")

        # Ensure required roles exist
        roles = {}

        for role_name in ROLE_NAMES:
            role = (
                db.query(Role)
                .filter(Role.name == role_name)
                .first()
            )

            if role is None:
                role = Role(
                    name=role_name,
                    is_active=True,
                )
                db.add(role)
                db.flush()

                print(f"[CREATED ROLE] {role_name}")
            else:
                print(f"[EXISTS] {role_name}")

            roles[role_name] = role

        db.commit()

        print("\nAll required roles are ready.")

        # Ask for Global Admin details
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip().lower()
        phone = input("Phone: ").strip()
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if not first_name:
            raise ValueError("First name is required.")

        if not email:
            raise ValueError("Email is required.")

        if not password:
            raise ValueError("Password is required.")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        # Prevent duplicate user
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("\n[ERROR] A user with this email already exists.")
            print(f"User ID: {existing_user.id}")
            print(f"Role ID: {existing_user.role_id}")
            return

        global_admin_role = roles["GLOBAL_ADMIN"]

        # GLOBAL_ADMIN is FleetSet-level.
        # Therefore company_id and branch_id remain NULL.
        global_admin = User(
            company_id=None,
            branch_id=None,
            role_id=global_admin_role.id,
            first_name=first_name,
            last_name=last_name or None,
            email=email,
            phone=phone or None,
            password_hash=hash_password(password),
            is_active=True,
        )

        db.add(global_admin)
        db.commit()
        db.refresh(global_admin)

        print("\n========================================")
        print("GLOBAL ADMIN CREATED SUCCESSFULLY")
        print("========================================")
        print(f"User ID : {global_admin.id}")
        print(f"Name    : {global_admin.first_name} {global_admin.last_name or ''}")
        print(f"Email   : {global_admin.email}")
        print(f"Role    : GLOBAL_ADMIN")
        print(f"Role ID : {global_admin.role_id}")
        print("Company : None")
        print("Branch  : None")
        print("========================================\n")

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()