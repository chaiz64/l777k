import requests
import re
import os
import json
import time
import random # <--- NEW
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= CONFIGURATION =================
INPUT_FILE = 'URL_config.ini'
MAX_WORKERS = 10 
TIMEOUT = 7 
# NEW: การหน่วงเวลาสุ่มเพื่อป้องกันการบล็อก (เวลาเป็นวินาที)
RANDOM_DELAY_MIN = 0.5 
RANDOM_DELAY_MAX = 1.5 

# Output Files
VALID_FILE_TXT = 'valid_ids.txt'      
INVALID_FILE_TXT = 'invalid_ids.txt'
VALID_FILE_JSON = 'valid_ids.json'    
INVALID_FILE_JSON = 'invalid_ids_failed.json' 
VALID_FILE_MD = 'VALID_ID_LIST.md'    
INVALID_FILE_MD = 'INVALID_ID_REPORT.md' 

# Headers (Same as before)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://live.douyin.com/",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
}
# =================================================

def extract_live_id(line):
    # (ฟังก์ชัน extract_live_id ยังคงเหมือนเดิม)
    line = line.strip()
    if not line:
        return None
    
    match = re.search(r'live\.douyin\.com/([a-zA-Z0-9_.-]+)', line)
    if match:
        return match.group(1)
        
    if re.fullmatch(r'^[a-zA-Z0-9_.-]+$', line):
        return line.split('|')[0].strip()
        
    return None

def extract_nickname(html_content):
    """พยายามดึงชื่อผู้ใช้งาน (Nickname) จาก HTML"""
    match = re.search(r'"nickname":"(.*?)"', html_content)
    if match:
        return match.group(1).encode('utf-8').decode('unicode-escape').strip()
    return "N/A"

def check_status(live_id):
    """ฟังก์ชันตรวจสอบสถานะและดึงชื่อผู้ใช้งาน (มีการหน่วงเวลาสุ่ม)"""
    if not live_id:
        return None, None, None
    
    # NEW: เพิ่มการหน่วงเวลาสุ่มก่อนยิง request
    delay = random.uniform(RANDOM_DELAY_MIN, RANDOM_DELAY_MAX)
    time.sleep(delay)
    
    check_url = f"https://live.douyin.com/{live_id}"
    
    # ... (ส่วนการตรวจสอบสถานะและดึงชื่อเหมือนเดิม) ...
    try:
        response = requests.get(check_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False)
        nickname = None
        status = None
        
        if response.status_code == 200:
            nickname = extract_nickname(response.text)
            if "已停用" in response.text or "已被封禁" in response.text or "不存在" in response.text:
                 status = "BANNED/DEACTIVATED"
            else:
                 status = "VALID"
            
        elif response.status_code == 404:
            status = "NOT_FOUND"
            
        elif response.status_code in [301, 302]:
            status = "REDIRECTED (POSSIBLE CHANGE/BLOCK)"
            
        else:
            # 403 Forbidden หรือสถานะผิดปกติอื่นๆ
            status = f"ERROR_{response.status_code}" 

    except Exception as e:
        status = f"CONNECTION_ERROR"

    return live_id, status, nickname

# (Export Functions และ Main Logic ยังคงเหมือนเดิม)

def export_to_json(filename, data):
    """บันทึกข้อมูลเป็นไฟล์ JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def export_to_markdown(filename, data, is_valid):
    """บันทึกข้อมูลเป็นไฟล์ Markdown"""
    
    if is_valid:
        title = "✅ รายการ ID ที่ใช้งานได้ (Valid ID List)"
        headers = ["ลำดับ", "Live ID", "ชื่อผู้ใช้งาน", "Live URL"]
    else:
        title = "❌ รายงาน ID ที่มีปัญหา (Invalid ID Report)"
        headers = ["ลำดับ", "Live ID", "สาเหตุ"]

    markdown_output = [
        f"# {title}",
        f"\n> วันที่ตรวจสอบ: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "\n---",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    
    for i, item in enumerate(data, 1):
        if is_valid:
            row = [
                str(i),
                item.get('live_id', 'N/A'),
                item.get('nickname', 'N/A'),
                f"[Go to Live]({item.get('url', '#')})"
            ]
        else:
            row = [
                str(i),
                item.get('live_id', 'N/A'),
                item.get('reason', 'N/A')
            ]
        markdown_output.append("| " + " | ".join(row) + " |")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_output))

def main():
    print("⚡ LEVEL BEYOND GOD MODE: LIVE ROOM VALIDATOR ACTIVATED ⚡")
    print(f"Reading from: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: File {INPUT_FILE} not found!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

    unique_ids_to_check = {} 
    for line in all_lines:
        live_id = extract_live_id(line)
        if live_id:
            unique_ids_to_check[live_id] = line.strip()

    ids_to_process = list(unique_ids_to_check.keys())
    
    if not ids_to_process:
        print("No valid IDs found in the input file to process.")
        return

    print(f"Loaded {len(all_lines)} lines, found {len(ids_to_process)} unique Live IDs. Starting verification...")
    
    valid_data = [] 
    invalid_data = [] 
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_id = {executor.submit(check_status, live_id): live_id for live_id in ids_to_process}
        
        processed = 0
        for future in as_completed(future_to_id):
            live_id_result, status, nickname = future.result()
            processed += 1
            
            if status == "VALID":
                url = f"https://live.douyin.com/{live_id_result}"
                
                valid_data.append({
                    'live_id': live_id_result,
                    'nickname': nickname,
                    'url': url
                })
                print(f"[{processed}/{len(ids_to_process)}] ✅ VALID: {live_id_result} ({nickname})...")
                
            elif status: 
                url = f"https://live.douyin.com/{live_id_result}"
                
                invalid_data.append({
                    'live_id': live_id_result,
                    'url': url,
                    'reason': status
                })
                print(f"[{processed}/{len(ids_to_process)}] ❌ INVALID: {live_id_result} ({status})")
    
    print("\nSorting data by Live ID...")
    valid_data.sort(key=lambda x: x['live_id'])
    invalid_data.sort(key=lambda x: x['live_id'])
    
    valid_urls_txt = [item['url'] for item in valid_data]

    # --- บันทึกผลลัพธ์ ---
    
    # 1. Export TXT files
    with open(VALID_FILE_TXT, 'w', encoding='utf-8') as f:
        f.writelines("\n".join(valid_urls_txt))
    with open(INVALID_FILE_TXT, 'w', encoding='utf-8') as f:
        f.writelines("\n".join([item['url'] + f" | Reason: {item['reason']}" for item in invalid_data]))

    # 2. Export JSON files
    export_to_json(VALID_FILE_JSON, valid_data)
    export_to_json(INVALID_FILE_JSON, invalid_data)
    
    # 3. Export Markdown files
    export_to_markdown(VALID_FILE_MD, valid_data, is_valid=True)
    export_to_markdown(INVALID_FILE_MD, invalid_data, is_valid=False)

    print("\n" + "="*40)
    print(f"MISSION COMPLETE.")
    print(f"✅ Valid IDs: {len(valid_data)}, ❌ Invalid IDs: {len(invalid_data)}")
    print("--- Exported Files ---")
    print(f"TXT (Config Ready): {VALID_FILE_TXT}, {INVALID_FILE_TXT}")
    print(f"JSON (Data Export): {VALID_FILE_JSON}, {INVALID_FILE_JSON}")
    print(f"MARKDOWN (Report): {VALID_FILE_MD}, {INVALID_FILE_MD}")
    print("="*40)

if __name__ == "__main__":
    main()
