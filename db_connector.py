# db_connector.py
import mysql.connector
from config import DB_CONFIG

def get_db_connection():
    """ينشئ ويعيد اتصال قاعدة البيانات."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"خطأ في الاتصال بقاعدة البيانات: {err}")
        return None

def execute_query(query, params=None, fetch=False):
    """ينفذ استعلام SQL ويعيد النتائج إذا طلب منه ذلك."""
    conn = get_db_connection()
    if conn is None:
        return [] if fetch else None
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return True
    except mysql.connector.Error as err:
        print(f"خطأ في تنفيذ الاستعلام: {err}\nالاستعلام: {query}")
        return False
    finally:
        cursor.close()
        conn.close()
