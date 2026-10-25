import sqlite3
import streamlit as st
import pandas as pd
from groq import Groq

# Page Config
st.set_page_config(page_title="Text-to-SQL App (Groq)", page_icon="⚡", layout="wide")

st.title("⚡ Text-to-SQL ")
st.write("Ask questions about your employee database in plain English, powered by Groq's ultra-fast LPU inference!")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if not api_key:
    st.warning("Please enter your Groq API key in the sidebar to proceed. (Get one free at console.groq.com)")
    st.stop()

# Initialize Groq Client
client = Groq(api_key=api_key)

# --- HELPER FUNCTIONS ---

def get_db_schema(db_path="company.db"):
    """Extracts table names and column definitions from SQLite to give context to the LLM."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_info = []
    for table_name in tables:
        t_name = table_name[0]
        cursor.execute(f"PRAGMA table_info({t_name});")
        columns = cursor.fetchall()
        col_desc = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
        schema_info.append(f"Table: {t_name}\nColumns: {col_desc}")
        
    conn.close()
    return "\n\n".join(schema_info)

def generate_sql_query(user_prompt, schema):
    """Uses Groq to convert a natural language prompt into an SQLite query."""
    system_prompt = f"""
    You are an advanced Text-to-SQL engine. Your job is to convert natural language questions into valid, executable SQLite queries based on the provided database schema.
    
    Database Schema:
    {schema}
    
    Rules:
    - Return ONLY the raw SQL query. 
    - Do NOT wrap the query in markdown code blocks (like ```sql).
    - Do NOT include any explanations, punctuation, or extra text.
    - Only write SELECT queries (read-only).
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",  # Fast, highly accurate open model on Groq
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    
    sql_query = response.choices[0].message.content.strip()
    return sql_query

def validate_sql(sql_query):
    """Basic safety check to ensure the query is read-only."""
    forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    upper_query = sql_query.upper()
    for word in forbidden_keywords:
        if word in upper_query:
            return False
    return True

def execute_query(sql_query, db_path="company.db"):
    """Executes the SQL query against the SQLite database and returns a pandas DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql_query, conn)
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

# --- MAIN UI WORKFLOW ---

schema = get_db_schema()

# Display schema in an expander
with st.expander("🔍 View Database Schema"):
    st.text(schema)

# User Input Box
user_prompt = st.text_input("What would you like to know?", placeholder="e.g., Who has the highest salary in the Engineering department?")

if st.button("Run Query", type="primary"):
    if not user_prompt.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("Generating query via Groq & running against SQLite..."):
            
            # Step 1: Generate SQL via Groq LLM
            sql_query = generate_sql_query(user_prompt, schema)
            
            # Step 2: Safety Validation
            if not validate_sql(sql_query):
                st.error("❌ Safety Error: Generated query failed security checks (Only SELECT statements are allowed).")
            else:
                # Step 3: Display generated SQL
                st.markdown("### 📝 Generated SQL Query")
                st.code(sql_query, language="sql")
                
                # Step 4: Execute Query
                df, error = execute_query(sql_query)
                
                if error:
                    st.error(f"❌ Database Execution Error: {error}")
                else:
                    st.markdown("### 📊 Results")
                    if df.empty:
                        st.info("The query returned no results.")
                    else:
                        st.dataframe(df, use_container_width=True)