import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Файл не найден в запросе"})
    
    file = request.files['file']
    action = request.form.get('action') # 'day' или 'hour'
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "Файл не выбран"})
    
    if file:
        # Здесь можно сохранить файл или сразу прочитать его через pandas / openpyxl
        filename = file.filename
        
        # --- ТВОЯ ЛОГИКА ОБРАБОТКИ EXCEL ---
        # Пример: файл получен, дальше можно вытаскивать ФИО и ПИНФЛ
        
        message = f"Файл '{filename}' успешно получен для режима '{action}'! Данные обработаны."
        return jsonify({"status": "success", "message": message})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
