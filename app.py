from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import pandas as pd
import os
from datetime import datetime
import csv
import json

app = FastAPI()

DATA_FILE = "call_logs.csv"

# Создаем файл с базовыми заголовками
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Raw Data', 'Received At'])

@app.post("/log")
async def receive_log(request: Request):
    try:
        # Пытаемся прочитать как JSON
        body = await request.json()
        data_str = json.dumps(body, ensure_ascii=False)
    except:
        # Если это не JSON, читаем как текст
        body = await request.body()
        data_str = body.decode('utf-8', errors='ignore')
    
    # Сохраняем «сырые» данные, чтобы вы точно их не потеряли
    row = [
        data_str,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    
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
    return {"message": "Server is running"}
