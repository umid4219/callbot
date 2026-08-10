import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/collect', methods=['POST'])
def collect_data():
    data = request.json
    action = data.get('action')
    
    # Здесь можно прописать логику сбора данных (например, обращение к телефонам или базе)
    if action == 'day':
        message = "Выполнен сбор данных за весь день. Всё успешно выгружено!"
    elif action == 'hour':
        message = "Выполнен сбор данных за последний час. Всё успешно выгружено!"
    else:
        message = "Неизвестное действие."
        
    return jsonify({"status": "success", "message": message})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
