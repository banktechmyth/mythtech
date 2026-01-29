from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Transaction, Category
from .forms import TransactionForm, CategoryForm

def login_view(request):
    """หน้าเข้าสู่ระบบ"""
    if request.user.is_authenticated:
        return redirect('ICANDEP:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'ยินดีต้อนรับ {username}!')
                return redirect('ICANDEP:dashboard')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        form = AuthenticationForm()
    
    return render(request, 'ICANDEP/login.html', {'form': form})

def register_view(request):
    """หน้าลงทะเบียน"""
    if request.user.is_authenticated:
        return redirect('ICANDEP:dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ลงทะเบียนสำเร็จ! ยินดีต้อนรับสู่ MoneyTracker')
            return redirect('ICANDEP:dashboard')
        else:
            messages.error(request, 'กรุณาแก้ไขข้อมูลที่ผิดพลาด')
    else:
        form = UserCreationForm()
    
    return render(request, 'ICANDEP/register.html', {'form': form})

def logout_view(request):
    """ออกจากระบบ"""
    logout(request)
    messages.success(request, 'ออกจากระบบสำเร็จ')
    return redirect('ICANDEP:login')

@login_required
def dashboard(request):
    """หน้าแดชบอร์ดหลัก"""
    try:
        # ข้อมูลสรุป
        today = timezone.now().date()
        this_month = today.replace(day=1)
        next_month = (this_month + timedelta(days=32)).replace(day=1)
        
        # รายรับรายจ่ายเดือนนี้ (เฉพาะผู้ใช้ปัจจุบัน)
        monthly_income = Transaction.objects.filter(
            user=request.user,
            transaction_type='income',
            date__gte=this_month,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__gte=this_month,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_balance = monthly_income - monthly_expense
        
        # รายการล่าสุด (เฉพาะผู้ใช้ปัจจุบัน)
        recent_transactions = Transaction.objects.filter(user=request.user).select_related('category')[:10]
        
        # สถิติตามหมวดหมู่ (เฉพาะผู้ใช้ปัจจุบัน) - รองรับกรณีที่ยังไม่มี Category
        try:
            category_stats = Transaction.objects.filter(
                user=request.user,
                date__gte=this_month,
                date__lt=next_month,
                category__isnull=False
            ).select_related('category').values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')[:5]
        except Exception:
            # หากเกิด error (เช่น ตาราง Category ยังไม่มี) ให้ใช้ list ว่าง
            category_stats = []
        
        context = {
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
            'monthly_balance': monthly_balance,
            'recent_transactions': recent_transactions,
            'category_stats': category_stats,
            'current_month': this_month.strftime('%B %Y'),
        }
        
        return render(request, 'ICANDEP/dashboard.html', context)
    except Exception as e:
        # แสดง error message ที่เป็นมิตรกับผู้ใช้
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}. กรุณาตรวจสอบว่าได้รัน migrations แล้วหรือยัง')
        return render(request, 'ICANDEP/dashboard.html', {
            'monthly_income': 0,
            'monthly_expense': 0,
            'monthly_balance': 0,
            'recent_transactions': [],
            'category_stats': [],
            'current_month': today.strftime('%B %Y'),
        })

@login_required
def transaction_list(request):
    """หน้ารายการธุรกรรม"""
    from .models import Category
    
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    
    # ตัวกรอง
    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    context = {
        'transactions': transactions,
        'transaction_types': Transaction.TRANSACTION_TYPES,
        'categories': Category.objects.filter(is_active=True).order_by('transaction_type', 'name'),
    }
    
    return render(request, 'ICANDEP/transaction_list.html', context)

@login_required
def add_transaction(request):
    """หน้าเพิ่มรายการธุรกรรม"""
    from .models import Category
    
    # รับ transaction_type จาก query string
    initial_type = request.GET.get('type', '')
    
    # ดึงหมวดหมู่ทั้งหมดก่อน (เพื่อให้แน่ใจว่ามีข้อมูล)
    try:
        categories = Category.objects.filter(is_active=True).order_by('transaction_type', 'name')
        if not categories.exists():
            # ถ้ายังไม่มีหมวดหมู่ ให้สร้างหมวดหมู่เริ่มต้น
            messages.warning(request, 'ยังไม่มีหมวดหมู่ในระบบ กำลังสร้างหมวดหมู่เริ่มต้น...')
            from django.core.management import call_command
            call_command('create_categories')
            categories = Category.objects.filter(is_active=True).order_by('transaction_type', 'name')
    except Exception as e:
        # ถ้าเกิด error (เช่น ตาราง Category ยังไม่มี) ให้ใช้ list ว่าง
        categories = []
        messages.error(request, f'เกิดข้อผิดพลาดในการโหลดหมวดหมู่: {str(e)}. กรุณาตรวจสอบว่าได้รัน migrations แล้วหรือยัง')
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'เพิ่มรายการธุรกรรมสำเร็จ!')
            return redirect('ICANDEP:transaction_list')
    else:
        form = TransactionForm(initial={'transaction_type': initial_type} if initial_type else {})
    
    context = {
        'form': form,
        'title': 'เพิ่มรายการธุรกรรม',
        'categories': categories,
    }
    
    return render(request, 'ICANDEP/transaction_form.html', context)

