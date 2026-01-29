from django.core.management.base import BaseCommand
from ICANDEP.models import Category

class Command(BaseCommand):
    help = 'สร้างหมวดหมู่เริ่มต้นสำหรับร้านอาหาร'

    def handle(self, *args, **options):
        # หมวดหมู่รายรับสำหรับร้านอาหาร
        income_categories = [
            {'name': 'ขายอาหาร', 'icon': 'bi-egg-fried'},
            {'name': 'ขายเครื่องดื่ม', 'icon': 'bi-cup'},
            {'name': 'ขายของหวาน', 'icon': 'bi-cake'},
            {'name': 'ขายของทานเล่น', 'icon': 'bi-bag'},
            {'name': 'รับจ้างจัดเลี้ยง', 'icon': 'bi-calendar-event'},
            {'name': 'รายรับอื่นๆ', 'icon': 'bi-wallet'},
        ]
        
        # หมวดหมู่รายจ่ายสำหรับร้านอาหาร
        expense_categories = [
            {'name': 'วัตถุดิบอาหาร', 'icon': 'bi-basket'},
            {'name': 'วัตถุดิบเครื่องดื่ม', 'icon': 'bi-cup-straw'},
            {'name': 'ค่าแรงพนักงาน', 'icon': 'bi-people'},
            {'name': 'ค่าเช่าที่', 'icon': 'bi-building'},
            {'name': 'ค่าน้ำ-ค่าไฟ', 'icon': 'bi-lightning'},
            {'name': 'ค่าแก๊ส', 'icon': 'bi-fire'},
            {'name': 'อุปกรณ์ครัว', 'icon': 'bi-tools'},
            {'name': 'ภาชนะบรรจุ', 'icon': 'bi-box'},
            {'name': 'ค่าโฆษณา', 'icon': 'bi-megaphone'},
            {'name': 'ค่าซ่อมบำรุง', 'icon': 'bi-wrench'},
            {'name': 'ค่าขนส่ง', 'icon': 'bi-truck'},
            {'name': 'ภาษี', 'icon': 'bi-receipt'},
            {'name': 'รายจ่ายอื่นๆ', 'icon': 'bi-cash-stack'},
        ]
        
        created_count = 0
        
        # สร้างหมวดหมู่รายรับ
        for cat_data in income_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                transaction_type='income',
                defaults={
                    'icon': cat_data.get('icon', ''),
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ สร้างหมวดหมู่รายรับ: {cat_data["name"]}')
                )
        
        # สร้างหมวดหมู่รายจ่าย
        for cat_data in expense_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                transaction_type='expense',
                defaults={
                    'icon': cat_data.get('icon', ''),
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ สร้างหมวดหมู่รายจ่าย: {cat_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ สร้างหมวดหมู่ทั้งหมด {created_count} รายการ')
        )
