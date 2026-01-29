from django.contrib import admin
from .models import Transaction, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'transaction_type', 'is_active', 'created_at']
    list_filter = ['transaction_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    list_per_page = 20

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'amount', 'transaction_type', 'category', 'date', 'created_at']
    list_filter = ['user', 'transaction_type', 'category', 'date']
    search_fields = ['title', 'description', 'user__username']
    date_hierarchy = 'date'
    list_per_page = 20
    
    fieldsets = (
        ('ข้อมูลผู้ใช้', {
            'fields': ('user',)
        }),
        ('ข้อมูลพื้นฐาน', {
            'fields': ('title', 'amount', 'transaction_type', 'category')
        }),
        ('รายละเอียดเพิ่มเติม', {
            'fields': ('description', 'date'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')