@login_required
def edit_transaction(request, pk):
    """หน้าแก้ไขรายการธุรกรรม"""
    from .models import Category
    
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    # ดึงหมวดหมู่ทั้งหมดก่อน
    try:
        categories = Category.objects.filter(is_active=True).order_by('transaction_type', 'name')
        if not categories.exists():
            from django.core.management import call_command
            call_command('create_categories')
            categories = Category.objects.filter(is_active=True).order_by('transaction_type', 'name')
    except Exception as e:
        categories = []
        messages.error(request, f'เกิดข้อผิดพลาดในการโหลดหมวดหมู่: {str(e)}')
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขรายการธุรกรรมสำเร็จ!')
            return redirect('ICANDEP:transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    
    context = {
        'form': form,
        'transaction': transaction,
        'title': 'แก้ไขรายการธุรกรรม',
        'categories': categories,
    }
    
    return render(request, 'ICANDEP/transaction_form.html', context)

@login_required
def delete_transaction(request, pk):
    """ลบรายการธุรกรรม"""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'ลบรายการธุรกรรมสำเร็จ!')
        return redirect('ICANDEP:transaction_list')
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'ICANDEP/delete_transaction.html', context)


@login_required
def manage_categories(request):
    """
    หน้าจัดการหมวดหมู่ (ไม่ต้องเข้า admin)
    - แสดงรายการหมวดหมู่ทั้งหมดของระบบ
    - เพิ่มหมวดหมู่ใหม่ได้จากฟอร์มด้านขวา
    """
    categories = Category.objects.all().order_by('transaction_type', 'name')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มหมวดหมู่สำเร็จ!')
            return redirect('ICANDEP:manage_categories')
    else:
        form = CategoryForm()

    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'ICANDEP/category_manage.html', context)

@login_required
def delete_category(request, pk):
    """ลบหมวดหมู่"""
    category = get_object_or_404(Category, pk=pk)
    
    # ตรวจสอบว่ามี transaction ใช้หมวดหมู่นี้อยู่หรือไม่
    transactions_count = Transaction.objects.filter(category=category).count()
    
    if request.method == 'POST':
        if transactions_count > 0:
            messages.error(request, f'ไม่สามารถลบหมวดหมู่ "{category.name}" ได้ เพราะมีรายการธุรกรรมที่ใช้หมวดหมู่นี้อยู่ {transactions_count} รายการ\n\nกรุณาลบหรือแก้ไขรายการธุรกรรมเหล่านั้นก่อน')
            return redirect('ICANDEP:manage_categories')
        
        category.delete()
        messages.success(request, f'ลบหมวดหมู่ "{category.name}" สำเร็จ!')
        return redirect('ICANDEP:manage_categories')
    
    context = {
        'category': category,
        'transactions_count': transactions_count,
    }
    
    return render(request, 'ICANDEP/delete_category.html', context)

