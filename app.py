import os
import glob
import traceback
from datetime import datetime
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
    
    filename = "".join(c for c in file.filename if c.isalnum() or c in ('_', '.', '-')).strip()
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"-> Успешно сохранен/обновлен файл отчета: {filename}")
    
    return jsonify({"status": "success", "message": "Отчет успешно загружен!"})

@app.route('/api/download-report', methods=['GET', 'POST'])
def download_report():
    try:
        all_files = glob.glob(os.path.join(UPLOAD_FOLDER, "Call_Report_*.csv"))
        csv_files = [f for f in all_files if f.endswith('.csv')]
        
        print(f"-> Найдено CSV файлов на сервере: {len(csv_files)}")
        for f in csv_files:
            print(f"   - {f}")

        if not csv_files:
            return jsonify({"status": "error", "message": "Ни один телефон еще не передал данные!"}), 404
        
        output_xlsx_path = os.path.join(UPLOAD_FOLDER, "Summary_Call_Report.xlsx")
        
        summary_list = []
        all_details_df = pd.DataFrame()

        for file_path in csv_files:
            base_name = os.path.basename(file_path)
            employee_name = base_name.replace("Call_Report_", "").replace(".csv", "").replace("_", " ")
            
            try:
                # Читаем файл со всеми колонками как текст
                df = pd.read_csv(file_path, sep=',', dtype=str)
                if df.empty:
                    print(f"   Файл пуст: {base_name}")
                    continue
                
                if len(df.columns) == 1:
                    df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)

                print(f"   Прочитано строк из {base_name}: {len(df)}")

                # Чистка номеров телефонов от .0
                for col in ['Number', 'number', 'Номер']:
                    if col in df.columns:
                        df[col] = df[col].astype(str).apply(lambda x: x[:-2] if str(x).endswith('.0') else x)

                df.insert(0, 'Сотрудник', employee_name)
                
                # Подсчет типов звонков
                df['CleanType'] = df['Type'].astype(str).str.lower().str.strip()
                
                total_calls = len(df)
                incoming = len(df[df['CleanType'].str.contains('вход|incoming', na=False)])
                outgoing = len(df[df['CleanType'].str.contains('исход|outgoing', na=False)])
                missed = len(df[df['CleanType'].str.contains('пропущ|missed', na=False)])
                
                df = df.drop(columns=['CleanType'], errors='ignore')
                
                summary_List_item = {
                    'Сотрудник': employee_name,
                    'Всего звонков': total_calls,
                    'Входящие': incoming,
                    'Исходящие': outgoing,
                    'Пропущенные': missed
                }
                summary_list.append(summary_List_item)
                
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
