import os
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

# Папка для хранения актуальных отчетов от телефона
UPLOAD_FOLDER = '/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# Эндпоинт, куда андроид-приложение отправляет готовый Excel-файл
@app.route('/api/upload-report', methods=['POST'])
def upload_report():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Файл не найден"}), 400
    
    file = request.files['file']
    action = request.form.get('action', 'day') # 'day' или 'hour'
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "Имя файла пустое"}), 400
    
    # Сохраняем под конкретный тип отчета
    filename = f"Call_Report_{action}.xlsx"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    return jsonify({"status": "success", "message": "Отчет успешно загружен с телефона!"})

# Эндпоинт, который скачивает отчет по нажатию кнопки на сайте
@app.route('/api/download-report', methods=['POST'])
def download_report():
    data = request.get_json() or {}
    action = data.get('action', 'day')
    
    filename = f"Call_Report_{action}.xlsx"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Если телефон еще не прислал файл
    if not os.path.exists(filepath):
        return jsonify({"status": "error", "message": "Телефон еще не передал данные!"}), 404
        
    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
