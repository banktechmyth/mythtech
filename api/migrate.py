"""
Vercel Serverless Function สำหรับรัน migrations
เรียกใช้ผ่าน: https://your-app.vercel.app/api/migrate
"""
import os
import sys
from pathlib import Path

# เพิ่ม project root เข้า Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# ตั้งค่า Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workapp.settings')

import django
django.setup()

from django.core.management import call_command
from django.http import JsonResponse

def handler(request):
    """Handler สำหรับ Vercel serverless function"""
    try:
        # รัน migrations
        call_command('migrate', verbosity=2, interactive=False)
        
        # สร้างหมวดหมู่เริ่มต้น (ถ้ายังไม่มี)
        try:
            call_command('create_categories')
        except Exception:
            pass  # ถ้ามีอยู่แล้วก็ไม่เป็นไร
        
        return JsonResponse({
            'status': 'success',
            'message': 'Migrations completed successfully'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
