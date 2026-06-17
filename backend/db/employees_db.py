import psycopg2 as ps2
import psycopg2.extras
import pandas as pd
import streamlit as st
import numpy as np

def connect_to_db():
    return ps2.connect(
        host=st.secrets["host"],
        database=st.secrets["database"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        sslmode="require"
)

def init_db():
    connection = connect_to_db()
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        registration_date DATE DEFAULT CURRENT_DATE,
        status VARCHAR(50) NOT NULL DEFAULT 'Permanent',
        embedding FLOAT8[],
        access_days INTEGER
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

def add_employees(name, status, embedding=None, access_days=None):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
    if cursor.fetchone() is not None:
        st.error("Employee with this name already exists")
        cursor.close()
        connection.close()
        return
    
    embedding = embedding.tolist() if embedding is not None else None
    
    cursor.execute(
        "INSERT INTO employees (name, status, embedding, access_days) VALUES (%s, %s, %s, %s);",
        (name, status, embedding, access_days)
    )
    connection.commit()
    cursor.close()
    connection.close()

def get_all_embeddings():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, embedding FROM employees WHERE embedding IS NOT NULL")

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    embeddings = []
    for row in rows:
        if row[2]:
            embedding_array = np.array(row[2])
            embeddings.append((row[0], row[1], embedding_array))
    
    return embeddings

def find_closest_embedding(target_embedding, threshold=0.56):
    """Find the closest matching embedding in the database"""
    from recognition.recognize import compare_faces
    
    embeddings_data = get_all_embeddings()
    if not embeddings_data:
        return None
    
    best_match = None
    best_similarity = 0
    
    for emp_id, name, db_embedding in embeddings_data:
        similarity, is_match = compare_faces(target_embedding, db_embedding, threshold)
        if is_match and similarity > best_similarity:
            best_similarity = similarity
            best_match = (emp_id, name, similarity)
    
    return best_match