"""Print the tables and constraints of the configured MySQL database."""

import json

from sqlalchemy import inspect

from database import load_database


def main():
    engine, _base, _session_local = load_database()
    schema = inspect(engine)
    report = []

    for table_name in schema.get_table_names():
        primary_key_columns = schema.get_pk_constraint(table_name).get("constrained_columns") or []
        columns = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "primary_key": column["name"] in primary_key_columns,
            }
            for column in schema.get_columns(table_name)
        ]
        report.append(
            {
                "table": table_name,
                "columns": columns,
                "foreign_keys": schema.get_foreign_keys(table_name),
            }
        )

    print(json.dumps(report, ensure_ascii=True, indent=2, default=str))
    engine.dispose()


if __name__ == "__main__":
    main()
