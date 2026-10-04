from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__, static_folder='.') # 告诉 Flask 当前目录就是网页目录
CORS(app)

# 设定Bug存放路径
BUG_DIR = "./bug" 
os.makedirs(BUG_DIR, exist_ok=True)

# 【新增】：让 Flask 直接提供 index.html 网页！
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/submit', methods=['POST'])
def submit_bug():
    data = request.json
    
    filename = f"bug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(BUG_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"【时间】: {datetime.now()}\n")
        f.write(f"【Bug取名】: {data.get('title', '无')}\n")
        f.write(f"【漏洞描述】: {data.get('desc', '无')}\n")
        f.write(f"【触发过程】: {data.get('steps', '无')}\n")
        
    print(f"[G.R.D.M.] 📥 收到新情报：{filename}")
    return jsonify({"status": "success", "msg": "G.R.D.M. 已成功接收报告！"})

if __name__ == '__main__':
    print("[G.R.D.M.] 🚀 正在启动情报接收服务器...")
    app.run(host='127.0.0.1', port=5000)

