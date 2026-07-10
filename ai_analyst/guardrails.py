"""The verification gate.

Before any AI-generated SQL is allowed to touch the warehouse, it must pass these
checks: single statement, read-only, and referencing only whitelisted tables. This is
the same "verify before you trust the output" discipline behind the governed-AI program
this whole project is modeled on. It is defense in depth: the database connection is
also opened read-only, so even a check that slipped through could not write.
"""
import re

# Side-effecting / DDL / DML keywords that must never appear in a read-only query.
# (Scalar functions like replace() are deliberately NOT listed, to avoid false blocks.)
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma|"
    r"export|import|install|load|call|truncate|grant|revoke|vacuum)\b",
    re.IGNORECASE,
)


def _strip(sql):
    """Remove comments and trailing semicolons/whitespace."""
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql.strip().rstrip(";").strip()


def validate_sql(sql, allowed_tables, max_rows=1000):
    """Validate an AI-generated query. Returns (ok, reason, safe_sql).

    safe_sql is the cleaned query with a LIMIT appended if one was missing.
    """
    cleaned = _strip(sql)
    if not cleaned:
        return False, "Empty query.", ""

    # 1. single statement only
    if ";" in cleaned:
        return False, "Multiple statements are not allowed.", ""

    # 2. must be a read-only SELECT / WITH
    head = cleaned.lstrip("(").lower()
    if not (head.startswith("select") or head.startswith("with")):
        return False, "Only SELECT / WITH (read-only) queries are allowed.", ""

    # 3. no side-effecting keywords
    hit = _FORBIDDEN.search(cleaned)
    if hit:
        return False, f"Forbidden keyword '{hit.group(0)}' (read-only queries only).", ""

    # 4. only whitelisted tables may be referenced (CTE names are allowed)
    referenced = set(re.findall(r"\bfrom\s+([a-zA-Z_]\w*)", cleaned, re.IGNORECASE))
    referenced |= set(re.findall(r"\bjoin\s+([a-zA-Z_]\w*)", cleaned, re.IGNORECASE))
    ctes = {c.lower() for c in re.findall(r"\b([a-zA-Z_]\w*)\s+as\s*\(", cleaned, re.IGNORECASE)}
    allowed = {t.lower() for t in allowed_tables}
    unknown = {r for r in referenced if r.lower() not in allowed and r.lower() not in ctes}
    if unknown:
        return False, f"Query references tables outside the approved set: {', '.join(sorted(unknown))}.", ""

    # 5. enforce a row cap
    safe_sql = cleaned
    if not re.search(r"\blimit\s+\d+", cleaned, re.IGNORECASE):
        safe_sql = f"{cleaned}\nLIMIT {max_rows}"
    return True, "OK", safe_sql