@login_required
def reports(request):
    """
    หน้ารายงานภาพรวม และสรุปกำไร/ขาดทุน
    - กราฟภาพรวม 6 เดือนล่าสุด (เหมือนเดิม)
    - เลือกช่วงวันที่เองได้ (รายวัน / รายเดือน / รายปี / ช่วงเวลาเอง)
    - แสดงยอดรวมรายรับ, รายจ่าย, กำไร/ขาดทุน สำหรับช่วงที่เลือก
    - แสดงตารางรายละเอียดธุรกรรม เพื่อนำไปปริ้น
    """
    today = timezone.now().date()

    # ====== กราฟภาพรวม 6 เดือนล่าสุด (เหมือนเดิม) ======
    months = []
    income_data = []
    expense_data = []
    
    for i in range(6):
        date = today - timedelta(days=30 * i)
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        income = Transaction.objects.filter(
            user=request.user,
            transaction_type='income',
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        months.append(month_start.strftime('%b %Y'))
        income_data.append(float(income))
        expense_data.append(float(expense))

    # ====== ตัวกรองช่วงเวลา ======
    # presets: today, this_month, this_year หรือช่วงเวลา custom
    preset = request.GET.get('preset', 'this_month')
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')

    # คำนวณค่าเริ่มต้นของช่วงเวลา
    if preset == 'today':
        period_start = today
        period_end = today
    elif preset == 'this_year':
        period_start = today.replace(month=1, day=1)
        period_end = today
    else:  # this_month หรืออื่นๆ
        period_start = today.replace(day=1)
        period_end = today

    # ถ้าผู้ใช้กรอกวันที่เอง ให้ override ค่า default
    if date_from_str:
        try:
            period_start = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to_str:
        try:
            period_end = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # ให้ period_end รวมทั้งวัน
    period_qs_end = period_end

    # queryset หลักสำหรับช่วงเวลาที่เลือก
    base_qs = Transaction.objects.filter(
        user=request.user,
        date__gte=period_start,
        date__lte=period_qs_end
    ).select_related('category').order_by('date', 'created_at')

    # ====== สรุปยอดสำหรับช่วงเวลาที่เลือก ======
    range_income = base_qs.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
    range_expense = base_qs.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    range_balance = range_income - range_expense

    # ====== สถิติหมวดหมู่เฉพาะในช่วงที่เลือก (รายจ่าย) ======
    category_expenses = base_qs.filter(
        transaction_type='expense',
        category__isnull=False
    ).values('category__id', 'category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # ====== สรุปข้อมูลทั้งหมดตั้งแต่เริ่มใช้ระบบ (เดิม) ======
    total_income = Transaction.objects.filter(
        user=request.user,
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expense = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    balance = total_income - total_expense
    ratio = (total_expense / total_income * 100) if total_income > 0 else 0

    context = {
        # กราฟภาพรวม
        'months': months[::-1],
        'income_data': income_data[::-1],
        'expense_data': expense_data[::-1],

        # ฟิลเตอร์ช่วงเวลา
        'preset': preset,
        'period_start': period_start,
        'period_end': period_end,

        # ตารางและสรุปสำหรับช่วงเวลาที่เลือก
        'range_transactions': base_qs,
        'range_income': range_income,
        'range_expense': range_expense,
        'range_balance': range_balance,

        # สถิติรายจ่ายตามหมวดหมู่ (ช่วงเวลาที่เลือก)
        'category_expenses': category_expenses,

        # สรุปภาพรวมทั้งระบบ (เดิม)
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'ratio': ratio,
    }
    
    return render(request, 'ICANDEP/reports.html', context)