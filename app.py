import os
import glob
import traceback
from functools import wraps
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify, Response

app = Flask(__name__)

# Папка для отчетов внутри проекта (постоянная)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'reports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- НАСТРОЙКИ ПАРОЛЯ ---
USERNAME = "admin"
PASSWORD = "my_secret_password" # Можешь изменить на свой

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        'Требуется авторизация!', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
# -----------------------

@app.route('/')
@requires_auth
def index():
    return render_template('index.html')

@app.route('/api/upload-report', methods=['POST'])
def upload_report():
    # Телефоны отправляют отчеты БЕЗ пароля
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Файл не найден"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Имя файла пустое"}), 400
    
    # Очистка имени файла
    filename = "".join(c for c in file.filename if c.isalnum() or c in ('_', '.', '-')).strip()
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"-> Файл получен: {filename}")
    
    return jsonify({"status": "success", "message": "Отчет успешно загружен!"})

@app.route('/api/download-report', methods=['GET', 'POST'])
@requires_auth
def download_report():
    try:
        all_files = glob.glob(os.path.join(UPLOAD_FOLDER, "Call_Report_*.csv"))
        if not all_files:
            return jsonify({"status": "error", "message": "Ни один телефон еще не передал данные!"}), 404
        
        output_xlsx_path = os.path.join(UPLOAD_FOLDER, "Summary_Call_Report.xlsx")
        summary_list = []
        all_details_df = pd.DataFrame()

        for file_path in all_files:
            base_name = os.path.basename(file_path)
            employee_name = base_name.replace("Call_Report_", "").replace(".csv", "").replace("_", " ")
            
            try:
                df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)
                df.insert(0, 'Сотрудник', employee_name)
                
                # Аналитика
                df['CleanType'] = df['Type'].astype(str).str.lower().str.strip()
                summary_list.append({
                    'Сотрудник': employee_name,
                    'Всего звонков': len(df),
                    'Входящие': len(df[df['CleanType'].str.contains('вход|incoming', na=False)]),
                    'Исходящие': len(df[df['CleanType'].str.contains('исход|outgoing', na=False)]),
                    'Пропущенные': len(df[df['CleanType'].str.contains('пропущ|missed', na=False)])
                })
                all_details_df = pd.concat([all_details_df, df.drop(columns=['CleanType'])], ignore_index=True)
            except Exception as e:
                print(f"Ошибка в файле {base_name}: {e}")

        with pd.ExcelWriter(output_xlsx_path, engine='openpyxl') as writer:
            pd.DataFrame(summary_list).to_excel(writer, sheet_name='Сводка', index=False)
            all_details_df.to_excel(writer, sheet_name='Детализация', index=False)

        return send_file(output_xlsx_path, as_attachment=True, download_name="Summary_Call_Report.xlsx")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
