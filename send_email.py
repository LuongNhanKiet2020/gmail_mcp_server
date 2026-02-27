import logging
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

from gmail import search_emails, get_email_content, reply_to_email

# ── Bước 1: Tìm email ỨNG TUYỂN GỐC gửi cho nathan@technext.asia ──
print("🔍 Bước 1: Tìm email ứng tuyển gốc...")
search_res = search_emails('to:nathan@technext.asia from:luongnhankiet2023@gmail.com subject:[AI Intern] - Lương Nhân Kiệt', max_results=1)
print(search_res)

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

# ── Bước 3: REPLY vào email từ nathan (bài đánh giá) ──
# Tìm email bài đánh giá từ nathan
print("\n🔍 Tìm email bài đánh giá từ nathan...")
nathan_search = search_emails('from:luongnhankiet2023@gmail.com subject:"Bài đánh giá năng lực"', max_results=1)
print(nathan_search)
nathan_msg_id = nathan_search.split('📧 ID: ')[1].split('\n')[0].strip()

print(f"\n✉️ Bước 3: Reply email từ nathan (ID: {nathan_msg_id})...")

reply_body = f"""Dạ em chào anh chị,
Em là Lương Nhân Kiệt, đây là bản test reply qua Gmail MCP – Đây là email tự động từ Antigravity/Claude Code để demo. Không cần phản hồi ạ.
Cho biết chính xác: Ngày giờ gửi: {send_date}. 10 từ đầu tiên trong email đó: "{first_10_words}"
 Em cảm ơn!"""

reply_res = reply_to_email(nathan_msg_id, reply_body)
print(reply_res)
