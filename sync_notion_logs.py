import os
import glob
import json
import urllib.request
import urllib.error
import re
from datetime import datetime

DATABASE_ID = "34153e5e-7e18-800b-8f95-c70e153b18a5"
CURSOR_FILE = ".vibe_sync_cursor.json"

def get_notion_key():
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("NOTION_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip("'\"")
                        break
        except FileNotFoundError:
            pass
    return key
    
def extract_meta(text):
    who = re.search(r'작성자\s*\(Who\):\s*(.*)', text)
    who = who.group(1).strip() if who else "Unknown"
    
    when = re.search(r'작성 일자\s*\(When\):\s*(.*)', text)
    when = when.group(1).strip() if when else datetime.now().strftime("%Y-%m-%d")
    
    obj = re.search(r'목표 기능\s*\(Objective\):\s*(.*)', text)
    obj = obj.group(1).strip() if obj else "Vibe Log"
    
    env = re.search(r'작업 브랜치/환경.*:\s*`?(.*?)`?', text)
    env = env.group(1).strip() if env else "main"
    
    session_title = f"[{env}] {obj} - {who}"
    return session_title, when, obj

def parse_markdown_to_blocks(text):
    blocks = []
    lines = text.split('\n')
    in_code = False
    code_content = []
    code_lang = ""
    for line in lines:
        if line.startswith("```"):
            if in_code:
                 # Limitation check, split if over 2000 chars (notion limit)
                 content = "\n".join(code_content)[:2000]
                 blocks.append({
                     "object": "block",
                     "type": "code",
                     "code": {
                         "language": code_lang if code_lang else "plain text",
                         "rich_text": [{"type": "text", "text": {"content": content}}]
                     }
                 })
                 in_code = False
                 code_content = []
                 code_lang = ""
            else:
                in_code = True
                code_lang = line.strip()[3:].strip()
                # Ensure supported type mappings
                if code_lang == "javascript" or code_lang == "js": code_lang = "javascript"
                elif code_lang == "python" or code_lang == "py": code_lang = "python"
                elif code_lang == "json": code_lang = "json"
                elif code_lang == "html": code_lang = "html"
                elif code_lang == "css": code_lang = "css"
                elif code_lang == "text": code_lang = "plain text"
                else: code_lang = "plain text"
            continue
            
        if in_code:
            code_content.append(line)
            continue
            
        # Parse simple markdown texts into robust blocks
        if line.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}})
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}})
        elif line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("- ") or line.startswith("* "):
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("> "):
            blocks.append({"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.strip() == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.strip():
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]}})
    return blocks

def post_to_notion(api_key, title, date, content_text):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        datetime.strptime(date[:10], "%Y-%m-%d")
        valid_date = date[:10]
    except:
        valid_date = datetime.now().strftime("%Y-%m-%d")
        
    blocks = parse_markdown_to_blocks(content_text)
    
    # max block check (notion allows max 100 blocks per request)
    blocks = blocks[:100]
    
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Session": {"title": [{"text": {"content": title[:2000]}}]},
            "Date": {"date": {"start": valid_date}},
        },
        "children": blocks
    }
    
    req = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 200:
                print(f"✅ Successfully synced log to Notion: {title}")
                return True
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to sync Notion: {e.read().decode('utf-8')}")
        return False
    return False

def main():
    api_key = get_notion_key()
    if not api_key:
        print("⏭️ NOTION_API_KEY not found in .env or system. Skipping Notion sync.")
        return

    cursor_data = {}
    if os.path.exists(CURSOR_FILE):
        try:
            with open(CURSOR_FILE, "r", encoding="utf-8") as f:
                cursor_data = json.load(f)
        except Exception:
            pass

    files = glob.glob("**/Vibe_Coding_Log.md", recursive=True)
    if not files:
        print("⏭️ No Vibe_Coding_Log.md found. Skipping sync.")
        return
        
    for file in files:
        if not os.path.isfile(file): continue
        path_key = file.replace("\\", "/")
        
        last_offset = cursor_data.get(path_key, 0)
        file_size = os.path.getsize(file)
        
        if file_size > last_offset:
            # File has appended data
            try:
                with open(file, "r", encoding="utf-8") as f:
                    f.seek(last_offset)
                    new_logs = f.read()
                    
                title, date, obj = extract_meta(new_logs)
                if not title.strip():
                    title = f"[Log] Update from {path_key}"
                    
                # 추후 프론트/백엔드 레포지토리 분할 및 통합 로깅 시 구분을 위한 자동 태깅
                if "frontend" in path_key.lower() and "frontend" not in title.lower():
                    title = f"[Frontend] {title}"
                elif "backend" in path_key.lower() and "backend" not in title.lower():
                    title = f"[Backend] {title}"
                    
                print(f"[Notion Sync] Found new logs in {path_key}. Syncing to Notion...")
                success = post_to_notion(api_key, title, date, new_logs)
                
                if success:
                    cursor_data[path_key] = file_size
            except Exception as e:
                print(f"❌ Error reading/syncing {file}: {e}")
                
    # save cursor securely
    with open(CURSOR_FILE, "w", encoding="utf-8") as f:
        json.dump(cursor_data, f)
        
    print("✨ Sync cycle complete.")

if __name__ == "__main__":
    main()
