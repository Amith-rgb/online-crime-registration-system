from models import db, User, CrimeReport, Audit
from sqlalchemy import inspect, text

def init_db(app):
    with app.app_context():
        # Create any missing tables (new tables like Audit)
        db.create_all()

        # Ensure default admin exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

        # Perform lightweight schema migration for SQLite: add missing columns to crime_report
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'crime_report' in tables:
            existing_cols = [c['name'] for c in inspector.get_columns('crime_report')]
            needed = {
                'image_path': 'TEXT',
                'latitude': 'REAL',
                'longitude': 'REAL',
                'verification_requested': 'INTEGER DEFAULT 0',
                'is_verified': 'INTEGER DEFAULT 0'
            }
            for col, coltype in needed.items():
                if col not in existing_cols:
                    # SQLite supports ADD COLUMN
                    stmt = text(f'ALTER TABLE crime_report ADD COLUMN {col} {coltype};')
                    db.session.execute(stmt)
                    db.session.commit()

        # Ensure Audit table exists (db.create_all already attempted, but double-check)
        if 'audit' not in tables:
            db.create_all()

        print("Database initialized and migrated (lightweight)!")

if __name__ == '__main__':
    from app import app
    init_db(app)