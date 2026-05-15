from sqlalchemy.types import UserDefinedType

try:
    from pgvector.sqlalchemy import Vector as PgVector
except ImportError:
    PgVector = None


def Vector(dimensions: int):
    if PgVector is not None:
        return PgVector(dimensions)

    class FallbackVector(UserDefinedType):
        cache_ok = True

        def get_col_spec(self, **kw) -> str:
            return f"VECTOR({dimensions})"

    return FallbackVector()
