import psycopg2 as ps2
import pandas as pd
import streamlit as st

def create_db_if_not_exists():
    conn = ps2.connect(
        host=st.secrets["host"],
        database="postgres",
        user=st.secrets["user"],
        password=st.secrets["password"]
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (st.secrets["database"],))
    if not cursor.fetchone():
        cursor.execute(f"CREATE DATABASE {st.secrets['database']}")
    cursor.close()
    conn.close()

def connect_to_db():
    return ps2.connect(
        host=st.secrets["host"],
        database=st.secrets["database"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        options="-c lc_messages=C"
)

def init_db():
    create_db_if_not_exists()
    connection = connect_to_db()
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        registration_date DATE DEFAULT CURRENT_DATE,
        status VARCHAR(50) NOT NULL DEFAULT 'Permanent'
    );
    """
    try:
        cursor.execute(create_table_query)
        connection.commit()
    except Exception as e:
        connection.rollback()
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def load_employees():
    connection = connect_to_db()
    query = "SELECT id, name, registration_date, status FROM employees ORDER BY id;"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

def delete_employee(employee_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM employees WHERE id = %s;", (int(employee_id),))
        connection.commit()
    except Exception as e:
        connection.rollback()
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def add_employees(name, status):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
    if cursor.fetchone() is not None:
        st.error("Employee with this name already exists")
        cursor.close()
        connection.close()
        return
    cursor.execute(
        "INSERT INTO employees (name, status) VALUES (%s, %s);",
        (name, status)
    )
    connection.commit()
    cursor.close()
    connection.close()