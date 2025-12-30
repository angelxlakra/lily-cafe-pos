"""
CRUD operations package.
"""

from app.crud.crud import (
    # Category operations
    get_categories,
    get_category,
    create_category,
    # Menu item operations
    get_menu_items,
    get_menu_item,
    create_menu_item,
    update_menu_item,
    delete_menu_item,
    # Order operations
    generate_order_number,
    get_orders,
    get_order,
    get_active_order_for_table,
    create_order,
    update_order,
    admin_edit_order,
    cancel_order,
    update_order_item_served_status,
    update_order_item_served_quantity,
    set_order_item_served_quantity,
    # Payment operations
    create_payment,
    create_payments_batch,
    get_payments_for_order,
    replace_order_payments,
)

__all__ = [
    # Categories
    "get_categories",
    "get_category",
    "create_category",
    # Menu items
    "get_menu_items",
    "get_menu_item",
    "create_menu_item",
    "update_menu_item",
    "delete_menu_item",
    # Orders
    "generate_order_number",
    "get_orders",
    "get_order",
    "get_active_order_for_table",
    "create_order",
    "update_order",
    "admin_edit_order",
    "cancel_order",
    "update_order_item_served_status",
    "update_order_item_served_quantity",
    "set_order_item_served_quantity",
    # Payments
    "create_payment",
    "create_payments_batch",
    "get_payments_for_order",
    "replace_order_payments",
]
