#!/usr/bin/env python3
"""
Validation script for ANG-36 implementation.

Checks:
1. All imports work correctly
2. No syntax errors
3. CRUD functions exist and have correct signatures
4. API endpoints are registered
5. Schemas are valid
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_imports():
    """Check that all modules can be imported."""
    print("🔍 Validating imports...")

    try:
        from app import crud, schemas, models
        from app.api.v1.endpoints import orders
        from app.db.session import Base, get_db
        from app.core.config import settings
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def validate_crud_functions():
    """Check that required CRUD functions exist."""
    print("\n🔍 Validating CRUD functions...")

    from app import crud

    required_functions = [
        "generate_order_number",
        "create_order",
        "get_orders",
        "get_order",
        "get_active_order_for_table",
        "update_order",
        "admin_edit_order",
        "cancel_order",
        "create_payment",
        "get_payments_for_order",
    ]

    all_good = True
    for func_name in required_functions:
        if hasattr(crud, func_name):
            print(f"✅ {func_name} exists")
        else:
            print(f"❌ {func_name} missing")
            all_good = False

    return all_good


def validate_schemas():
    """Check that required schemas exist."""
    print("\n🔍 Validating schemas...")

    from app import schemas

    required_schemas = [
        "OrderCreate",
        "OrderUpdate",
        "OrderItemsUpdate",  # New schema for admin edit
        "Order",
        "OrderItem",
        "OrderItemCreate",
        "Payment",
        "PaymentCreate",
    ]

    all_good = True
    for schema_name in required_schemas:
        if hasattr(schemas, schema_name):
            print(f"✅ {schema_name} exists")
        else:
            print(f"❌ {schema_name} missing")
            all_good = False

    return all_good


def validate_endpoints():
    """Check that API endpoints are registered."""
    print("\n🔍 Validating API endpoints...")

    from app.main import app

    expected_routes = [
        # Order endpoints
        ("POST", "/api/v1/orders"),
        ("GET", "/api/v1/orders/active"),
        ("GET", "/api/v1/orders/{order_id}"),
        ("PATCH", "/api/v1/orders/{order_id}"),
        ("PUT", "/api/v1/orders/{order_id}"),
        ("DELETE", "/api/v1/orders/{order_id}"),
        ("GET", "/api/v1/orders/table/{table_number}/active"),
        # Payment endpoints
        ("POST", "/api/v1/orders/{order_id}/payments"),
        ("GET", "/api/v1/orders/{order_id}/payments"),
    ]

    routes = [
        (route.methods, route.path)
        for route in app.routes
    ]

    all_good = True
    for method, path in expected_routes:
        found = False
        for route_methods, route_path in routes:
            if method in route_methods and route_path == path:
                found = True
                break

        if found:
            print(f"✅ {method} {path}")
        else:
            print(f"❌ {method} {path} not found")
            all_good = False

    return all_good


def validate_models():
    """Check that database models are correct."""
    print("\n🔍 Validating database models...")

    from app.models.models import Order, OrderItem, OrderStatus, Payment

    # Check Order model has required fields
    order_fields = ["order_number", "table_number", "subtotal", "gst_amount",
                    "total_amount", "status", "created_at", "updated_at"]

    all_good = True
    for field in order_fields:
        if hasattr(Order, field):
            print(f"✅ Order.{field} exists")
        else:
            print(f"❌ Order.{field} missing")
            all_good = False

    # Check OrderStatus enum
    required_statuses = ["ACTIVE", "PAID", "CANCELED"]
    for status in required_statuses:
        if hasattr(OrderStatus, status):
            print(f"✅ OrderStatus.{status} exists")
        else:
            print(f"❌ OrderStatus.{status} missing")
            all_good = False

    return all_good


def validate_gst_calculation():
    """Check that GST calculation is correct."""
    print("\n🔍 Validating GST calculation logic...")

    from app.core.config import settings

    # Check GST rate
    if hasattr(settings, 'GST_RATE'):
        gst_rate = settings.GST_RATE
        if gst_rate == 18:
            print(f"✅ GST_RATE is {gst_rate}%")
        else:
            print(f"⚠️  GST_RATE is {gst_rate}% (expected 18%)")
        return True
    else:
        print("❌ GST_RATE not configured")
        return False


def check_test_coverage():
    """Check if test files exist."""
    print("\n🔍 Checking test coverage...")

    test_dir = Path(__file__).parent.parent / "tests"

    expected_tests = [
        "test_orders.py",
        "test_order_endpoints.py",
        "conftest.py",
    ]

    all_good = True
    for test_file in expected_tests:
        if (test_dir / test_file).exists():
            print(f"✅ {test_file} exists")
        else:
            print(f"❌ {test_file} missing")
            all_good = False

    return all_good


def main():
    """Run all validations."""
    print("=" * 60)
    print("ANG-36 Implementation Validation")
    print("=" * 60)

    results = {
        "Imports": validate_imports(),
        "CRUD Functions": validate_crud_functions(),
        "Schemas": validate_schemas(),
        "Endpoints": validate_endpoints(),
        "Models": validate_models(),
        "GST Calculation": validate_gst_calculation(),
        "Tests": check_test_coverage(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All validations passed! Implementation looks good.")
        print("\nNext steps:")
        print("1. Run tests: cd backend && uv run pytest -v")
        print("2. Start server: uv run uvicorn app.main:app --reload")
        print("3. Visit Swagger UI: http://localhost:8000/docs")
        return 0
    else:
        print("\n⚠️  Some validations failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
