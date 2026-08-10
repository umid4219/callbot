import os
from flask import Flask, render_template, request, send_file
import pandas as pd
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download-report', methods=['POST'])
def download_report():
    data = request.get_json() or {}
    action = data.get('action', 'day') # 'day' или 'hour'
    
    # --- ЗДЕСЬ БУДЕТ ЛОГИКА ПОЛУЧЕНИЯ ДАННЫХ С ТЕЛЕФОНА ---
    # Пока формируем тестовый отчет по звонкам сотрудников на основе запроса
    
    # Имитация данных, полученных с телефона
    call_data = [
        {"Сотрудник": "Алексей Иванов", "Количество звонков": 45, "Время разговоров (мин)": 120, "Период": action},
        {"Сотрудник": "Марина Смирнова", "Количество звонков": 38, "Время разговоров (мин)": 95, "Период": action},
        {"Сотрудник": "Дмитрий Петров", "Количество звонков": 52, "Время разговоров (мин)": 150, "Период": action},
    ]
    
    df = pd.DataFrame(call_data)
    
    # Имя файла с текущей датой
    filename = f"Call_Report_{action}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    filepath = os.path.join('/tmp', filename)
    
    # Сохраняем в Excel с красивым оформлением через pandas/openpyxl
    df.to_excel(filepath, index=False)
    
    # Отправляем файл пользователю на скачивание
    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
