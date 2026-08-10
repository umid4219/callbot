import os
import glob
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload-report', methods=['POST'])
def upload_report():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Файл не найден"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Имя файла пустое"}), 400
    
    filename = secure_filename_custom(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    file.save(filepath)
    print(f"Успешно сохранен отчет: {filename}")
    
    return jsonify({"status": "success", "message": "Отчет успешно загружен!"})

@app.route('/api/download-report', methods=['POST'])
def download_report():
    search_path = os.path.join(UPLOAD_FOLDER, "Call_Report_*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        return jsonify({"status": "error", "message": "Ни один телефон еще не передал данные!"}), 404
    
    output_xlsx_path = os.path.join(UPLOAD_FOLDER, "Summary_Call_Report.xlsx")
    
    with pd.ExcelWriter(output_xlsx_path, engine='openpyxl') as writer:
        summary_list = []
        all_details_df = pd.DataFrame()

        for file_path in csv_files:
            base_name = os.path.basename(file_path)
            employee_name = base_name.replace("Call_Report_", "").replace(".csv", "").replace("_", " ")
            
            try:
                df = pd.read_csv(file_path, sep=',')
                if df.empty:
                    continue
                
                if len(df.columns) == 1:
                    df = pd.read_csv(file_path, sep=None, engine='python')
                
                df.insert(0, 'Сотрудник', employee_name)
                
                total_calls = len(df)
                incoming = len(df[df['Type'].astype(str).str.contains('Входящий|Incoming', case=False, na=False)])
                outgoing = len(df[df['Type'].astype(str).str.contains('Исходящий|Outgoing', case=False, na=False)])
                missed = len(df[df['Type'].astype(str).str.contains('Пропущенный|Missed', case=False, na=False)])
                
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

        if summary_list:
            summary_df = pd.DataFrame(summary_list)
            summary_df.to_excel(writer, sheet_name='Сводка', index=False)

        if not all_details_df.empty:
            cols = ['Сотрудник', 'Номер телефона', 'Тип вызова', 'Дата и время', 'Длительность (сек)']
            if len(all_details_df.columns) == len(cols):
                all_details_df.columns = cols
            all_details_df.to_excel(writer, sheet_name='Детализация звонков', index=False)

    return send_file(
        output_xlsx_path, 
        as_attachment=True, 
        download_name="Summary_Call_Report.xlsx"
    )

def secure_filename_custom(filename):
    return "".join(c for c in filename if c.isalnum() or c in ('_', '.', '-')).strip()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
