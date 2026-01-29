from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    """หมวดหมู่สำหรับรายรับและรายจ่าย"""
    TRANSACTION_TYPES = [
        ('income', 'รายรับ'),
        ('expense', 'รายจ่าย'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="ประเภท")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="ไอคอน")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    
    class Meta:
        ordering = ['transaction_type', 'name']
        verbose_name = "หมวดหมู่"
        verbose_name_plural = "หมวดหมู่"
        unique_together = ['name', 'transaction_type']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.name}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'รายรับ'),
        ('expense', 'รายจ่าย'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ใช้")
    title = models.CharField(max_length=200, verbose_name="หัวข้อ")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="จำนวนเงิน")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="ประเภท")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="หมวดหมู่", null=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    date = models.DateField(default=timezone.now, verbose_name="วันที่")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่อัปเดต")
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "รายการธุรกรรม"
        verbose_name_plural = "รายการธุรกรรม"
    
    def __str__(self):
        return f"{self.title} - {self.amount} บาท"
    
    @property
    def is_income(self):
        return self.transaction_type == 'income'
    
    @property
    def is_expense(self):
        return self.transaction_type == 'expense'
