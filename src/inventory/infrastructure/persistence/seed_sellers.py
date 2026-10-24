"""Script to load sellers into PostgreSQL (>= 3,000 sellers).

Reads credentials securely from the .env file through the project's
existing configuration module. No passwords or usernames are hardcoded
in this file.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from inventory.infrastructure.config import (
    POS_DB_HOST,
    POS_DB_PORT,
    POS_DB_NAME,
    POS_DB_USER,
    POS_DB_PASSWORD,
)

BASE_SELLERS = [
    ("SEL-001", "MercaAndes Retail Colombia", "own", "CO"),
    ("SEL-ABC", "Test Seller", "own", "CO"),
    ("SEL-3P-101", "AndesMarket Global", "third_party", "CL"),
    ("SEL-002", "MercaAndes Retail Peru", "own", "PE"),
]

TOTAL_TARGET_SELLERS = 3000


def build_sellers_catalog(target_count: int = TOTAL_TARGET_SELLERS) -> list[dict[str, str]]:
    """Builds a catalog of at least target_count sellers including base sellers."""
    sellers_dict: dict[str, dict[str, str]] = {}

    for seller_id, name, seller_type, country in BASE_SELLERS:
        sellers_dict[seller_id] = {
            "seller_id": seller_id,
            "name": name,
            "seller_type": seller_type,
            "country": country,
        }

    countries = ["CO", "PE", "CL", "BO", "EC"]
    types = ["own", "third_party"]
    prefixes = [
        "MercaAndes",
        "AndesMarket",
        "Comercial",
        "Distribuidora",
        "Tienda",
        "Retail",
        "Almacenes",
        "Supermercados",
        "Importadora",
    ]
    categories = [
        "Express",
        "Plus",
        "Global",
        "Direct",
        "Prime",
        "Logistics",
        "Store",
        "Electronica",
        "Moda",
        "Hogar",
        "Alimentos",
    ]

    idx = 1
    while len(sellers_dict) < target_count:
        sid = f"SEL-{idx:04d}"
        if sid not in sellers_dict:
            country = countries[idx % len(countries)]
            seller_type = types[idx % len(types)]
            p = prefixes[(idx // 11) % len(prefixes)]
            c = categories[(idx // 3) % len(categories)]
            name = f"{p} {c} {country} {idx}"
            sellers_dict[sid] = {
                "seller_id": sid,
                "name": name,
                "seller_type": seller_type,
                "country": country,
            }
        idx += 1

    return list(sellers_dict.values())


def main() -> None:
    DATABASE_URL = (
        f"postgresql+psycopg://{POS_DB_USER}:{POS_DB_PASSWORD}"
        f"@{POS_DB_HOST}:{POS_DB_PORT}/{POS_DB_NAME}"
    )

    sellers = build_sellers_catalog(TOTAL_TARGET_SELLERS)

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.sellers (
                seller_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                seller_type VARCHAR(50) NOT NULL,
                country VARCHAR(10) NOT NULL
            );
        """))

        count = conn.execute(text("SELECT COUNT(*) FROM public.sellers")).scalar()
        if count and count >= TOTAL_TARGET_SELLERS:
            print(f"Database already initialized with {count} sellers.")
            return

        conn.execute(
            text("""
                INSERT INTO public.sellers (seller_id, name, seller_type, country)
                VALUES (:seller_id, :name, :seller_type, :country)
                ON CONFLICT (seller_id) DO NOTHING;
            """),
            sellers,
        )

        conn.commit()
        print(f"Successfully loaded {len(sellers)} sellers into PostgreSQL.")
        print("Example seller_ids available for Swagger:")
        for s in sellers[:5]:
            print(f"  - {s['seller_id']}: {s['name']}")


if __name__ == "__main__":
    main()
