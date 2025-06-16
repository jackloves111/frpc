from flask import Flask, render_template, request, jsonify
import toml
import os
import subprocess
import requests
import time
import socket

app = Flask(__name__, static_folder='/app/static', static_url_path='/static')

# 配置文件路径
FRPC_CONFIG = '/frp/frpc.toml'
TITLE_CONFIG = './title.txt'

def check_frpc_running():
    """检查frpc进程是否正在运行"""
    try:
        # 备用方案：检查frpc通常使用的端口
        try:
            # 尝试从配置文件中获取实际端口
            with open(FRPC_CONFIG, 'r') as f:
                config = toml.load(f)
                admin_port = config.get('adminPort', 7400)
            
            # 检查端口是否被监听
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', admin_port))
            sock.close()
            return result == 0
        except:
            # 如果配置文件检查失败，尝试使用进程检查
            try:
                process = subprocess.run(['ps', '-ef'], capture_output=True, text=True)
                return 'frpc' in process.stdout
            except:
                # 如果所有方法都失败，假设服务在运行
                return True
    except Exception as e:
        print(f'检查frpc状态失败: {str(e)}')
        return True

def restart_frpc():
    """重启frpc服务"""
    try:
        # 检查重启前的状态
        was_running = check_frpc_running()
        
        # 使用进程方式重启frpc服务
        try:
            # 尝试杀死现有的frpc进程
            subprocess.run(['pkill', '-f', 'frpc'], capture_output=True)
            print('已停止frpc进程')
        except Exception as e:
            print(f'停止frpc进程失败: {str(e)}')
        
        # 等待进程完全停止
        time.sleep(2)
        
        try:
            # 启动新的frpc进程
            subprocess.Popen(['/frp/frpc', '-c', '/frp/frpc.toml'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            print('已启动frpc进程')
        except Exception as e:
            print(f'启动frpc进程失败: {str(e)}')
        
        # 等待服务启动
        time.sleep(3)
        
        # 检查重启后的状态
        now_running = check_frpc_running()
        
        # 判断重启结果
        if not was_running and now_running:
            return "启动成功"
        elif was_running and now_running:
            return "重启成功"
        elif was_running and not now_running:
            return "停止失败"
        else:
            return "启动失败"
            
    except Exception as e:
        print(f'重启frpc服务异常: {str(e)}')
        return "重启过程异常"

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

def read_title():
    """读取系统标题"""
    try:
        if os.path.exists(TITLE_CONFIG):
            with open(TITLE_CONFIG, 'r', encoding='utf-8') as f:
                title = f.read().strip()
                return title if title else 'FRP隧道管理系统'
        return 'FRP隧道管理系统'
    except Exception as e:
        print(f'读取标题文件错误: {str(e)}')
        return 'FRP隧道管理系统'

def save_title(title):
    """保存系统标题"""
    try:
        with open(TITLE_CONFIG, 'w', encoding='utf-8') as f:
            f.write(title.strip())
        return True
    except Exception as e:
        print(f'保存标题文件错误: {str(e)}')
        return False

@app.route('/')
def index():
    """主页面"""
    result = read_config()
    title = read_title()
    return render_template('index.html', config=result, title=title)

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
        save_result = save_config(config)
        
        if not save_result:
            return jsonify({'success': False, 'message': '保存配置失败'}), 500
            
        # 保存成功后重启服务并获取重启结果
        restart_result = restart_frpc()
        
        # 根据重启结果返回不同的消息
        if restart_result in ["重启成功", "启动成功"]:
            return jsonify({'success': True, 'message': f'配置已更新，服务{restart_result}'})
        else:
            # 即使重启失败，配置也已保存成功
            return jsonify({'success': True, 'message': f'配置已更新，但服务{restart_result}'})
            
    except Exception as e:
        print(f'更新配置异常: {str(e)}')
        return jsonify({'success': False, 'message': f'更新配置异常: {str(e)}'}), 500

@app.route('/api/title', methods=['GET'])
def get_title():
    """获取系统标题"""
    try:
        title = read_title()
        return jsonify({'success': True, 'title': title})
    except Exception as e:
        print(f'获取标题异常: {str(e)}')
        return jsonify({'success': False, 'message': f'获取标题异常: {str(e)}'}), 500

@app.route('/api/title', methods=['POST'])
def update_title():
    """更新系统标题"""
    try:
        data = request.get_json()
        title = data.get('title', 'FRP隧道管理系统')
        
        if not title.strip():
            title = 'FRP隧道管理系统'
            
        save_result = save_title(title)
        
        if save_result:
            return jsonify({'success': True, 'message': '标题已保存', 'title': title})
        else:
            return jsonify({'success': False, 'message': '保存标题失败'}), 500
            
    except Exception as e:
        print(f'更新标题异常: {str(e)}')
        return jsonify({'success': False, 'message': f'更新标题异常: {str(e)}'}), 500

if __name__ == '__main__':
    # 从环境变量获取端口号，默认为7070
    port = int(os.environ.get('PORT', 7070))
    app.run(host='0.0.0.0', port=port)