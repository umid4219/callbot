from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import pandas as pd
import os
from datetime import datetime
import csv

app = FastAPI()

DATA_FILE = "call_logs.csv"

# Создаем файл с красивыми заголовками для колонок в Excel
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Device Name', 'Phone Number', 'Call Type', 'Contact Number', 'Date & Time', 'Duration (sec)', 'Received At'])

@app.post("/log")
async def receive_log(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    
    # Извлекаем поля, которые присылает приложение
    row = [
        data.get('device_name', data.get('phone_name', 'Unknown')),
        data.get('phone_number', 'Unknown'),
        data.get('call_type', 'Unknown'),
        data.get('contact_number', data.get('number', 'Unknown')),
        data.get('date_time', data.get('timestamp', 'Unknown')),
        data.get('duration', 0),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    
    # Записываем строку в CSV
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)
        
    return {"status": "success"}

@app.get("/download-report")
async def download_report():
    if not os.path.exists(DATA_FILE):
        return {"error": "No data found"}
    
    df = pd.read_csv(DATA_FILE)
    output_filename = "Call_Report.xlsx"
    df.to_excel(output_filename, index=False)
    
    return FileResponse(output_filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='Call_Report.xlsx')

@app.get("/")
def read_root():
    return {"message": "Call Logger Server is running and ready!"}

# Эта часть гарантирует, что Render успешно запустит сервер без падений
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
