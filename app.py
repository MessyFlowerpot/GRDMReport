from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)

# 【核心修复】配置 CORS
# 允许所有来源访问（或者你可以指定 origins=['https://messyflowerpot.github.io']）
# 允许所有 Header，允许 POST/GET/OPTIONS 方法
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 确保 bug 目录存在
BUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bug")
if not os.path.exists(BUG_DIR):
    os.makedirs(BUG_DIR)

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit_bug():
    # 处理预检请求 (Preflight Request)
    # 浏览器在发正式 POST 前会先发一个 OPTIONS 请求探路
    if request.method == 'OPTIONS':
        resp = jsonify({'status': 'ok'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 200

    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "没有接收到数据"}), 400

        # 生成文件名 (使用时间戳防止覆盖)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bug_report_{timestamp}.json"
        filepath = os.path.join(BUG_DIR, filename)

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"[G.R.D.M. Server] 收到新情报: {filename}")
        return jsonify({"message": "情报接收成功！", "file": filename}), 200

    except Exception as e:
        print(f"[G.R.D.M. Server] 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "G.R.D.M. Server is running. Do not access this directly."

if __name__ == '__main__':
    # 监听 0.0.0.0 确保 Cloudflare 能连上本地端口
    app.run(host='0.0.0.0', port=5000, debug=False)
