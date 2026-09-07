import sqlite3
import json
import os
from datetime import datetime

# Base dir is two levels up (app/models)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(base_dir, "dfir_workbench.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        origin_ip TEXT,
        threat_score INTEGER,
        fraud_taxonomy TEXT,
        json_data TEXT NOT NULL
    )
    ''')
    
    # Settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    ''')
    
    # Seed default retention policy (30 days)
    cursor.execute('''
    INSERT OR IGNORE INTO settings (key, value) VALUES ('retention_days', '30')
    ''')
    
    conn.commit()
    conn.close()

def save_case(case_data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    case_id = case_data["ingestion"]["hash_sha256"]
    timestamp = case_data["ingestion"]["timestamp"]
    origin_ip = case_data["forensics"]["origin_ip"]
    threat_score = case_data["forensics"]["threat_score"]
    
    ai_analysis = case_data.get("ai_analysis")
    fraud_taxonomy = ai_analysis.get("fraud_taxonomy") if ai_analysis else "unknown"
    
    cursor.execute('''
    INSERT OR REPLACE INTO cases (case_id, timestamp, origin_ip, threat_score, fraud_taxonomy, json_data)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (case_id, timestamp, origin_ip, threat_score, fraud_taxonomy, json.dumps(case_data)))
    
    conn.commit()
    conn.close()

def get_cases():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT case_id, timestamp, origin_ip, threat_score, fraud_taxonomy FROM cases ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_case_by_id(case_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT json_data FROM cases WHERE case_id = ?', (case_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['json_data'])
    return None

def get_retention_days() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'retention_days'")
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return int(row['value'])
        except ValueError:
            return 30
    return 30

def purge_old_cases():
    days = get_retention_days()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We query the DB and parse ISO strings since sqlite doesn't have native datetime
    cursor.execute('SELECT case_id, timestamp FROM cases')
    rows = cursor.fetchall()
    
    now = datetime.utcnow()
    deleted_count = 0
    
    for row in rows:
        try:
            case_time = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            if (now.replace(tzinfo=case_time.tzinfo) - case_time).days > days:
                cursor.execute('DELETE FROM cases WHERE case_id = ?', (row['case_id'],))
                deleted_count += 1
                
                # Also delete associated .eml from uploads if exists
                upload_path = os.path.join(os.getcwd(), "uploads", f"{row['case_id']}.eml")
                if os.path.exists(upload_path):
                    try:
                        os.remove(upload_path)
                    except:
                        pass
        except Exception as e:
            print(f"Error parsing timestamp for case {row['case_id']}: {e}")
            
    conn.commit()
    conn.close()
    return deleted_count

# Initialize DB on module load
init_db()
