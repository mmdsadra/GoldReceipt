# GoldReceipt

اپ دسکتاپ ساده برای محاسبه و چاپ فاکتور فروش طلا (Windows 11) با Python و PySide6.

## اجرا در ویندوز

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## خروجی EXE

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name GoldReceipt main.py
```

فایل خروجی در `dist/GoldReceipt.exe` قرار می‌گیرد.

## محاسبات نسخه فعلی

- ارزش طلای خام = وزن خالص × قیمت هر گرم
- اجرت = ارزش طلای خام × درصد اجرت
- سود = (ارزش طلا + اجرت) × درصد سود
- مالیات = (اجرت + سود) × درصد مالیات
- مبلغ نهایی = طلا + اجرت + سود + مالیات + هزینه/تخفیف متفرقه

**توجه:** فرمول و پایه مالیات باید با مقررات جاری و روش حسابداری فروشگاه تطبیق داده شود. تمام مبالغ ورودی پولی در این نسخه ریال هستند. محاسبات با Decimal انجام می‌شوند.
