import requests
import re
import json
from urllib.parse import urlparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_ip_from_service(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        domain = urlparse(url).netloc
        print(f'测试服务: {domain}')
        print(f'状态码: {response.status_code}')
        if response.status_code == 200:
            content = response.text
            print(f'响应内容: {content[:200]}...' if len(content) > 200 else f'响应内容: {content}')
            
            # 尝试提取IP地址
            if 'pconline' in url:
                # 太平洋电脑网的特殊处理
                match = re.search(r'\"ip\":\"([^\"]+)\"', content)
                if match:
                    return match.group(1)
            elif 'ipip.net' in url:
                # ipip.net的特殊处理
                match = re.search(r'当前 IP：([\d\.]+)', content)
                if match:
                    return match.group(1)
            elif 'baidubce.com' in url or 'baidu.com' in url:
                # 百度API的特殊处理
                try:
                    data = json.loads(content)
                    # 直接从JSON中提取IP
                    if 'ip' in data:
                        return data.get('ip')
                    return data.get('data', {}).get('ip', '无法解析')
                except Exception as e:
                    return f'解析JSON失败: {str(e)}'
            elif 'useragentinfo' in url:
                # useragentinfo的特殊处理
                try:
                    data = json.loads(content)
                    return data.get('ip', '无法解析')
                except Exception as e:
                    return f'解析JSON失败: {str(e)}'
            elif 'ipify.org' in url:
                # ipify的特殊处理
                try:
                    data = json.loads(content)
                    return data.get('ip', '无法解析')
                except Exception as e:
                    return f'解析JSON失败: {str(e)}'
            elif 'httpbin.org' in url:
                # httpbin的特殊处理
                try:
                    data = json.loads(content)
                    return data.get('origin', '无法解析')
                except Exception as e:
                    return f'解析JSON失败: {str(e)}'
            
            # 通用IP提取尝试
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            match = re.search(ip_pattern, content)
            if match:
                return match.group(0)
            
            return '无法识别IP格式'
        else:
            return f'请求失败: {response.status_code}'
    except Exception as e:
        return f'发生错误: {str(e)}'

def analyze_ip_results(results):
    """分析不同服务返回的IP结果"""
    # 统计各个IP出现的次数
    ip_counts = {}
    valid_ips = []
    
    for service, ip in results.items():
        # 跳过解析失败或错误的情况
        if any(msg in ip for msg in ['无法解析', '发生错误', '请求失败', '解析JSON失败']):
            continue
            
        valid_ips.append(ip)
        ip_counts[ip] = ip_counts.get(ip, 0) + 1
    
    # 分析结果
    print("\nIP分析结果:")
    print("=" * 50)
    if not valid_ips:
        print("所有服务都未能成功返回有效IP")
        return
    
    # 找出出现次数最多的IP
    most_common_ip = max(ip_counts.items(), key=lambda x: x[1])
    print(f"最常见的IP: {most_common_ip[0]} (出现 {most_common_ip[1]} 次)")
    
    # 不同IP之间的分析
    if len(ip_counts) > 1:
        print("\n检测到多个不同的IP地址:")
        for ip, count in ip_counts.items():
            services = [service for service, result in results.items() if result == ip]
            print(f"IP: {ip} - 出现次数: {count} - 来源服务: {', '.join([urlparse(s).netloc for s in services])}")
        
        print("\n可能的原因:")
        print("1. 您的网络可能使用了多个出口IP (NAT池)")
        print("2. 部分服务可能返回了中间代理IP而非真实出口IP")
        print("3. 您可能正在使用VPN或代理服务")
        print("4. 某些服务可能存在延迟，返回了之前的连接IP")
        
        # 检查IP前两段是否相同(是否属于同一网段)
        ip_prefixes = {}
        for ip in ip_counts.keys():
            prefix = '.'.join(ip.split('.')[:2])
            ip_prefixes[prefix] = ip_prefixes.get(prefix, 0) + 1
        
        if len(ip_prefixes) == 1:
            prefix = list(ip_prefixes.keys())[0]
            print(f"\n所有IP都属于同一网段 ({prefix}.x.x)，更可能是NAT池中的不同IP")
        else:
            print("\nIP来自不同网段，可能是不同的网络连接或代理服务")
    else:
        print("所有成功的服务都返回了相同的IP地址")
    
    # 建议
    print("\n建议:")
    if most_common_ip[1] > 1:
        print(f"使用出现频率最高的IP地址: {most_common_ip[0]}")
    else:
        print("考虑使用包含地理位置信息的服务返回的IP (如太平洋电脑网或ipip.net)")
    
    print("如果需要更可靠的IP检测，建议使用多个服务交叉验证")

def test_network_utils_method():
    """测试新实现的NetworkUtils.get_reliable_public_ip方法"""
    from src.utils.network import NetworkUtils
    
    print('\n\n测试 NetworkUtils.get_reliable_public_ip() 方法')
    print('=' * 50)
    
    try:
        ip, details = NetworkUtils.get_reliable_public_ip()
        
        print(f"返回的IP: {ip}")
        print(f"可信度: {details.get('confidence', 0):.1f}%")
        print(f"来源数量: {details.get('source_count', 0)}/{details.get('total_sources', 0)}")
        print(f"结果一致性: {'一致' if details.get('is_consistent', False) else '不一致'}")
        
        print("\n所有检测到的IP:")
        for ip, count in details.get('all_ips', {}).items():
            print(f"- {ip}: {count}次")
        
        print("\n地理位置信息:")
        geo_info = details.get('geo', {})
        if geo_info:
            for key, value in geo_info.items():
                print(f"- {key}: {value}")
        else:
            print("未获取到地理位置信息")
            
        print("\n详细结果:")
        for service_id, info in details.get('details', {}).items():
            print(f"- {service_id}: {info.get('ip')}")
            geo = info.get('geo', {})
            if geo:
                geo_str = ', '.join([f"{k}: {v}" for k, v in geo.items() if v])
                if geo_str:
                    print(f"  地理位置: {geo_str}")
    
    except Exception as e:
        print(f"测试失败: {str(e)}")

def test_get_public_ip():
    """测试修改后的get_public_ip方法，查看IP记录保存到数据库的情况"""
    from src.utils.network import NetworkUtils
    from src.core.database import DatabaseManager
    from src.core.ip_record_manager import IPRecordManager
    from src.config.database import get_default_paths
    
    print('\n\n测试 NetworkUtils.get_public_ip() 方法')
    print('=' * 50)
    
    try:
        # 初始化数据库
        db_paths = get_default_paths()
        db_manager = DatabaseManager()
        
        print("正在初始化数据库...")
        success = db_manager.initialize(db_paths)
        if not success:
            print("数据库初始化失败，无法继续测试")
            return
            
        # 确保表结构存在
        db_manager.create_tables()
        
        # 调用get_public_ip方法
        ip = NetworkUtils.get_public_ip()
        print(f"获取到的公网IP: {ip}")
        
        # 查询数据库中的IP记录
        with db_manager.get_session() as session:
            ip_manager = IPRecordManager(session)
            
            # 查询所有活跃IP
            all_ips = ip_manager.get_all_ips()
            active_count = len(all_ips)
            
            # 获取不同类型的IP
            manual_ips = ip_manager.get_ips_by_source('manual')
            error_ips = ip_manager.get_ips_by_source('error')
            history_ips = ip_manager.get_ips_by_source('history')
            
            print(f"\n数据库中的IP记录:")
            print(f"- 活跃IP总数: {active_count}")
            
            print(f"\nManual类型IP (用于白名单): {len(manual_ips)}")
            for i, ip in enumerate(manual_ips):
                source = ip_manager.get_ip_source(ip)
                print(f"  {i+1}. {ip} (来源: {source})")
            
            print(f"\nError类型IP (错误产生): {len(error_ips)}")
            for i, ip in enumerate(error_ips):
                source = ip_manager.get_ip_source(ip)
                print(f"  {i+1}. {ip} (来源: {source})")
            
            print(f"\nHistory类型IP (历史记录): {len(history_ips)}")
            for i, ip in enumerate(history_ips):
                source = ip_manager.get_ip_source(ip)
                print(f"  {i+1}. {ip} (来源: {source})")
            
            # 判断刚才获取的IP是否在数据库中
            if ip:
                ip_source = ip_manager.get_ip_source(ip)
                if ip_source:
                    print(f"\n当前获取的IP [{ip}] 在数据库中的类型为: {ip_source}")
                else:
                    print(f"\n当前获取的IP [{ip}] 未保存到数据库")
            
            print("\n注意: 如果您多次运行测试，可能会观察到history类型IP的增加，这是正常的，因为每次运行会保存新检测到的IP")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    # 测试的IP服务列表
    services = [
        'https://qifu-api.baidubce.com/ip/local/geo/v1/district',
        'https://qifu.baidu.com/ip/local/geo/v1/district',
        'https://whois.pconline.com.cn/ipJson.jsp',
        'https://myip.ipip.net',
        'https://ip.useragentinfo.com/json',
        'https://api.ipify.org?format=json',     # 增加一个国际服务
        'https://httpbin.org/ip'                # 增加另一个国际服务
    ]

    # 测试结果
    print('正在测试多个公网IP获取服务...')
    print('=' * 50)

    results = {}
    for service in services:
        print(f'\n测试服务: {service}')
        ip = get_ip_from_service(service)
        results[service] = ip
        print(f'获取到的IP: {ip}')
        print('-' * 50)

    # 总结
    print('\n总结:')
    print('=' * 50)
    for service, ip in results.items():
        print(f'{service}: {ip}')
    
    # 分析结果
    analyze_ip_results(results)
    
    # 测试NetworkUtils的方法
    test_network_utils_method()
    
    # 测试get_public_ip方法及数据库记录
    test_get_public_ip()

if __name__ == "__main__":
    main() 