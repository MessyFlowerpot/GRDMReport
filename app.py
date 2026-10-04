from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)

# 【核心修复】配置 CORS：允许所有来源、所有方法、所有 Header
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 确保 bug 目录存在
BUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bug")
if not os.path.exists(BUG_DIR):
    os.makedirs(BUG_DIR)
    print(f"[G.R.D.M.] 创建了 bug 文件夹: {BUG_DIR}")

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit_bug():
    print("[G.R.D.M.] 收到一个新的 /submit 请求！") # 【调试】证明服务器收到了请求
    
    # 处理浏览器预检请求 (Preflight)
    if request.method == 'OPTIONS':
        print("[G.R.D.M.] 处理 OPTIONS 预检请求...")
        resp = jsonify({'status': 'ok'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 200

    try:
        # 【关键修改】force=True 强制解析，silent=True 防止直接报错中断
        data = request.get_json(force=True, silent=True)
        
        if not data:
            print("[G.R.D.M.] [WARN] 接收到的数据为空或格式错误")
            return jsonify({"error": "接收到的数据为空"}), 400

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bug_report_{timestamp}.json"
        filepath = os.path.join(BUG_DIR, filename)

        print(f"[G.R.D.M.] [WRITE]正在写入文件: {filename}") # 【调试】证明正在写文件

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"[G.R.D.M.] [DONE] 情报接收成功: {filename}")
        return jsonify({"message": "提交成功！", "file": filename}), 200

    except Exception as e:
        # 【核心调试】打印完整的错误堆栈到终端
        import traceback
        error_detail = traceback.format_exc()
        print(f"[G.R.D.M.] [ERROR] 发生严重错误:\n{error_detail}") 
        
        # 返回具体的错误信息给前端
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def index():
    return "G.R.D.M. Server is running."

if __name__ == '__main__':
    print("[G.R.D.M.] Flask 服务器启动中... 监听端口 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
