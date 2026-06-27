import sqlite3, os, sys

def check_db(path, label):
    if not os.path.exists(path):
        print(f"--- {label}: FILE NOT FOUND ---")
        return {}
    size = os.path.getsize(path)
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        result = {"size": size, "tables": len(tables), "rows": {}}
        print(f"\n--- {label} ({path}) ---")
        print(f"  Size: {size} bytes")
        print(f"  Tables: {len(tables)}")
        for t in tables:
            tname = t[0]
            cnt = cur.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
            result["rows"][tname] = cnt
            print(f"    {tname}: {cnt}")
        conn.close()
        return result
    except Exception as e:
        print(f"--- {label}: ERROR - {e} ---")
        return {"size": size, "tables": 0, "rows": {}, "error": str(e)}

# Current db
current = check_db("db.sqlite3", "CURRENT DB")

# Check several backup sizes
backup_dir = "backups"
important = ['auth_user','products_product','products_category','products_productvariant',
             'orders_order','orders_orderitem','accounts_customeraddress',
             'promotions_voucher','wishlist','payments_payment',
             'shipping_shippingconfig','carts_cart','carts_cartitem',
             'products_brand','products_productimage','products_fragrancenote',
             'products_fragrancefamily','regions_district','regions_province',
             'promotions_uservoucher',
             'account_emailaddress','socialaccount_socialapp',
             'account_emailconfirmation','django_session','auth_permission',
             'auth_group','django_content_type','django_migrations',
             'django_admin_log','orders_orderstatushistory','payments_paymentstatushistory',
             'account_account','socialaccount_socialtoken']

# Sample backups - all 1961984 size (latest)
targets = [
    "db_backup_20260627_201218.sqlite3",
    "db_backup_20260627_201203.sqlite3",
    "db_backup_20260627_201145.sqlite3",
    "db_backup_20260627_201100.sqlite3",
    "db_backup_20260627_200605.sqlite3",
    "db_backup_20260627_200600.sqlite3",
    "db_backup_20260627_200533.sqlite3",
    "db_backup_20260627_191426.sqlite3",
    "db_backup_20260627_191413.sqlite3",
    "db_backup_20260627_185438.sqlite3",
    "db_backup_20260627_185422.sqlite3",
    "db_backup_20260627_185402.sqlite3",
    "db_backup_20260627_185133.sqlite3",
]

# Also check some medium sized ones for comparison
medium_targets = [
    "db_backup_20260627_182607.sqlite3",  # 1572864
    "db_backup_20260627_181804.sqlite3",  # 1572864
    "db_backup_20260627_171229.sqlite3",  # 1548288
    "db_backup_20260627_170244.sqlite3",  # 1548288
    "db_backup_20260627_032813.sqlite3",  # 1441792
    "db_backup_20260627_014346.sqlite3",  # 1441792
    "db_backup_20260626_210029.sqlite3",  # 1441792
    "db_backup_20260626_185248.sqlite3",  # 1433600
    "db_backup_20260626_184105.sqlite3",  # 1159168
    "db_backup_20260626_182359.sqlite3",  # 741376
    "db_backup_20260626_024244.sqlite3",  # 1441792 (early large)
]

for f in targets:
    check_db(os.path.join(backup_dir, f), f)

print("\n\n===== MEDIUM BACKUPS =====")
for f in medium_targets:
    check_db(os.path.join(backup_dir, f), f)

print("\n\n===== SUMMARY =====")
print("\nCurrent db.sqlite3 tables:", current.get("tables"))
r = current.get("rows", {})
for t in sorted(r.keys()):
    print(f"  {t}: {r[t]}")
