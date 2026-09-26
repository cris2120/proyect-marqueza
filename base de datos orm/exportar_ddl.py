"""Export MySQL table definitions without exporting table data."""

import argparse
import os
import re
from pathlib import Path

import MySQLdb
from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / "backend" / "API" / ".env"


def export_schema(output_path):
    settings = {**dotenv_values(ENV_FILE), **os.environ}
    database = settings.get("MYSQL_DB") or settings.get("MYSQL_DATABASE") or settings.get("mysql_db")
    host = settings.get("MYSQL_HOST") or settings.get("mysql_host")
    user = settings.get("MYSQL_USER") or settings.get("mysql_user")
    password = settings.get("MYSQL_PASSWORD") or settings.get("mysql_password")
    port = int(settings.get("MYSQL_PORT") or settings.get("mysql_port") or 3306)

    if not all((database, host, user)):
        raise RuntimeError("Faltan variables MySQL para conectarse a la base de datos.")

    connection = MySQLdb.connect(
        host=host,
        port=port,
        user=user,
        passwd=password or "",
        db=database,
        charset="utf8mb4",
        connect_timeout=5,
    )
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        if not tables:
            raise RuntimeError("La base de datos no contiene tablas para exportar.")

        statements = []
        for table in tables:
            quoted_table = table.replace("`", "``")
            cursor.execute(f"SHOW CREATE TABLE `{quoted_table}`")
            ddl = re.sub(r"\sAUTO_INCREMENT=\d+", "", cursor.fetchone()[1], count=1)
            statements.append(ddl + ";")
        cursor.close()
    finally:
        connection.close()

    output_path = Path(output_path).resolve()
    output_path.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
    return output_path, len(tables)


def main():
    parser = argparse.ArgumentParser(description="Exporta el DDL MySQL sin datos.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "schema.mysql.sql",
        help="Ruta del archivo SQL de salida.",
    )
    args = parser.parse_args()
    output_path, table_count = export_schema(args.output)
    print(f"Exportadas {table_count} tablas a {output_path}")


if __name__ == "__main__":
    main()