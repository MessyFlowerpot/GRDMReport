from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import traceback

app = Flask(__name__)

# 【核心修复】配置 CORS：允许所有来源、所有方法、所有 Header
# 这一步能解决 90% 的“卡死”问题，因为浏览器不再等待预检响应了
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 确保 bug 目录存在
BUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bug")
if not os.path.exists(BUG_DIR):
    os.makedirs(BUG_DIR)
    print(f"[G.R.D.M.] 创建了 bug 文件夹: {BUG_DIR}")

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit_bug():
    # 【关键】处理浏览器的“侦察兵”请求 (Preflight)
    # 如果不处理这个，浏览器就会一直转圈等待
    if request.method == 'OPTIONS':
        resp = jsonify({'status': 'ok'})
        # 显式告诉浏览器：你可以 POST，可以用 Content-Type
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 200

    try:
        print("[G.R.D.M.] 收到 POST 请求，正在解析数据...")
        
        # 【关键】force=True 强制解析，silent=True 防止解析失败直接报错
        data = request.get_json(force=True, silent=True)
        
        if not data:
            print("[G.R.D.M.] 警告: 接收到的数据为空")
            return jsonify({"error": "数据为空"}), 400

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bug_report_{timestamp}.json"
        filepath = os.path.join(BUG_DIR, filename)

        print(f"[G.R.D.M.] 正在写入文件: {filename}")

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"[G.R.D.M.] ✅ 情报接收成功: {filename}")
        return jsonify({"message": "提交成功！", "file": filename}), 200

    except Exception as e:
        # 【调试】打印完整的错误堆栈到终端
        error_detail = traceback.format_exc()
        print(f"[G.R.D.M.] ❌ 发生严重错误:\n{error_detail}") 
        
        # 返回具体的错误信息给前端
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def index():
    return "G.R.D.M. Server is running."

if __name__ == '__main__':
    print("[G.R.D.M.] Flask 服务器启动中... 监听端口 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
