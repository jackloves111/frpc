from flask import Flask, render_template, request, jsonify
import toml
import os

app = Flask(__name__)

# 配置文件路径
FRPC_CONFIG = '/frp/frpc.toml'

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
            return jsonify({'success': True, 'message': '配置已更新'})
        return jsonify({'success': False, 'message': '保存配置失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070)