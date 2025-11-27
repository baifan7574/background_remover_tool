"""
简化的测试Flask应用 - 用于验证路由是否正常工作
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'Hello World'})

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Test health endpoint'
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    return jsonify({
        'message': 'Test register endpoint',
        'status': 'success'
    })

if __name__ == '__main__':
    print("🚀 启动测试Flask应用...")
    print("🌐 访问地址: http://localhost:5000")
    print("📈 健康检查: http://localhost:5000/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)