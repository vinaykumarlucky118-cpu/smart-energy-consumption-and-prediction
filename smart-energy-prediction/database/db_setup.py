"""
AI-Based Smart Energy Consumption Prediction and Monitoring System
Database Module (SQLite) with User Authentication & Extended Platform Tables
"""

import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "energy.db")

def get_connection(db_path=None):
    """Establish and return SQLite database connection."""
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    """Initialize the database tables and apply migrations if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'User',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        voltage REAL NOT NULL,
        current REAL NOT NULL,
        usage_hours REAL NOT NULL,
        number_of_appliances INTEGER NOT NULL,
        temperature REAL NOT NULL,
        previous_consumption REAL NOT NULL,
        predicted_consumption REAL NOT NULL,
        consumption_level TEXT NOT NULL,
        recommendation TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 3. User Profiles (settings / preferences)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        home_type TEXT DEFAULT 'Apartment',
        num_people INTEGER DEFAULT 2,
        monthly_budget REAL DEFAULT 2000.0,
        tariff_rate REAL DEFAULT 6.0,
        region TEXT DEFAULT 'India',
        currency TEXT DEFAULT '₹',
        emission_factor REAL DEFAULT 0.82,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 4. Appliance entries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        power_watts REAL NOT NULL,
        quantity INTEGER DEFAULT 1,
        hours_per_day REAL DEFAULT 1.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 5. Simulator sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulator_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_data TEXT NOT NULL,
        total_current_kwh REAL DEFAULT 0,
        total_new_kwh REAL DEFAULT 0,
        energy_saved_kwh REAL DEFAULT 0,
        money_saved REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 6. Advisor conversation history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS advisor_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        topic TEXT DEFAULT 'general',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Schema Migration: Ensure user_id column exists if table was previously created
    cursor.execute("PRAGMA table_info(predictions)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'user_id' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN user_id INTEGER")
        print("[Database] Migrated predictions table: added user_id column.")

    conn.commit()
    conn.close()

    # Auto-seed default demo users if table is empty
    seed_default_users(db_path)

def seed_default_users(db_path=None):
    """Seed default admin and student demo user accounts."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    if count == 0:
        default_users = [
            {
                'name': 'System Administrator',
                'email': 'admin@energy.ai',
                'password': 'admin123',
                'role': 'Admin'
            },
            {
                'name': 'Demo Student / User',
                'email': 'student@energy.ai',
                'password': 'energy123',
                'role': 'User'
            }
        ]
        for u in default_users:
            p_hash = generate_password_hash(u['password'])
            cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """, (u['name'], u['email'].lower(), p_hash, u['role']))

        conn.commit()
        print("[Database] Seeded default credentials: admin@energy.ai (admin123) and student@energy.ai (energy123)")

    conn.close()

# ========================= USER CRUD =========================

def create_user(name, email, password, role="User", db_path=None):
    """Create a new user record with hashed password."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        p_hash = generate_password_hash(password)
        cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
        """, (name.strip(), email.strip().lower(), p_hash, role))
        user_id = cursor.lastrowid
        conn.commit()
        # Create default profile
        cursor.execute("""
        INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)
        """, (user_id,))
        conn.commit()
        conn.close()
        return user_id, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "An account with this email address already exists."
    except Exception as e:
        conn.close()
        return None, str(e)

def get_user_by_email(email, db_path=None):
    """Retrieve user dictionary by email."""
    if not email:
        return None
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id, db_path=None):
    """Retrieve user dictionary by ID."""
    if not user_id:
        return None
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_user_credentials(email, password, db_path=None):
    """Verify email and password credentials. Returns user dict or None."""
    user = get_user_by_email(email, db_path)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

# ========================= USER PROFILE =========================

def get_user_profile(user_id, db_path=None):
    """Get user profile or create a default one."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_user_profile(user_id, data, db_path=None):
    """Update user profile settings."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    # Ensure profile exists
    cursor.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,))

    cursor.execute("""
    UPDATE user_profiles SET
        home_type = ?,
        num_people = ?,
        monthly_budget = ?,
        tariff_rate = ?,
        region = ?,
        currency = ?,
        emission_factor = ?,
        updated_at = ?
    WHERE user_id = ?
    """, (
        data.get('home_type', 'Apartment'),
        int(data.get('num_people', 2)),
        float(data.get('monthly_budget', 2000.0)),
        float(data.get('tariff_rate', 6.0)),
        data.get('region', 'India'),
        data.get('currency', '₹'),
        float(data.get('emission_factor', 0.82)),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_id
    ))
    conn.commit()
    conn.close()

def update_user_name(user_id, name, db_path=None):
    """Update user display name."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name.strip(), user_id))
    conn.commit()
    conn.close()

