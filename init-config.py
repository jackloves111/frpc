#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
容器启动时的配置文件初始化脚本
在容器启动时检查配置文件是否存在，如果不存在则自动生成默认配置
"""

import os
import toml

# 配置文件路径
FRPC_CONFIG = '/frp/frpc.toml'

def create_default_config():
    """创建默认配置文件"""
    default_config = {
        'serverAddr': '114.114.114.114',
        'serverPort': 3699,
        'proxies': [
            {
                'name': 'NT',
                'type': 'tcp',
                'localIP': '127.0.0.1',
                'localPort': 3000,
                'remotePort': 3000
            },
            {
                'name': 'MP',
                'type': 'tcp',
                'localIP': '127.0.0.1',
                'localPort': 3005,
                'remotePort': 3005
            }
        ]
    }
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(FRPC_CONFIG), exist_ok=True)
        
        with open(FRPC_CONFIG, 'w', encoding='utf-8') as f:
            # 添加服务器设置与隧道规则之间的空白换行
            toml.dump({'serverAddr': default_config['serverAddr'], 'serverPort': default_config['serverPort']}, f)
            f.write('\n')  # 添加空白换行
            toml.dump({'proxies': default_config['proxies']}, f)
        
        print(f'✅ 已自动生成默认配置文件: {FRPC_CONFIG}')
        return True
    except Exception as e:
        print(f'❌ 生成配置文件失败: {str(e)}')
        return False

def main():
    """主函数"""
    print('🔍 检查配置文件...')
    
    if os.path.exists(FRPC_CONFIG):
        print(f'✅ 配置文件已存在: {FRPC_CONFIG}')
    else:
        print(f'⚠️  配置文件不存在: {FRPC_CONFIG}')
        print('🔧 正在生成默认配置文件...')
        
        if create_default_config():
            print('🎉 配置文件初始化完成！')
        else:
            print('💥 配置文件初始化失败！')
            exit(1)

if __name__ == '__main__':
    main()