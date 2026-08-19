import os
import glob
import traceback
from datetime import datetime
from functools import wraps
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify, Response

app = Flask(__name__)

# Постоянная папка для отчетов
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'reports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Укажи здесь свои логин и пароль для доступа к сайту
USERNAME = "admin"
PASSWORD = "my_secret_password"

def check_auth(username, password):
    """Проверка правильности логина и пароля"""
    return username == USERNAME and password == PASSWORD

def authenticate():
    """Запрос ввода логина и пароля у браузера"""
    return Response(
        'Требуется авторизация!', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    """Декоратор для защиты страниц паролем"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth  # <-- Защитили главную страницу паролем
def index():
    return render_template('index.html')

@app.route('/api/upload-report', methods=['POST'])
def upload_report():
    # Телефоны отправляют отчеты без изменений (скрытый API-эндпоинт)
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Файл не найден"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Имя файла пустое"}), 400
    
    filename = "".join(c for c in file.filename if c.isalnum() or c in ('_', '.', '-')).strip()
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"-> Успешно сохранен/обновлен файл отчета: {filename}")
    
    return jsonify({"status": "success", "message": "Отчет успешно загружен!"})

@app.route('/api/download-report', methods=['GET', 'POST'])
@requires_auth  # <-- Защитили скачивание отчета паролем
def download_report():
    try:
        all_files = glob.glob(os.path.join(UPLOAD_FOLDER, "Call_Report_*.csv"))
        csv_files = [f for f in all_files if f.endswith('.csv')]
        
        if not csv_files:
            return jsonify({"status": "error", "message": "Ни один телефон еще не передал данные!"}), 404
        
        output_xlsx_path = os.path.join(UPLOAD_FOLDER, "Summary_Call_Report.xlsx")
        
        summary_list = []
        all_details_df = pd.DataFrame()

        for file_path in csv_files:
            base_name = os.path.basename(file_path)
            employee_name = base_name.replace("Call_Report_", "").replace(".csv", "").replace("_", " ")
            
            try:
                df = pd.read_csv(file_path, sep=',', dtype=str)
                if df.empty:
                    continue
                
                if len(df.columns) == 1:
                    df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)

                for col in ['Number', 'number', 'Номер']:
                    if col in df.columns:
                        df[col] = df[col].astype(str).apply(lambda x: x[:-2] if str(x).endswith('.0') else x)

                df.insert(0, 'Сотрудник', employee_name)
                
                df['CleanType'] = df['Type'].astype(str).str.lower().str.strip()
                
                total_calls = len(df)
                incoming = len(df[df['CleanType'].str.contains('вход|incoming', na=False)])
                outgoing = len(df[df['CleanType'].str.contains('исход|outgoing', na=False)])
                missed = len(df[df['CleanType'].str.contains('пропущ|missed', na=False)])
                
                df = df.drop(columns=['CleanType'], errors='ignore')
                
                summary_list.append({
                    'Сотрудник': employee_name,
                    'Всего звонков': total_calls,
                    'Входящие': incoming,
                    'Исходящие': outgoing,
                    'Пропущенные': missed
                })
                
                all_details_df = pd.concat([all_details_df, df], ignore_index=True)
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")

        if all_details_df.empty or not summary_list:
            return jsonify({"status": "error", "message": "В файлах не найдено данных о звонках!"}), 404

        with pd.ExcelWriter(output_xlsx_path, engine='openpyxl') as writer:
            summary_df = pd.DataFrame(summary_list)
            summary_df.to_excel(writer, sheet_name='Сводка', index=False)

            def format_duration(seconds):
                try:
                    sec = int(float(seconds))
                    m, s = divmod(sec, 60)
                    if m > 0:
                        return f"{m} мин {s} сек"
                    return f"{s} сек"
                except:
                    return seconds

            for col_name in ['Длительность (сек)', 'Duration', 'duration']:
                if col_name in all_details_df.columns:
                    all_details_df[col_name] = all_details_df[col_name].apply(format_duration)
                    break

            all_details_df.to_excel(writer, sheet_name='Детализация', index=False)

        return send_file(
            output_xlsx_path, 
            as_attachment=True, 
            download_name="Summary_Call_Report.xlsx"
        )
    except Exception as e:
        print("КРИТИЧЕСКАЯ ОШИБКА В /api/download-report:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
