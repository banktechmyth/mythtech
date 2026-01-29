"""
สคริปต์ตรวจสอบและแก้ไขปัญหาการตั้งค่า
"""
import os
import sys
import django

# ตั้งค่า Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workapp.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection

def check_database():
    """ตรวจสอบว่าตาราง Category มีอยู่หรือไม่"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ICANDEP_category'")
            result = cursor.fetchone()
            if result:
                print("✓ ตาราง Category มีอยู่แล้ว")
                return True
            else:
                print("✗ ตาราง Category ยังไม่มี")
                return False
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาดในการตรวจสอบ: {e}")
        return False

def check_migrations():
    """ตรวจสอบว่า migration รันแล้วหรือยัง"""
    try:
        from django.db.migrations.recorder import MigrationRecorder
        migrations = MigrationRecorder.Migration.objects.filter(app='ICANDEP')
        category_migration = migrations.filter(name__contains='category').exists()
        if category_migration:
            print("✓ Migration สำหรับ Category รันแล้ว")
            return True
        else:
            print("✗ Migration สำหรับ Category ยังไม่ได้รัน")
            return False
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาดในการตรวจสอบ migration: {e}")
        return False

def main():
    print("=" * 50)
    print("ตรวจสอบการตั้งค่าระบบ")
    print("=" * 50)
    
    # ตรวจสอบ database
    has_category_table = check_database()
    
    # ตรวจสอบ migrations
    has_migration = check_migrations()
    
    print("\n" + "=" * 50)
    if not has_category_table or not has_migration:
        print("⚠️  ต้องรัน migrations!")
        print("\nคำแนะนำ:")
        print("1. รันคำสั่ง: python manage.py migrate")
        print("2. รันคำสั่ง: python manage.py create_categories")
        print("3. รีสตาร์ทเซิร์ฟเวอร์")
    else:
        print("✓ ระบบพร้อมใช้งาน")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