# ========================= PREDICTIONS =========================

def insert_prediction(data, db_path=None):
    """Insert a prediction record into the database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = data.get('user_id')

    cursor.execute("""
    INSERT INTO predictions (
        timestamp, voltage, current, usage_hours, number_of_appliances,
        temperature, previous_consumption, predicted_consumption,
        consumption_level, recommendation, user_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now_str,
        float(data['voltage']),
        float(data['current']),
        float(data['usage_hours']),
        int(data['number_of_appliances']),
        float(data['temperature']),
        float(data['previous_consumption']),
        float(data['predicted_consumption']),
        str(data['consumption_level']),
        str(data['recommendation']),
        user_id
    ))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_prediction_by_id(record_id, db_path=None):
    """Retrieve a single prediction by its primary key ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_predictions(db_path=None, limit=100, offset=0, filter_level=None, search=None, user_id=None, date_filter=None):
    """Retrieve list of predictions with optional filtering and pagination."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM predictions WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if filter_level and filter_level.upper() in ['LOW', 'NORMAL', 'HIGH']:
        query += " AND consumption_level = ?"
        params.append(filter_level.upper())

    if search:
        query += " AND (timestamp LIKE ? OR recommendation LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    cutoff = None
    if date_filter:
        now = datetime.now()
        if date_filter == 'day':
            cutoff = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        elif date_filter == 'week':
            cutoff = (now - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M:%S")
        elif date_filter == 'month':
            cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        if cutoff:
            query += " AND timestamp >= ?"
            params.append(cutoff)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    # Get total count
    count_query = "SELECT COUNT(*) FROM predictions WHERE 1=1"
    count_params = []
    if user_id:
        count_query += " AND user_id = ?"
        count_params.append(user_id)
    if filter_level and filter_level.upper() in ['LOW', 'NORMAL', 'HIGH']:
        count_query += " AND consumption_level = ?"
        count_params.append(filter_level.upper())
    if search:
        count_query += " AND (timestamp LIKE ? OR recommendation LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])
    if date_filter and cutoff:
        count_query += " AND timestamp >= ?"
        count_params.append(cutoff)

    cursor.execute(count_query, tuple(count_params))
    total_count = cursor.fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total_count

def get_dashboard_stats(db_path=None, user_id=None):
    """Calculate dynamic aggregate statistics for the dashboard."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    filter_sql = " WHERE user_id = ?" if user_id else ""
    params = [user_id] if user_id else []

    cursor.execute(f"SELECT COUNT(*), AVG(predicted_consumption), MAX(predicted_consumption), MIN(predicted_consumption) FROM predictions{filter_sql}", tuple(params))
    summary = cursor.fetchone()

    total = summary[0] if summary else 0
    avg_kwh = round(summary[1], 2) if summary and summary[1] is not None else 0.0
    max_kwh = round(summary[2], 2) if summary and summary[2] is not None else 0.0
    min_kwh = round(summary[3], 2) if summary and summary[3] is not None else 0.0

    # Level distribution
    cursor.execute(f"SELECT consumption_level, COUNT(*) FROM predictions{filter_sql} GROUP BY consumption_level", tuple(params))
    level_counts = dict(cursor.fetchall())

    low_count = level_counts.get('LOW', 0)
    normal_count = level_counts.get('NORMAL', 0)
    high_count = level_counts.get('HIGH', 0)

    # Recent 20 predictions for charts
    cursor.execute(f"SELECT id, timestamp, predicted_consumption, consumption_level, voltage, current, usage_hours, temperature, number_of_appliances, previous_consumption FROM predictions{filter_sql} ORDER BY id DESC LIMIT 20", tuple(params))
    recent = [dict(r) for r in cursor.fetchall()]
    recent.reverse()

    # Monthly aggregates (last 6 months)
    cursor.execute(f"""
        SELECT strftime('%Y-%m', timestamp) as month,
               AVG(predicted_consumption) as avg_kwh,
               COUNT(*) as count,
               SUM(predicted_consumption) as total_kwh
        FROM predictions{filter_sql}
        GROUP BY strftime('%Y-%m', timestamp)
        ORDER BY month DESC LIMIT 6
    """, tuple(params))
    monthly = [dict(r) for r in cursor.fetchall()]
    monthly.reverse()

    conn.close()
    return {
        'total': total,
        'avg_kwh': avg_kwh,
        'max_kwh': max_kwh,
        'min_kwh': min_kwh,
        'low_count': low_count,
        'normal_count': normal_count,
        'high_count': high_count,
        'recent': recent,
        'monthly': monthly
    }

def get_comparison_data(user_id=None, db_path=None):
    """Get data for current month vs previous month comparison."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now()
    current_month_start = now.replace(day=1).strftime("%Y-%m-%d")
    prev_month_end = (now.replace(day=1) - timedelta(days=1))
    prev_month_start = prev_month_end.replace(day=1).strftime("%Y-%m-%d")
    prev_month_end_str = prev_month_end.strftime("%Y-%m-%d 23:59:59")

    base_filter = " AND user_id = ?" if user_id else ""
    base_params = [user_id] if user_id else []

    # Current month
    cursor.execute(f"""
        SELECT COUNT(*) as count, COALESCE(AVG(predicted_consumption), 0) as avg_kwh,
               COALESCE(SUM(predicted_consumption), 0) as total_kwh
        FROM predictions WHERE timestamp >= ?{base_filter}
    """, tuple([current_month_start] + base_params))
    current = dict(cursor.fetchone())

    # Previous month
    cursor.execute(f"""
        SELECT COUNT(*) as count, COALESCE(AVG(predicted_consumption), 0) as avg_kwh,
               COALESCE(SUM(predicted_consumption), 0) as total_kwh
        FROM predictions WHERE timestamp >= ? AND timestamp <= ?{base_filter}
    """, tuple([prev_month_start, prev_month_end_str] + base_params))
    previous = dict(cursor.fetchone())

    conn.close()
    return {
        'current': {k: round(v, 2) if isinstance(v, float) else v for k, v in current.items()},
        'previous': {k: round(v, 2) if isinstance(v, float) else v for k, v in previous.items()}
    }

# ========================= APPLIANCES =========================

def get_user_appliances(user_id, db_path=None):
    """Get all appliances for a user."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances WHERE user_id = ? ORDER BY id", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_appliance(user_id, name, power_watts, quantity, hours_per_day, db_path=None):
    """Add an appliance entry."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO appliances (user_id, name, power_watts, quantity, hours_per_day)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, float(power_watts), int(quantity), float(hours_per_day)))
    aid = cursor.lastrowid
    conn.commit()
    conn.close()
    return aid

def delete_appliance(appliance_id, user_id, db_path=None):
    """Delete an appliance entry."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances WHERE id = ? AND user_id = ?", (appliance_id, user_id))
    conn.commit()
    conn.close()

def clear_user_appliances(user_id, db_path=None):
    """Clear all appliances for a user."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def populate_default_appliances(user_id, db_path=None):
    """Populate realistic standard household appliances for a user."""
    defaults = [
        ('Air Conditioner (1.5T)', 1500, 1, 6.0),
        ('Refrigerator', 200, 1, 24.0),
        ('Ceiling Fan', 75, 3, 10.0),
        ('LED Lights', 10, 6, 6.0),
        ('Television', 120, 1, 4.0),
        ('Washing Machine', 500, 1, 1.5),
        ('Water Heater (Geyser)', 2000, 1, 1.0)
    ]
    conn = get_connection(db_path)
    cursor = conn.cursor()
    for name, power, qty, hrs in defaults:
        cursor.execute("""
        INSERT INTO appliances (user_id, name, power_watts, quantity, hours_per_day)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, power, qty, hrs))
    conn.commit()
    conn.close()

# ========================= SIMULATOR =========================

def save_simulator_session(user_id, session_data, totals, db_path=None):
    """Save a simulator session."""
    import json
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO simulator_sessions (user_id, session_data, total_current_kwh, total_new_kwh, energy_saved_kwh, money_saved)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, json.dumps(session_data),
          float(totals.get('current_kwh', 0)),
          float(totals.get('new_kwh', 0)),
          float(totals.get('saved_kwh', 0)),
          float(totals.get('money_saved', 0))))
    conn.commit()
    conn.close()

# ========================= SEED SAMPLE DATA =========================

def seed_sample_predictions(db_path=None):
    """Seed initial sample historical predictions if database is empty."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM predictions")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        samples = [
            {
                'voltage': 230.0, 'current': 3.2, 'usage_hours': 4.5, 'number_of_appliances': 3,
                'temperature': 25.0, 'previous_consumption': 3.1, 'predicted_consumption': 3.45,
                'consumption_level': 'LOW',
                'recommendation': 'Your energy consumption is relatively low. Continue your energy-efficient practices.',
                'user_id': 1
            },
            {
                'voltage': 228.5, 'current': 6.8, 'usage_hours': 7.0, 'number_of_appliances': 6,
                'temperature': 31.5, 'previous_consumption': 8.5, 'predicted_consumption': 8.92,
                'consumption_level': 'NORMAL',
                'recommendation': 'Your energy consumption is in a moderate range. Optimize cooling appliances during peak hours.',
                'user_id': 1
            },
            {
                'voltage': 234.0, 'current': 12.5, 'usage_hours': 14.0, 'number_of_appliances': 10,
                'temperature': 38.0, 'previous_consumption': 18.2, 'predicted_consumption': 19.84,
                'consumption_level': 'HIGH',
                'recommendation': 'High energy consumption detected. Reduce simultaneous heavy appliance usage and check for phantom loads.',
                'user_id': 2
            },
            {
                'voltage': 231.0, 'current': 4.5, 'usage_hours': 6.0, 'number_of_appliances': 4,
                'temperature': 27.0, 'previous_consumption': 5.8, 'predicted_consumption': 5.95,
                'consumption_level': 'LOW',
                'recommendation': 'Healthy consumption footprint. Maintain regular equipment maintenance.',
                'user_id': 2
            },
            {
                'voltage': 229.0, 'current': 9.2, 'usage_hours': 9.5, 'number_of_appliances': 8,
                'temperature': 34.0, 'previous_consumption': 12.4, 'predicted_consumption': 13.15,
                'consumption_level': 'HIGH',
                'recommendation': 'Elevated consumption detected. Set AC thermostats to 24°C to save up to 20% cooling power.',
                'user_id': 1
            }
        ]
        for s in samples:
            insert_prediction(s, db_path)
        print("[Database] Seeded initial sample predictions.")

# ========================= ADVISOR HISTORY =========================

def save_advisor_conversation(user_id, question, answer, topic='general', db_path=None):
    """Save an advisor Q&A pair to history."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO advisor_history (user_id, question, answer, topic)
    VALUES (?, ?, ?, ?)
    """, (user_id, question, answer, topic))
    conn.commit()
    conn.close()

def get_advisor_history(user_id, limit=20, db_path=None):
    """Get recent advisor conversations for a user."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM advisor_history WHERE user_id = ?
    ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_weekly_consumption(user_id=None, db_path=None):
    """Get consumption data grouped by day for the past 7 days."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    filter_sql = " AND user_id = ?" if user_id else ""
    params = [user_id] if user_id else []
    cursor.execute(f"""
        SELECT strftime('%Y-%m-%d', timestamp) as day,
               AVG(predicted_consumption) as avg_kwh,
               COUNT(*) as count
        FROM predictions
        WHERE timestamp >= datetime('now', '-7 days'){filter_sql}
        GROUP BY strftime('%Y-%m-%d', timestamp)
        ORDER BY day ASC
    """, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user_password(user_id, new_password, db_path=None):
    """Update user's password hash."""
    from werkzeug.security import generate_password_hash
    conn = get_connection(db_path)
    cursor = conn.cursor()
    new_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_sample_predictions()
