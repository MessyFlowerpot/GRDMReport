from flask import Flask, request, jsonify, make_response
import os
import json
from datetime import datetime

app = Flask(__name__)

# 确保 bug 目录存在
BUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bug")
if not os.path.exists(BUG_DIR):
    os.makedirs(BUG_DIR)

@app.after_request
def add_cors_headers(response):
    """
    【终极防御】不管发生什么，每个响应都强制带上 CORS 头
    这是解决 GitHub Pages 跨域的最暴力、最有效的方法
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit_bug():
    # 专门处理浏览器的“预检请求” (Preflight)
    # 很多 CORS 失败都是因为 Flask 忽略了这个 OPTIONS 请求
    if request.method == 'OPTIONS':
        return make_response('', 200)

    try:
        # 接收数据
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "数据为空"}), 400

        # 生成文件名并写入
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bug_report_{timestamp}.json"
        filepath = os.path.join(BUG_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"[G.R.D.M.] ✅ 收到情报: {filename}")
        
        return jsonify({"message": "提交成功！", "file": filename}), 200

    except Exception as e:
        print(f"[G.R.D.M.] ❌ 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "G.R.D.M. Server is running."

if __name__ == '__main__':
    print("[G.R.D.M.] 🚀 服务器启动中... (已开启终极 CORS 防御)")
    app.run(host='0.0.0.0', port=5000, debug=False)
