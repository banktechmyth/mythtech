from django import forms
from .models import Transaction, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'transaction_type', 'category', 'description', 'date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ใส่หัวข้อรายการ'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_transaction_type'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'รายละเอียดเพิ่มเติม (ไม่บังคับ)'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ตั้งค่าวันที่เริ่มต้นเป็นวันนี้
        if not self.instance.pk:  # ถ้าเป็นการสร้างใหม่
            self.fields['date'].initial = forms.DateField().to_python(None)
        
        # กรองหมวดหมู่ตาม transaction_type
        try:
            transaction_type = self.data.get('transaction_type') or (self.instance.transaction_type if self.instance.pk else None)
            if transaction_type:
                self.fields['category'].queryset = Category.objects.filter(
                    transaction_type=transaction_type,
                    is_active=True
                ).order_by('name')
            else:
                self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('name')
            
            # ตั้งค่า required สำหรับ category
            self.fields['category'].required = True
            self.fields['category'].empty_label = '-- เลือกหมวดหมู่ --'
        except Exception:
            # ถ้าเกิด error (เช่น ตาราง Category ยังไม่มี) ให้ใช้ queryset ว่าง
            self.fields['category'].queryset = Category.objects.none()
            self.fields['category'].required = False
            self.fields['category'].empty_label = '-- ยังไม่มีหมวดหมู่ --'
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('จำนวนเงินต้องมากกว่า 0')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        category = cleaned_data.get('category')
        
        if transaction_type and category:
            if category.transaction_type != transaction_type:
                raise forms.ValidationError({
                    'category': 'หมวดหมู่ที่เลือกไม่ตรงกับประเภทธุรกรรม'
                })
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """ฟอร์มเพิ่ม/แก้ไขหมวดหมู่ (ให้ผู้ใช้จัดการเองในระบบ)"""

    class Meta:
        model = Category
        fields = ['name', 'transaction_type', 'description', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'เช่น วัตถุดิบอาหารทะเล',
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'รายละเอียดเพิ่มเติม (ไม่บังคับ)',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'เลือกอิโมจิหรือใส่ชื่อไอคอน (ไม่บังคับ)',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }