# 🚀 คู่มือ Deploy บน Vercel

## ปัญหา: "attempt to write a readonly database"

ปัญหานี้เกิดจาก **SQLite ไม่สามารถเขียนไฟล์ได้บน Vercel** เพราะ Vercel เป็น serverless platform ที่ file system เป็น read-only

## ✅ วิธีแก้ไข: ใช้ PostgreSQL

### ขั้นตอนที่ 1: สร้าง Vercel Postgres Database

1. เข้าไปที่ [Vercel Dashboard](https://vercel.com/dashboard)
2. เลือกโปรเจคของคุณ
3. ไปที่แท็บ **Storage**
4. คลิก **Create Database** → เลือก **Postgres**
5. เลือกแผนที่ต้องการ (Hobby plan ฟรี)
6. รอให้สร้างเสร็จ

### ขั้นตอนที่ 2: เชื่อมต่อ Database กับโปรเจค

1. ในหน้า Storage → Postgres database ของคุณ
2. คลิก **.env.local** tab
3. คัดลอก `POSTGRES_URL` (จะมีรูปแบบประมาณ `postgres://...`)
4. ไปที่โปรเจค → **Settings** → **Environment Variables**
5. เพิ่ม environment variable:
   - **Key:** `POSTGRES_URL`
   - **Value:** คัดลอกจาก `.env.local` ที่ได้
   - **Environment:** Production, Preview, Development (เลือกทั้งหมด)

### ขั้นตอนที่ 3: เพิ่ม Environment Variables อื่นๆ

ใน **Settings** → **Environment Variables** เพิ่ม:

1. **SECRET_KEY**
   - Key: `SECRET_KEY`
   - Value: สร้างใหม่ด้วยคำสั่ง `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - Environment: Production, Preview, Development

2. **DEBUG**
   - Key: `DEBUG`
   - Value: `False` (สำหรับ production)
   - Environment: Production

### ขั้นตอนที่ 4: รัน Migrations บน Vercel

หลังจาก deploy แล้ว คุณต้องรัน migrations:

**วิธีที่ 1: ใช้ Vercel CLI**
```bash
vercel env pull .env.local
python manage.py migrate
```

**วิธีที่ 2: ใช้ Vercel Dashboard**
1. ไปที่โปรเจค → **Deployments**
2. คลิกที่ deployment ล่าสุด
3. ไปที่ **Functions** tab
4. คลิกที่ function → **Runtime Logs**
5. หรือใช้ Vercel CLI: `vercel --prod`

**วิธีที่ 3: สร้าง Management Command (แนะนำ)**
สร้างไฟล์ `api/migrate.py`:
```python
from django.core.management import execute_from_command_line
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workapp.settings')
    execute_from_command_line(['manage.py', 'migrate'])
```

แล้วเพิ่มใน `vercel.json`:
```json
{
  "routes": [
    {
      "src": "/api/migrate",
      "dest": "api/migrate.py"
    }
  ]
}
```

### ขั้นตอนที่ 5: สร้างหมวดหมู่เริ่มต้น

หลังจาก migrations แล้ว ให้สร้างหมวดหมู่เริ่มต้น:

1. เข้าไปที่ URL: `https://your-app.vercel.app/app/categories/`
2. ระบบจะสร้างหมวดหมู่ให้อัตโนมัติ (ถ้ายังไม่มี)
3. หรือใช้ Django shell บน Vercel

## 📝 หมายเหตุสำคัญ

1. **SQLite ใช้ได้แค่ local development** - บน Vercel ต้องใช้ PostgreSQL
2. **Environment Variables** - ต้องตั้งค่าให้ครบก่อน deploy
3. **Migrations** - ต้องรัน migrations หลังจาก deploy ครั้งแรก
4. **Static Files** - ใช้ WhiteNoise สำหรับ serve static files

## 🔧 Troubleshooting

### ถ้ายังมี error "readonly database"
- ตรวจสอบว่าเพิ่ม `POSTGRES_URL` ใน Environment Variables แล้วหรือยัง
- ตรวจสอบว่า database connection string ถูกต้องหรือไม่
- ลอง redeploy ใหม่

### ถ้า migrations ไม่ทำงาน
- ตรวจสอบว่า database มีอยู่จริงใน Vercel Storage
- ลองรัน migrations ผ่าน Vercel CLI
- ตรวจสอบ logs ใน Vercel Dashboard

### ถ้า static files ไม่แสดง
- ตรวจสอบว่า `collectstatic` รันแล้วหรือยัง
- ตรวจสอบว่า WhiteNoise middleware ถูกเพิ่มแล้ว
- ตรวจสอบ `STATIC_ROOT` และ `STATIC_URL` ใน settings.py

## 🎯 สรุป

1. ✅ สร้าง Vercel Postgres Database
2. ✅ เพิ่ม `POSTGRES_URL` ใน Environment Variables
3. ✅ เพิ่ม `SECRET_KEY` และ `DEBUG` ใน Environment Variables
4. ✅ Deploy ใหม่
5. ✅ รัน migrations
6. ✅ สร้างหมวดหมู่เริ่มต้น

หลังจากทำตามขั้นตอนนี้แล้ว ระบบจะสามารถลงทะเบียนและใช้งานได้ปกติบน Vercel! 🎉
