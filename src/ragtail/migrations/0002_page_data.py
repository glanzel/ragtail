"""Add JSON storage for typed page subclass fields."""

depends_on = "0001_ragtail_initial"


def upgrade(ctx):
    """Apply migration."""
    ctx.add_column(
        "oxytail_pages",
        {
            "name": "page_data",
            "python_type": "str",
            "db_type": "TEXT",
            "nullable": True,
            "primary_key": False,
            "unique": False,
            "default": None,
            "auto_increment": False,
            "max_length": None,
            "max_digits": None,
            "decimal_places": None,
        },
    )


def downgrade(ctx):
    """Revert migration."""
    ctx.drop_column("oxytail_pages", "page_data")
