"""
سكربت بسيط لتنظيف المسافات المخفية (Non-Breaking Space U+00A0)
من أي ملف بايثون، وحل مشكلة:
SyntaxError: invalid non-printable character U+00A0

طريقة الاستخدام:
    python3 fix_unicode.py hassan.py

يسوي نسخة احتياطية باسم hassan.py.bak قبل التعديل،
وبعدين يحفظ النسخة النظيفة بنفس اسم الملف الأصلي.
"""

import sys
import shutil


def clean_file(path: str) -> None:
    backup_path = path + ".bak"
    shutil.copyfile(path, backup_path)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    cleaned = (
        content
        .replace("\u00a0", " ")   # مسافة غير قابلة للكسر
        .replace("\u200b", "")    # مسافة بعرض صفر
        .replace("\ufeff", "")    # BOM
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print(f"تم تنظيف الملف: {path}")
    print(f"نسخة احتياطية من الأصل محفوظة بـ: {backup_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("الاستخدام: python3 fix_unicode.py اسم_الملف.py")
        sys.exit(1)

    clean_file(sys.argv[1])
