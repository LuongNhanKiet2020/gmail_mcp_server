# auth.py — Chạy riêng để đăng nhập Google OAuth và tạo token.json
# Sau khi chạy xong, MCP server sẽ dùng token.json này
import os
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

print("=== Gmail OAuth Authentication ===")
print("Browser sẽ mở để bạn đăng nhập Google...")
print("Hãy đăng nhập bằng tài khoản: luongnhankiet2023@gmail.com")
print()

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, "w") as token:
    token.write(creds.to_json())

print()
print(f"✅ Đăng nhập thành công! Token đã lưu tại: {TOKEN_FILE}")
print("Bạn có thể đóng script này và dùng Gmail MCP bình thường.")
