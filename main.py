import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QFont
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFormLayout, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QSpinBox, QGroupBox, QMessageBox, QPlainTextEdit, QComboBox)

D = Decimal
ZERO = D("0")
CENT = D("1")


def dec(widget):
    raw = widget.text().strip().replace(",", "").replace("٬", "")
    try:
        return D(raw or "0")
    except InvalidOperation:
        return ZERO


def money(value):
    return f"{value.quantize(CENT, rounding=ROUND_HALF_UP):,.0f}"


class GoldReceipt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoldReceipt | فاکتور طلا")
        self.resize(1000, 760)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        title = QLabel("GoldReceipt — محاسبه و صدور فاکتور طلا")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:700;padding:12px")
        layout.addWidget(title)

        grid = QGridLayout()
        layout.addLayout(grid)
        self.fields = {}
        specs = [
            ("seller", "نام فروشگاه", "طلافروشی"),
            ("customer", "نام مشتری", ""),
            ("phone", "تلفن مشتری", ""),
            ("item", "شرح کالا", "طلا"),
            ("weight", "وزن خالص (گرم)", "0"),
            ("gold_price", "قیمت هر گرم طلا (ریال)", "0"),
            ("wage_pct", "اجرت ساخت (%)", "0"),
            ("profit_pct", "سود فروشنده (%)", "0"),
            ("vat_pct", "مالیات (%)", "0"),
            ("other", "هزینه/تخفیف متفرقه (ریال؛ منفی هم مجاز)", "0"),
            ("description", "توضیحات", ""),
        ]
        for i, (key, label, default) in enumerate(specs):
            edit = QLineEdit(default)
            edit.setClearButtonEnabled(True)
            edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.fields[key] = edit
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(edit, i, 1)
        # Numeric defaults that are commonly changed
        self.fields["weight"].setPlaceholderText("مثلاً 2.350")
        self.fields["gold_price"].setPlaceholderText("قیمت روز هر گرم")
        self.fields["wage_pct"].setPlaceholderText("مثلاً 7")
        self.fields["profit_pct"].setPlaceholderText("مثلاً 7")
        self.fields["vat_pct"].setPlaceholderText("مثلاً 10")

        buttons = QHBoxLayout()
        layout.addLayout(buttons)
        calc = QPushButton("محاسبه و نمایش فاکتور")
        calc.setStyleSheet("font-size:16px;padding:10px;background:#176b55;color:white")
        calc.clicked.connect(self.calculate)
        buttons.addWidget(calc)
        preview = QPushButton("پیش‌نمایش چاپ")
        preview.clicked.connect(self.preview)
        buttons.addWidget(preview)
        print_btn = QPushButton("چاپ مستقیم…")
        print_btn.clicked.connect(self.print_invoice)
        buttons.addWidget(print_btn)
        clear = QPushButton("فاکتور جدید")
        clear.clicked.connect(self.clear)
        buttons.addWidget(clear)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.output.setPlaceholderText("خلاصه محاسبات اینجا نمایش داده می‌شود…")
        self.output.setStyleSheet("font-size:15px")
        layout.addWidget(self.output, 1)
        self.invoice_html = ""
        self.amounts = {}

        note = QLabel("مبالغ به ریال هستند. مبنای مالیات در این نسخه: اجرت + سود؛ تنظیمات را مطابق مقررات روز فروشگاه بررسی کنید.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#a45b00;padding:5px")
        layout.addWidget(note)

    def calculate(self):
        f = self.fields
        weight, price = dec(f["weight"]), dec(f["gold_price"])
        wage_pct, profit_pct, vat_pct = dec(f["wage_pct"]), dec(f["profit_pct"]), dec(f["vat_pct"])
        other = dec(f["other"])
        if weight <= 0 or price <= 0:
            QMessageBox.warning(self, "ورودی نامعتبر", "وزن و قیمت هر گرم باید بزرگ‌تر از صفر باشند.")
            return
        gold = weight * price
        wage = gold * wage_pct / D("100")
        profit = (gold + wage) * profit_pct / D("100")
        vat_base = wage + profit
        vat = vat_base * vat_pct / D("100")
        total = gold + wage + profit + vat + other
        self.amounts = dict(weight=weight, price=price, gold=gold, wage=wage, profit=profit,
                            vat_base=vat_base, vat=vat, other=other, total=total)
        lines = [
            f"ارزش طلای خام: {money(gold)} ریال",
            f"اجرت ساخت ({wage_pct}%): {money(wage)} ریال",
            f"سود فروشنده ({profit_pct}%): {money(profit)} ریال",
            f"مبنای مالیات: {money(vat_base)} ریال",
            f"مالیات ({vat_pct}%): {money(vat)} ریال",
            f"هزینه/تخفیف متفرقه: {money(other)} ریال",
            "─" * 45,
            f"مبلغ نهایی: {money(total)} ریال",
        ]
        self.output.setPlainText("\n".join(lines))
        self.invoice_html = self.make_html()
        return True

    def make_html(self):
        f, a = self.fields, self.amounts
        def val(k): return f[k].text().strip() or "—"
        rows = [
            ("وزن خالص", f"{a['weight']} گرم"),
            ("قیمت هر گرم", f"{money(a['price'])} ریال"),
            ("ارزش طلای خام", f"{money(a['gold'])} ریال"),
            ("اجرت ساخت", f"{money(a['wage'])} ریال"),
            ("سود فروشنده", f"{money(a['profit'])} ریال"),
            ("مبنای مالیات", f"{money(a['vat_base'])} ریال"),
            ("مالیات", f"{money(a['vat'])} ریال"),
            ("متفرقه", f"{money(a['other'])} ریال"),
        ]
        trs = "".join(f"<tr><td>{x}</td><th>{y}</th></tr>" for x,y in rows)
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
        body{{font-family: sans-serif;direction:rtl;color:#111;font-size:13pt}}
        h1,h2,p{{text-align:center}} h1{{font-size:22pt}} table{{width:100%;border-collapse:collapse;margin-top:20px}}
        td,th{{border:1px solid #777;padding:9px}} .total{{font-size:18pt;background:#eee}}
        .muted{{color:#555;font-size:10pt}} </style></head><body>
        <h1>فاکتور فروش طلا</h1><h2>{val('seller')}</h2>
        <p>شماره/تاریخ: — / {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p>مشتری: {val('customer')} &nbsp; | &nbsp; تلفن: {val('phone')}</p>
        <p>شرح کالا: {val('item')}</p><table>{trs}
        <tr class="total"><td><b>مبلغ قابل پرداخت</b></td><th><b>{money(a['total'])} ریال</b></th></tr></table>
        <p>توضیحات: {val('description')}</p><br><p>امضای فروشنده: ______________ &nbsp;&nbsp; امضای مشتری: ______________</p>
        <p class="muted">این فاکتور بر اساس اطلاعات واردشده صادر شده است.</p></body></html>"""

    def document(self):
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Tahoma", 11))
        doc.setHtml(self.invoice_html)
        return doc

    def preview(self):
        if not self.amounts and not self.calculate(): return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        dlg = QPrintPreviewDialog(printer, self)
        dlg.paintRequested.connect(self.document().print)
        dlg.exec()

    def print_invoice(self):
        if not self.amounts and not self.calculate(): return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            self.document().print(printer)

    def clear(self):
        for key in ("customer","phone","weight","gold_price","description"):
            self.fields[key].clear()
        self.output.clear()
        self.amounts = {}
        self.invoice_html = ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyle("Fusion")
    window = GoldReceipt()
    window.show()
    sys.exit(app.exec())
