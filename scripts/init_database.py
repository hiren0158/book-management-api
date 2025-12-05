#!/usr/bin/env python3
"""
Database Initialization Script for Render Deployment

This script should be run once after initial deployment to:
1. Ensure database extensions are installed
2. Run all migrations
3. Create initial roles
4. Verify database setup
"""

import os
import sys

# Add project root to Python path for imports to work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlmodel import create_engine, Session, select
from sqlalchemy import text


def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)

    # Fix for render.com postgres:// -> postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return db_url


def install_extensions(engine):
    """Install required PostgreSQL extensions."""
    print("\n📦 Installing PostgreSQL extensions...")

    try:
        with engine.connect() as conn:
            # Install pg_trgm for fuzzy text search
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            print("  ✓ pg_trgm extension installed")

            # Install btree_gin for better indexing
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gin;"))
            print("  ✓ btree_gin extension installed")

            conn.commit()
        return True
    except Exception as e:
        print(f"  ⚠️  Error installing extensions: {e}")
        print("  → You may need to install these manually via PSQL")
        return False


def run_migrations():
    """Run Alembic migrations."""
    print("\n🔄 Running database migrations...")

    try:
        import subprocess

        result = subprocess.run(
            ["alembic", "upgrade", "head"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("  ✓ Migrations completed successfully")
            return True
        else:
            print(f"  ❌ Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Error running migrations: {e}")
        return False


def create_initial_roles(engine):
    """Create initial user roles."""
    print("\n👥 Creating initial roles...")

    try:
        from src.model.role import Role

        with Session(engine) as session:
            # Check if roles already exist
            existing = session.exec(select(Role)).first()
            if existing:
                print("  ℹ️  Roles already exist, skipping creation")
                return True

            # Create roles
            roles = [
                Role(id=1, name="Member", description="Regular library member"),
                Role(id=2, name="Admin", description="System administrator"),
                Role(id=3, name="Librarian", description="Library staff"),
            ]

            for role in roles:
                session.add(role)

            session.commit()
            print("  ✓ Created 3 roles: Member, Admin, Librarian")
            return True

    except Exception as e:
        print(f"  ❌ Error creating roles: {e}")
        return False


def verify_setup(engine):
    """Verify database setup is correct."""
    print("\n✅ Verifying database setup...")

    checks_passed = 0
    checks_total = 0

    try:
        with engine.connect() as conn:
            # Check pg_trgm extension
            checks_total += 1
            result = conn.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm');"
                )
            )
            if result.scalar():
                print("  ✓ pg_trgm extension: Installed")
                checks_passed += 1
            else:
                print("  ❌ pg_trgm extension: Missing")

            # Check btree_gin extension
            checks_total += 1
            result = conn.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'btree_gin');"
                )
            )
            if result.scalar():
                print("  ✓ btree_gin extension: Installed")
                checks_passed += 1
            else:
                print("  ❌ btree_gin extension: Missing")

            # Check tables exist
            checks_total += 1
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
                )
            )
            table_count = result.scalar()
            if table_count > 0:
                print(f"  ✓ Database tables: {table_count} tables created")
                checks_passed += 1
            else:
                print("  ❌ Database tables: No tables found")

            # Check roles exist
            checks_total += 1
            from src.model.role import Role

            with Session(engine) as session:
                role_count = session.exec(select(Role)).all()
                if len(role_count) >= 3:
                    print(f"  ✓ Initial roles: {len(role_count)} roles created")
                    checks_passed += 1
                else:
                    print(f"  ⚠️  Initial roles: Only {len(role_count)} roles found")

        print(f"\n📊 Verification: {checks_passed}/{checks_total} checks passed")
        return checks_passed == checks_total

    except Exception as e:
        print(f"  ❌ Verification failed: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("🚀 Book Management API - Database Setup")
    print("=" * 60)

    # Get database URL
    db_url = get_database_url()
    print(f"\n🔗 Database: {db_url[:30]}...")

    # Create engine
    engine = create_engine(db_url, echo=False)

    # Install extensions
    install_extensions(engine)

    # Run migrations
    if not run_migrations():
        print("\n⚠️  Migrations failed, but continuing...")

    # Create initial roles
    create_initial_roles(engine)

    # Verify setup
    success = verify_setup(engine)

    print("\n" + "=" * 60)
    if success:
        print("✅ Database setup completed successfully!")
    else:
        print("⚠️  Database setup completed with warnings")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
