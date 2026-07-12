from db.connection import get_db_connection


def init_db():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) NOT NULL
            );
            """
            try:
                cursor.execute(create_table_query)
                connection.commit()
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")


def add_log(name: str, status: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                        INSERT INTO logs (name, status)
                        SELECT %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM logs WHERE name = %s
                            AND status = %s AND time > NOW() - INTERVAL '1 minute'
                        )
                        """,
                (name, status, name, status),
            )
        conn.commit()


def get_all_logs(start_date=None, end_date=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = "SELECT id, name, time, status FROM logs"
            params = []
            if start_date and end_date:
                query += " WHERE time >= %s AND time < %s"
                params.extend([start_date, end_date])
            query += " ORDER BY time DESC LIMIT 100"
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "time": str(r[2]), "status": r[3]} for r in rows]


def delete_old_logs():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM logs WHERE time < NOW() - INTERVAL '3 days'")
        conn.commit()


def get_last_entry(employee_name):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT time FROM logs WHERE name = %s ORDER BY time DESC LIMIT 1",
                (employee_name,),
            )
            row = cur.fetchone()
    if row:
        return row[0]
    return None


def get_last_entries():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, MAX(time) FROM logs GROUP BY name")
            rows = cur.fetchall()
    return {row[0]: row[1] for row in rows}
