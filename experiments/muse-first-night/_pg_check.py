"""Quick PG connectivity + capability check."""
import psycopg2

DB = dict(host="localhost", port=5433, dbname="consonance", user="kai", password="resonance")

with psycopg2.connect(**DB) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        print("server:", cur.fetchone()[0])

        # List all databases
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
        dbs = [r[0] for r in cur.fetchall()]
        print("databases:", dbs)

        # List installed extensions
        cur.execute("SELECT extname, extversion FROM pg_extension ORDER BY extname")
        exts = cur.fetchall()
        print("extensions in 'consonance':", exts)

        # Check if TimescaleDB is *available* (not necessarily installed)
        cur.execute("SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name LIKE %s OR name LIKE %s", ("timescale%", "%timescale%"))
        avail = cur.fetchall()
        print("timescale available:", avail)

        # List tables in current DB
        cur.execute("""
            SELECT table_schema, table_name FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog','information_schema')
            ORDER BY table_schema, table_name
        """)
        tables = cur.fetchall()
        print("tables in 'consonance':")
        for s, t in tables:
            print(f"  {s}.{t}")
