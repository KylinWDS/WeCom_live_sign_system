import random

# 生成1000个唯一的IP记录
values = []
used_ips = set()  # 用于跟踪已生成的IP

for i in range(1, 1001):
    # 生成随机IP，确保不在139.210网段且不重复
    while True:
        first = random.randint(1, 254)
        second = random.randint(0, 255)
        # 严格避免139.210网段
        if first == 139 and second == 210:
            continue
            
        third = random.randint(0, 255)
        fourth = random.randint(1, 254)
        ip = f"{first}.{second}.{third}.{fourth}"
        
        # 检查IP是否已存在
        if ip not in used_ips:
            used_ips.add(ip)
            break
    
    values.append(f"('{ip}', 'infer', '2025-03-22 13:20:28', '2025-03-22 21:22:14.556019', 1)")

# 生成完整的SQL语句
sql = 'INSERT INTO "main"."ip_records" ("ip", "source", "created_at", "updated_at", "is_active") VALUES\n' + ',\n'.join(values) + ';'

print(sql) 