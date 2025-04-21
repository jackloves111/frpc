from flask import Flask, render_template, request, jsonify
import toml
import os
import subprocess
import requests

app = Flask(__name__, static_folder='frpc-web-admin/static', static_url_path='/static')

# 配置文件路径
FRPC_CONFIG = '/frp/frpc.toml'

def restart_frpc():
    """重启frpc服务"""
    try:
        # 使用HTTP接口重启frpc服务
        response = requests.post('http://localhost:9001/RPC2', 
            auth=('admin', 'admin'),  # 默认用户名和密码
            headers={'Content-Type': 'text/xml'},
            data='''<?xml version="1.0"?>
            <methodCall>
                <methodName>supervisor.stopProcess</methodName>
                <params><param><value><string>frpc</string></value></param></params>
            </methodCall>''')
        
        if response.status_code != 200:
            raise Exception("停止服务失败")
            
        response = requests.post('http://localhost:9001/RPC2',
            auth=('admin', 'admin'),
            headers={'Content-Type': 'text/xml'},
            data='''<?xml version="1.0"?>
            <methodCall>
                <methodName>supervisor.startProcess</methodName>
                <params><param><value><string>frpc</string></value></param></params>
            </methodCall>''')
            
        if response.status_code != 200:
            raise Exception("启动服务失败")
            
        return True
    except Exception as e:
        print(f'重启frpc服务失败: {str(e)}')
        return False

def read_config():
    """读取frpc.toml配置文件"""
    try:
        if os.path.exists(FRPC_CONFIG):
            with open(FRPC_CONFIG, 'r', encoding='utf-8') as f:
                return {'success': True, 'data': toml.load(f)}
        return {'success': False, 'message': '请映射/frp/frpc.toml文件才可以使用', 'data': {'serverAddr': '', 'serverPort': 0, 'proxies': []}}
    except Exception as e:
        print(f'读取配置文件错误: {str(e)}')
        return {'success': False, 'message': str(e), 'data': {'serverAddr': '', 'serverPort': 0, 'proxies': []}}

def save_config(config):
    """保存frpc.toml配置文件"""
    try:
        with open(FRPC_CONFIG, 'w', encoding='utf-8') as f:
            # 添加服务器设置与隧道规则之间的空白换行
            toml.dump({'serverAddr': config['serverAddr'], 'serverPort': config['serverPort']}, f)
            f.write('\n')  # 添加空白换行
            toml.dump({'proxies': config['proxies']}, f)
        return True
    except Exception as e:
        print(f'保存配置文件错误: {str(e)}')
        return False

@app.route('/')
def index():
    """主页面"""
    result = read_config()
    return render_template('index.html', config=result)

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    result = read_config()
    if not result['success']:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        config = request.get_json()
        if save_config(config):
            # 重启frpc服务
            if restart_frpc():
                return jsonify({'success': True, 'message': '配置已更新并重启服务'})
            return jsonify({'success': False, 'message': '配置已更新，但重启服务失败'}), 500
        return jsonify({'success': False, 'message': '保存配置失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070)