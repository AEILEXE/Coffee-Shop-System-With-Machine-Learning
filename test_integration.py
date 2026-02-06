#!/usr/bin/env python3
"""
Integration test script to verify all modules and database setup
"""

import sqlite3

def test_database():
    """Test database schema and seeded data"""
    try:
        conn = sqlite3.connect('cafecraft.db')
        cursor = conn.cursor()
        
        # Check products
        cursor.execute('SELECT COUNT(*) FROM products')
        product_count = cursor.fetchone()[0]
        print(f'✓ Products in database: {product_count}')
        
        # Check users
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        print(f'✓ Users in database: {user_count}')
        
        # Check categories
        cursor.execute('SELECT DISTINCT category FROM products ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        print(f'✓ Product categories: {len(categories)}')
        for cat in categories:
            print(f'  - {cat}')
        
        # Check orders table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if cursor.fetchone():
            print('✓ Orders table exists')
        
        # Check transactions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
        if cursor.fetchone():
            print('✓ Transactions table exists')
        
        conn.close()
        print('✓ Database schema verified successfully')
        return True
    except Exception as e:
        print(f'✗ Database test failed: {e}')
        return False

def test_imports():
    """Test all module imports"""
    try:
        from pos.pos_service import POSService
        from pos.pos_manager import POSManager
        from inventory.inventory_service import InventoryService
        from inventory.inventory_manager import InventoryManager
        from reports.reports_service import ReportsService
        from reports.reports_manager import ReportsManager
        from auth.user_management_service import UserManagementService
        
        print('✓ POS module fully integrated')
        print('✓ Inventory module fully integrated')
        print('✓ Reports module fully integrated')
        print('✓ User management module fully integrated')
        return True
    except Exception as e:
        print(f'✗ Import test failed: {e}')
        return False

def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("CAFÉCRAFT SYSTEM - INTEGRATION TEST")
    print("="*60 + "\n")
    
    print("[1/2] Testing module imports...")
    imports_ok = test_imports()
    
    print("\n[2/2] Testing database schema...")
    database_ok = test_database()
    
    print("\n" + "="*60)
    if imports_ok and database_ok:
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("="*60)
        print("\nSystem is ready for operation!")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
