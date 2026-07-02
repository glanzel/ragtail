"""Auto-generated migration.

Created: 2026-07-01 23:06:18
"""

depends_on = None


def upgrade(ctx):
    """Apply migration."""
    ctx.create_table(
        "oxytail_users",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'username',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': 150,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'email',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': 254,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'password_hash',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_active',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '1',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_staff',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '1',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
    )
    ctx.create_table(
        "oxytail_locales",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'language_code',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': 16,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'display_name',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 120,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_default',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_active',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '1',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'sort_order',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
    )
    ctx.create_table(
        "oxytail_menus",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'name',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 120,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'slug',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 80,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_active',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '1',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'locale_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_oxytail_menus_locale_id',
                'columns': [
                    'locale_id'
                ],
                'ref_table': 'oxytail_locales',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            }
        ],
    )
    ctx.create_table(
        "oxytail_pages",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'title',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'slug',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 120,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'path',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 512,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'depth',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '1',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'sort_order',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'translation_key',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 36,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'content_type',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': "'page'",
                'auto_increment': False,
                'max_length': 100,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'page_data',
                'python_type': 'str',
                'db_type': 'TEXT',
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'body',
                'python_type': 'str',
                'db_type': 'TEXT',
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'seo_title',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'search_description',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 500,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'live',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'show_in_menus',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'first_published_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'last_published_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'locale_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'parent_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        indexes=[
            {
                'name': 'oxytail_pages_locale_slug_idx',
                'fields': [
                    'locale',
                    'slug'
                ],
                'unique': False,
                'method': None
            },
            {
                'name': 'oxytail_pages_parent_sort_order_idx',
                'fields': [
                    'parent',
                    'sort_order'
                ],
                'unique': False,
                'method': None
            },
            {
                'name': 'oxytail_pages_translation_key_locale_idx',
                'fields': [
                    'translation_key',
                    'locale'
                ],
                'unique': False,
                'method': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_oxytail_pages_locale_id',
                'columns': [
                    'locale_id'
                ],
                'ref_table': 'oxytail_locales',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'RESTRICT',
                'on_update': 'CASCADE'
            },
            {
                'name': 'fk_oxytail_pages_parent_id',
                'columns': [
                    'parent_id'
                ],
                'ref_table': 'oxytail_pages',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            }
        ],
    )
    ctx.create_table(
        "oxytail_menu_items",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'label',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 120,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'url',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 512,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'sort_order',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_active',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '1',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'open_in_new_tab',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'menu_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'parent_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'page_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        indexes=[
            {
                'name': 'oxytail_menu_items_menu_parent_sort_order_idx',
                'fields': [
                    'menu',
                    'parent',
                    'sort_order'
                ],
                'unique': False,
                'method': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_oxytail_menu_items_menu_id',
                'columns': [
                    'menu_id'
                ],
                'ref_table': 'oxytail_menus',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'name': 'fk_oxytail_menu_items_parent_id',
                'columns': [
                    'parent_id'
                ],
                'ref_table': 'oxytail_menu_items',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'name': 'fk_oxytail_menu_items_page_id',
                'columns': [
                    'page_id'
                ],
                'ref_table': 'oxytail_pages',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'SET NULL',
                'on_update': 'CASCADE'
            }
        ],
    )
    ctx.create_table(
        "oxytail_sites",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'hostname',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'port',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '80',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'site_name',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'is_default_site',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'prefix_default_language',
                'python_type': 'bool',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'root_page_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_oxytail_sites_root_page_id',
                'columns': [
                    'root_page_id'
                ],
                'ref_table': 'oxytail_pages',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'SET NULL',
                'on_update': 'CASCADE'
            }
        ],
    )
    ctx.create_table(
        "oxytail_images",
        fields=[
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': 'CURRENT_TIMESTAMP',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'title',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'file',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 512,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'width',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'height',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'focal_point_x',
                'python_type': 'float',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'focal_point_y',
                'python_type': 'float',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'file_hash',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 64,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'file_size',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
    )
    ctx.create_table(
        "oxytail_renditions",
        fields=[
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'filter_spec',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 255,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'file',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': 512,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'width',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'height',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'image_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        indexes=[
            {
                'name': 'oxytail_renditions_image_filter_spec_idx',
                'fields': [
                    'image',
                    'filter_spec'
                ],
                'unique': False,
                'method': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_oxytail_renditions_image_id',
                'columns': [
                    'image_id'
                ],
                'ref_table': 'oxytail_images',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            }
        ],
    )


def downgrade(ctx):
    """Revert migration."""
    ctx.drop_table("oxytail_renditions")
    ctx.drop_table("oxytail_images")
    ctx.drop_table("oxytail_sites")
    ctx.drop_table("oxytail_menu_items")
    ctx.drop_table("oxytail_pages")
    ctx.drop_table("oxytail_menus")
    ctx.drop_table("oxytail_locales")
    ctx.drop_table("oxytail_users")
