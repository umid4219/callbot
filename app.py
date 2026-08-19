from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import pandas as pd
import os
from datetime import datetime
import csv

app = FastAPI()

# Имя файла с данными
DATA_FILE = "call_logs.csv"

# Создаем файл с заголовками, если он еще не существует
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Device Name', 'Phone Number', 'Call Type', 'Contact Number', 'Date & Time', 'Duration (sec)', 'Received At'])

@app.post("/log")
async def receive_log(request: Request):
    data = await request.json()
    
    # Извлекаем данные из JSON (названия полей должны совпадать с тем, что шлет приложение)
    row = [
        data.get('device_name', 'Unknown'),
        data.get('phone_number', 'Unknown'),
        data.get('call_type', 'Unknown'),
        data.get('contact_number', 'Unknown'),
        data.get('date_time', 'Unknown'),
        data.get('duration', 0),
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
    
    # Читаем CSV и конвертируем в Excel
    df = pd.read_csv(DATA_FILE)
    output_filename = "Call_Report.xlsx"
    df.to_excel(output_filename, index=False)
    
    # Отдаем файл для скачивания
    return FileResponse(output_filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='Call_Report.xlsx')

@app.get("/")
def read_root():
    return {"message": "Call Logger Server is running. Use /download-report to get the Excel file."}
