import sqlite3
import os

# 创建样本数据库（脱敏，每表100条）
src = 'data/qinlin_local.db'
dst = 'data/qinlin_local_sample.db'

if os.path.exists(dst):
    os.remove(dst)

conn_s = sqlite3.connect(src)
conn_d = sqlite3.connect(dst)
cursor_s = conn_s.cursor()
cursor_d = conn_d.cursor()

# 获取所有表（排除系统表）
cursor_s.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [r[0] for r in cursor_s.fetchall()]
print(f'源数据库共 {len(tables)} 张表（已排除系统表）')

for table in tables:
    # 获取表结构
    cursor_s.execute(f'PRAGMA table_info("{table}")')
    columns = [c[1] for c in cursor_s.fetchall()]

    # 获取前100条
    cursor_s.execute(f'SELECT * FROM "{table}" LIMIT 100')
    rows = cursor_s.fetchall()

    # 创建表结构
    cols_def = ', '.join([f'"{c}" TEXT' for c in columns])
    cursor_d.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols_def})')

    # 插入数据（脱敏处理）
    qmarks = ', '.join(['?'] * len(columns))
    for row in rows:
        row_list = list(row)
        for i, c in enumerate(columns):
            val = row_list[i]
            if val and ('手机' in c or '电话' in c or 'mobile' in c.lower()):
                row_list[i] = None
            if val and ('联系人' in c or 'contact' in c.lower()):
                row_list[i] = '测试联系人'
        cursor_d.execute(f'INSERT INTO "{table}" VALUES ({qmarks})', row_list)

    conn_d.commit()
    print(f'  ✅ {table}: {len(rows)} 条样本数据（已脱敏）')

conn_d.close()
conn_s.close()
print()
print('样本数据库创建成功：data/qinlin_local_sample.db')
