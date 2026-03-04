"""
Generate SQLAlchemy ORM models and Pydantic schemas from schema_output.json
"""
import json
import os
from collections import defaultdict

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema_output.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "app")

def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)

def pg_to_sqlalchemy(col):
    """Map PostgreSQL column info to SQLAlchemy type string."""
    dt = col["data_type"]
    udt = col.get("udt_name") or dt
    nullable = col["is_nullable"] == "YES"
    default = col.get("column_default")
    char_max = col.get("character_maximum_length")
    num_prec = col.get("numeric_precision")
    num_scale = col.get("numeric_scale")

    # Exact type mapping
    if udt == "uuid":
        return "UUID(as_uuid=True)", nullable, default
    if dt == "character varying" or udt == "varchar":
        length = f", {char_max}" if char_max else ""
        return f"String(length={char_max or 255})", nullable, default
    if dt == "text" or udt == "text":
        return "Text", nullable, default
    if udt in ("int4", "integer"):
        return "Integer", nullable, default
    if udt in ("int8", "bigint"):
        return "BigInteger", nullable, default
    if udt in ("int2", "smallint"):
        return "SmallInteger", nullable, default
    if udt in ("serial", "serial4"):
        return "Integer", False, default  # autoincrement
    if udt in ("bigserial", "serial8"):
        return "BigInteger", False, default
    if dt == "boolean" or udt == "bool":
        return "Boolean", nullable, default
    if "timestamp" in dt or udt in ("timestamptz", "timestamp"):
        return "DateTime(timezone=True)" if "with time zone" in dt or udt == "timestamptz" else "DateTime", nullable, default
    if dt == "date" or udt == "date":
        return "Date", nullable, default
    if dt in ("numeric", "decimal") or udt in ("numeric", "decimal"):
        prec = num_prec or 18
        scale = num_scale or 4
        return f"Numeric(precision={prec}, scale={scale})", nullable, default
    if dt in ("real", "float4"):
        return "Float", nullable, default
    if dt in ("double precision", "float8"):
        return "Float", nullable, default
    if dt in ("json", "jsonb") or udt in ("json", "jsonb"):
        return "JSON", nullable, default
    if dt == "ARRAY" or udt == "array":
        return "ARRAY(String)", nullable, default  # generic array
    if udt == "bytea":
        return "LargeBinary", nullable, default
    # fallback
    return "String(255)", nullable, default

def snake_to_pascal(snake_str):
    return "".join(x.capitalize() for x in snake_str.split("_"))

def table_to_class_name(table_name):
    return snake_to_pascal(table_name.rstrip("s") if table_name.endswith("s") else table_name)

def main():
    schema = load_schema()
    tables = schema["tables"]
    columns = schema["columns"]
    pks = schema["primary_keys"]
    fks = schema["foreign_keys"]

    pk_map = defaultdict(list)  # table -> [col names]
    for r in pks:
        pk_map[r["table_name"]].append(r["column_name"])

    fk_map = defaultdict(list)  # (table, column) -> (to_table, to_column)
    for r in fks:
        fk_map[(r["from_table"], r["from_column"])] = (r["to_table"], r["to_column"])

    cols_by_table = defaultdict(list)
    for c in columns:
        cols_by_table[c["table_name"]].append(c)

    # Build model lines per table
    imports = set()
    model_lines = []

    for table_name in tables:
        class_name = table_to_class_name(table_name)
        model_lines.append(f'\nclass {class_name}(Base):')
        model_lines.append(f'    __tablename__ = "{table_name}"')
        model_lines.append("")

        for col in sorted(cols_by_table[table_name], key=lambda x: x["ordinal_position"]):
            cname = col["column_name"]
            # Reserved in SQLAlchemy Declarative API
            attr_name = f"{cname}_" if cname == "metadata" else cname
            sa_type, nullable, default = pg_to_sqlalchemy(col)
            fk_target = fk_map.get((table_name, cname))
            pk = cname in pk_map[table_name]
            parts = [sa_type]
            if fk_target:
                to_table, to_col = fk_target
                parts.append(f'ForeignKey("{to_table}.{to_col}")')
            if pk:
                parts.append("primary_key=True")
            if default and isinstance(default, str) and "nextval" in default:
                parts.append("autoincrement=True")
            parts.append(f"nullable={nullable}")
            if attr_name != cname:
                model_lines.append(f'    {attr_name} = Column("{cname}", {", ".join(parts)})')
            else:
                model_lines.append(f'    {cname} = Column({", ".join(parts)})')
            # track imports from sa_type
            for token in ["UUID", "DateTime", "Date", "Text", "Numeric", "JSON", "BigInteger", "SmallInteger", "Boolean", "LargeBinary", "ARRAY"]:
                if token in sa_type:
                    imports.add(token)
            if fk_target:
                imports.add("ForeignKey")

    # Write models.py
    os.makedirs(OUT_DIR, exist_ok=True)
    imports.add("Column")
    imports.add("String")
    imports.add("Integer")
    imports.add("Float")

    imp_list = sorted(imports)
    base_imports = "from sqlalchemy import Column, String, Integer, Float, DateTime, Date, Text, Boolean, ForeignKey, Numeric, BigInteger, SmallInteger, LargeBinary\nfrom sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY\nfrom sqlalchemy.orm import declarative_base\n\nBase = declarative_base()"

    with open(os.path.join(OUT_DIR, "models.py"), "w") as f:
        f.write('"""SQLAlchemy ORM models generated from PostgreSQL schema (stakflo_dev)."""\n\n')
        f.write(base_imports)
        f.write("\n\n")
        f.write("\n".join(model_lines))
        f.write("\n")

    print("Generated app/models.py")
    return 0

if __name__ == "__main__":
    exit(main())
