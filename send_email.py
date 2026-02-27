import base64
import logging
from email.mime.text import MIMEText

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

from gmail import _get_gmail_service, search_emails, get_email_content

service = _get_gmail_service()

# ── Bước 1: Tìm email gửi cho nathan@technext.asia ──
print("🔍 Bước 1: Tìm email ứng tuyển gửi cho nathan@technext.asia...")
search_res = search_emails('to:nathan@technext.asia from:luongnhankiet2023@gmail.com', max_results=1)
print(search_res)

if '📧 ID: ' not in search_res:
    print("❌ Không tìm thấy email.")
    exit(1)

msg_id = search_res.split('📧 ID: ')[1].split('\n')[0].strip()

# ── Bước 2: Đọc nội dung email đó ──
print("\n📖 Bước 2: Đọc nội dung email...")
content = get_email_content(msg_id)
print(content)

# Trích xuất ngày giờ
date_line = [line for line in content.split('\n') if line.startswith('Date: ')]
send_date = date_line[0].replace('Date: ', '') if date_line else 'Không xác định'

# Trích xuất 10 từ đầu tiên
body_part = content.split('--- Body ---')[1].strip()
first_10_words = ' '.join(body_part.split()[:10])

print(f"\n✅ Trích xuất thành công:")
print(f"   👉 Ngày giờ gửi: {send_date}")
print(f"   👉 10 từ đầu tiên: {first_10_words}")

# ── Bước 3: Gửi email mới tới luongnhankiet2012@gmail.com ──
print("\n✉️ Bước 3: Gửi email tới luongnhankiet2012@gmail.com...")

email_body = f"""Dạ em chào anh chị,
Em là Lương Nhân Kiệt, đây là bản test reply qua Gmail MCP – Đây là email tự động từ Antigravity/Claude Code để demo. Không cần phản hồi ạ.
Cho biết chính xác: Ngày giờ gửi: {send_date}. 10 từ đầu tiên trong email đó: "{first_10_words}"
 Em cảm ơn!"""

msg = MIMEText(email_body, _charset='utf-8')
msg['to'] = 'luongnhankiet2012@gmail.com'
msg['subject'] = 'Test ứng tuyển bằng gmail mcp server'

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()

print(f"\n✅ Email đã gửi thành công!")
print(f"   Message ID: {sent['id']}")
print(f"   To: luongnhankiet2012@gmail.com")
print(f"   Subject: Test ứng tuyển bằng gmail mcp server")
