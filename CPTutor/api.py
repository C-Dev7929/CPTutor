import urllib.request
import json
import ssl

import subprocess

def query_gemini_cli(system_instruction, user_message):
    # Kết hợp role và câu hỏi
    full_prompt = "{0}\n\nCÂU HỎI VÀ CONTEXT:\n{1}".format(system_instruction, user_message)
    
    try:
        # Gọi lệnh gemini từ terminal
        # Sử dụng -p để chạy ở chế độ headless (non-interactive)
        # Sử dụng --raw-output để lấy text thuần túy
        # Thêm --skip-trust để bỏ qua kiểm tra thư mục tin cậy trong chế độ tự động
        cmd = ["gemini", "--prompt", full_prompt, "--approval-mode", "plan", "--raw-output", "--skip-trust"]
        
        # Chạy lệnh và lấy kết quả
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate(timeout=60)
        
        if process.returncode == 0:
            # Lọc bỏ các dòng thông báo hệ thống nếu có
            return stdout.strip()
        else:
            return "Lỗi Gemini CLI: {0}".format(stderr or stdout)
            
    except Exception as e:
        return "Không thể chạy Gemini CLI. Hãy chắc chắn bạn đã cài đặt và đăng nhập gemini (npm install -g @google/gemini-cli && gemini login). Lỗi: {0}".format(str(e))

def query_gemini(api_key, system_instruction, user_message):
    # Sử dụng Gemini 1.5 Flash (v1)
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={0}".format(api_key)
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192
        }
    }
    
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        # Compatibility check for SSL context (Python 3.3 vs 3.4+)
        if hasattr(ssl, '_create_unverified_context'):
            context = ssl._create_unverified_context()
            response = urllib.request.urlopen(req, timeout=30, context=context)
        else:
            # Fallback for Python 3.3 which doesn't support 'context' in urlopen
            response = urllib.request.urlopen(req, timeout=30)
            
        res_data = response.read().decode("utf-8")
        res_json = json.loads(res_data)
        
        if "candidates" in res_json and len(res_json["candidates"]) > 0:
            content = res_json["candidates"][0].get("content", {})
            parts = content.get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
            else:
                return "Lỗi API: Phản hồi không có nội dung văn bản."
        else:
            return "Lỗi API: Không tìm thấy candidates trong phản hồi."
            
    except urllib.error.HTTPError as e:
        error_content = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_content)
            return "Lỗi API Gemini (HTTP {0}): {1}".format(e.code, error_json.get("error", {}).get("message", "Lỗi không xác định"))
        except:
            return "Lỗi API Gemini (HTTP {0}): {1}".format(e.code, error_content)
    except Exception as e:
        return "Lỗi kết nối đến Gemini: {0}".format(str(e))
