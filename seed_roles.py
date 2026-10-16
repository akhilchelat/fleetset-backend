
from app.db.session import SessionLocal
from app.models.role import Role


def seed_roles():
    db = SessionLocal()

    roles = [
        "GLOBAL_ADMIN",
        "SUPER_ADMIN",
        "BRANCH_ADMIN",
        "DRIVER",
    ]

    try:
        for role_name in roles:
            existing_role = (
                db.query(Role)
                .filter(Role.name == role_name)
                .first()
            )

            if existing_role:
                print(f"Already exists: {role_name}")
                continue

            role = Role(
                name=role_name,
                is_active=True,
            )

            db.add(role)
            print(f"Created: {role_name}")

        db.commit()
        print("\nRole seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()