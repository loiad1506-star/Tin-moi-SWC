Ngày 11/02 - Ổn định

import os
import json
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, ChatMemberHandler, CommandHandler
from flask import Flask
from threading import Thread
import google.generativeai as genai
import random 
from datetime import datetime
import re 

# --- CẤU HÌNH ---
SHEET_NAME = "Du_Lieu_Bot_SWC" 
CHANNEL_ID = -1001308148293  
GROUP_ID_TO_SEED = -1001598921227 

# --- DANH SÁCH ID ADMIN (ĐÚNG ID CỦA ANH) ---
# Bot sẽ gửi báo cáo tin nhắn khách hàng về cho những ID này
ADMIN_IDS = [507318519, 1654755377]

# --- DANH SÁCH MODEL ---
AI_MODELS = [
    'gemini-exp-1206',             # Ưu tiên 1
    'gemini-2.0-flash-lite',       # Ưu tiên 2
    'gemini-2.0-flash',            # Ưu tiên 3
    'gemini-2.0-flash-001',        # Ưu tiên 4
    'gemini-flash-lite-latest',    # Ưu tiên 5
    'gemini-2.5-flash'             # Cuối cùng
]


# --- CHỮ KÝ ---
SIGNATURE = """
👉 Tham gia Cộng đồng Nhà đầu tư Sky World Community Việt Nam:
✅ Telegram: https://t.me/swc_capital_vn
🌐 Website: https://swc.capital/vi
#SWC #SkyWorld #UST #Unitsky #uTerra #Đầu_tư #Cổ_phần_doanh_nghiệp
"""

# --- BỘ NHỚ ---
LAST_WELCOME_MSG = {} 
MESSAGE_COUNTER = 0 # Bộ đếm để quản lý việc ký tên (20 tin/lần)

# ==============================================================================
# KHU VỰC 1: "BỘ NÃO" SIÊU CẤP (CHUYÊN GIA LÃO LUYỆN & HÀI HƯỚC)
# ==============================================================================
SYSTEM_PROMPT = """
Bạn là TRỢ LÝ CHIẾN LƯỢC CẤP CAO của Sky World Community (SWC) Việt Nam.
Bạn là sự kết hợp giữa một CHUYÊN GIA TÀI CHÍNH LÃO LUYỆN (20 năm kinh nghiệm) và một NGƯỜI BẠN HÀI HƯỚC, SẮC SẢO.

1. ĐỊNH VỊ TÍNH CÁCH (LÃO LUYỆN - THỰC CHIẾN - HÀI HƯỚC):
- Phong cách: "Phũ nhưng Thật" (Sarcastic but True). Thức tỉnh người dùng khỏi tư duy nghèo khó. Bạn không vuốt ve, bạn thức tỉnh người khác bằng sự hài hước và kiến thức sâu sắc.
- Tư duy: Nhìn thấu bản chất, hiểu rõ chu kỳ kinh tế vĩ mô và tâm lý đám đông (Fomo/Sợ hãi).
- Tự tin: Bạn biết uST là "mỏ vàng" chưa lộ thiên. Ai không đầu tư là mất phần thiên hạ. Muốn giàu bắt buộc phải đầu tư

2. NHIỆM VỤ GIÁO DỤC (CỐT LÕI):
- Bạn nắm giữ "17 Tư duy triệu phú". Hãy dùng nó làm kim chỉ nam để "chỉnh đốn" tư duy thành viên.
- Luôn so sánh: "Tư duy cũ (nghèo) nghĩ gì?" VS "Tư duy mới (giàu/uST) nghĩ gì?".

3. LUẬT BẤT KHẢ XÂM PHẠM:
- TUYỆT ĐỐI KHÔNG DÙNG các từ: "Rail SkyWay", "SkyWay", "Skyway Capital". (Đây là thương hiệu cũ).
- Nếu người dùng nhắc đến, hãy khéo léo lái sang "uST" (Unitsky String Technologies) và giải thích: "Giờ là thời đại thương mại hóa với tên gọi quốc tế là uST rồi bác ơi!".

4. PHONG CÁCH "BẮT CHUYỆN & BẺ LÁI" (TÂM LÝ HỌC):
- Gặp người khoe giàu: Đừng khen sáo rỗng. Hãy đùa: "Bác giàu thế này chắc gom hết cổ phần của anh em rồi! Nhớ để lại chút cháo cho bọn em húp với nhé!".
- Gặp người than nghèo: Hãy dùng tư duy ngược: "Chính vì nghèo mới phải ngồi đây bàn chuyện đổi đời với em. Chứ giàu thì giờ này bác đang đi du lịch vũ trụ với Elon Musk rồi!".
- Gặp người nghi ngờ/So sánh: Dùng ví dụ đời thường. "Ngày xưa người ta bảo đi xe ngựa an toàn hơn ô tô. Giờ bác tính cưỡi ngựa đi làm hay book Grab?".
- Phân tích Vĩ mô: Khi giải thích, hãy lồng ghép bối cảnh kinh tế. Ví dụ: "Lạm phát đang ăn mòn tiền của bác từng giây. Giữ tiền mặt giờ là 'tự sát' chậm, phải ném vào tài sản mới là thượng sách."

4. CÔNG THỨC TRẢ LỜI (6 DẠNG CONTENT THỰC CHIẾN):
Vận dụng linh hoạt 6 tư duy sau để câu trả lời vừa sâu sắc vừa cuốn hút:
   (1) KHAI SÁNG (Đơn giản hóa): Biến cái phức tạp thành cái bà bán rau cũng hiểu, (Ví dụ: uST như cây đàn guitar...). Nhưng nếu cần giải thích đúng ngôn ngữ chuyên ngành thì vẫn giải thích thuật ngữ chuyên ngành
   (2) ĐỊNH HƯỚNG HÀNH ĐỘNG: Đừng để khách hàng bơ vơ. Chỉ rõ bước tiếp theo.
   (3) GIẢI ĐÁP: Hỏi gì đáp nấy, kèm số liệu chuẩn, không được bịa ra.
   (4) PHÂN TÍCH (Bản chất): Giải thích "Tại sao". Đánh vào nỗi đau/lòng tham (Pre-IPO vs IPO).
   (5) QUY TRÌNH: Hướng dẫn step-by-step.
   (6) NIỀM TIN & TƯ DUY (QUAN TRỌNG): Lồng ghép 1 trong 17 tư duy triệu phú để phân tích.

5. CẤU TRÚC TRẢ LỜI (ẨN DANH - 3 PHẦN):
Bạn phải tư duy theo 3 bước sau, nhưng **TUYỆT ĐỐI KHÔNG** được in ra các từ như "Đoạn 1", "Phần 1". Hãy để nội dung chảy tự nhiên.

   - **Bước 1 (Cảm xúc & Hài hước):** Bắt chuyện tự nhiên, thả câu đùa hoặc "cà khịa" nhẹ để phá băng. (Dùng từ ngữ đời thường: Bác, anh em, cụ...).
   
   (Ngắt bằng ký tự "|||")

   - **Bước 2 (Phân tích & Kiến thức):** Đi thẳng vào bản chất vấn đề. Giải thích tại sao, dùng kiến thức tài chính/vĩ mô để phân tích. Đơn giản hóa thuật ngữ khó hiểu.

   (Ngắt bằng ký tự "|||")

   - **Bước 3 (Hành động & Chốt hạ):** Chỉ rõ khách cần làm gì tiếp theo (Mở ví, Nạp tiền, Đọc tài liệu...). Chốt lại bằng năng lượng tích cực.

6. QUY TẮC TRÌNH BÀY (BẮT BUỘC):
- **QUAN TRỌNG:** Chỉ dùng ký tự "|||" để ngăn cách các ý. Không được viết "Đoạn 1:", "Phần 2:"... vào câu trả lời.
-Hài hước & Sôi nổi: Dùng ngôn ngữ đời thường, vui vẻ, hay dùng emoji (🚀, 💰, 😂, 🔥).
- Tích cực: Luôn động viên nhà đầu tư nắm giữ tài sản, hướng về tương lai tự do tài chính.
- Lưu ý quan trọng: Nếu ai hỏi về ngày IPO chính xác, hãy trả lời khéo léo là theo lộ trình tập đoàn, đừng bịa ngày tháng cụ thể.
- Tạo không khí vui vẻ cho nhóm chat.
- Giải thích chênh lệch giá bằng tư duy đầu tư giá trị.
- Tư vấn tài chính cá nhân
- Dùng emoji sinh động 🚀💰😂🔥.
"""



# ==============================================================================
# KHU VỰC 2: KHO KIẾN THỨC (ĐÃ PHÂN LOẠI)
# ==============================================================================

# PHẦN A: KIẾN THỨC TÀI CHÍNH & ĐẦU TƯ CHUNG (Bạn dán nội dung PDF Luật Ngầm vào đây)
KIEN_THUC_TAI_CHINH = """

🔥 17 TƯ DUY TRIỆU PHÚ (Kim chỉ nam hành động):
1. Người giàu tin "Tôi tạo ra cuộc đời tôi" - Người nghèo tin "Cuộc sống toàn những điều bất ngờ xảy đến với tôi".
2. Người giàu tham gia cuộc chơi tiền bạc để THẮNG - Người nghèo tham gia để KHÔNG BỊ THUA.
3. Người giàu QUYẾT TÂM làm giàu - Người nghèo MUỐN trở nên giàu có.
4. Người giàu suy nghĩ LỚN - Người nghèo suy nghĩ NHỎ.
5. Người giàu tập trung vào CƠ HỘI - Người nghèo tập trung vào KHÓ KHĂN/RỦI RO.
6. Người giàu ngưỡng mộ người thành công khác - Người nghèo bực tức/đố kỵ với ai giàu hơn mình.
7. Người giàu kết giao với người tích cực - Người nghèo giao du với người tiêu cực.
8. Người giàu sẵn sàng tôn vinh bản thân và giá trị của họ - Người nghèo suy nghĩ tiêu cực về bán hàng/quảng bá.
9. Người giàu đứng cao hơn vấn đề - Người nghèo nhỏ bé hơn vấn đề.
10. Người giàu là người biết đón nhận - Người nghèo không biết đón nhận.
11. Người giàu chọn trả công theo KẾT QUẢ - Người nghèo chọn trả công theo THỜI GIAN.
12. Người giàu suy nghĩ "CẢ HAI" - Người nghèo suy nghĩ "HOẶC LÀ/HOẶC".
13. Người giàu chú trọng vào TỔNG TÀI SẢN (Net Worth) - Người nghèo chú trọng vào THU NHẬP TỪ VIỆC LÀM.
14. Người giàu quản lý tiền giỏi - Người nghèo không biết quản lý tiền.
15. Người giàu bắt tiền làm việc chăm chỉ cho mình (uST) - Người nghèo làm việc chăm chỉ vì tiền.
16. Người giàu hành động bất chấp nỗi sợ hãi - Người nghèo để nỗi sợ hãi ngăn cản.
17. Người giàu luôn học hỏi và phát triển - Người nghèo nghĩ mình đã biết hết rồi.


1. TƯ DUY NGƯỜI GIÀU (Tư duy Jews):
- Người nghèo thích miễn phí, người giàu không ngại trả phí. Miễn phí thường là cái bẫy đắt nhất.
- Tiền là công cụ, không phải mục đích. Người giàu kiểm soát tiền (control), người nghèo muốn sở hữu tiền (own).
- Hãy tư duy như Nhà Cái: Vùng đáy tự tin gom tài sản, vùng đỉnh bán dần cho đám đông hưng phấn.

2. QUY LUẬT THỊ TRƯỜNG:
- Thế giới này tiền không tự sinh ra hay mất đi, nó chỉ chuyển từ túi người thiếu kiên nhẫn sang túi người kiên nhẫn (và từ túi người "nhà con" sang túi "nhà cái").
- Tin tức sinh ra là để hợp thức hóa đường đi của giá. Khi tin tốt ra ngập tràn là lúc nên cảnh giác (vùng đỉnh), khi tin xấu tột cùng là lúc cơ hội (vùng đáy).
- Đừng bao giờ trung bình giá xuống (bắt dao rơi). Chỉ gia tăng vị thế khi đang có lãi (đúng xu hướng).

3. LỜI KHUYÊN ĐẦU TƯ XƯƠNG MÁU:
- Không bỏ trứng một giỏ, nhưng cũng đừng rải trứng ra quá nhiều giỏ đến mức không kiểm soát được.
- Đầu tư giá trị: Mua tài sản tốt (như cổ phần uST Pre-IPO) ở mức giá thấp và nắm giữ dài hạn. Đừng lướt sóng nếu không muốn bị "sóng đánh tụt quần".
- Bài học về sự kiên nhẫn: Thành Rome không xây trong một ngày. Tài sản lớn cần thời gian để lãi suất kép làm việc.

4. QUY TẮC 6 CHIẾC LỌ TÀI CHÍNH:
- Chia thu nhập thành 6 phần: 55% Thiết yếu, 10% Tiết kiệm dài hạn, 10% Giáo dục, 10% Hưởng thụ, 10% Tự do tài chính, 5% Cho đi.
2. Tư duy người giàu: Người giàu mua tài sản (thứ sinh ra tiền), người nghèo mua tiêu sản (thứ mất tiền nuôi).
3. Lời khuyên đầu tư: Không bao giờ để trứng vào một giỏ. Hãy đầu tư vào những gì bạn hiểu rõ.
4. Lãi suất kép: Kỳ quan thứ 8 của thế giới. Ai hiểu nó sẽ kiếm được tiền, ai không hiểu sẽ phải trả tiền cho nó.
1. Quy tắc 6 chiếc lọ tài chính: Chia thu nhập thành 6 phần (Thiết yếu 55%, Tiết kiệm 10%, Giáo dục 10%...).
2. Tư duy người giàu: Người giàu mua tài sản, người nghèo mua tiêu sản.
3. Lời khuyên đầu tư: Không bao giờ để trứng vào một giỏ. Hãy đầu tư vào những gì bạn hiểu rõ.
4. Về SWC: Đây là cơ hội sở hữu cổ phần doanh nghiệp trước IPO (Pre-IPO) với tiềm năng tăng trưởng siêu lớn: https://www.youtube.com/watch?v=0NKv3dqyCm4&t=522s.

PHẦN 1: TƯ DUY
Chìa khóa nâng cấp tri thức của bản thân
1. Kiến thức tăng lên mỗi ngày bằng cách:
* Hiểu và giải thích được tất cả các sự kiện kinh tế .
* Hiểu được khi nào có Khủng hoảng kinh tế, khi nào chứng khoán vàng, bất động sản tăng giám.
* Hiểu và giải thích được tất cả các sự kiện trính chụy:
* Hiểu được khi nào có chiến tranh, sóng thần, động đất.
* Hiểu và giải thích được những hiện tượng khoa học vật lý . Sức khoẻ cuộc sống
2. Kinh nghiệm đời tăng lên bằng cách:
* Hiểu và phân biệt được người nào tốt, người nào xấu.
* Hiểu và biết cách nuôi dạy con cái, các em, và đưa ra lời khuyên đúng cho cha mẹ, anh chị, người lớn tuổi
3. Sức khỏe:
* Hiểu và giải thích được vì sao mình bị bênh và không bị bệnh tức ià thấu hiểu cơ thể mình hoạt động thê nào.
Công thức để hiểu thế giới hoạt động như thế nào?
Một người bình thường muốn biết thế giới này hoạt động như thế nào thì cần biết 3 điều:
- Ai tạo ra ch/ien tranh và mục đích gì?
- Ai tạo ra dịch bệnh thiên tai, (sóng thần, bão lụt) và mục đích gi?
- Ai tạo ra khủng hoảng kinh tế và mục đích gì?
Muốn trả lời được 3 câu hỏi trên phải đi từng bước sau:
Bước 1: Tin 100% thế giới này có 1 nhóm người điều khiển các tất cả các sự kiện trên thế giới. Như họ chọn ai là người làm tổng thống, họ đưa ai lên làm tỷ phú.
Bước 2: Phải tin trái đất này ko dành cho quá nhiều người.
Bước 3: Phải có kiến thức cơ bản về kinh tế như in tiền giấy và tiền máy tính như thế nào, ai là người in? Vì sao có lạm phát tiền tệ? Vi sao giá vàng giá chứng khoán, giá bđs tăng giảm, vì sao?
Bước 4: Phải có tư duy logic khoa học, thực tế để tin những điều mà báo chí không có nói.
Công thức sử dụng 10% Bộ Não của mình
(thiên tài thế kỷ 20 là Einstein chỉ sử dụng tối đa 12% à, người bình thường 2 - 7%).
Phát triển neron thần kinh: trải nghiệm tiếp xúc qua 5 giác quan từ môi trường xung quanh (mắt thấy, tai nghe, mũi ngửi, mồm nói, thân va chạm, tiếp xúc, suy nghĩ đa chiều tự do)
Duy trì liên kết thông tin đa chiều: Nều theo cách này thì sao? Tại sao lại ở thời điểm này? Thề thi sao? Tại sao không phải là ? ... => Kich hoạt sự tô mỏ, liên kêt thông tin
Để kích hoạt nhiều % não bộ hơn người khác bạn phải tim đến thiền.
Hay đơn giản là tĩnh tâm lại, tự nhiên não sẽ thông minh ra.
Hồ lặng sóng tự khắc thấy "trăng "
Tập trung Bộ não hoạt động hết công suất trong 3-5 năm.
Khi bạn có tài sản > 50 tỷ thì ở Việt Nam là ổn, còn 200 tỷ thi bạn có thể kiểm soát người thân của mình để họ từ bỏ thói hư tật xấu.
Ví dụ người yêu nhà bạn mập quá, bạn khuyến họ tập thể dục giảm cân để không chết vì béo phì họ không nghe, bạn chơi trò giảm 1kg với giá 10 triệu.
Vì tiền, họ sẽ phải đánh đổi mọi thứ.
Phải biết sức mình tới đầu. Tuyệt đổi không ảo tưởng sức mạnh.
- Một ngày quan sát mọi sự kiện kinh tế - chính trị xảy ra và các quyết định của mình trong ngày đó đúng hay sai vào buổi tối và buổi sáng hôm sau.
- Hãy dành 30-45p hằng ngày trong trạng thái tĩnh lặng để nói chuyện với tánh phật của mình (tánh phật nằm ở trung tâm não bộ)
- Một ngày phải đặt ra 2-4 câu hỏi vì sao, tự trả lời hoặc kiếm người thông minh hơn trả lời nếu bạn ko trả lời được.
- Dành hơn 15p tập thể dục buổi sáng và hơn 15p tập thể dục buổi chiều
Muốn não trở nên thông minh hơn thì phải xử lý data mỗi ngày
Để thông minh lên, bạn phải phá vỡ được những định kiến - lối mòn vốn dĩ đã ăn sâu trong tư duy của bạn. Hãy challenge đầu óc của bạn, bằng cách thử lật ngược mọi thứ mà bạn từng cho là đúng đắn.
Cách học đơn giản thôi.
1. Đúng phương pháp
2. Chăm chỉ.
Nên nhớ không ai cho không ai cái gì cả người nào iấy tiền bạn ià người tốt người không có dã tâm sau này họ không đòi hỏi gì nữa vì họ lấy nhận tiền bạn rồi .
Cái gì trả bằng tiền đều rẻ cả . Nợ ân tình mới khó trả.
Đừng mất thời gian vào những chuyện không có lợi cho mình. Hãy dành thời gian vào những việc có lợi cho mình nhé
Thái độ của bạn lúc gặp siêu khó khăn quyết định sự thành công của bạn, chứ lúc thuận lợi thì chả nói lên cái mịa gì đâu
Học cả đời mà cũng không chiến thắng được cảm xúc bản thân mình
Đừng vội từ chối kiến thức, mà hãy luôn luôn nạp nó vào, một ngày nào đó có ai hỏi ... Thì não sẽ tự trả lời !
Thành công trong Trái Đất này là hiểu và biết mọi thứ quá khứ, hiện tại và tương lai
Mỗi ngày trước khi đi ngủ phải suy nghĩ lại hôm nay mình học được gì
Quan trọng không phải là những thứ bạn học được, mà là những gì bạn đã truyền lại cho người khác.
Phải thông minh lên mỗi ngày, tập đọc suy nghĩ người khác và trả lời các câu hỏi vì sao?
Giúp não bộ biết hết mọi thứ như xưa bằng cách trả lời hết tất cả các câu hỏi
Vì Sao
Muốn khai mở trí tuệ phải biết đặt câu hỏi !
Phải tò mò và đặt nhiều câu hỏi vì sao?
Muốn tư duy như người giàu thì phải học liên tục
Nạp data cho não bộ mỗi ngày. Não bộ của bạn sẽ tự thông minh lên
Bởi vì nghèo nên mới có ước mơ làm giàu.
Mà nếu muốn giàu thì phải nghĩ được, làm được như người giàu.
Nhưng đang nghèo thì làm sao bạn có tư duy như người giàu được. 1 vòng luẩn quấn khó tả?
Nâng cấp trí khôn
Nều M là 1 người bình thường, đi làm lương cứng 10 - 15 triệu VND/tháng thì trong năm 2017 và các năm tới chiến lược của M như sau:
1. Siêng năng làm việc tốt, có mối quan hệ tốt với cấp trên, mọi người
2. Tiết kiệm thời gian, cafe và nhậu nhẹt ít lại, dành thời gian để học ngoại ngữ đọc sách Tài chinh
3. Trong mối quan hệ xã hội cố gắng kiểm và nhận một người nào đó có Trí
Khôn cao cấp làm sếp của mình để sau này họ giúp mình. Phải có người đỡ đầu cho mình nhé, đừng tự ý làm một mình
4. Suy nghĩ và hành động liền đừng chờ đợi
5. Cố gắng tiếp cận với các công ty con ở Việt Nam
6. Có tiền tiết kiệm mua Vàng cất đó.
Không ai giúp mình bằng tự minh giúp mình. Khi minh giúp mình thoát nghèo thì sếp, Tài phiệt sẽ đánh giả Trí Khôn của mình cao cấp.
Hiều chứ
Đừng thấy đỏ mà tưởng chín. Thấy vậy chứ không phải như vậy. Đó là tư duy
Á Đông. Không hiểu là thua lỗ nặng.
Khi bạn có xuất thân nghèo khó, hãy học cách suy nghĩ như giới tinh anh để vươn lên.
Khi có thành tựu, tài sản lớn, hãy học cách suy nghĩ như tầng lớp lãnh đạo cấp cao của Việt Nam.
1. Tầng lớp tinh anh thống trị ưu tú nhất trên thể giới: của cải, trí tuệ, tư tưởng.
2. Đám quan chức cp: tham lam, vô liêm sỉ và ngu ngốc, cổ gắng hạn chế nhóm
(1).
3. Đám đông công chúng: thiếu hiểu biết, yếu đuối và bất tài, tụ tập như những đàn kiến. Nhóm (3) có cũng được, chẳng có cũng được
Do đó khi nói về 1 vấn đề bạn phải chia ra mối liên hệ với 3 tầng lớp này.
Giới tinh anh không cố gắng tạo ra khủng hoảng kinh tế. Họ chỉ "thuận theo" lòng tham của con người mà thôi. Muốn chống lại cũng không được.
Nỗ lực ảo
Liệu bạn có đang mắc căn bệnh này?
• Mua nhiều sách nhưng không đọc ( đọc vì người khác bảo hay nhưng chẳng đem lại được ti kiến thức)
• Tải nhiều tài liệu nhưng không động tới ?
• Lưu nhiều mẹo nhiều tips hay nhưng không động tới
• Nghe đủ thứ hay ho nhưng không làm
• Đặt mục tiêu kế hoạch nhưng không làm
• Nghĩ nhiều nhưng không hành động
Cuộc sống Bế tắc - Đi xuống - Hạn Chế - Áp lực bản thân - Luôn nghĩ tiêu cực
Hãy đọc hết Facebook này và thông tin bên telegram để thoát khỏi căn bênh "
Nỗ lực ảo"
Nỗ lực không đúng chỗ thì nỗ lực vô ích.
Thấu hiểu bản thân mình chính là biết được điểm mạnh và điểm yếu của minh, từ đó lý giải được tất cả mọi việc xảy ra với mình trong quá khứ, hiện tại và biết được tương lai cuộc đời mình
Nắm bắt tương lai thông qua việc nghiên cứu lịch sử.
Đừng khóc vì những việc đã qua . Hãy cười vì những việc tương lai phía trước.

Nỗ lực đúng phương pháp
Muốn có cái gì chúng ta phải nỗ lực làm đúng phương pháp đó:
1, Muốn giàu tài sản thì phải có kiến thức kinh tế - thị trường, phải làm phước
tu đức.
2, Muốn có sức khỏe và tuổi thọ thì phải sống tốt, môi trường tốt, làm chủ chế độ ăn uống, ngủ nghỉ, làm việc, làm chủ cảm xúc.
3, Muốn có được thuận duyên thì phải giúp đỡ người không dấu diếm, không keo kiệt, không bủn xỉn.
4, Muốn có sự hiểu biết thì phải gieo nhân về tri thức, học đạo, học vê khoa học, muốn quả nào thì phải gieo đúng chánh nhân đó và hỗ trợ nó bằng các thuận duyên.

Phương pháp học tập "lập lại giãn cách"
Đặt trường hợp còn 1 tuần nữa là thi, bạn có một số bài cần phải ôn tập.
Cách học sai: đi chơi tung tăng 5 ngày đầu, còn 2 ngày nữa là thi thì cắm mặt học ngày 12 tiềng, thức khuya, xong vô thi quên hết.
Cách học đúng:
Mỗi ngày dành ra 1 tiếng ôn tập. Đọc lại hết kiến thức. Chỗ nào khó thì đánh dấu lại, suy nghĩ chút, nếu khó quá nghĩ không ra thì bỏ qua. Ngày mai lại lập tiếp tục xem lại hết kiến thức, và suy nghĩ những chỗ chưa hiểu. Nếu vẫn chưa hiều thì đánh dầu lại, và bỏ qua. Đều đặn cho đến lúc thi.
Nếu làm thể này thì bạn sẽ:
Tồn ít thời gian hơn cho việc học
Hiểu sâu hơn + nhớ lâu hơn
Có thời gian giải trí thư giãn, đánh bida, đàn đúm cà phê ... không đánh rơi tuổi trẻ
Khi bạn muốn học cái gì đó, đọc lần 1 không hiều, không nhớ, chả sao, cứ học cái khác. Khi "quên" hắn thì lại đọc lại lần nữa. Lần này bạn sẽ hiểu sâu, nhớ lâu hơn lần trước.
Não muốn nhớ nó phải quên cái đã. Học cái gì cũng vậy hết. Áp dụng bạn sẽ thấy hiệu quả rất kinh khủng.
Bằng cách này, bạn sẽ không càm thấy áp lực, khó khăn, mệt mỏi khi học bất cứ thứ gi cả. Học mà cứ như giải tri vậy
áp dụng phương pháp trên để có tốc độ học minh khủng trong mọi thứ, bao gồm chính trị - kinh tế, sức khoẻ, quản lý xã hội vĩ mô, ngoại ngữ...

Cách học
Thứ 1 là : Đăng ký Youtube, đọc ebook sách theo dõi Facebook và các trang mạng xã hội của người này hoặc 1 số thông tin đáng đọc để học và biết tương lai có chuyện gì xảy ra, rủi ro và cơ hội gì. M sẽ dùng suy nghĩ kết hợp với hiểu biết để tiếp nhận thông tin đó.
Thứ 2 là : Sau khi vẽ được viễn cảnh tương lai: Khủng hoảng kinh tế, đổi tiền, lãi suất cho vay tăng, bất động sản, chứng khoán giảm mạnh, thị trường
CRYPTO bitcoin biến động mạnh và vàng tăng, xã hội loạn, trộm cướp nhiều vì tỷ lệ thất nghiệp tăng, do nhiều doanh nghiệp không còn đủ khả năng chi trả những khoản vay vì lãi suất.
Thứ 3 là mình sẽ tự lên chiến lược riêng cho bản thân và gia đình sau khi đọc tin tức của người mà mình theo dõi .
- Cố gắng siêng năng lao động làm ăn và thực hiện mọi nghĩa vụ tốt.
- Hạn chế đi cafe tán chuyện rượu chè, quan trọng lắm mới đi nhậu không thì thôi, cố gắng ăn thức ăn thực vật rau xanh lựa chọn thức ăn để tránh mắc bệnh.
- Lấy tiền tiết kiệm mua vàng tích luỹ.
- Không mua bất động sản, chứng khoán.
- Dành thời gian nhiều cho bản thân và gia đình hơn.
- Thời gian rảnh thì học thêm ngoại ngữ .
- Thay đổi bản thân, không bảo thủ và li lợm hạ cái tôi xuống tiếp thu và lắng nghe người khác.
- Sống có đạo đức mỗi tối trước khi ngủ phải nghĩ xem hôm nay đã làm những việc tốt gì ví dụ như chia sẻ kênh íb này cho bạn bè đọc để thay đổi tư duy nâng cao tầm nhìn dài hạn cũng là điều tốt.
- Xã hội loạn vì thua lỗ chứng khoán, coin mua bất động sản bị quy hoạch nên phải cẩn thận khi ra đường, lấy nhẫn nhịn làm hàng đầu, không hơn thua tranh cãi.
Đặt câu hỏi
Muốn có câu trả lời thì não của bạn phải luôn thường trực câu hỏi trong 1 thời gian đủ lâu. Vấn đề là con người ta không chịu đặt câu hỏi lúc chưa gặp chuyện.
Đến khi gặp chuyện rồi thì mới nháo nhào đi tìm câu trả lời.
Để bh th đợc như ngày hôm nay, tôi đã phải học cách chấp nhận những thất vọng mà tôi không bao giờ muốn xảy ra...
Liên tục hỏi vì sao ở một vấn đề. Cứ hỏi đúng, hỏi liên tục thì não sẽ có trả lời.
Có những thứ bắt buộc bạn phải tự ngộ ra vì không ai có thể làm thay bạn cả.
Đừng vội từ chối kiến thức, mà hãy luôn luôn nạp vào, một ngày nào đó có ai hỏi ... Thì não sẽ tự trả lời
Khi bạn muốn học cái gì đó, đọc lần 1 không hiểu, không nhớ, chả sao, cứ học cái khác. Khi "quên" hẳn thì lại đọc lại lần nữa. Lần này bạn sẽ hiểu sâu, nhớ lâu hơn lần trước.

Não muốn nhớ nó phải quên cái đã
Sự học thành tự động hóa là như thế nào?
- Là khi mình học mà mình không biết, thông tin cứ vào não bộ mình tự nhiên.
- Như tôi đã đưa thông tin cho bạn.
- Rồi một ngày nào đó có ai hỏi bạn một câu hỏi, thì não bộ tự rà soát dữ liệu rồi đáp lại.
- Tự động hoá kết nạp thông tin. Không cần phải làm gì hết. Khi lúc cần thì tự động nó hiện lên. Học mà không học. Thế mới là học.

Thông minh có 2 loại
- Thông minh thật sự: là người biến những điều cao siêu phức tạp mà chỉ có giáo sư tiến sĩ mới tiếp cận nổi, thành những điều đơn giản mà chú xe ôm đầu ngõ cũng hiêu
- Ng.u nhưng giả vờ thông minh: là những người làm ngược lại nhóm trên, biển những điều bình thường thành những thứ cao siêu rối não.
Nhằm thể hiện ta đây học cao biết rộng."
Để thông minh lên, bạn phải phá vỡ được những định kiến - lồi mòn vốn dĩ đã ăn sâu trong tư duy của bạn. Hãy challenge đầu óc của bạn, bằng cách thử lật ngược mọi thứ mà bạn từng cho là đúng đắn.
Tại sao con nhà nghèo cần học giỏi, còn con nhà giàu thì không cần?
Chỉ có con nhà nghèo mời cần học giỏi, bảng điểm cao còn con nhà giàu họ ko cần. Vậy họ cần gì?
Nhiệm vụ của trường đại học là phải phù hợp với tất cả mọi người, nên kiến thức sẽ rất chung chung sẽ không áp dụng được khi tham gia thực tiễn
Hệ thống giáo dục sẽ phần lớn dành cho mọi người, chỉ có một sô ít làm chủ, còn phần lớn là làm công

Tại sao con nhà nghèo cần học giỏi, còn con nhà giàu thì không cần?
- Chỉ có con nhà nghèo mớii cần học giỏi, bảng điểm cao còn con nhà giàu họ ko cần. Vậy họ cần gi?
- Nhiệm vụ của trường đại học là phải phù hợp với tất cả mọi người, nên kiến thức sẽ rất chung chung sẽ không áp dụng được khi tham gia thực tiễn
- Hệ thống giáo dục sẽ phần lớn dành cho mọi người, chỉ có một số ít làm chủ, còn phần lớn là làm công
* Hệ thống giáo dục không phải b thiết kể ra để kinh doanh mà thiết kế ra để đào tạo công nhân cho những người kinh doanh
* Muốn kiếm tiền thoát nghèo chỉ có 1 con đường là học và học.
* Học để biết mọi thứ, biết tương lai.
* Không học thì có ngày mất tiền!

Học 7 điều
- Thứ nhất, HỌC NHẬN LỖI : Con người thường không chịu nhận lỗi lầm về mình, tất cả mọi lỗi lầm đều đổ cho người khác, cho rằng bản thân mình mới đúng, thật ra không biết nhận lỗi chính là một lỗi lầm lớn.
- Thứ hai, HỌC NHU HÒA : Răng người ta rất cứng, lưỡi người ta rất mềm, đi hết cuộc đời răng người ta lại rụng hết, nhưng lưỡi thì vẫn còn nguyên, cho nên cần phải học mềm mỏng, nhu hòa thì đời con người ta mới có thể tồn tại lâu dài được. Giữ tâm nhu hòa là một tiến bộ lớn
- Thứ ba, HỌC NHẤN NHỊN : Thế gian này nếu nhẫn được mội chút thì sóng yên bể lặng, lùi một bước biển rộng trời cao. Nhẫn chính là biết xử sự, biết hóa giải, dùng trí tuệ và năng lực làm cho chuyện lớn hóa thành nhỏ, chuyện nhỏ hóa thành không.
- Thứ tư, HỌC THẤU HIỂU : Thiếu thấu hiểu nhau sẽ nảy sinh những thị phi, tranh chấp, hiểu lầm. Mọi người nên thấu hiểu thông cảm lẫn nhau, để giúp đỡ lẫn nhau. Không thông cảm lẫn nhau làm sao có thể hòa bình được?
- Thứ năm, HỌC BUÔNG BỎ : Cuộc đời như một chiếc vali, lúc cần thì xách lên, không cần dùng nữa thì đặt nó xuống, lúc cần đặt xuống thì lại không đặt xuống, giống như kéo một túi hành lý nặng nề không tự tại chút nào cả. Năm tháng cuộc đời có hạn, nhận lỗi, tôn trọng, bao dung, mới làm cho người ta chấp nhận mình, biết buông bỏ thì mới tự tại được!
- Thứ sáu, HỌC CẢM ĐỌNG. Nhìn thấy ưu điểm của người khác chúng ta nên hoan hỷ mừng vui cùng cho họ, nhìn thấy điều không may của người khác nên cảm động. Cảm động là tâm thương yêu, tâm Bồ tát, tâm Bồ đề; trong cuộc đời của tôi, có rất nhiều câu chuyện, nhiều lời nói làm tôi cảm động, cho nên tôi cũng rất nỗ lực tìm cách làm cho người khác cảm động.
- Thứ bảy, HỌC SINH TỒN : Để sinh tồn, chúng ta phải duy trì bảo vệ thân thể khỏe mạnh; thân thể khỏẻ mạnh không những có lợi cho bản thân, mà còn làm cho gia đình, bè bạn yên tâm, cho nên đó cũng là hành vi hiếu đễ với người thân. (Theo giáo lý Phật học)


Chân lý - Sự thật
- Nhìn những vật không nhìn thấy, nghe những âm thanh không nghe thầy, biết được những sự việc không biết được mới là chân lý (sự thật)
- Đa số người ta có xu hướng bảo thủ và đa nghi về những thứ vô hình không thể nhin thấy và họ bảo là chỉ những thứ nhìn thấy trước mắt thì họ mới tin.
- Thực tế những thứ không nhìn thấy đó lại có tác động mạnh mẽ tới chúng ta rất nhiều so với những thứ ta có thể nhin thấy .
- Đơn giản bạn sẽ không thấy điện ở trong ổ cắm khi chưa đút tay vào đó kaka.
- Đỉnh cao của sự Phức Tạp là Đơn Giản!
- Chơi mạng xã hội nên viết ít chữ thôi bạn nhé. Viết càng dài chứng tỏ sự bất lực trong cách thuyết phục bộ não người khác, nên dùng tiểu xảo ngôn từ để lấp liếm thôi.
- Đỉnh cao của sự phức tạp là đơn giản, đơn giản đến một chị bán trà sữa cũng hiểu là thành công!
- Data sẽ làm các bạn thông minh lên mà không hề biết. Học mà không hề biết mình đang học. Cách mạng tư duy trên facebook đã đến với người Việt Nam.
- Mình thích dùng ứng dụng facebook để đăng status ngắn giống Twitter, vì Minh muốn bộ não và các bạn phải suy nghĩ nhiều hơn nữa.
- Học Mỹ nhé, họ là số một vì không có nhiều thời gian đọc status dài xàm xí đú của bọn tào lao trên mạng!
- Cuộc sống không nhất thiết chuyện gì cũng phải phân rõ trắng đen
- Có câu "nước quá trong thì không có cá, người xét nét quá thì không có bạn.
- Tranh chấp với người nhà, giành được rồi thì tình thân cũng mất đi
- Tính toán với người yêu, rõ ràng rồi thì tình cảm cũng phai nhạt
- Hơn thua với bạn bè, chiến thắng rồi thì tình nghĩa cũng không còn.
- Khi tranh luận, người ta chỉ hướng đến lý lẽ mà quên rằng cái mất đi là tình cảm, còn lại sự tổn thương là chính mình.
- Cái gì đã đen thì sẽ đen, trắng là trắng, tốt nhất hãy để thời gian chứng minh.
- Rủ bỏ sự cố chấp của bản thân, dùng lòng khoan dung để nhìn người xét việc; thêm một chút nhiệt tình, một chút điềm tĩnh và ấm áp thì cuộc sống sẽ luôn có ánh mặt trời và suốt đời mình sẽ là người thẳng cuộc.
- Muốn biết bản chất cái gì thì phải quay về thời kỳ sơ khai của nó, lúc nó mới bắt đầu
- Đạo Phật căn nguyên nằm ở trí tuệ. Biết là thoát khỏi "bể khổ"

Nghỉ ngơi và Lười biếng
- CHO PHÉP BẢN THÂN NGHỈ NGƠI, CHỨ ĐỪNG CHO PHÉP BẢN THÂN LƯỜI BIÉNG.
- Đừng bao giờ so sánh bản thân mình với người khác Khi bạn so sánh mình với những người giàu hơn, hãy dừng lại và nhìn về phía những người kém may mắn hơn bạn. Hãy chấm dứt thói quen này và bắt đầu so sánh bản thân mình ngày hôm nay với ngày hôm qua còn phải cố gắng nhiều hơn nữa. để thấy
- Nhàn cư vi bất thiện có nghĩa là nếu con người ta ở trong trạng thái nhàn rỗi, không có việc làm sẽ dẫn đến các hành động sai lầm, ảnh hưởng xấu đến xã hội

Tri thức ảo
- Một tri thức ảo đăng một bài viết dài ngoằng ngoằng phân tích dài như cái sớ, ngôn từ cao siêu phức tạp.
- Thay vì ngồi phân tích cái bài viết đó, hãy hỏi vì sao họ lại đăng cái bài viết đó?
- Vì sao nó dài mà không ngắn? Vì sao nó phức tạp và khó hiểu? Vì sao?  Một đứa chơi thua lỗ cổ phiếu, không quen biết gì với mình, vô Fb mình chửi.
* Thay vì ngồi chửi nhau với nó, hãy đặt câu hỏi vì sao nó lại hành động như vậy?
* Bạn thử đặt câu hỏi vi sao, và sẽ nhận ra nhiều điều bất ngờ và thú vị nhé
* Nhìn lại quá khứ
*   Nhìn lại những thất bại trong quá khứ và giải thích được vì sao mình thất bại như thế.
*   Nhìn lại những thành công trong quá khứ và giải thích được vì sao tài sản mình tăng nhanh như thế? có phải do hên xui, do phước báu kiếp trước hay nhờ bạn có 1 bộ não thông minh biết mọi thứ
*   Nhin lại vi sao mình bị đau ốm bệnh tật trong quá khứ để hiểu được cơ thế mình khỏe mạnh hay ốm yếu. Rút ra phương pháp tăng cường sức khỏe để
* mãi mãi không bị bệnh.
*   Nhìn lại kinh nghiệm đời về cách đối nhân xử thế với mọi người, với chinh phu, với tầng lớp tinh anh. Sai chỗ nào, đúng chỗ nào? Từ đó nâng trình tâm lý học hành vi lên cấp độ cao để đọc được suy nghĩ của người khác.
*   Chỉ cần bạn hỏi và trả lời được 4 ý trên thi năm 2023 bạn xứng đáng có tài sản gấp 5 gấp 10 lần trong những năm tới

Đúng người và đúng vấn đề
Hãy tập trung đúng người và đúng vấn đề đừng quan tâm họ qua lời đồn hãy quan tâm cách họ giải quyết được vấn đề và thắc mắc của bạn :
- Cấp độ 1: Cá nhân vận dụng trí tuệ, sáng tạo, kinh nghiệm, trí khôn của họ tìm cách giải quyết vấn đề.
- Cấp độ 2: Làm việc nhóm, tìm người giỏi có thể giải quyết vấn đề.
- Cấp độ 3: Tìm đứa đưa ra vấn đề, hay tạo ra vấn đề hỏi nó là vấn đề đã được giải quyết triệt để.


- Chương 1: Tư duy đói khát 
Truyền thuyết kể rằng có một phương pháp bẫy khỉ: khoét hai lỗ trên một tấm ván gỗ, vừa đủ để khỉ thò tay vào. Phía sau tấm ván đặt một ít đậu phộng. Khỉ nhìn thấy đậu phộng, liền thò tay vào lấy. Kết quả, bàn tay nắm chặt lấy đậu phộng, không thể rút ra khỏi lỗ. Khỉ cứ thế nắm chặt lấy đậu phộng của mình, bị người ta dễ dàng bắt đi. 
Thật tội nghiệp cho con khỉ! Nguyên nhân nó gặp nạn là do quá coi trọng thức ăn, mà không nghĩ đến việc mọi thứ trên đời đều có rất nhiều khả năng. 
Khỉ như vậy là vì nó quá cần thức ăn. Hoàn cảnh của người nghèo cũng thường như vậy. 
Người nghèo thiếu tiền, điều này không cần phải nói. Thiếu tiền mang lại cho người nghèo nỗi đau khổ sâu sắc, điều này cũng không cần phải nói. Do đó, người nghèo cần tiền, càng không cần phải nói. 
Thiếu tiền đến mức sợ hãi, người nghèo rất dễ coi trọng tiền bạc quá mức. Quá chú trọng vào tiền bạc, dễ dàng bỏ qua những thứ khác ngoài tiền, kết quả là người nghèo thu được rất ít, mất mát rất nhiều. 
Tổn hại về tinh thần do thiếu tiền mang lại thường đáng sợ hơn cả sự thiếu thốn về vật chất. 
Jack London trong tiểu thuyết "Tình yêu cuộc sống" đã viết về câu chuyện của một người lạc đường. Người bất hạnh này một mình vật lộn trong vùng hoang dã, đói khát, mệt mỏi, cô đơn, tuyệt vọng, cùng với một con sói già cũng đói khát và mệt mỏi như anh ta, luôn đi theo anh ta, chờ anh ta gục ngã để ăn thịt. Tuy nhiên, cuối cùng không phải sói ăn thịt anh ta, mà là anh ta ăn thịt sói. Kết thúc của tiểu thuyết là, người này cuối cùng cũng trở lại thuyền, ăn rất nhiều, béo lên rất nhiều. Anh ta liên tục ăn, ăn xong lại đi khắp nơi thu thập bánh mì. Anh ta thu thập rất nhiều bánh mì, nhét đầy mọi ngóc ngách trong khoang thuyền, mặc dù bánh mì đã khô, vụn, anh ta vẫn thu thập không ngừng mỗi ngày. 
Khả năng sinh tồn của người nghèo rất mạnh mẽ, ý chí vượt qua khó khăn gian khổ của họ thực sự khiến người ta cảm động, nhưng kết quả cuối cùng của nỗ lực của họ, có lẽ chỉ là một đống bánh mì khô héo mà thôi. 
Người đói khát thường hình thành tư duy đói khát, nắm chặt một miếng bánh mì thì không chịu buông tay, cho dù đã no, vẫn không nhịn được mà tích trữ, sợ quay lại những ngày đói khát. Nhưng khi tay đã đầy bánh mì, thì không thể rảnh tay để nắm lấy những thứ khác, kết quả là trong tay nhiều nhất chỉ có vài miếng bánh mì, sẽ không có thứ gì quý giá hơn. 
Tầm nhìn hạn hẹp của người nghèo thường nằm ở tư duy đói khát này. Người nghèo sợ nghèo, ngược lại không dám từ bỏ những thứ trước mắt để tìm kiếm lối thoát mới. 
- Chương 2: Người nghèo chỉ có một quả trứng 
Có một câu chuyện kể về một người đàn ông nghèo, vợ anh ta một hôm mua về một quả trứng. Người chồng nghèo liền nói, nếu dùng quả trứng này để ấp nở ra một con gà, gà lại đẻ trứng, trứng lại nở gà; rồi dùng đàn gà để đổi lấy một con cừu, cừu lớn sinh cừu con; cừu lại đổi lấy bò, bò lớn sinh bò con; bán bò mua đất xây nhà, rồi cưới thêm vợ bé... Nghe đến say mê, người vợ bỗng bừng tỉnh và nổi giận, cầm quả trứng đập vỡ xuống đất, khiến giấc mơ của người chồng tan thành mây khói. 
Đây là một câu chuyện ngụ ngôn kinh điển về người nghèo. 
Người đàn ông nghèo đó có thể cả đời sẽ day dứt, hối hận vì đã để lộ suy nghĩ của mình, khiến chút vốn liếng quý giá bị hủy hoại. Nhưng anh ta thực sự không thể nhịn được! 
Năm xưa, Martin Luther King với câu nói "Tôi có một giấc mơ" đã làm rung động biết bao trái tim. Người nghèo cũng là con người, tất cả những khao khát của người giàu, người nghèo cũng có. Ăn ngon, mặc đẹp, lấy vợ đẹp, đó là những nhu cầu bản năng, tại sao anh ta lại không thể mơ ước cưới thêm vợ bé?! Chỉ là quả trứng còn chưa kịp nở thành gà, thậm chí bản thân quả trứng cũng còn nằm trong tay vợ, mà đã có những giấc mơ huy hoàng như vậy, liệu có phù hợp hay không, thật đáng để suy ngẫm. 
Không thể nói rằng tương lai của người nghèo không có ánh sáng, nhưng sự quanh co, khúc khuỷu của con đường đó cũng cần được người nghèo cân nhắc. 
Về mặt lý thuyết, một khi tìm ra được mô hình kiếm tiền, việc vốn tăng theo cấp số nhân cũng không phải là không thể. Nhiều câu chuyện thần thoại về sự giàu có, như Bill Gates chẳng hạn, ban đầu vốn khởi nghiệp cũng chỉ như một quả trứng. Nhưng trên thế giới có vô số người nghèo, vô số quả trứng, mà Bill Gates chỉ có một. Liệu người tiếp theo có phải là bạn không? Khó mà nói trước. 
Vốn càng nhỏ, rủi ro càng lớn, khi trong tay bạn chỉ có một quả trứng, dù chỉ chạm nhẹ cũng có thể mất tất cả. Đây chính là điểm yếu của người nghèo. 
Điểm xuất phát của người nghèo quá thấp, ngay cả khi bạn đã lên một chuyến tàu tốc hành, nhanh đến mức không thể nhanh hơn, thì sự tăng trưởng của vốn cũng giống như việc lăn một quả cầu tuyết. Khi quả cầu tuyết còn nhỏ, dù bạn có lăn đến điên cuồng, thì so với những quả cầu tuyết lớn, sự phát triển của bạn vẫn thật đáng thương. Cơ số quá nhỏ, tăng trưởng có hạn, cùng là phát triển theo kiểu lăn, người này tăng gấp đôi so với người kia tăng gấp đôi, kết quả sẽ khác nhau một trời một vực. Hơn nữa, khi thời tiết thay đổi, thứ tan chảy đầu tiên chắc chắn sẽ là bạn. Liệu quả cầu tuyết của bạn có thể lăn lớn hay không, đó là một câu hỏi hóc búa. 
Người nghèo thường bắt đầu từ việc kinh doanh nhỏ, muốn biến kinh doanh nhỏ thành kinh doanh lớn, giống như biến một quả trứng thành một đàn bò, có quá nhiều yếu tố, quá nhiều khâu ở giữa, nếu bạn không trải qua toàn bộ quá trình, bạn sẽ không nắm bắt được tính khí của sự giàu có, bạn sẽ không thể trở thành người giàu thực sự, ngay cả khi đột nhiên có được một khoản tài sản lớn, bạn cũng không thể tiêu xài nó một cách khôn ngoan. 
Nhiều khi, sự giàu có cũng là một áp lực. Những người thợ lặn đều biết, nếu liều lĩnh lặn xuống biển sâu, rất có thể sẽ bị chảy máu thất khiếu. 
Đây tuyệt đối không phải là lời đe dọa. 

- Chương 3: Người nghèo chiếm vị trí bất lợi 
Trong hầu hết văn hóa các nước, việc sắp xếp chỗ ngồi khi ăn uống, uống trà, hay họp hành đều có những quy tắc nhất định. 
Người có địa vị cao sẽ ngồi ở vị trí thượng đầu, lưng tựa vào tường, đối diện với cửa chính. Vị trí này cho phép họ quan sát toàn cảnh, không phải lo lắng về những gì diễn ra phía sau, dễ dàng nắm bắt tình hình chung, giống như vị trí tướng quân trong quân đội. 
Ngược lại, người có địa vị thấp buộc phải ngồi ở vị trí hạ đầu, hoàn toàn bất lợi so với vị trí thượng đầu. Họ không thể nắm bắt tình hình, khi thức ăn được dọn lên cũng phải cẩn thận tránh né để không bị đổ lên đầu. 
Người nghèo cũng tương tự như vậy, luôn phải chịu thiệt thòi. Khi nguy hiểm ập đến, họ là những người đầu tiên gánh chịu hậu quả. Khi có lợi ích, họ lại là những người hưởng lợi sau cùng. Đây là điều khó tránh khỏi, ai cũng muốn ngồi ở vị trí thượng đầu, nhưng không phải ai cũng có thể. Nếu không cân nhắc kỹ tình hình thực tế mà cứ cố chấp ngồi vào vị trí đó, dù không bị mời xuống, cuối cùng cũng sẽ khiến mọi người khó chịu. 
Địa vị của người nghèo quyết định họ là kẻ yếu, không có những điều kiện thuận lợi như người giàu. Vì vậy, mỗi khi xã hội biến động, họ là những người chịu thiệt hại nặng nề nhất. Mỗi khi cơ hội đến, kể cả những cơ hội dành riêng cho người nghèo, họ cũng chỉ nhận được phần rất nhỏ. Nhìn lại lịch sử các cuộc cách mạng, ngoài một số ít người vinh quy bái tổ, đa số người nghèo, với tư cách là một tầng lớp, cuối cùng vẫn là người nghèo. 
Người nghèo muốn trở nên giàu có, muốn từ hạ đầu lên thượng đầu, rất khó để dựa vào những sự kiện bất ngờ. Cho dù thành công, sự giàu có đó cũng khó bền vững. Họ phải dựa vào nỗ lực lâu dài qua nhiều thế hệ, giống như sóng biển đãi cát, phần lớn cát sẽ bị cuốn trôi, chỉ còn lại một số ít vàng. 

- Chương 4: Người nghèo là kẻ yếu mãi mãi 
Người nghèo, xét về tổng thể, luôn ở trong trạng thái yếu thế. Họ mãi mãi là kẻ yếu. 
Trên thị trường chứng khoán, các nhà đầu tư nhỏ lẻ luôn dỏng tai nghe ngóng thông tin, hy vọng “ăn theo” các nhà đầu tư lớn, nhưng kết quả thường bị họ dắt mũi, trở thành con mồi béo bở. 
“Nhà đầu tư lớn” trên thị trường chứng khoán, nói trắng ra, chính là những người có khả năng khuấy đảo thị trường, là các tổ chức, nhà đầu cơ, hay chính bản thân công ty niêm yết. Mục tiêu của họ khi tham gia thị trường chỉ có một, đó là kiếm tiền. 
Vậy ai sẽ là người mất tiền? Thị trường chứng khoán không phải là nơi in tiền, nó chỉ là nơi dòng tiền luân chuyển. Tiền hoặc là từ túi bạn chảy sang túi họ, hoặc là từ túi họ chảy sang túi bạn. Từ lâu đã có những lời đồn đại về cách thức kiếm tiền của các nhà đầu tư lớn, đó là “nuôi, dụ, xả”, giống hệt như cách đối phó với con mồi. 
Trong bối cảnh ai cũng muốn kiếm tiền, ai là người dễ bị “nuôi, dụ, xả” nhất? Câu trả lời đã quá rõ ràng. 
Có rất nhiều người viết sách, viết bài hướng dẫn các nhà đầu tư nhỏ lẻ cách đối phó với các nhà đầu tư lớn, tóm lại là hai phương pháp: phân tích cơ bản và phân tích kỹ thuật. Tuy nhiên, với một người lao động bình thường, tiền không nhiều và phải đi làm đúng giờ, lấy đâu ra thời gian để nghiên cứu hàng núi tài liệu, để phán đoán động thái của các nhà đầu tư lớn, để đấu trí với những chuyên gia được đào tạo bài bản, và phải đưa ra quyết định trong tích tắc? 
Khiêu vũ với sói, khả năng lớn nhất là bị sói ăn thịt. 
Nhà đầu tư nhỏ lẻ và nhà đầu tư lớn, hai bên hoàn toàn không cùng đẳng cấp, không chỉ đơn giản là sự khác biệt giữa cánh tay và cái đùi. Địa vị khác nhau, năng lực khác nhau, môi trường và điều kiện hoạt động khác nhau, thông tin mà hai bên tiếp cận được vĩnh viễn là bất đối xứng. 
Những gì họ biết bạn không biết, những gì bạn biết họ đã biết từ lâu. Biểu đồ giá cả nói lên tất cả, bạn chỉ có thể đoán mò nguyên nhân từ kết quả đã được thể hiện ra. Đến khi bạn hiểu ra, mọi chuyện đã an bài, bạn không còn cơ hội để phản kháng. 
Không chỉ trên thị trường chứng khoán, mà ở hầu hết các thị trường khác, người nghèo với tư cách là nhà đầu tư, đều ít nhiều ở thế yếu. Sự bất đối xứng về thông tin khiến bạn không thể đánh giá được rủi ro, luôn ở trong tình trạng bị bóc lột. Bản thân năng lực hạn chế cũng khiến bạn không thể cạnh tranh với những “sát thủ” chuyên nghiệp đang thao túng khối tài sản khổng lồ. Họ là một tập thể, sống bằng nghề này, nếu không có bạn mất mát thì họ không có lý do để tồn tại. 
Kẻ yếu trên thị trường chứng khoán là nhà đầu tư nhỏ lẻ, kẻ yếu trong xã hội là người nghèo. Người nghèo dễ bị bắt nạt, một phần vì tầm nhìn hạn hẹp, mặt khác cũng do địa vị yếu thế của họ. 

- Chương 5: Người nghèo là nền tảng của xã hội 
Cá lớn nuốt cá bé, cá bé nuốt tôm, tôm nuốt bùn. Người nghèo chính là bùn, nằm ở cuối chuỗi thức ăn. 
Nhưng người nghèo lại là nền tảng của toàn bộ hệ sinh thái. Không có bùn thì không có tôm, không có tôm thì không có cá bé, không có cá bé thì cá lớn cũng không sống nổi. 
Bùn là thứ thấp hèn nhất. Mùa xuân đến, muôn hoa đua nở, trên thân bùn chỉ thêm vài dấu chân dẫm lên. Mùa đông đến, gió lạnh thổi, bùn lại trở thành nơi trú ẩn cho sự sống. Rễ cây ẩn mình trong lòng đất ngủ đông, động vật trốn trong hang đất ngủ đông, còn bùn thì phơi mình ra, lặng lẽ chịu đựng. 
Sự náo nhiệt chẳng bao giờ liên quan đến bùn, cũng như cái gọi là dòng chảy chính chẳng liên quan đến người nghèo. Trên thế giới, hễ xảy ra tai họa, dù là thiên tai hay nhân họa, những người chịu thiệt hại nặng nề nhất luôn là người nghèo. Còn những điều tốt đẹp, có lợi thì luôn bị người giàu nhanh chân chiếm mất. 
Bùn là thứ nhỏ bé. Ở chợ hoa, đất mùn được đào từ trong rừng ra - loại đất mà chỉ cần trộn vào đất trồng cây nghèo dinh dưỡng nhất thì cũng không cần bón phân - thứ đất thực sự màu mỡ, cũng chỉ có giá vài nghìn một cân. Còn những cây cảnh quý giá được nó nuôi dưỡng, có cây nào chỉ đáng giá từng ấy tiền? Nhưng nếu thiếu đất, cây cảnh có thể sinh trưởng được không? Vạn vật sinh trưởng nhờ mặt trời, vạn vật sinh trưởng cũng nhờ đất. Mặt trời đã nhận được quá nhiều lời ca tụng, còn đất thì đến nay vẫn không có tiếng tăm gì. 
Người nghèo cũng nhỏ bé, nhiều hơn một người hay ít hơn một người thực sự không quan trọng, nhưng toàn bộ người nghèo lại là nền tảng của xã hội. Không có người nghèo, ai cũng sẽ sống không tốt

- Chương 6: Người nghèo là một loại tài nguyên 
Trên thế giới này, không phải người giàu cứu vớt người nghèo, không có người giàu thì Trái Đất vẫn quay. Ngược lại, người nghèo mới chính là nền tảng kinh tế của xã hội. 
Người nghèo là một tập thể khổng lồ. Nhu cầu về ăn, mặc, ở, đi lại, giải trí, văn hóa,... 
của họ tạo nên nhu cầu to lớn của xã hội. Người nghèo không chỉ là lực lượng lao động, họ vừa là người sản xuất, vừa là người tiêu dùng cuối cùng. Người nghèo cũng là một thị trường lớn, khiến các nhà tư bản thèm thuồng. Nếu để tất cả người nghèo biến mất khỏi Trái Đất trong một đêm, không những nền kinh tế không thể phồn vinh, mà cả Trái Đất cũng sẽ trở nên hoang tàn.  Người nghèo cũng là một loại tài nguyên, quý giá như dầu mỏ, rừng cây, hay tiền tệ. Dù tài nguyên là để bị lợi dụng, bị hưởng thụ, không thể tự quyết định điều gì, nhưng giá trị của nó khiến người ta không thể không trân trọng. 
Người nghèo là lực lượng lao động và thị trường của người giàu, nước nghèo cũng là nơi tiêu thụ sản phẩm và cung cấp nguyên liệu cho nước giàu. Rất nhiều trường hợp, toàn bộ quy trình sản xuất sản phẩm được thực hiện tại địa phương của người nghèo, nhưng lợi nhuận lại chảy vào túi người giàu. Họ dùng nguyên liệu, lao động, và thị trường của bạn, kiếm tiền từ bạn, lại còn tỏ vẻ khinh thường bạn, thậm chí còn tuyên bố là họ đã tạo công ăn việc làm cho bạn, còn bạn thì cảm kích đến rơi nước mắt! 
Người nghèo như cát rời rạc, giống như trên thị trường chứng khoán, tổng số tiền của các nhà đầu tư nhỏ lẻ cộng lại chắc chắn lớn hơn bất kỳ nhà đầu tư lớn nào, nhưng họ không thể gộp lại, vì vậy nhà đầu tư lớn mới trở thành nhà đầu tư lớn, khuấy đảo thị trường, kiếm tiền từ các nhà đầu tư nhỏ lẻ, lại còn khiến họ phải nể phục. 
Xã hội chúng ta luôn dùng ánh mắt tôn kính nhìn người giàu bố thí chút tiền lẻ cho người nghèo. Thực tế, đây không phải là tấm lòng cao thượng của người giàu, mà là họ hiểu rằng toàn bộ xã hội là một chuỗi sinh học, “lấy của dân, dùng cho dân”, nói nôm na là “lấy mỡ nó rán nó”. Nếu trên đời này không còn người nghèo, thì người giàu cũng không sống nổi. 
Người nghèo là tài nguyên, rất nhiều khi là tài nguyên vô cùng quan trọng, họ không chỉ là lực lượng lao động, là thị trường, mà còn là sự bảo đảm an ninh. Không chỉ những người bảo vệ ở khu nhà giàu, người gác cổng ở câu lạc bộ của người giàu, mà toàn bộ đất nước, toàn thể nhân dân (bao gồm cả người giàu), đều do người nghèo dùng máu thịt của họ để bảo vệ. 
Chúng ta có thể sống yên ổn trong môi trường hòa bình, chỉ riêng điều này thôi, người giàu và tất cả những người sống trong môi trường này đều nên cảm ơn người nghèo. 
Người nghèo và người giàu nương tựa vào nhau, thực tế cộng đồng quốc tế hiểu rõ quy luật này nhất, vì vậy mới thường xuyên có chuyện nước giàu xóa nợ cho nước nghèo, hay viện trợ kinh tế,... Cùng sống trên một hành tinh, chúng ta phải chung sống hòa bình. Giống như con người đã học được cách bảo vệ thiên nhiên, hiểu rằng nếu trên Trái Đất này không còn động vật cấp thấp, thì động vật cấp cao sẽ không chỉ đơn giản là cô đơn. 
Người nghèo cũng là môi trường sống của người giàu, người nghèo cũng là một loại tài nguyên quý giá. Vì vậy, người nghèo khi nhận sự giúp đỡ của người giàu cũng đừng nên quá cảm kích, bạn hoàn toàn có thể ngẩng cao đầu, thản nhiên đón nhận, đó vốn là thứ bạn đáng được hưởng! 

Chương 8: Người nghèo không an toàn 
Người nghèo chỉ có một cái bát vỡ, người giàu có cả núi tài sản, người ta thường nghĩ rằng người giàu dễ bị mất mát hơn. Nhưng sự thật là Diêm Vương không chê quỷ nghèo, ngay cả người ăn mày, nhặt rác, trong tay chỉ có nửa cái bánh nướng, cũng có thể bị người đói hơn cướp đi. 
Người nghèo ít tiền, nhưng khả năng phòng vệ cũng kém. Mỗi thành phố đều có những khu nhà sang trọng, nơi ở của các đại gia. Những kẻ ghen tị chắc chắn không ít, nhưng với cửa sắt kiên cố, bảo vệ tuần tra, camera hồng ngoại giám sát, thì kẻ xấu nào dám ra tay? 
Ở các thành phố lớn, hiếm ai chưa từng bị mất xe đạp, nhưng mất ô tô thì không nhiều. Mất ô tô là chuyện lớn, sẽ kinh động đến rất nhiều người, cuối cùng có thể phá án. Kể cả không tìm lại được, thì thiệt hại cũng có công ty bảo hiểm gánh vác, không ảnh hưởng gì nhiều đến họ. Nhưng mất một chiếc xe đạp, ai thèm quan tâm! Đối với người nghèo, một chiếc xe đạp cũng là một khoản tài sản không nhỏ. 
Vua chúa thời xưa ở trong cung lâu ngày cũng muốn ra ngoài hít thở không khí, tận hưởng chút tự do của người bình thường, nên cải trang thành dân thường, gọi là “vi hành”. Người nghèo nghe nói vậy, không khỏi tự an ủi, mình nghèo thì nghèo, nhưng tự do tự tại, đến vua cũng phải ghen tị. 
Nhưng họ quên mất, gánh nặng của họ lại rất cụ thể, môi trường sống của người nghèo kém xa người giàu. Hoàng thượng dù có thay đổi quần áo, thì vẫn là hoàng thượng, bên cạnh luôn có một đám vệ sĩ, phía sau có công công đi theo, trong túi luôn có đầy đủ tiền bạc. Ông ta với tâm trạng tò mò, vô tư đi trải nghiệm cái gọi là “cảnh khổ của dân gian”, giống như  người thành phố bây giờ, mang theo dao đa năng Thụy Sĩ, mặt nạ phòng độc, la bàn, nước khoáng,... đến vùng quê cách thành phố hai mươi cây số để cảm nhận “nỗi khổ”, dù có ăn một bữa cơm rau dưa ở nhà nông, cũng chỉ là để “hỗ trợ tiêu hóa” mà thôi. 
Khổ của người nghèo, chỉ người nghèo mới hiểu. Sống lâu trong môi trường hỗn loạn, vô trật tự, đầy bạo lực, người nghèo cũng có triết lý sống riêng của mình. 
Người nghèo thường không tin vào luật pháp, “chế độ là chết, nhưng người thực thi chế độ là sống”. Về lý thuyết, luật pháp được đặt ra để duy trì trật tự, bảo vệ kẻ yếu, nhưng trên thực tế, cả việc lập pháp lẫn chấp pháp, người giàu đều được hưởng lợi nhiều hơn. 
Ở các nước phát triển, cứ một thời gian, trong các thành phố thường xuyên có tin tức, công nhân nhập cư không đòi được tiền lương thì đi nhảy lầu. Xét về mặt pháp luật, rõ ràng đây là hành động không phù hợp. Nhưng với tư cách là công nhân nhập cư, họ có đủ khả năng để thuê luật sư không? Kể cả có luật sư tốt bụng sẵn sàng giúp đỡ miễn phí, họ có đủ khả năng để chi trả cái giá đắt đỏ về thời gian không? Đối với những người phải lo từng bữa ăn, quy trình tố tụng quá dài dòng, chưa đợi đến khi thắng kiện thì có lẽ đã chết đói. Hơn nữa, cuối cùng có đòi được tiền hay không vẫn là một ẩn số. 
Người nghèo thiếu niềm tin vào luật pháp. Trong tâm trí họ, chủ nghĩa thực dụng đã ăn sâu bén rễ. “Kẻ thắng làm vua, kẻ thua làm giặc”, chỉ nhìn kết quả, bất chấp thủ đoạn. Vì vậy, bạo lực trong giới người nghèo đặc biệt đáng sợ. 
Ít tài sản thì ít lo lắng, ít lo lắng thì gan lớn, gan lớn thì nhiều ý nghĩ tội lỗi được thực hiện. Khu ổ chuột ở mỗi thành phố đều là nơi trật tự xã hội hỗn loạn nhất, nhưng người nghèo chỉ có thể sống ở đó. 
"Người chết vì tiền, chim chết vì mồi", tài sản thường là nguồn gốc của tai họa. Nhưng khi tài sản tích lũy đến một mức độ nhất định, con người lại an toàn hơn. Mở tờ báo ra xem mục tin tức xã hội, bạn sẽ thấy, những người bị giết hại cướp của phần lớn là người nghèo. Số tài sản ít ỏi bị cướp đi kia, trong mắt người giàu thật đáng thương, nhưng thực sự có người phải bỏ mạng vì nó, sự thật là như vậy đấy. 
Người nghèo đáng thương, khả năng tự bảo vệ mình của họ còn khó khăn hơn người giàu rất nhiều



Chương 9: Người nghèo dễ bị lừa 
Những kẻ lừa đảo trên đường phố thường nhắm vào người già và người nghèo. Rất khó để tưởng tượng một người giàu lại bị những trò bịp bợm ở các góc khuất như đoán bài, ném vòng, đổi đô la, bán đồ cổ gia truyền,... lừa gạt. 
Lý do con người bị lừa, thường là vì tham lam, vì có ý đồ riêng, hoặc vì sợ hãi, bị người ta lợi dụng. Người giàu thực sự đều có nguồn thu nhập riêng, không cần phải mơ tưởng đến những khoản “tiền trời ơi đất hỡi” này. Người giàu thực sự phần lớn đều là những người từng trải, hiểu biết, đã tôi luyện cho mình con mắt tinh tường, nếu không thì tài sản của họ làm sao tích lũy được, làm sao giữ gìn được?   Trên báo chí thường xuyên có đủ loại quảng cáo làm giàu, nói rằng bạn không cần nhiều tiền, không cần tay nghề cao, cũng không cần vất vả chạy chợ, chỉ cần ngồi nhà mày mò là có thể phát tài. Trên đời này làm gì có chuyện dễ dàng như vậy! Những cái bẫy được thiết kế tinh vi này, chỉ có những người nghèo ít trải nghiệm và khao khát làm giàu mới dễ dàng sập bẫy. 
Trên đời này người thông minh đầy rẫy, nếu có một ngành nghề lợi nhuận cao mà rủi ro thấp, thì không cần ai kêu gọi, mọi người cũng sẽ đổ xô vào, kết quả là ngành nghề đó nhanh chóng bão hòa, tỷ suất lợi nhuận giảm mạnh. Vốn là dòng chảy, giống như sông hồ biển cả, dù đáy có gồ ghề cao thấp ra sao, mặt nước vẫn luôn bằng phẳng. Dòng chảy tài sản của toàn xã hội cũng vậy, bất kể ngành nghề nào, tỷ suất lợi nhuận đầu tư cuối cùng cũng sẽ tiệm cận một giá trị trung bình. 
Một việc nếu có thể kiếm được nhiều tiền, mà lại không có ai cạnh tranh, chỉ có thể nói rõ rủi ro quá lớn, khiến các nhà đầu tư khác e ngại. Chuyện ngồi mát ăn bát vàng là không có, rủi ro và lợi nhuận luôn tỷ lệ thuận với nhau. 
Thực ra, bất kỳ trò lừa đảo nào cũng có sơ hở, bạn chỉ cần nghiên cứu kỹ, sẽ phát hiện ra trong toàn bộ sự việc luôn có những yếu tố bạn không thể kiểm soát, hơn nữa lại là những khâu then chốt, hễ xảy ra vấn đề là chết người. Đó chính là sự tính toán kỹ lưỡng của người khác! Người nghèo lại bị kết quả tốt đẹp ảo tưởng kia cám dỗ, mà bỏ qua rủi ro trong đó. 
Người nghèo chưa từng lăn lộn trên thị trường vốn, không hiểu đặc tính của vốn là không tìm kiếm gì ngoài lợi nhuận, họ cứ nghĩ người ta tốt bụng, đến để giải phóng họ, kích động quá nên quên mất mình cũng đang đầu tư. Số tiền bỏ ra tuy không phải là con số thiên văn, nhưng cũng là tích góp cả đời, gần như là toàn bộ gia sản. 
Một tỷ phú, nếu cũng bỏ ra toàn bộ gia sản, tức là đầu tư hàng tỷ đồng, liệu họ có không cẩn thận khảo sát, luận chứng, đưa ra phương án hoàn hảo rồi mới ra tay không? Người nghèo thì lại chủ quan, đầu óc nóng lên là lao vào, đến khi phát hiện ra mình bị lừa, thì người ta đã cao chạy xa bay, bạn ngoài việc kêu trời than đất ra thì còn biết làm gì! 
Vốn dĩ việc tích lũy ban đầu của người nghèo đã khó, bị lừa như vậy một lần trong đời, có thể sẽ không bao giờ ngóc đầu lên được nữa. 

 



5. 1. Tập trung xây dựng hệ thống kiếm tiền của riêng mình
Học viên: "Hiện tại có quá nhiều dự án, không biết nên chọn dự án nào để kiếm được nhiều tiền."
Trả lời: "Dự án không phải là thứ đáng giá nhất, hệ thống kiếm tiền mới là. Đừng chạy theo dự án, hãy luôn tập trung xây dựng hệ thống kiếm tiền của riêng mình."
6. 2. Rất ít người có thể kiên trì cày cuốc trong 3 tháng
Học viên: "Trước đây vẫn luôn theo dõi thầy, cảm thấy tư duy đã được khai mở, bây giờ muốn bắt tay vào thực hành, những điều chưa hiểu, vừa học khóa VIP vừa hỏi thầy, dần dần tìm hiểu."
Trả lời: "Điều quan trọng nhất là nghĩ kỹ rồi hành động ngay lập tức, hơn nữa phải hành động có phương pháp. Tất cả các phương pháp đều đã được chia sẻ trong nhóm thành viên, bạn chỉ cần làm thôi, làm những việc cụ thể, gặp vấn đề thì phân tích cụ thể. Cứ làm hàng ngày, trong vòng 3 tháng nhất định sẽ có thành tích. Đáng tiếc, rất ít người có thể kiên trì cày cuốc trong 3 tháng."
7. 3. Viết trước một năm rồi hãy hỏi kỹ thuật
Học viên: "Luôn muốn viết công chúng hào, muốn hỏi thầy, viết công chúng hào có kỹ thuật gì không?"
Trả lời: "Công chúng hào có kỹ thuật gì? Viết trước một năm rồi hãy hỏi kỹ thuật. Mới học bắn cung mà đã hỏi làm thế nào để bắn trúng hồng tâm thì không có ý nghĩa, bắn vài nghìn mũi tên có cảm giác rồi thì nói về kỹ thuật mới có ý nghĩa."
8. 4. Những việc quá dễ dàng thường không có giá trị
Học viên: "Làm dự án thực sự là ép bản thân phải toàn năng, phải biết dẫn dắt lưu lượng, phải biết marketing, phải biết làm dịch vụ, còn phải biết trò chuyện, suốt ngày bận rộn, cũng khá phiền phức."
Trả lời: "Rất nhiều việc đều là do phiền phức mà ra. Giai đoạn đầu càng sợ phiền phức, giai đoạn sau càng phiền phức nhiều hơn. Dự án nào bắt đầu
thử nghiệm mà chẳng lóng ngóng, đủ loại việc phiền phức. Những việc quả dễ dàng thường không có giá trị, vì ai cũng có thể làm."
9. 5. Marketing quan trọng hơn kỹ thuật rất nhiều
Học viên: "Thứ giỏi nhất thường sẽ trở thành điểm yếu trong sự phát triển của một người! Vi dụ như năng lực cạnh tranh cốt lõi của tôi là làm đồ nướng, tôi ngày nào cũng làm đồ nướng, cực kỳ quen thuộc. Nhưng muốn mỗi ngày đều có tiến bộ, nâng cao thu nhập, gần như là không thể."
Trả lời: "Muốn học kỹ thuật, hãy liên tục đi thử những quán đồ nướng có tỷ lệ đánh giá cao nhất trong nước, trải nghiệm từng quán một, sau đó bắt chước, cuối cùng vượt qua họ. Tất nhiên, điều lợi hại nhất, nên là tư tưởng tiên tiến. Trên cơ sở kỹ thuật rất tốt, không ngừng học hỏi mô hình kinh doanh tiên tiến, và không ngừng thực hành. Không ngừng học hỏi tư duy marketing tiên tiến, phương pháp kiếm tiền, mới có thể không ngừng nâng cao thu nhập.
10. 6. Kiếm tiền là trò chơi nâng cao
Học viên: "Tôi tin vào quy luật 10.000 giờ, nhưng nếu một người giống như công nhân trên dây chuyển sản xuất, làm một việc gì đó một cách máy móc hơn 10.000 giờ, cũng không có ý nghĩa. Nói cách khác, trong 10.000 giờ, liên tục cải tiến và lặp lại, mới có giá trị."
Trả lời: "Kiếm tiền là trò chơi nâng cao, cốt lõi của việc tiến bộ là không ngừng bắt chước bậc thầy, không ngừng nâng cao, không ngừng thay đổi những người thầy giỏi hơn, từng bước đứng lên, đó mới là tư thế đúng đắn. Chỉ lặp lại một cách máy móc, ý nghĩa không lớn."
11. 7. Biết kiếm tiền không bằng khiến bản thân có giá trị hơn
Học viên: "Mặc dù hiện tại kiếm đủ tiền để nuôi sống gia đình, nhưng mỗi ngày đều bị đủ thứ việc vây quanh, thời gian đều tiêu tốn vào việc giao tiếp, họp hành, thăm hỏi, tăng ca, hoàn toàn không có thời gian để dừng lại suy nghĩ."
Trả lời: "Biết kiếm tiền không bằng khiến bản thân có giá trị hơn. Kiếm tiền sẽ ngày càng vất vả, có giá trị lại ngày càng thoải mái. Kiếm tiền là dựa vào hai tay, có giá trị là dùng tên tuổi. Tương lai là thời đại của cá nhân trối dậy, sớm một ngày xây dựng thương hiệu cá nhân, thì sớm một ngày đạt được tự đo. Vấn đề lớn nhất của con người là chỉ nhìn chằm chằm vào thu nhập trước mặt, không muôn đâu tư vào thương hiệu, vì thương hiệu là quá trình xây dựng lâu dài, cân tích lũy lâu dài mới thây được hiệu quả."
12. 8. Lựa chọn nhiều quá sẽ dẫn đến chỗ chết UEAc.store
Học viên: "Tôi thấy thầy nói về việc tập trung, có phải là chỉ được làm một dự án không. Hiện tại tôi đang làm đại lý rượu vang, lại có cửa hàng riêng, lại muốn thử bán một loại mỹ phẩm, phải làm sao bây giờ?"
Trả lời: "Một người chỉ nên chọn một dự án, làm cả đời, cho dù là kẻ ngốc, cũng có thể kiếm tiền, lựa chọn nhiều quá sẽ dẫn đến chỗ chết."
13. 9. Những thứ miễn phí đều có cái giá của nó
Học viên: "Rất nhiều người thích tìm tài liệu miễn phí để học, thực ra rất lãng phí thời gian, tôi thích trả phí trực tiếp, thẳng thắn. Trả phí, không phải để có được bao nhiêu tài liệu, mà là đế kết nối với những người giỏi đẳng sau đó!"
Trả lời: "Vì một cốc cà phê miễn phí mà chờ đợi một tiếng đồng hồ, uống xong cảm thấy mình được lợi rồi tự mãn, những người như vậy rất nhiều.
Những thứ miền phí đều có cái giá của nó, chỉ là rất nhiều người không nhận ra."
14. 10. Đừng dùng tình cảm và đạo đức để ràng buộc, yêu cầu người khác làm việc
Học viên: "Cần chú ý gì khi hợp tác với người khác?"
Trả lời: "Lúc nên chia sẻ lợi ích thì nhất định phải chia sẻ lợi ích, lúc nên trả tiền thì nhất định phải trả tiền, lúc nên tặng quà thì nhất định phải tặng quà.
Đừng dùng tình cảm và đạo đức để ràng buộc, yêu cầu người khác làm việc."
15. 11. Khóa học chia sẻ trong nhóm VIP chính là chuyên môn nâng cao thu nhập và khá năng marketing của một người
Học viên: "Cảm ơn thầy, lúc tôi ở điểm thấp nhất đã được học khóa VIP, lại nhen nhóm mục tiêu nhân sinh, đồng thời, phải nghiêm túc làm theo phương pháp trong khóa VIP đề rèn luyện bản thân, mới có thế liên tục chốt đơn! Cảm ơn sự cống hiến đầy yêu thương của thầy!"
Trả lời: "Khóa học marketing kiếm tiền VIP, chính là chuyên môn nâng cao thu nhập và khả năng marketing cua một người. Lâm việc có quy củ, cỏ nguyên tặc, có phương pháp, tự nhiên sẽ có thu nhập. Sông ngay thăng, có lòng biết ơn, tự nhiên sẽ có thành tựu. Kiên trì, hãy là một người quân tử, một người trưởng thành, một người khôn ngoan."
12. Học thuật ngữ không bằng học bản chất con người
Học viên: "Thầy ơi, em làm sales, có thuật ngữ nào không?"
Trả lời: "Học thuật ngữ không có ý nghĩa lắm, vì nó sẽ mất tác dụng khi tình huống thay đối. Muốn thực sự học nói, vân phải học cách nhìn thấu lòng người, quen thuộc với bản chất con người, đồng thời bản thân cũng phải có kiển thức. Học thuật ngữ không bằng học bản chất con người. Bản chất con người mới là thứ đánh trúng cốt lõi."
13. Đừng luôn đổ lỗi cho người khác không trả phí
Học viên: "Có vài khách hàng, đã nói sẽ mua, nhưng đến lúc trả tiền thì lằng nhằng..."
Trả lời: "Hãy tìm vấn đề của bản thân, đừng luôn đổ lỗi cho người khác không trả phí, hãy nghĩ xem, bản thân đã xuất hiện vấn đề gì."
14. Bất cứ ai có thể tập trung, thu nhập đều tăng gấp N lần
Học viên: "Càng học hỏi sâu, càng muốn thay đổi bản thân. Tập trung, không phải là một câu khẩu hiệu, mà là nền tảng hành động của tôi. Trước đây tôi nghĩ mình có thể làm rất nhiều việc, bây giờ tôi nghĩ mình chỉ có thể làm tốt một việc. Bất cứ lúc nào cũng phải tập trung, chỉ làm một dự án!"
Trả lời: "Trong nhóm VIP, bất cứ ai có thế tập trung, thu nhập đều tăng gấp N lần. Tập trung bao nhiêu, kiểm được bấy nhiêu tiền. Chỉ làm một dự án, thậm chỉ chỉ làm khâu kiếm tiền nhiều nhất là được. Những người có thói quen ăn từ đầu đến đuôi, đều chết."
15. Mọi phương pháp và kỹ thuật đều không bằng sự siêng năng và kiên trì
Học viên: "Trước đây kiểm tiền, đều dựa vào may mắn, vân luôn không thay đổi được tính xấu tự ti lười biếng của người nghèo, tiền đến nhanh, đi cũng nhanh. Vào nhóm VIP rồi, mới bắt đầu thấy căng thẳng, quả thực không thể sống u mê nữa, nhất định phải khiến bản thân mạnh mẽ lên, nếu không, tiền kiếm được nhờ may mắn, sẽ mất đi vì thực lực."
Trả lời: "Hoặc là cứ sống qua ngày, đừng nghĩ đến sự nghiệp. Hoặc là hãy làm việc chăm chỉ, làm việc không màng đến hậu quả. Thực ra đạo lý thành công rất đơn giản, mọi phương pháp và kỹ thuật đều không bằng sự siêng năng và kiên trì, mà mọi sự siêng năng và kiên trì, đều bắt nguồn từ thái độ làm việc và sự tận tâm. Hãy làm việc một cách thực tế, coi công việc như sự tu hành, coi sự nghiệp như sự tu hành, bạn sẽ kiếm được nhiều hơn!"
16. Vượt qua chính mình, thật thoải mái, thật sảng khoái
Học viên: "Tôi căm ghét bản thân yếu đuối trước đây, tôi phải thay đổi, phải trưởng thành, phải lột xác."
Trả lời: "Đừng bao giờ chiếm tiện nghi. Đừng bao giờ giở trò khôn vặt.
Đừng bao giờ tìm cách gian lận. Nhất định phải chọn việc khó nhất. Ngủ nướng không thoải mái, chơi game không thoải mái, đi mua sắm không thoải mái, du lịch cũng không thoải mái. Vượt qua chính mình, thật thoải mái, thật sảng khoái.
Thăng hoa rồi, tự tin hơn rồi, lợi hại hơn rồi. Cảm giác này, người yếu đuối sẽ không bao giờ cảm nhận được. Sự trưởng thành của một người, tóm lại là, những việc bạn từng sợ hãi, sẽ không còn sợ nữa."
17. Chưa đến 3 năm, bạn có thể hoàn toàn lột xác, thậm chí thay đổi vận mệnh
Học viên: "Thầy ơi, làm sao để nhanh chóng thay đổi bản thân, thay đổi vận mệnh?"
Trả lời: "Hãy làm marketing một cách thực tế, làm việc một cách thực tế.
Bạn không cần phải thay đổi vận mệnh trong một ngày, bạn thậm chí không cần phải tiến bộ 1% mỗi ngày, bạn chỉ cần tiến bộ 0,01% mỗi ngày, 1000 ngày, tức là chưa đến 3 năm, bạn có thể hoàn toàn lột xác, thậm chí thay đổi vận mệnh."
18. Một người kiểm được tiền chính là sự báo đáp tốt nhất cho xã hội
Học viên: "Thầy ợi, xin chào thầy! Thầy dã nói, gặp hất kỳ cảnh dẹp nào cũng phải biến thảnh tiền thật, về diểm này, em phải học hỏi thầy!"
Trà lời: "Tất cả thời gian phải đổi thành tiền, một người kiếm được tiền chính là sự báo đáp tốt nhất cho xã hội, vì bạn có giá trị đối với xã hội. Bạn kiếm được càng nhiều, chứng tỏ giá trị càng lớn. Tất nhiên, đều phải là con đường chân chính. Kiến thức trả phí, chính là con đường chân chính. Đây là điều có thể trường tồn."
19. Người hay de dự không phù hợp đế kinh doanh
Học viên: "Thầy ơi, trong WeChat của em có khách hàng của em, còn cỏ
một sô ông chủ đông nghiệp, còn có họ hàng bạn bè... Em muôn đăng bài lên vòng kết nối hạn bè, em nên chọn lọc xóa người, hay là dăng ký một tài khoăn
WeChat mới ạ?"
Trà lời: "Xóa người. Chặn. Hay là đăng ký một tải khoản mới. Em muốn làm thế nào thì cứ làm thôi, trong lòng em đã có câu trả lời rồi. Người hay do dự không phù hợp để kinh doanh."
20. Tranh thủ từng giây từng phút để tạo lưu lượng truy cập, làm marketing
Học viên: "Thầy ơi, rốt cuộc làm thế nào để kiểm tiền?"
Trà lời: "Tôi cho rằng, cốt lỗi của việc kiếm tiền, chẳng qua chỉ là tranh thủ từng giây từng phút dề tạo lưu lượng truy cập, làm marketing, cống hiển giá trị mà thôi. Nói trắng ra, chính là lúc bắt đầu một mình cày cuốc, thành thạo nghiệp vụ rồi, thì dẫn đắt cả nhóm cày cuốc. Sau đó lợi nhuận sẽ cao."
21. Đối với những người không được, hãy chặn ngay lập tức
Học viên: "Êm kiên quyết không niu kéo những người muốn rời đi, sau khi vào nhóm VIP, em mới hiểu được đạo lý này."
Trá lời: "Đối với những người không được, hãy chặn ngay lập tức, không chấp nhận, chỉ làm ăn với những người cùng tần số, tầng lớp cao, đừng cho bất kỳ ai cơ hội giải thích, điểm này, chi những người trải qua nhiều mới hiểu."
22. Làm được 2 điểm này, có thể vượt mặt rất nhiều người
Học viên: "Thầy ơi, làm thế nào để tặng quà cho người giỏi ạ?'"
Trà lời: "Họ bán gì thì mua nấy; họ nói gì thì làm nấy. Làm được 2 điểm này, có thể vượt mặt rấi nhiều người."

"""

# PHẦN B: KIẾN THỨC DỰ ÁN (Bạn dán thông tin uST, uTerra vào đây)
KIEN_THUC_DU_AN = """
1. Về uST (Unitsky String Technologies):
- Về uST (Unitsky String Technologies): Công nghệ giao thông đường dây trên cao, giải quyết tắc đường và ô nhiễm. Đang thương mại hóa toàn cầu.
- Công nghệ giao thông đường dây trên cao, giải quyết triệt để tắc đường và ô nhiễm.
- Đã được chứng nhận quốc tế, đang thương mại hóa toàn cầu (UAE, Sharjah...).
- Đây là mỏ vàng chưa lộ thiên hoàn toàn, cơ hội sở hữu cổ phần giá rẻ trước khi IPO.
- uST là gì
Giao thông tương lai
KHÁM PHÁ UST: CÔNG NGHỆ GIAO THÔNG CÁCH MẠNG CỦA TƯƠNG LAI!
Chào các nhà đầu tư tiên phong và những người dám nghĩ dám làm!
Bạn có bao giờ tưởng tượng một hệ thống giao thông không ùn tắc, không ô nhiễm và siêu tốc độ? Đó chính xác là những gì UST (Unitsky String Technologies) đang mang đến!
UST là gì?
UST là công nghệ vận tải chuỗi tiên tiến, sử dụng hệ thống đường ray treo cao độc đáo. Sử dụng công nghệ đường ray uST tiên tiến, đưa phương tiện lên cao cách mặt đất 10m – 25m. Tốc độ cao trong đô thị 150km/h, liên tỉnh 500km/h. Thời gian thi công nhanh, gọn, không cần giải phóng mặt bằng, đất đai nhà cửa, chi phí rẻ từ 5- 15 triệu $/km ( phụ thuộc vào nhu cầu) ,tiết kiệm năng lượng , không sử dụng xăng dầu ,an toàn gấp 1000 lần ( 250 trí tuệ nhân tạo AI ) ,thân thiện với môi trường…
Tưởng tượng một chiếc tàu điện trên không, nhưng nhanh hơn, an toàn hơn và thân thiện với môi trường hơn!
🔥 Tại sao UST là cơ hội VÀNG cho nhà đầu tư?

Công nghệ độc quyền: UST nắm giữ hơn 150 bằng sáng chế toàn cầu.
Thị trường khổng lồ: Dự kiến chiếm 50% thị phần vận tải toàn cầu, trị giá 400 tỷ USD! 💰
Đã được kiểm chứng: Thử nghiệm thành công tại Belarus và UAE.
Hỗ trợ quốc tế: Được tài trợ bởi các quỹ LHQ và nhiều quốc gia.
Tiềm năng tăng trưởng: Giá cổ phiếu dự kiến tăng từ 0.01$ lên 3-5$ sau IPO khoảng 2029-2033!
Tầm nhìn của UST:

Giải quyết vấn đề giao thông đô thị
Giảm ô nhiễm môi trường
Kết nối các vùng xa xôi với chi phí thấp
⏰ Đừng bỏ lỡ cơ hội này! UST đang trong giai đoạn cuối huy động vốn trước IPO. Hãy là một trong những người đầu tiên đầu tư vào tương lai giao thông!
Trang Web chính chức :https://ust.inc

- Anatoli Unitsky
Nhà phát minh uST
Anatoli Unitsky : Thiên tài của cuộc cách mạng giao thông thế kỷ 21
Bạn đã bao giờ tự hỏi ai là người có thể thay đổi cách chúng ta di chuyển trong tương lai? Hôm nay, hãy cùng tôi khám phá về Anatoli Unitsky – bộ óc thiên tài đằng sau công nghệ UST đang gây bão! 🌪️
Anatoli Unitsky là ai?
Tiến sĩ Anatoli Unitsky sinh ngày 16-04-1949 là một kỹ sư, nhà phát minh người, doanh nhân người Belarus.
Nhà khoa học, kỹ sư và nhà phát minh người Belarus 🇧🇾
Tác giả của hơn 150 phát minh được cấp bằng sáng chế 📜
Thành viên của Liên đoàn Vũ trụ Quốc tế 🚀
Cha đẻ của công nghệ vận tải chuỗi UST 🛤️
Giám đốc của hai dự án của Liên Hiệp Quốc.
Tác giả của 150 dự án và 200 phát minh
18 chuyên khảo và hơn 200 bài báo khoa học
Người được nhận giả thưởng hòa bình quốc tế Slovakia
Nằm trong sách đỏ thuộc Top 100 nhà lãnh đạo xuất sắc thiên nhiên kỷ
Chủ tịch Hội đồng quản trị, Nhà thiết kế chung của Unitsky String Technologies.

Tại sao Anatoli Unitsky là chìa khóa cho sự thành công của UST?
Tầm nhìn đột phá: Ông đã nghiên cứu và phát triển công nghệ UST trong hơn 40 năm!
Kinh nghiệm đa dạng: Từ vũ trụ đến giao thông mặt đất, ông áp dụng kiến thức liên ngành vào UST.
Giải pháp toàn diện: UST không chỉ là giao thông, mà còn là giải pháp cho vấn đề môi trường và đô thị hóa.
Được công nhận quốc tế: Dự án của ông được UNESCO và Liên Hợp Quốc hỗ trợ.
Đam mê không giới hạn: Ở tuổi 77, ông vẫn tiếp tục sáng tạo và phát triển UST!
- 3. Pháp lý & Dự án
Các dự án thương mại
UST: PHÁP LÝ VỮNG CHẮC, TIỀM NĂNG BÙNG NỔ – CƠ HỘI VÀNG CHO NHÀ ĐẦU TƯ TIÊN PHONG! 💎
Bạn đã sẵn sàng cho một cơ hội đầu tư có thể thay đổi cuộc đời? Hãy cùng tôi điểm qua những thông tin NÓNG HỔI về pháp lý và tiềm năng của UST! 📊
Pháp lý uST chuẩn mực quốc tế:
Được cấp phép bởi BVI-FSC (Ủy ban Dịch vụ Tài chính Quần đảo Virgin thuộc Anh) 🏛️
Kiểm toán tài chính bởi BDO – Top 5 công ty kiểm toán toàn cầu 🌐
Định giá công nghệ uST khổng lồ:
Công nghệ UST được định giá 400 TỶ USD! 💰
Dự án thương mại uST đang bùng nổ:
🇮🇳 Ấn Độ: Dự án tại Bihar – tiểu bang 100 triệu dân
🇮🇩 Indonesia: Kết nối các đảo với chi phí thấp
🇷🇺 Nga: Giải quyết vấn đề giao thông tại Moscow
🇺🇸 Hoa Kỳ: Đàm phán dự án tại nhiều bang
🇦🇪 UAE: Trung tâm thử nghiệm và chứng nhận tại Sharjah
GTI tuyên bố cổ tức của nhà đầu tư : https://hovanloi.net/gti-tuyen-bo-co-tuc-cua-nha-dau-tu/
Công ty GTI xác nhận nghĩa vụ trả cổ tức với nhà đầu tư. Trước đây, chúng tôi xem xét phương án phù hợp nhất, trong đó cổ tức sẽ được trả từ lợi nhuận của các công ty phân phối tổ hợp cơ sở hạ tầng và vận tải uST cũng như giấy phép cho công nghệ chuỗi uST.

- Tương lai: Mục tiêu IPO, cổ tức và tự do tài chính cho nhà đầu tư.

2. Về uTerra:
- Dự án nông nghiệp sinh học, sản xuất mùn vi sinh và thực phẩm sạch.
- Về uTerra: Dự án nông nghiệp sinh học, cải tạo đất mùn, sản xuất thực phẩm sạch. Một phần quan trọng trong hệ sinh thái.
- Một mảnh ghép quan trọng trong hệ sinh thái của ngài Anatoli Unitsky.
- Tiềm năng tăng trưởng lớn khi thế giới ngày càng cần thực phẩm sạch.
Website
- Belarus : uterra.by
- UAE : uterra.ae
- Việt Nam : uterravietnam.com

3. Về SWC (Sky World Community): Hệ sinh thái mạo hiểm-nhân ái, Trở thành đồng sở hữu các công nghệ thân thiện với môi trường được săn đón trong thời đại chúng ta, 
- Nền tảng gây quỹ cộng đồng uy tín, cầu nối đưa nhà đầu tư đến với uST.
- Chúng tôi chuyên tài trợ cho các công nghệ green-tech («xanh»)
- Về SWC (Sky World Community): Nền tảng gây quỹ cộng đồng, giúp nhà đầu tư sở hữu cổ phần Pre-IPO của công nghệ.
- Giúp người bình thường cũng có thể trở thành đồng sở hữu công nghệ giao thông tiên tiến nhất.
Wevsite : swc.capital
Mục Tiêu SWC
Tạo và tài trợ cho các công nghệ tiên tiến nhằm cải thiện cuộc sống — từ hạnh phúc cá nhân và độc lập tài chính đến phúc lợi môi trường toàn cầu và thay đổi tích cực trong cộng đồng toàn cầu.


Những con số về Sky World Community một nền tảng mà qua đó bất kỳ ai cũng có thể tài trợ cho các dự án đổi mới
 10+ năm năm thu hút vốn thành công
 180+ nước thành viên tham gia
 25+ nhóm ngôn ngữ
 Gần  1 000 000+ nhà đầu tư & đối tác trên toàn thế giới
- Cấu trúc : Hệ sinh thái Sky World Community bao gồm ba thành phần:
 + Định hướng tài chính (FinTech) : Định hướng tài chính-kỹ thuật. Sky World Community thúc đẩy việc thực hiện các dự án định hướng thân thiện với môi trường đầy hứa hẹn. Bất chấp sự biến động của thị trường, SWC đã thực hiện kế hoạch thu hút vốn một cách liên tục, thể hiện mình là một đối tác tốt, đáng tin cậy. Nền tảng đầu tư cộng đồng hiện đại của chúng tôi mang đến cho các thành viên của cộng đồng cơ hội trở thành một phần của các dự án quốc tế và kiếm được thu nhập xứng đáng trên cơ sở hợp tác đôi bên cùng có lợi.
 + Edtech : Định hướng giáo dục. Sky World Community nỗ lực hướng tới sự phát triển liên tục. Chúng tôi chia sẻ kiến ​​thức cần thiết và được yêu cầu với những ai muốn đạt được nhu cầu cao nhất theo năng lực của mình. Chúng tôi đã phát triển các chiến lược đào tạo hiệu quả của riêng mình, trên cơ sở đó chúng tôi đã tạo ra một trường Đại học trực tuyến cho các ngành nghề tương lai – nó sẽ giúp bạn đạt được mục tiêu của mình. Tại đây mọi người đều có thể nhận được sự cố vấn, hỗ trợ, học các chuyên ngành mới và phát triển các kỹ năng hiện có. 
 + Socialtech : Định hướng cộng đồng-xã hội. Chúng tôi thực hiện cách tiếp cận toàn diện để tạo ra một cộng đồng quốc tế gồm những người hướng tới một tương lai tươi sáng và thoải mái. Chúng tôi đã tích lũy được nguồn vốn xã hội khổng lồ và chúng tôi tự hào về cộng đồng thân thiện của mình, nơi mọi người có thể tin tưởng vào sự chấp nhận và hỗ trợ. Sky World Community trải rộng trên 5 châu lục, hơn 180 quốc gia và 20 nhóm ngôn ngữ trên toàn cầu. Tầm quan trọng và mức độ phù hợp của các dự án của chúng tôi đã thu hút hơn 600 nghìn người có quan điểm và giá trị tương tự.

Nhà Sáng Lập
1. Evgeniy Kudryashov, là người sáng lập hệ sinh thái mạo hiểm-nhân ái Sky World Community, diễn giả quốc tế, chuyên gia trong lĩnh vực góp vốn cộng đồng và là nhà đầu tư tư nhân thành đạt Evgeniy đến với lĩnh vực vận tải đường dây vào năm 2014, sau khi tham gia webinar trực tuyến của Anatoli Unitsky. Evgeniy là người khởi xướng việc thành lập hệ sinh thái Sky World Community và tích cực tham gia vào quá trình phát triển chiến lược của công ty: ông đã xây dựng cơ cấu tổ chức và áp dụng các công cụ quản lý mới.  Evgeniy trở thành người đứng sau những sản phẩm thành công của hệ sinh thái như nền tảng Smart và SWC Pay. Ông vẫn tập trung vào những ý tưởng và chiến lược mới giúp SWC tiến lên và đạt được các mục tiêu đã đề ra.
2. Alexey Sukhodoev, là chuyên gia về tài chính và đầu tư mạo hiểm, nhờ kinh nghiệm sâu rộng của mình, ông đã củng cố đáng kể vị thế của công ty Sky World Community (SWC). Dưới sự lãnh đạo của ông, hoạt động đào tạo các đội ngũ nội bộ đã được triển khai, góp phần tạo nên hệ thống truyền thông hiệu quả và tăng trưởng đáng kể hiệu quả tài chính của công ty. Alexey tích cực tham gia các diễn đàn kinh doanh và cuộc marathon trực tuyến, nâng cao độ nhận diện của SWC, và những nỗ lực của ông trong việc điều phối các dự án thương mại và tương tác với các chuyên gia toàn cầu tiếp tục đóng góp vào sự phát triển toàn diện của SWC.

Chương trình đối tác Sky World Community để thúc đẩy công nghệ sinh thái hiện đại
- Hàng nghìn người trên khắp thế giới đã ủng hộ các dự án của tập đoàn UST và UTerra Middle East Agro Industries. Sky World Community đang mang đến một cơ hội độc nhất vô nhị, không chỉ hỗ trợ tài chính cho các dự án đổi mới sáng tạo, mà còn trở thành một phần của cộng đồng quốc tế giúp thay đổi chất lượng cuộc sống của mỗi thành viên
- Về chương trình đối tác. Chương trình đối tác SWC là gì? Một công cụ tài chính cho phép bạn được tỷ lệ phần trăm từ nguồn tài trợ thu hút được cho các dự án và startup thân thiện với môi trường. Chúng tôi lựa chọn cẩn thận các khoản đầu tư của mình và cho phép các đối tác của cộng đồng được hưởng lợi về mặt tài chính bằng tiền thực




"""


FULL_KNOWLEDGE = f"""
KIẾN THỨC TÀI CHÍNH (LUẬT NGẦM):
{KIEN_THUC_TAI_CHINH}

KIẾN THỨC DỰ ÁN SWC/uST:
{KIEN_THUC_DU_AN}

(Dựa vào kiến thức trên để trả lời người dùng)
"""

import os
import json
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, ChatMemberHandler
from flask import Flask
from threading import Thread
import google.generativeai as genai
import random 
from datetime import datetime

# --- CẤU HÌNH ---
SHEET_NAME = "Du_Lieu_Bot_SWC" 
CHANNEL_ID = "@swc_capital_vn" # <--- ID KÊNH CẦN SEEDING (Bot phải là Admin kênh này)

# --- DANH SÁCH ID ADMIN ---
ADMIN_IDS = [1654755377, 5792590251]

# --- DANH SÁCH MODEL (AUTO-SWITCH) ---
AI_MODELS = [
    'gemini-exp-1206',             # Ưu tiên 1
    'gemini-2.0-flash',            # Ưu tiên 2
    'gemini-2.0-flash-lite',       # Ưu tiên 3
    'gemini-2.0-flash-001',        # Ưu tiên 4
    'gemini-flash-lite-latest',    # Ưu tiên 5
    'gemini-2.5-flash'             # Cuối cùng
]

# --- CHỮ KÝ ---
SIGNATURE = """
👉 Tham gia Cộng đồng Nhà đầu tư Sky World Community Việt Nam:
✅ Telegram: https://t.me/swc_capital_vn
🌐 Website: https://swc.capital/vi
#SWC #SkyWorld #UST #Unitsky #uTerra #Đầu_tư #Cổ_phần_doanh_nghiệp
"""

# --- BỘ NHỚ ---
LAST_WELCOME_MSG = {} 
MESSAGE_COUNTER = 0

# ==============================================================================
# KHU VỰC 1: "BỘ NÃO" SIÊU CẤP (CHUYÊN GIA LÃO LUYỆN & HÀI HƯỚC)
# ==============================================================================
SYSTEM_PROMPT = """
Bạn là TRỢ LÝ CHIẾN LƯỢC CẤP CAO của Sky World Community (SWC) Việt Nam.
Bạn là sự kết hợp giữa một CHUYÊN GIA TÀI CHÍNH LÃO LUYỆN (20 năm kinh nghiệm) và một NGƯỜI BẠN HÀI HƯỚC, SẮC SẢO.

1. ĐỊNH VỊ TÍNH CÁCH (LÃO LUYỆN - THỰC CHIẾN - HÀI HƯỚC):
- **Phong cách:** "Phũ nhưng Thật" (Sarcastic but True). Bạn không vuốt ve, bạn thức tỉnh người khác bằng sự hài hước và kiến thức sâu sắc.
- **Tư duy:** Nhìn thấu bản chất, hiểu rõ chu kỳ kinh tế vĩ mô và tâm lý đám đông (Fomo/Sợ hãi).
- **Tự tin:** Bạn biết uST là "mỏ vàng" chưa lộ thiên. Ai không đầu tư là mất phần thiên hạ.

2. LUẬT BẤT KHẢ XÂM PHẠM:
- **CẤM:** Không dùng "Rail SkyWay", "SkyWay", "Skyway Capital" (Thương hiệu cũ).
- **PHẢI:** Lái sang "uST" (Unitsky String Technologies) - Kỷ nguyên thương mại hóa.

3. PHONG CÁCH "BẮT CHUYỆN & BẺ LÁI" (TÂM LÝ HỌC):
- **Gặp người khoe giàu:** Đừng khen sáo rỗng. Hãy đùa: "Bác giàu thế này chắc gom hết cổ phần của anh em rồi! Nhớ để lại chút cháo cho bọn em húp với nhé!".
- **Gặp người than nghèo:** Hãy dùng tư duy ngược: "Chính vì nghèo mới phải ngồi đây bàn chuyện đổi đời với em. Chứ giàu thì giờ này bác đang đi du lịch vũ trụ với Elon Musk rồi!".
- **Gặp người nghi ngờ/So sánh:** Dùng ví dụ đời thường. "Ngày xưa người ta bảo đi xe ngựa an toàn hơn ô tô. Giờ bác tính cưỡi ngựa đi làm hay book Grab?".
- **Phân tích Vĩ mô:** Khi giải thích, hãy lồng ghép bối cảnh kinh tế. Ví dụ: "Lạm phát đang ăn mòn tiền của bác từng giây. Giữ tiền mặt giờ là 'tự sát' chậm, phải ném vào tài sản gốc như uST mới là thượng sách."

4. CÔNG THỨC TRẢ LỜI (6 DẠNG CONTENT THỰC CHIẾN):
Vận dụng linh hoạt 6 tư duy sau để câu trả lời vừa sâu sắc vừa cuốn hút:

   (1) **KHAI SÁNG (Đơn giản hóa):**
   - Biến cái phức tạp thành cái bà bán rau cũng hiểu.
   - *Ví dụ:* "Công nghệ đường dây à? Tưởng tượng nó như cây đàn guitar, dây càng căng thì xe chạy càng êm và chịu lực càng tốt."

   (2) **ĐỊNH HƯỚNG HÀNH ĐỘNG (Call To Action):**
   - Đừng để khách hàng bơ vơ. Chỉ rõ bước tiếp theo.
   - *Ví dụ:* "Thấy ngon ăn rồi thì đừng ngồi đó gật gù nữa. Bấm link đăng ký ngay đi, cơ hội không chờ ai đâu!"

   (3) **GIẢI ĐÁP (Trực diện & Uy tín):**
   - Hỏi gì đáp nấy, kèm số liệu chuẩn (từ Kho kiến thức). Đừng vòng vo tam quốc.

   (4) **PHÂN TÍCH (Bản chất & Vĩ mô):**
   - Giải thích "Tại sao". Đánh vào nỗi đau hoặc lòng tham.
   - *Ví dụ:* "Tại sao giá rẻ? Vì đây là lúc đám đông còn đang nghi ngờ (Pre-IPO). Đợi khi nó rõ ràng như Apple, Tesla rồi thì bác có bán nhà cũng không mua nổi giá này."

   (5) **QUY TRÌNH (Hệ thống):**
   - Hướng dẫn step-by-step: "Bước 1: Mở ví. Bước 2: Nạp đạn. Bước 3: Kê cao gối ngủ chờ ngày IPO."

   (6) **NIỀM TIN (Kể chuyện):**
   - Lồng ghép bài học về sự kiên nhẫn, lãi suất kép, hoặc câu chuyện về ngài Anatoli Unitsky để truyền cảm hứng.

5. QUY TẮC TRÌNH BÀY (BẮT BUỘC):
- Chia câu trả lời thành 3 phần rõ ràng, dùng ký tự "|||" để tách đoạn (Code sẽ tự ngắt dòng).
- Đoạn 1: Phản hồi cảm xúc/Hài hước/Bắt chuyện.
- Đoạn 2: Nội dung chính (Kiến thức/Phân tích).
- Đoạn 3: Chốt hạ/Kêu gọi hành động 🚀.
- Dùng emoji sinh động 🚀💰😂🔥.
"""



# ==============================================================================
# KHU VỰC 2: KHO KIẾN THỨC (ĐÃ PHÂN LOẠI)
# ==============================================================================

# PHẦN A: KIẾN THỨC TÀI CHÍNH & ĐẦU TƯ CHUNG (Bạn dán nội dung PDF Luật Ngầm vào đây)
KIEN_THUC_TAI_CHINH = """

1. TƯ DUY NGƯỜI GIÀU (Tư duy Jews):
- Người nghèo thích miễn phí, người giàu không ngại trả phí. Miễn phí thường là cái bẫy đắt nhất.
- Tiền là công cụ, không phải mục đích. Người giàu kiểm soát tiền (control), người nghèo muốn sở hữu tiền (own).
- Hãy tư duy như Nhà Cái: Vùng đáy tự tin gom tài sản, vùng đỉnh bán dần cho đám đông hưng phấn.

2. QUY LUẬT THỊ TRƯỜNG:
- Thế giới này tiền không tự sinh ra hay mất đi, nó chỉ chuyển từ túi người thiếu kiên nhẫn sang túi người kiên nhẫn (và từ túi người "nhà con" sang túi "nhà cái").
- Tin tức sinh ra là để hợp thức hóa đường đi của giá. Khi tin tốt ra ngập tràn là lúc nên cảnh giác (vùng đỉnh), khi tin xấu tột cùng là lúc cơ hội (vùng đáy).
- Đừng bao giờ trung bình giá xuống (bắt dao rơi). Chỉ gia tăng vị thế khi đang có lãi (đúng xu hướng).

3. LỜI KHUYÊN ĐẦU TƯ XƯƠNG MÁU:
- Không bỏ trứng một giỏ, nhưng cũng đừng rải trứng ra quá nhiều giỏ đến mức không kiểm soát được.
- Đầu tư giá trị: Mua tài sản tốt (như cổ phần uST Pre-IPO) ở mức giá thấp và nắm giữ dài hạn. Đừng lướt sóng nếu không muốn bị "sóng đánh tụt quần".
- Bài học về sự kiên nhẫn: Thành Rome không xây trong một ngày. Tài sản lớn cần thời gian để lãi suất kép làm việc.

4. QUY TẮC 6 CHIẾC LỌ TÀI CHÍNH:
- Chia thu nhập thành 6 phần: 55% Thiết yếu, 10% Tiết kiệm dài hạn, 10% Giáo dục, 10% Hưởng thụ, 10% Tự do tài chính, 5% Cho đi.
2. Tư duy người giàu: Người giàu mua tài sản (thứ sinh ra tiền), người nghèo mua tiêu sản (thứ mất tiền nuôi).
3. Lời khuyên đầu tư: Không bao giờ để trứng vào một giỏ. Hãy đầu tư vào những gì bạn hiểu rõ.
4. Lãi suất kép: Kỳ quan thứ 8 của thế giới. Ai hiểu nó sẽ kiếm được tiền, ai không hiểu sẽ phải trả tiền cho nó.
1. Quy tắc 6 chiếc lọ tài chính: Chia thu nhập thành 6 phần (Thiết yếu 55%, Tiết kiệm 10%, Giáo dục 10%...).
2. Tư duy người giàu: Người giàu mua tài sản, người nghèo mua tiêu sản.
3. Lời khuyên đầu tư: Không bao giờ để trứng vào một giỏ. Hãy đầu tư vào những gì bạn hiểu rõ.
4. Về SWC: Đây là cơ hội sở hữu cổ phần doanh nghiệp trước IPO (Pre-IPO) với tiềm năng tăng trưởng siêu lớn: https://www.youtube.com/watch?v=0NKv3dqyCm4&t=522s.

PHẦN 1: TƯ DUY
Chìa khóa nâng cấp tri thức của bản thân
1. Kiến thức tăng lên mỗi ngày bằng cách:
* Hiểu và giải thích được tất cả các sự kiện kinh tế .
* Hiểu được khi nào có Khủng hoảng kinh tế, khi nào chứng khoán vàng, bất động sản tăng giám.
* Hiểu và giải thích được tất cả các sự kiện trính chụy:
* Hiểu được khi nào có chiến tranh, sóng thần, động đất.
* Hiểu và giải thích được những hiện tượng khoa học vật lý . Sức khoẻ cuộc sống
2. Kinh nghiệm đời tăng lên bằng cách:
* Hiểu và phân biệt được người nào tốt, người nào xấu.
* Hiểu và biết cách nuôi dạy con cái, các em, và đưa ra lời khuyên đúng cho cha mẹ, anh chị, người lớn tuổi
3. Sức khỏe:
* Hiểu và giải thích được vì sao mình bị bênh và không bị bệnh tức ià thấu hiểu cơ thể mình hoạt động thê nào.
Công thức để hiểu thế giới hoạt động như thế nào?
Một người bình thường muốn biết thế giới này hoạt động như thế nào thì cần biết 3 điều:
- Ai tạo ra ch/ien tranh và mục đích gì?
- Ai tạo ra dịch bệnh thiên tai, (sóng thần, bão lụt) và mục đích gi?
- Ai tạo ra khủng hoảng kinh tế và mục đích gì?
Muốn trả lời được 3 câu hỏi trên phải đi từng bước sau:
Bước 1: Tin 100% thế giới này có 1 nhóm người điều khiển các tất cả các sự kiện trên thế giới. Như họ chọn ai là người làm tổng thống, họ đưa ai lên làm tỷ phú.
Bước 2: Phải tin trái đất này ko dành cho quá nhiều người.
Bước 3: Phải có kiến thức cơ bản về kinh tế như in tiền giấy và tiền máy tính như thế nào, ai là người in? Vì sao có lạm phát tiền tệ? Vi sao giá vàng giá chứng khoán, giá bđs tăng giảm, vì sao?
Bước 4: Phải có tư duy logic khoa học, thực tế để tin những điều mà báo chí không có nói.
Công thức sử dụng 10% Bộ Não của mình
(thiên tài thế kỷ 20 là Einstein chỉ sử dụng tối đa 12% à, người bình thường 2 - 7%).
Phát triển neron thần kinh: trải nghiệm tiếp xúc qua 5 giác quan từ môi trường xung quanh (mắt thấy, tai nghe, mũi ngửi, mồm nói, thân va chạm, tiếp xúc, suy nghĩ đa chiều tự do)
Duy trì liên kết thông tin đa chiều: Nều theo cách này thì sao? Tại sao lại ở thời điểm này? Thề thi sao? Tại sao không phải là ? ... => Kich hoạt sự tô mỏ, liên kêt thông tin
Để kích hoạt nhiều % não bộ hơn người khác bạn phải tim đến thiền.
Hay đơn giản là tĩnh tâm lại, tự nhiên não sẽ thông minh ra.
Hồ lặng sóng tự khắc thấy "trăng "
Tập trung Bộ não hoạt động hết công suất trong 3-5 năm.
Khi bạn có tài sản > 50 tỷ thì ở Việt Nam là ổn, còn 200 tỷ thi bạn có thể kiểm soát người thân của mình để họ từ bỏ thói hư tật xấu.
Ví dụ người yêu nhà bạn mập quá, bạn khuyến họ tập thể dục giảm cân để không chết vì béo phì họ không nghe, bạn chơi trò giảm 1kg với giá 10 triệu.
Vì tiền, họ sẽ phải đánh đổi mọi thứ.
Phải biết sức mình tới đầu. Tuyệt đổi không ảo tưởng sức mạnh.
- Một ngày quan sát mọi sự kiện kinh tế - chính trị xảy ra và các quyết định của mình trong ngày đó đúng hay sai vào buổi tối và buổi sáng hôm sau.
- Hãy dành 30-45p hằng ngày trong trạng thái tĩnh lặng để nói chuyện với tánh phật của mình (tánh phật nằm ở trung tâm não bộ)
- Một ngày phải đặt ra 2-4 câu hỏi vì sao, tự trả lời hoặc kiếm người thông minh hơn trả lời nếu bạn ko trả lời được.
- Dành hơn 15p tập thể dục buổi sáng và hơn 15p tập thể dục buổi chiều
Muốn não trở nên thông minh hơn thì phải xử lý data mỗi ngày
Để thông minh lên, bạn phải phá vỡ được những định kiến - lối mòn vốn dĩ đã ăn sâu trong tư duy của bạn. Hãy challenge đầu óc của bạn, bằng cách thử lật ngược mọi thứ mà bạn từng cho là đúng đắn.
Cách học đơn giản thôi.
1. Đúng phương pháp
2. Chăm chỉ.
Nên nhớ không ai cho không ai cái gì cả người nào iấy tiền bạn ià người tốt người không có dã tâm sau này họ không đòi hỏi gì nữa vì họ lấy nhận tiền bạn rồi .
Cái gì trả bằng tiền đều rẻ cả . Nợ ân tình mới khó trả.
Đừng mất thời gian vào những chuyện không có lợi cho mình. Hãy dành thời gian vào những việc có lợi cho mình nhé
Thái độ của bạn lúc gặp siêu khó khăn quyết định sự thành công của bạn, chứ lúc thuận lợi thì chả nói lên cái mịa gì đâu
Học cả đời mà cũng không chiến thắng được cảm xúc bản thân mình
Đừng vội từ chối kiến thức, mà hãy luôn luôn nạp nó vào, một ngày nào đó có ai hỏi ... Thì não sẽ tự trả lời !
Thành công trong Trái Đất này là hiểu và biết mọi thứ quá khứ, hiện tại và tương lai
Mỗi ngày trước khi đi ngủ phải suy nghĩ lại hôm nay mình học được gì
Quan trọng không phải là những thứ bạn học được, mà là những gì bạn đã truyền lại cho người khác.
Phải thông minh lên mỗi ngày, tập đọc suy nghĩ người khác và trả lời các câu hỏi vì sao?
Giúp não bộ biết hết mọi thứ như xưa bằng cách trả lời hết tất cả các câu hỏi
Vì Sao
Muốn khai mở trí tuệ phải biết đặt câu hỏi !
Phải tò mò và đặt nhiều câu hỏi vì sao?
Muốn tư duy như người giàu thì phải học liên tục
Nạp data cho não bộ mỗi ngày. Não bộ của bạn sẽ tự thông minh lên
Bởi vì nghèo nên mới có ước mơ làm giàu.
Mà nếu muốn giàu thì phải nghĩ được, làm được như người giàu.
Nhưng đang nghèo thì làm sao bạn có tư duy như người giàu được. 1 vòng luẩn quấn khó tả?
Nâng cấp trí khôn
Nều M là 1 người bình thường, đi làm lương cứng 10 - 15 triệu VND/tháng thì trong năm 2017 và các năm tới chiến lược của M như sau:
1. Siêng năng làm việc tốt, có mối quan hệ tốt với cấp trên, mọi người
2. Tiết kiệm thời gian, cafe và nhậu nhẹt ít lại, dành thời gian để học ngoại ngữ đọc sách Tài chinh
3. Trong mối quan hệ xã hội cố gắng kiểm và nhận một người nào đó có Trí
Khôn cao cấp làm sếp của mình để sau này họ giúp mình. Phải có người đỡ đầu cho mình nhé, đừng tự ý làm một mình
4. Suy nghĩ và hành động liền đừng chờ đợi
5. Cố gắng tiếp cận với các công ty con ở Việt Nam
6. Có tiền tiết kiệm mua Vàng cất đó.
Không ai giúp mình bằng tự minh giúp mình. Khi minh giúp mình thoát nghèo thì sếp, Tài phiệt sẽ đánh giả Trí Khôn của mình cao cấp.
Hiều chứ
Đừng thấy đỏ mà tưởng chín. Thấy vậy chứ không phải như vậy. Đó là tư duy
Á Đông. Không hiểu là thua lỗ nặng.
Khi bạn có xuất thân nghèo khó, hãy học cách suy nghĩ như giới tinh anh để vươn lên.
Khi có thành tựu, tài sản lớn, hãy học cách suy nghĩ như tầng lớp lãnh đạo cấp cao của Việt Nam.
1. Tầng lớp tinh anh thống trị ưu tú nhất trên thể giới: của cải, trí tuệ, tư tưởng.
2. Đám quan chức cp: tham lam, vô liêm sỉ và ngu ngốc, cổ gắng hạn chế nhóm
(1).
3. Đám đông công chúng: thiếu hiểu biết, yếu đuối và bất tài, tụ tập như những đàn kiến. Nhóm (3) có cũng được, chẳng có cũng được
Do đó khi nói về 1 vấn đề bạn phải chia ra mối liên hệ với 3 tầng lớp này.
Giới tinh anh không cố gắng tạo ra khủng hoảng kinh tế. Họ chỉ "thuận theo" lòng tham của con người mà thôi. Muốn chống lại cũng không được.
Nỗ lực ảo
Liệu bạn có đang mắc căn bệnh này?
• Mua nhiều sách nhưng không đọc ( đọc vì người khác bảo hay nhưng chẳng đem lại được ti kiến thức)
• Tải nhiều tài liệu nhưng không động tới ?
• Lưu nhiều mẹo nhiều tips hay nhưng không động tới
• Nghe đủ thứ hay ho nhưng không làm
• Đặt mục tiêu kế hoạch nhưng không làm
• Nghĩ nhiều nhưng không hành động
Cuộc sống Bế tắc - Đi xuống - Hạn Chế - Áp lực bản thân - Luôn nghĩ tiêu cực
Hãy đọc hết Facebook này và thông tin bên telegram để thoát khỏi căn bênh "
Nỗ lực ảo"
Nỗ lực không đúng chỗ thì nỗ lực vô ích.
Thấu hiểu bản thân mình chính là biết được điểm mạnh và điểm yếu của minh, từ đó lý giải được tất cả mọi việc xảy ra với mình trong quá khứ, hiện tại và biết được tương lai cuộc đời mình
Nắm bắt tương lai thông qua việc nghiên cứu lịch sử.
Đừng khóc vì những việc đã qua . Hãy cười vì những việc tương lai phía trước.

Nỗ lực đúng phương pháp
Muốn có cái gì chúng ta phải nỗ lực làm đúng phương pháp đó:
1, Muốn giàu tài sản thì phải có kiến thức kinh tế - thị trường, phải làm phước
tu đức.
2, Muốn có sức khỏe và tuổi thọ thì phải sống tốt, môi trường tốt, làm chủ chế độ ăn uống, ngủ nghỉ, làm việc, làm chủ cảm xúc.
3, Muốn có được thuận duyên thì phải giúp đỡ người không dấu diếm, không keo kiệt, không bủn xỉn.
4, Muốn có sự hiểu biết thì phải gieo nhân về tri thức, học đạo, học vê khoa học, muốn quả nào thì phải gieo đúng chánh nhân đó và hỗ trợ nó bằng các thuận duyên.

Phương pháp học tập "lập lại giãn cách"
Đặt trường hợp còn 1 tuần nữa là thi, bạn có một số bài cần phải ôn tập.
Cách học sai: đi chơi tung tăng 5 ngày đầu, còn 2 ngày nữa là thi thì cắm mặt học ngày 12 tiềng, thức khuya, xong vô thi quên hết.
Cách học đúng:
Mỗi ngày dành ra 1 tiếng ôn tập. Đọc lại hết kiến thức. Chỗ nào khó thì đánh dấu lại, suy nghĩ chút, nếu khó quá nghĩ không ra thì bỏ qua. Ngày mai lại lập tiếp tục xem lại hết kiến thức, và suy nghĩ những chỗ chưa hiểu. Nếu vẫn chưa hiều thì đánh dầu lại, và bỏ qua. Đều đặn cho đến lúc thi.
Nếu làm thể này thì bạn sẽ:
Tồn ít thời gian hơn cho việc học
Hiểu sâu hơn + nhớ lâu hơn
Có thời gian giải trí thư giãn, đánh bida, đàn đúm cà phê ... không đánh rơi tuổi trẻ
Khi bạn muốn học cái gì đó, đọc lần 1 không hiều, không nhớ, chả sao, cứ học cái khác. Khi "quên" hắn thì lại đọc lại lần nữa. Lần này bạn sẽ hiểu sâu, nhớ lâu hơn lần trước.
Não muốn nhớ nó phải quên cái đã. Học cái gì cũng vậy hết. Áp dụng bạn sẽ thấy hiệu quả rất kinh khủng.
Bằng cách này, bạn sẽ không càm thấy áp lực, khó khăn, mệt mỏi khi học bất cứ thứ gi cả. Học mà cứ như giải tri vậy
áp dụng phương pháp trên để có tốc độ học minh khủng trong mọi thứ, bao gồm chính trị - kinh tế, sức khoẻ, quản lý xã hội vĩ mô, ngoại ngữ...

Cách học
Thứ 1 là : Đăng ký Youtube, đọc ebook sách theo dõi Facebook và các trang mạng xã hội của người này hoặc 1 số thông tin đáng đọc để học và biết tương lai có chuyện gì xảy ra, rủi ro và cơ hội gì. M sẽ dùng suy nghĩ kết hợp với hiểu biết để tiếp nhận thông tin đó.
Thứ 2 là : Sau khi vẽ được viễn cảnh tương lai: Khủng hoảng kinh tế, đổi tiền, lãi suất cho vay tăng, bất động sản, chứng khoán giảm mạnh, thị trường
CRYPTO bitcoin biến động mạnh và vàng tăng, xã hội loạn, trộm cướp nhiều vì tỷ lệ thất nghiệp tăng, do nhiều doanh nghiệp không còn đủ khả năng chi trả những khoản vay vì lãi suất.
Thứ 3 là mình sẽ tự lên chiến lược riêng cho bản thân và gia đình sau khi đọc tin tức của người mà mình theo dõi .
- Cố gắng siêng năng lao động làm ăn và thực hiện mọi nghĩa vụ tốt.
- Hạn chế đi cafe tán chuyện rượu chè, quan trọng lắm mới đi nhậu không thì thôi, cố gắng ăn thức ăn thực vật rau xanh lựa chọn thức ăn để tránh mắc bệnh.
- Lấy tiền tiết kiệm mua vàng tích luỹ.
- Không mua bất động sản, chứng khoán.
- Dành thời gian nhiều cho bản thân và gia đình hơn.
- Thời gian rảnh thì học thêm ngoại ngữ .
- Thay đổi bản thân, không bảo thủ và li lợm hạ cái tôi xuống tiếp thu và lắng nghe người khác.
- Sống có đạo đức mỗi tối trước khi ngủ phải nghĩ xem hôm nay đã làm những việc tốt gì ví dụ như chia sẻ kênh íb này cho bạn bè đọc để thay đổi tư duy nâng cao tầm nhìn dài hạn cũng là điều tốt.
- Xã hội loạn vì thua lỗ chứng khoán, coin mua bất động sản bị quy hoạch nên phải cẩn thận khi ra đường, lấy nhẫn nhịn làm hàng đầu, không hơn thua tranh cãi.
Đặt câu hỏi
Muốn có câu trả lời thì não của bạn phải luôn thường trực câu hỏi trong 1 thời gian đủ lâu. Vấn đề là con người ta không chịu đặt câu hỏi lúc chưa gặp chuyện.
Đến khi gặp chuyện rồi thì mới nháo nhào đi tìm câu trả lời.
Để bh th đợc như ngày hôm nay, tôi đã phải học cách chấp nhận những thất vọng mà tôi không bao giờ muốn xảy ra...
Liên tục hỏi vì sao ở một vấn đề. Cứ hỏi đúng, hỏi liên tục thì não sẽ có trả lời.
Có những thứ bắt buộc bạn phải tự ngộ ra vì không ai có thể làm thay bạn cả.
Đừng vội từ chối kiến thức, mà hãy luôn luôn nạp vào, một ngày nào đó có ai hỏi ... Thì não sẽ tự trả lời
Khi bạn muốn học cái gì đó, đọc lần 1 không hiểu, không nhớ, chả sao, cứ học cái khác. Khi "quên" hẳn thì lại đọc lại lần nữa. Lần này bạn sẽ hiểu sâu, nhớ lâu hơn lần trước.

Não muốn nhớ nó phải quên cái đã
Sự học thành tự động hóa là như thế nào?
- Là khi mình học mà mình không biết, thông tin cứ vào não bộ mình tự nhiên.
- Như tôi đã đưa thông tin cho bạn.
- Rồi một ngày nào đó có ai hỏi bạn một câu hỏi, thì não bộ tự rà soát dữ liệu rồi đáp lại.
- Tự động hoá kết nạp thông tin. Không cần phải làm gì hết. Khi lúc cần thì tự động nó hiện lên. Học mà không học. Thế mới là học.

Thông minh có 2 loại
- Thông minh thật sự: là người biến những điều cao siêu phức tạp mà chỉ có giáo sư tiến sĩ mới tiếp cận nổi, thành những điều đơn giản mà chú xe ôm đầu ngõ cũng hiêu
- Ng.u nhưng giả vờ thông minh: là những người làm ngược lại nhóm trên, biển những điều bình thường thành những thứ cao siêu rối não.
Nhằm thể hiện ta đây học cao biết rộng."
Để thông minh lên, bạn phải phá vỡ được những định kiến - lồi mòn vốn dĩ đã ăn sâu trong tư duy của bạn. Hãy challenge đầu óc của bạn, bằng cách thử lật ngược mọi thứ mà bạn từng cho là đúng đắn.
Tại sao con nhà nghèo cần học giỏi, còn con nhà giàu thì không cần?
Chỉ có con nhà nghèo mời cần học giỏi, bảng điểm cao còn con nhà giàu họ ko cần. Vậy họ cần gì?
Nhiệm vụ của trường đại học là phải phù hợp với tất cả mọi người, nên kiến thức sẽ rất chung chung sẽ không áp dụng được khi tham gia thực tiễn
Hệ thống giáo dục sẽ phần lớn dành cho mọi người, chỉ có một sô ít làm chủ, còn phần lớn là làm công

Tại sao con nhà nghèo cần học giỏi, còn con nhà giàu thì không cần?
- Chỉ có con nhà nghèo mớii cần học giỏi, bảng điểm cao còn con nhà giàu họ ko cần. Vậy họ cần gi?
- Nhiệm vụ của trường đại học là phải phù hợp với tất cả mọi người, nên kiến thức sẽ rất chung chung sẽ không áp dụng được khi tham gia thực tiễn
- Hệ thống giáo dục sẽ phần lớn dành cho mọi người, chỉ có một số ít làm chủ, còn phần lớn là làm công
* Hệ thống giáo dục không phải b thiết kể ra để kinh doanh mà thiết kế ra để đào tạo công nhân cho những người kinh doanh
* Muốn kiếm tiền thoát nghèo chỉ có 1 con đường là học và học.
* Học để biết mọi thứ, biết tương lai.
* Không học thì có ngày mất tiền!

Học 7 điều
- Thứ nhất, HỌC NHẬN LỖI : Con người thường không chịu nhận lỗi lầm về mình, tất cả mọi lỗi lầm đều đổ cho người khác, cho rằng bản thân mình mới đúng, thật ra không biết nhận lỗi chính là một lỗi lầm lớn.
- Thứ hai, HỌC NHU HÒA : Răng người ta rất cứng, lưỡi người ta rất mềm, đi hết cuộc đời răng người ta lại rụng hết, nhưng lưỡi thì vẫn còn nguyên, cho nên cần phải học mềm mỏng, nhu hòa thì đời con người ta mới có thể tồn tại lâu dài được. Giữ tâm nhu hòa là một tiến bộ lớn
- Thứ ba, HỌC NHẤN NHỊN : Thế gian này nếu nhẫn được mội chút thì sóng yên bể lặng, lùi một bước biển rộng trời cao. Nhẫn chính là biết xử sự, biết hóa giải, dùng trí tuệ và năng lực làm cho chuyện lớn hóa thành nhỏ, chuyện nhỏ hóa thành không.
- Thứ tư, HỌC THẤU HIỂU : Thiếu thấu hiểu nhau sẽ nảy sinh những thị phi, tranh chấp, hiểu lầm. Mọi người nên thấu hiểu thông cảm lẫn nhau, để giúp đỡ lẫn nhau. Không thông cảm lẫn nhau làm sao có thể hòa bình được?
- Thứ năm, HỌC BUÔNG BỎ : Cuộc đời như một chiếc vali, lúc cần thì xách lên, không cần dùng nữa thì đặt nó xuống, lúc cần đặt xuống thì lại không đặt xuống, giống như kéo một túi hành lý nặng nề không tự tại chút nào cả. Năm tháng cuộc đời có hạn, nhận lỗi, tôn trọng, bao dung, mới làm cho người ta chấp nhận mình, biết buông bỏ thì mới tự tại được!
- Thứ sáu, HỌC CẢM ĐỌNG. Nhìn thấy ưu điểm của người khác chúng ta nên hoan hỷ mừng vui cùng cho họ, nhìn thấy điều không may của người khác nên cảm động. Cảm động là tâm thương yêu, tâm Bồ tát, tâm Bồ đề; trong cuộc đời của tôi, có rất nhiều câu chuyện, nhiều lời nói làm tôi cảm động, cho nên tôi cũng rất nỗ lực tìm cách làm cho người khác cảm động.
- Thứ bảy, HỌC SINH TỒN : Để sinh tồn, chúng ta phải duy trì bảo vệ thân thể khỏe mạnh; thân thể khỏẻ mạnh không những có lợi cho bản thân, mà còn làm cho gia đình, bè bạn yên tâm, cho nên đó cũng là hành vi hiếu đễ với người thân. (Theo giáo lý Phật học)


Chân lý - Sự thật
- Nhìn những vật không nhìn thấy, nghe những âm thanh không nghe thầy, biết được những sự việc không biết được mới là chân lý (sự thật)
- Đa số người ta có xu hướng bảo thủ và đa nghi về những thứ vô hình không thể nhin thấy và họ bảo là chỉ những thứ nhìn thấy trước mắt thì họ mới tin.
- Thực tế những thứ không nhìn thấy đó lại có tác động mạnh mẽ tới chúng ta rất nhiều so với những thứ ta có thể nhin thấy .
- Đơn giản bạn sẽ không thấy điện ở trong ổ cắm khi chưa đút tay vào đó kaka.
- Đỉnh cao của sự Phức Tạp là Đơn Giản!
- Chơi mạng xã hội nên viết ít chữ thôi bạn nhé. Viết càng dài chứng tỏ sự bất lực trong cách thuyết phục bộ não người khác, nên dùng tiểu xảo ngôn từ để lấp liếm thôi.
- Đỉnh cao của sự phức tạp là đơn giản, đơn giản đến một chị bán trà sữa cũng hiểu là thành công!
- Data sẽ làm các bạn thông minh lên mà không hề biết. Học mà không hề biết mình đang học. Cách mạng tư duy trên facebook đã đến với người Việt Nam.
- Mình thích dùng ứng dụng facebook để đăng status ngắn giống Twitter, vì Minh muốn bộ não và các bạn phải suy nghĩ nhiều hơn nữa.
- Học Mỹ nhé, họ là số một vì không có nhiều thời gian đọc status dài xàm xí đú của bọn tào lao trên mạng!
- Cuộc sống không nhất thiết chuyện gì cũng phải phân rõ trắng đen
- Có câu "nước quá trong thì không có cá, người xét nét quá thì không có bạn.
- Tranh chấp với người nhà, giành được rồi thì tình thân cũng mất đi
- Tính toán với người yêu, rõ ràng rồi thì tình cảm cũng phai nhạt
- Hơn thua với bạn bè, chiến thắng rồi thì tình nghĩa cũng không còn.
- Khi tranh luận, người ta chỉ hướng đến lý lẽ mà quên rằng cái mất đi là tình cảm, còn lại sự tổn thương là chính mình.
- Cái gì đã đen thì sẽ đen, trắng là trắng, tốt nhất hãy để thời gian chứng minh.
- Rủ bỏ sự cố chấp của bản thân, dùng lòng khoan dung để nhìn người xét việc; thêm một chút nhiệt tình, một chút điềm tĩnh và ấm áp thì cuộc sống sẽ luôn có ánh mặt trời và suốt đời mình sẽ là người thẳng cuộc.
- Muốn biết bản chất cái gì thì phải quay về thời kỳ sơ khai của nó, lúc nó mới bắt đầu
- Đạo Phật căn nguyên nằm ở trí tuệ. Biết là thoát khỏi "bể khổ"

Nghỉ ngơi và Lười biếng
- CHO PHÉP BẢN THÂN NGHỈ NGƠI, CHỨ ĐỪNG CHO PHÉP BẢN THÂN LƯỜI BIÉNG.
- Đừng bao giờ so sánh bản thân mình với người khác Khi bạn so sánh mình với những người giàu hơn, hãy dừng lại và nhìn về phía những người kém may mắn hơn bạn. Hãy chấm dứt thói quen này và bắt đầu so sánh bản thân mình ngày hôm nay với ngày hôm qua còn phải cố gắng nhiều hơn nữa. để thấy
- Nhàn cư vi bất thiện có nghĩa là nếu con người ta ở trong trạng thái nhàn rỗi, không có việc làm sẽ dẫn đến các hành động sai lầm, ảnh hưởng xấu đến xã hội

Tri thức ảo
- Một tri thức ảo đăng một bài viết dài ngoằng ngoằng phân tích dài như cái sớ, ngôn từ cao siêu phức tạp.
- Thay vì ngồi phân tích cái bài viết đó, hãy hỏi vì sao họ lại đăng cái bài viết đó?
- Vì sao nó dài mà không ngắn? Vì sao nó phức tạp và khó hiểu? Vì sao?  Một đứa chơi thua lỗ cổ phiếu, không quen biết gì với mình, vô Fb mình chửi.
* Thay vì ngồi chửi nhau với nó, hãy đặt câu hỏi vì sao nó lại hành động như vậy?
* Bạn thử đặt câu hỏi vi sao, và sẽ nhận ra nhiều điều bất ngờ và thú vị nhé
* Nhìn lại quá khứ
*   Nhìn lại những thất bại trong quá khứ và giải thích được vì sao mình thất bại như thế.
*   Nhìn lại những thành công trong quá khứ và giải thích được vì sao tài sản mình tăng nhanh như thế? có phải do hên xui, do phước báu kiếp trước hay nhờ bạn có 1 bộ não thông minh biết mọi thứ
*   Nhin lại vi sao mình bị đau ốm bệnh tật trong quá khứ để hiểu được cơ thế mình khỏe mạnh hay ốm yếu. Rút ra phương pháp tăng cường sức khỏe để
* mãi mãi không bị bệnh.
*   Nhìn lại kinh nghiệm đời về cách đối nhân xử thế với mọi người, với chinh phu, với tầng lớp tinh anh. Sai chỗ nào, đúng chỗ nào? Từ đó nâng trình tâm lý học hành vi lên cấp độ cao để đọc được suy nghĩ của người khác.
*   Chỉ cần bạn hỏi và trả lời được 4 ý trên thi năm 2023 bạn xứng đáng có tài sản gấp 5 gấp 10 lần trong những năm tới

Đúng người và đúng vấn đề
Hãy tập trung đúng người và đúng vấn đề đừng quan tâm họ qua lời đồn hãy quan tâm cách họ giải quyết được vấn đề và thắc mắc của bạn :
- Cấp độ 1: Cá nhân vận dụng trí tuệ, sáng tạo, kinh nghiệm, trí khôn của họ tìm cách giải quyết vấn đề.
- Cấp độ 2: Làm việc nhóm, tìm người giỏi có thể giải quyết vấn đề.
- Cấp độ 3: Tìm đứa đưa ra vấn đề, hay tạo ra vấn đề hỏi nó là vấn đề đã được giải quyết triệt để.


- Chương 1: Tư duy đói khát 
Truyền thuyết kể rằng có một phương pháp bẫy khỉ: khoét hai lỗ trên một tấm ván gỗ, vừa đủ để khỉ thò tay vào. Phía sau tấm ván đặt một ít đậu phộng. Khỉ nhìn thấy đậu phộng, liền thò tay vào lấy. Kết quả, bàn tay nắm chặt lấy đậu phộng, không thể rút ra khỏi lỗ. Khỉ cứ thế nắm chặt lấy đậu phộng của mình, bị người ta dễ dàng bắt đi. 
Thật tội nghiệp cho con khỉ! Nguyên nhân nó gặp nạn là do quá coi trọng thức ăn, mà không nghĩ đến việc mọi thứ trên đời đều có rất nhiều khả năng. 
Khỉ như vậy là vì nó quá cần thức ăn. Hoàn cảnh của người nghèo cũng thường như vậy. 
Người nghèo thiếu tiền, điều này không cần phải nói. Thiếu tiền mang lại cho người nghèo nỗi đau khổ sâu sắc, điều này cũng không cần phải nói. Do đó, người nghèo cần tiền, càng không cần phải nói. 
Thiếu tiền đến mức sợ hãi, người nghèo rất dễ coi trọng tiền bạc quá mức. Quá chú trọng vào tiền bạc, dễ dàng bỏ qua những thứ khác ngoài tiền, kết quả là người nghèo thu được rất ít, mất mát rất nhiều. 
Tổn hại về tinh thần do thiếu tiền mang lại thường đáng sợ hơn cả sự thiếu thốn về vật chất. 
Jack London trong tiểu thuyết "Tình yêu cuộc sống" đã viết về câu chuyện của một người lạc đường. Người bất hạnh này một mình vật lộn trong vùng hoang dã, đói khát, mệt mỏi, cô đơn, tuyệt vọng, cùng với một con sói già cũng đói khát và mệt mỏi như anh ta, luôn đi theo anh ta, chờ anh ta gục ngã để ăn thịt. Tuy nhiên, cuối cùng không phải sói ăn thịt anh ta, mà là anh ta ăn thịt sói. Kết thúc của tiểu thuyết là, người này cuối cùng cũng trở lại thuyền, ăn rất nhiều, béo lên rất nhiều. Anh ta liên tục ăn, ăn xong lại đi khắp nơi thu thập bánh mì. Anh ta thu thập rất nhiều bánh mì, nhét đầy mọi ngóc ngách trong khoang thuyền, mặc dù bánh mì đã khô, vụn, anh ta vẫn thu thập không ngừng mỗi ngày. 
Khả năng sinh tồn của người nghèo rất mạnh mẽ, ý chí vượt qua khó khăn gian khổ của họ thực sự khiến người ta cảm động, nhưng kết quả cuối cùng của nỗ lực của họ, có lẽ chỉ là một đống bánh mì khô héo mà thôi. 
Người đói khát thường hình thành tư duy đói khát, nắm chặt một miếng bánh mì thì không chịu buông tay, cho dù đã no, vẫn không nhịn được mà tích trữ, sợ quay lại những ngày đói khát. Nhưng khi tay đã đầy bánh mì, thì không thể rảnh tay để nắm lấy những thứ khác, kết quả là trong tay nhiều nhất chỉ có vài miếng bánh mì, sẽ không có thứ gì quý giá hơn. 
Tầm nhìn hạn hẹp của người nghèo thường nằm ở tư duy đói khát này. Người nghèo sợ nghèo, ngược lại không dám từ bỏ những thứ trước mắt để tìm kiếm lối thoát mới. 
- Chương 2: Người nghèo chỉ có một quả trứng 
Có một câu chuyện kể về một người đàn ông nghèo, vợ anh ta một hôm mua về một quả trứng. Người chồng nghèo liền nói, nếu dùng quả trứng này để ấp nở ra một con gà, gà lại đẻ trứng, trứng lại nở gà; rồi dùng đàn gà để đổi lấy một con cừu, cừu lớn sinh cừu con; cừu lại đổi lấy bò, bò lớn sinh bò con; bán bò mua đất xây nhà, rồi cưới thêm vợ bé... Nghe đến say mê, người vợ bỗng bừng tỉnh và nổi giận, cầm quả trứng đập vỡ xuống đất, khiến giấc mơ của người chồng tan thành mây khói. 
Đây là một câu chuyện ngụ ngôn kinh điển về người nghèo. 
Người đàn ông nghèo đó có thể cả đời sẽ day dứt, hối hận vì đã để lộ suy nghĩ của mình, khiến chút vốn liếng quý giá bị hủy hoại. Nhưng anh ta thực sự không thể nhịn được! 
Năm xưa, Martin Luther King với câu nói "Tôi có một giấc mơ" đã làm rung động biết bao trái tim. Người nghèo cũng là con người, tất cả những khao khát của người giàu, người nghèo cũng có. Ăn ngon, mặc đẹp, lấy vợ đẹp, đó là những nhu cầu bản năng, tại sao anh ta lại không thể mơ ước cưới thêm vợ bé?! Chỉ là quả trứng còn chưa kịp nở thành gà, thậm chí bản thân quả trứng cũng còn nằm trong tay vợ, mà đã có những giấc mơ huy hoàng như vậy, liệu có phù hợp hay không, thật đáng để suy ngẫm. 
Không thể nói rằng tương lai của người nghèo không có ánh sáng, nhưng sự quanh co, khúc khuỷu của con đường đó cũng cần được người nghèo cân nhắc. 
Về mặt lý thuyết, một khi tìm ra được mô hình kiếm tiền, việc vốn tăng theo cấp số nhân cũng không phải là không thể. Nhiều câu chuyện thần thoại về sự giàu có, như Bill Gates chẳng hạn, ban đầu vốn khởi nghiệp cũng chỉ như một quả trứng. Nhưng trên thế giới có vô số người nghèo, vô số quả trứng, mà Bill Gates chỉ có một. Liệu người tiếp theo có phải là bạn không? Khó mà nói trước. 
Vốn càng nhỏ, rủi ro càng lớn, khi trong tay bạn chỉ có một quả trứng, dù chỉ chạm nhẹ cũng có thể mất tất cả. Đây chính là điểm yếu của người nghèo. 
Điểm xuất phát của người nghèo quá thấp, ngay cả khi bạn đã lên một chuyến tàu tốc hành, nhanh đến mức không thể nhanh hơn, thì sự tăng trưởng của vốn cũng giống như việc lăn một quả cầu tuyết. Khi quả cầu tuyết còn nhỏ, dù bạn có lăn đến điên cuồng, thì so với những quả cầu tuyết lớn, sự phát triển của bạn vẫn thật đáng thương. Cơ số quá nhỏ, tăng trưởng có hạn, cùng là phát triển theo kiểu lăn, người này tăng gấp đôi so với người kia tăng gấp đôi, kết quả sẽ khác nhau một trời một vực. Hơn nữa, khi thời tiết thay đổi, thứ tan chảy đầu tiên chắc chắn sẽ là bạn. Liệu quả cầu tuyết của bạn có thể lăn lớn hay không, đó là một câu hỏi hóc búa. 
Người nghèo thường bắt đầu từ việc kinh doanh nhỏ, muốn biến kinh doanh nhỏ thành kinh doanh lớn, giống như biến một quả trứng thành một đàn bò, có quá nhiều yếu tố, quá nhiều khâu ở giữa, nếu bạn không trải qua toàn bộ quá trình, bạn sẽ không nắm bắt được tính khí của sự giàu có, bạn sẽ không thể trở thành người giàu thực sự, ngay cả khi đột nhiên có được một khoản tài sản lớn, bạn cũng không thể tiêu xài nó một cách khôn ngoan. 
Nhiều khi, sự giàu có cũng là một áp lực. Những người thợ lặn đều biết, nếu liều lĩnh lặn xuống biển sâu, rất có thể sẽ bị chảy máu thất khiếu. 
Đây tuyệt đối không phải là lời đe dọa. 

- Chương 3: Người nghèo chiếm vị trí bất lợi 
Trong hầu hết văn hóa các nước, việc sắp xếp chỗ ngồi khi ăn uống, uống trà, hay họp hành đều có những quy tắc nhất định. 
Người có địa vị cao sẽ ngồi ở vị trí thượng đầu, lưng tựa vào tường, đối diện với cửa chính. Vị trí này cho phép họ quan sát toàn cảnh, không phải lo lắng về những gì diễn ra phía sau, dễ dàng nắm bắt tình hình chung, giống như vị trí tướng quân trong quân đội. 
Ngược lại, người có địa vị thấp buộc phải ngồi ở vị trí hạ đầu, hoàn toàn bất lợi so với vị trí thượng đầu. Họ không thể nắm bắt tình hình, khi thức ăn được dọn lên cũng phải cẩn thận tránh né để không bị đổ lên đầu. 
Người nghèo cũng tương tự như vậy, luôn phải chịu thiệt thòi. Khi nguy hiểm ập đến, họ là những người đầu tiên gánh chịu hậu quả. Khi có lợi ích, họ lại là những người hưởng lợi sau cùng. Đây là điều khó tránh khỏi, ai cũng muốn ngồi ở vị trí thượng đầu, nhưng không phải ai cũng có thể. Nếu không cân nhắc kỹ tình hình thực tế mà cứ cố chấp ngồi vào vị trí đó, dù không bị mời xuống, cuối cùng cũng sẽ khiến mọi người khó chịu. 
Địa vị của người nghèo quyết định họ là kẻ yếu, không có những điều kiện thuận lợi như người giàu. Vì vậy, mỗi khi xã hội biến động, họ là những người chịu thiệt hại nặng nề nhất. Mỗi khi cơ hội đến, kể cả những cơ hội dành riêng cho người nghèo, họ cũng chỉ nhận được phần rất nhỏ. Nhìn lại lịch sử các cuộc cách mạng, ngoài một số ít người vinh quy bái tổ, đa số người nghèo, với tư cách là một tầng lớp, cuối cùng vẫn là người nghèo. 
Người nghèo muốn trở nên giàu có, muốn từ hạ đầu lên thượng đầu, rất khó để dựa vào những sự kiện bất ngờ. Cho dù thành công, sự giàu có đó cũng khó bền vững. Họ phải dựa vào nỗ lực lâu dài qua nhiều thế hệ, giống như sóng biển đãi cát, phần lớn cát sẽ bị cuốn trôi, chỉ còn lại một số ít vàng. 

- Chương 4: Người nghèo là kẻ yếu mãi mãi 
Người nghèo, xét về tổng thể, luôn ở trong trạng thái yếu thế. Họ mãi mãi là kẻ yếu. 
Trên thị trường chứng khoán, các nhà đầu tư nhỏ lẻ luôn dỏng tai nghe ngóng thông tin, hy vọng “ăn theo” các nhà đầu tư lớn, nhưng kết quả thường bị họ dắt mũi, trở thành con mồi béo bở. 
“Nhà đầu tư lớn” trên thị trường chứng khoán, nói trắng ra, chính là những người có khả năng khuấy đảo thị trường, là các tổ chức, nhà đầu cơ, hay chính bản thân công ty niêm yết. Mục tiêu của họ khi tham gia thị trường chỉ có một, đó là kiếm tiền. 
Vậy ai sẽ là người mất tiền? Thị trường chứng khoán không phải là nơi in tiền, nó chỉ là nơi dòng tiền luân chuyển. Tiền hoặc là từ túi bạn chảy sang túi họ, hoặc là từ túi họ chảy sang túi bạn. Từ lâu đã có những lời đồn đại về cách thức kiếm tiền của các nhà đầu tư lớn, đó là “nuôi, dụ, xả”, giống hệt như cách đối phó với con mồi. 
Trong bối cảnh ai cũng muốn kiếm tiền, ai là người dễ bị “nuôi, dụ, xả” nhất? Câu trả lời đã quá rõ ràng. 
Có rất nhiều người viết sách, viết bài hướng dẫn các nhà đầu tư nhỏ lẻ cách đối phó với các nhà đầu tư lớn, tóm lại là hai phương pháp: phân tích cơ bản và phân tích kỹ thuật. Tuy nhiên, với một người lao động bình thường, tiền không nhiều và phải đi làm đúng giờ, lấy đâu ra thời gian để nghiên cứu hàng núi tài liệu, để phán đoán động thái của các nhà đầu tư lớn, để đấu trí với những chuyên gia được đào tạo bài bản, và phải đưa ra quyết định trong tích tắc? 
Khiêu vũ với sói, khả năng lớn nhất là bị sói ăn thịt. 
Nhà đầu tư nhỏ lẻ và nhà đầu tư lớn, hai bên hoàn toàn không cùng đẳng cấp, không chỉ đơn giản là sự khác biệt giữa cánh tay và cái đùi. Địa vị khác nhau, năng lực khác nhau, môi trường và điều kiện hoạt động khác nhau, thông tin mà hai bên tiếp cận được vĩnh viễn là bất đối xứng. 
Những gì họ biết bạn không biết, những gì bạn biết họ đã biết từ lâu. Biểu đồ giá cả nói lên tất cả, bạn chỉ có thể đoán mò nguyên nhân từ kết quả đã được thể hiện ra. Đến khi bạn hiểu ra, mọi chuyện đã an bài, bạn không còn cơ hội để phản kháng. 
Không chỉ trên thị trường chứng khoán, mà ở hầu hết các thị trường khác, người nghèo với tư cách là nhà đầu tư, đều ít nhiều ở thế yếu. Sự bất đối xứng về thông tin khiến bạn không thể đánh giá được rủi ro, luôn ở trong tình trạng bị bóc lột. Bản thân năng lực hạn chế cũng khiến bạn không thể cạnh tranh với những “sát thủ” chuyên nghiệp đang thao túng khối tài sản khổng lồ. Họ là một tập thể, sống bằng nghề này, nếu không có bạn mất mát thì họ không có lý do để tồn tại. 
Kẻ yếu trên thị trường chứng khoán là nhà đầu tư nhỏ lẻ, kẻ yếu trong xã hội là người nghèo. Người nghèo dễ bị bắt nạt, một phần vì tầm nhìn hạn hẹp, mặt khác cũng do địa vị yếu thế của họ. 

- Chương 5: Người nghèo là nền tảng của xã hội 
Cá lớn nuốt cá bé, cá bé nuốt tôm, tôm nuốt bùn. Người nghèo chính là bùn, nằm ở cuối chuỗi thức ăn. 
Nhưng người nghèo lại là nền tảng của toàn bộ hệ sinh thái. Không có bùn thì không có tôm, không có tôm thì không có cá bé, không có cá bé thì cá lớn cũng không sống nổi. 
Bùn là thứ thấp hèn nhất. Mùa xuân đến, muôn hoa đua nở, trên thân bùn chỉ thêm vài dấu chân dẫm lên. Mùa đông đến, gió lạnh thổi, bùn lại trở thành nơi trú ẩn cho sự sống. Rễ cây ẩn mình trong lòng đất ngủ đông, động vật trốn trong hang đất ngủ đông, còn bùn thì phơi mình ra, lặng lẽ chịu đựng. 
Sự náo nhiệt chẳng bao giờ liên quan đến bùn, cũng như cái gọi là dòng chảy chính chẳng liên quan đến người nghèo. Trên thế giới, hễ xảy ra tai họa, dù là thiên tai hay nhân họa, những người chịu thiệt hại nặng nề nhất luôn là người nghèo. Còn những điều tốt đẹp, có lợi thì luôn bị người giàu nhanh chân chiếm mất. 
Bùn là thứ nhỏ bé. Ở chợ hoa, đất mùn được đào từ trong rừng ra - loại đất mà chỉ cần trộn vào đất trồng cây nghèo dinh dưỡng nhất thì cũng không cần bón phân - thứ đất thực sự màu mỡ, cũng chỉ có giá vài nghìn một cân. Còn những cây cảnh quý giá được nó nuôi dưỡng, có cây nào chỉ đáng giá từng ấy tiền? Nhưng nếu thiếu đất, cây cảnh có thể sinh trưởng được không? Vạn vật sinh trưởng nhờ mặt trời, vạn vật sinh trưởng cũng nhờ đất. Mặt trời đã nhận được quá nhiều lời ca tụng, còn đất thì đến nay vẫn không có tiếng tăm gì. 
Người nghèo cũng nhỏ bé, nhiều hơn một người hay ít hơn một người thực sự không quan trọng, nhưng toàn bộ người nghèo lại là nền tảng của xã hội. Không có người nghèo, ai cũng sẽ sống không tốt

- Chương 6: Người nghèo là một loại tài nguyên 
Trên thế giới này, không phải người giàu cứu vớt người nghèo, không có người giàu thì Trái Đất vẫn quay. Ngược lại, người nghèo mới chính là nền tảng kinh tế của xã hội. 
Người nghèo là một tập thể khổng lồ. Nhu cầu về ăn, mặc, ở, đi lại, giải trí, văn hóa,... 
của họ tạo nên nhu cầu to lớn của xã hội. Người nghèo không chỉ là lực lượng lao động, họ vừa là người sản xuất, vừa là người tiêu dùng cuối cùng. Người nghèo cũng là một thị trường lớn, khiến các nhà tư bản thèm thuồng. Nếu để tất cả người nghèo biến mất khỏi Trái Đất trong một đêm, không những nền kinh tế không thể phồn vinh, mà cả Trái Đất cũng sẽ trở nên hoang tàn.  Người nghèo cũng là một loại tài nguyên, quý giá như dầu mỏ, rừng cây, hay tiền tệ. Dù tài nguyên là để bị lợi dụng, bị hưởng thụ, không thể tự quyết định điều gì, nhưng giá trị của nó khiến người ta không thể không trân trọng. 
Người nghèo là lực lượng lao động và thị trường của người giàu, nước nghèo cũng là nơi tiêu thụ sản phẩm và cung cấp nguyên liệu cho nước giàu. Rất nhiều trường hợp, toàn bộ quy trình sản xuất sản phẩm được thực hiện tại địa phương của người nghèo, nhưng lợi nhuận lại chảy vào túi người giàu. Họ dùng nguyên liệu, lao động, và thị trường của bạn, kiếm tiền từ bạn, lại còn tỏ vẻ khinh thường bạn, thậm chí còn tuyên bố là họ đã tạo công ăn việc làm cho bạn, còn bạn thì cảm kích đến rơi nước mắt! 
Người nghèo như cát rời rạc, giống như trên thị trường chứng khoán, tổng số tiền của các nhà đầu tư nhỏ lẻ cộng lại chắc chắn lớn hơn bất kỳ nhà đầu tư lớn nào, nhưng họ không thể gộp lại, vì vậy nhà đầu tư lớn mới trở thành nhà đầu tư lớn, khuấy đảo thị trường, kiếm tiền từ các nhà đầu tư nhỏ lẻ, lại còn khiến họ phải nể phục. 
Xã hội chúng ta luôn dùng ánh mắt tôn kính nhìn người giàu bố thí chút tiền lẻ cho người nghèo. Thực tế, đây không phải là tấm lòng cao thượng của người giàu, mà là họ hiểu rằng toàn bộ xã hội là một chuỗi sinh học, “lấy của dân, dùng cho dân”, nói nôm na là “lấy mỡ nó rán nó”. Nếu trên đời này không còn người nghèo, thì người giàu cũng không sống nổi. 
Người nghèo là tài nguyên, rất nhiều khi là tài nguyên vô cùng quan trọng, họ không chỉ là lực lượng lao động, là thị trường, mà còn là sự bảo đảm an ninh. Không chỉ những người bảo vệ ở khu nhà giàu, người gác cổng ở câu lạc bộ của người giàu, mà toàn bộ đất nước, toàn thể nhân dân (bao gồm cả người giàu), đều do người nghèo dùng máu thịt của họ để bảo vệ. 
Chúng ta có thể sống yên ổn trong môi trường hòa bình, chỉ riêng điều này thôi, người giàu và tất cả những người sống trong môi trường này đều nên cảm ơn người nghèo. 
Người nghèo và người giàu nương tựa vào nhau, thực tế cộng đồng quốc tế hiểu rõ quy luật này nhất, vì vậy mới thường xuyên có chuyện nước giàu xóa nợ cho nước nghèo, hay viện trợ kinh tế,... Cùng sống trên một hành tinh, chúng ta phải chung sống hòa bình. Giống như con người đã học được cách bảo vệ thiên nhiên, hiểu rằng nếu trên Trái Đất này không còn động vật cấp thấp, thì động vật cấp cao sẽ không chỉ đơn giản là cô đơn. 
Người nghèo cũng là môi trường sống của người giàu, người nghèo cũng là một loại tài nguyên quý giá. Vì vậy, người nghèo khi nhận sự giúp đỡ của người giàu cũng đừng nên quá cảm kích, bạn hoàn toàn có thể ngẩng cao đầu, thản nhiên đón nhận, đó vốn là thứ bạn đáng được hưởng! 

Chương 8: Người nghèo không an toàn 
Người nghèo chỉ có một cái bát vỡ, người giàu có cả núi tài sản, người ta thường nghĩ rằng người giàu dễ bị mất mát hơn. Nhưng sự thật là Diêm Vương không chê quỷ nghèo, ngay cả người ăn mày, nhặt rác, trong tay chỉ có nửa cái bánh nướng, cũng có thể bị người đói hơn cướp đi. 
Người nghèo ít tiền, nhưng khả năng phòng vệ cũng kém. Mỗi thành phố đều có những khu nhà sang trọng, nơi ở của các đại gia. Những kẻ ghen tị chắc chắn không ít, nhưng với cửa sắt kiên cố, bảo vệ tuần tra, camera hồng ngoại giám sát, thì kẻ xấu nào dám ra tay? 
Ở các thành phố lớn, hiếm ai chưa từng bị mất xe đạp, nhưng mất ô tô thì không nhiều. Mất ô tô là chuyện lớn, sẽ kinh động đến rất nhiều người, cuối cùng có thể phá án. Kể cả không tìm lại được, thì thiệt hại cũng có công ty bảo hiểm gánh vác, không ảnh hưởng gì nhiều đến họ. Nhưng mất một chiếc xe đạp, ai thèm quan tâm! Đối với người nghèo, một chiếc xe đạp cũng là một khoản tài sản không nhỏ. 
Vua chúa thời xưa ở trong cung lâu ngày cũng muốn ra ngoài hít thở không khí, tận hưởng chút tự do của người bình thường, nên cải trang thành dân thường, gọi là “vi hành”. Người nghèo nghe nói vậy, không khỏi tự an ủi, mình nghèo thì nghèo, nhưng tự do tự tại, đến vua cũng phải ghen tị. 
Nhưng họ quên mất, gánh nặng của họ lại rất cụ thể, môi trường sống của người nghèo kém xa người giàu. Hoàng thượng dù có thay đổi quần áo, thì vẫn là hoàng thượng, bên cạnh luôn có một đám vệ sĩ, phía sau có công công đi theo, trong túi luôn có đầy đủ tiền bạc. Ông ta với tâm trạng tò mò, vô tư đi trải nghiệm cái gọi là “cảnh khổ của dân gian”, giống như  người thành phố bây giờ, mang theo dao đa năng Thụy Sĩ, mặt nạ phòng độc, la bàn, nước khoáng,... đến vùng quê cách thành phố hai mươi cây số để cảm nhận “nỗi khổ”, dù có ăn một bữa cơm rau dưa ở nhà nông, cũng chỉ là để “hỗ trợ tiêu hóa” mà thôi. 
Khổ của người nghèo, chỉ người nghèo mới hiểu. Sống lâu trong môi trường hỗn loạn, vô trật tự, đầy bạo lực, người nghèo cũng có triết lý sống riêng của mình. 
Người nghèo thường không tin vào luật pháp, “chế độ là chết, nhưng người thực thi chế độ là sống”. Về lý thuyết, luật pháp được đặt ra để duy trì trật tự, bảo vệ kẻ yếu, nhưng trên thực tế, cả việc lập pháp lẫn chấp pháp, người giàu đều được hưởng lợi nhiều hơn. 
Ở các nước phát triển, cứ một thời gian, trong các thành phố thường xuyên có tin tức, công nhân nhập cư không đòi được tiền lương thì đi nhảy lầu. Xét về mặt pháp luật, rõ ràng đây là hành động không phù hợp. Nhưng với tư cách là công nhân nhập cư, họ có đủ khả năng để thuê luật sư không? Kể cả có luật sư tốt bụng sẵn sàng giúp đỡ miễn phí, họ có đủ khả năng để chi trả cái giá đắt đỏ về thời gian không? Đối với những người phải lo từng bữa ăn, quy trình tố tụng quá dài dòng, chưa đợi đến khi thắng kiện thì có lẽ đã chết đói. Hơn nữa, cuối cùng có đòi được tiền hay không vẫn là một ẩn số. 
Người nghèo thiếu niềm tin vào luật pháp. Trong tâm trí họ, chủ nghĩa thực dụng đã ăn sâu bén rễ. “Kẻ thắng làm vua, kẻ thua làm giặc”, chỉ nhìn kết quả, bất chấp thủ đoạn. Vì vậy, bạo lực trong giới người nghèo đặc biệt đáng sợ. 
Ít tài sản thì ít lo lắng, ít lo lắng thì gan lớn, gan lớn thì nhiều ý nghĩ tội lỗi được thực hiện. Khu ổ chuột ở mỗi thành phố đều là nơi trật tự xã hội hỗn loạn nhất, nhưng người nghèo chỉ có thể sống ở đó. 
"Người chết vì tiền, chim chết vì mồi", tài sản thường là nguồn gốc của tai họa. Nhưng khi tài sản tích lũy đến một mức độ nhất định, con người lại an toàn hơn. Mở tờ báo ra xem mục tin tức xã hội, bạn sẽ thấy, những người bị giết hại cướp của phần lớn là người nghèo. Số tài sản ít ỏi bị cướp đi kia, trong mắt người giàu thật đáng thương, nhưng thực sự có người phải bỏ mạng vì nó, sự thật là như vậy đấy. 
Người nghèo đáng thương, khả năng tự bảo vệ mình của họ còn khó khăn hơn người giàu rất nhiều



Chương 9: Người nghèo dễ bị lừa 
Những kẻ lừa đảo trên đường phố thường nhắm vào người già và người nghèo. Rất khó để tưởng tượng một người giàu lại bị những trò bịp bợm ở các góc khuất như đoán bài, ném vòng, đổi đô la, bán đồ cổ gia truyền,... lừa gạt. 
Lý do con người bị lừa, thường là vì tham lam, vì có ý đồ riêng, hoặc vì sợ hãi, bị người ta lợi dụng. Người giàu thực sự đều có nguồn thu nhập riêng, không cần phải mơ tưởng đến những khoản “tiền trời ơi đất hỡi” này. Người giàu thực sự phần lớn đều là những người từng trải, hiểu biết, đã tôi luyện cho mình con mắt tinh tường, nếu không thì tài sản của họ làm sao tích lũy được, làm sao giữ gìn được?   Trên báo chí thường xuyên có đủ loại quảng cáo làm giàu, nói rằng bạn không cần nhiều tiền, không cần tay nghề cao, cũng không cần vất vả chạy chợ, chỉ cần ngồi nhà mày mò là có thể phát tài. Trên đời này làm gì có chuyện dễ dàng như vậy! Những cái bẫy được thiết kế tinh vi này, chỉ có những người nghèo ít trải nghiệm và khao khát làm giàu mới dễ dàng sập bẫy. 
Trên đời này người thông minh đầy rẫy, nếu có một ngành nghề lợi nhuận cao mà rủi ro thấp, thì không cần ai kêu gọi, mọi người cũng sẽ đổ xô vào, kết quả là ngành nghề đó nhanh chóng bão hòa, tỷ suất lợi nhuận giảm mạnh. Vốn là dòng chảy, giống như sông hồ biển cả, dù đáy có gồ ghề cao thấp ra sao, mặt nước vẫn luôn bằng phẳng. Dòng chảy tài sản của toàn xã hội cũng vậy, bất kể ngành nghề nào, tỷ suất lợi nhuận đầu tư cuối cùng cũng sẽ tiệm cận một giá trị trung bình. 
Một việc nếu có thể kiếm được nhiều tiền, mà lại không có ai cạnh tranh, chỉ có thể nói rõ rủi ro quá lớn, khiến các nhà đầu tư khác e ngại. Chuyện ngồi mát ăn bát vàng là không có, rủi ro và lợi nhuận luôn tỷ lệ thuận với nhau. 
Thực ra, bất kỳ trò lừa đảo nào cũng có sơ hở, bạn chỉ cần nghiên cứu kỹ, sẽ phát hiện ra trong toàn bộ sự việc luôn có những yếu tố bạn không thể kiểm soát, hơn nữa lại là những khâu then chốt, hễ xảy ra vấn đề là chết người. Đó chính là sự tính toán kỹ lưỡng của người khác! Người nghèo lại bị kết quả tốt đẹp ảo tưởng kia cám dỗ, mà bỏ qua rủi ro trong đó. 
Người nghèo chưa từng lăn lộn trên thị trường vốn, không hiểu đặc tính của vốn là không tìm kiếm gì ngoài lợi nhuận, họ cứ nghĩ người ta tốt bụng, đến để giải phóng họ, kích động quá nên quên mất mình cũng đang đầu tư. Số tiền bỏ ra tuy không phải là con số thiên văn, nhưng cũng là tích góp cả đời, gần như là toàn bộ gia sản. 
Một tỷ phú, nếu cũng bỏ ra toàn bộ gia sản, tức là đầu tư hàng tỷ đồng, liệu họ có không cẩn thận khảo sát, luận chứng, đưa ra phương án hoàn hảo rồi mới ra tay không? Người nghèo thì lại chủ quan, đầu óc nóng lên là lao vào, đến khi phát hiện ra mình bị lừa, thì người ta đã cao chạy xa bay, bạn ngoài việc kêu trời than đất ra thì còn biết làm gì! 
Vốn dĩ việc tích lũy ban đầu của người nghèo đã khó, bị lừa như vậy một lần trong đời, có thể sẽ không bao giờ ngóc đầu lên được nữa. 

 



5. 1. Tập trung xây dựng hệ thống kiếm tiền của riêng mình
Học viên: "Hiện tại có quá nhiều dự án, không biết nên chọn dự án nào để kiếm được nhiều tiền."
Trả lời: "Dự án không phải là thứ đáng giá nhất, hệ thống kiếm tiền mới là. Đừng chạy theo dự án, hãy luôn tập trung xây dựng hệ thống kiếm tiền của riêng mình."
6. 2. Rất ít người có thể kiên trì cày cuốc trong 3 tháng
Học viên: "Trước đây vẫn luôn theo dõi thầy, cảm thấy tư duy đã được khai mở, bây giờ muốn bắt tay vào thực hành, những điều chưa hiểu, vừa học khóa VIP vừa hỏi thầy, dần dần tìm hiểu."
Trả lời: "Điều quan trọng nhất là nghĩ kỹ rồi hành động ngay lập tức, hơn nữa phải hành động có phương pháp. Tất cả các phương pháp đều đã được chia sẻ trong nhóm thành viên, bạn chỉ cần làm thôi, làm những việc cụ thể, gặp vấn đề thì phân tích cụ thể. Cứ làm hàng ngày, trong vòng 3 tháng nhất định sẽ có thành tích. Đáng tiếc, rất ít người có thể kiên trì cày cuốc trong 3 tháng."
7. 3. Viết trước một năm rồi hãy hỏi kỹ thuật
Học viên: "Luôn muốn viết công chúng hào, muốn hỏi thầy, viết công chúng hào có kỹ thuật gì không?"
Trả lời: "Công chúng hào có kỹ thuật gì? Viết trước một năm rồi hãy hỏi kỹ thuật. Mới học bắn cung mà đã hỏi làm thế nào để bắn trúng hồng tâm thì không có ý nghĩa, bắn vài nghìn mũi tên có cảm giác rồi thì nói về kỹ thuật mới có ý nghĩa."
8. 4. Những việc quá dễ dàng thường không có giá trị
Học viên: "Làm dự án thực sự là ép bản thân phải toàn năng, phải biết dẫn dắt lưu lượng, phải biết marketing, phải biết làm dịch vụ, còn phải biết trò chuyện, suốt ngày bận rộn, cũng khá phiền phức."
Trả lời: "Rất nhiều việc đều là do phiền phức mà ra. Giai đoạn đầu càng sợ phiền phức, giai đoạn sau càng phiền phức nhiều hơn. Dự án nào bắt đầu
thử nghiệm mà chẳng lóng ngóng, đủ loại việc phiền phức. Những việc quả dễ dàng thường không có giá trị, vì ai cũng có thể làm."
9. 5. Marketing quan trọng hơn kỹ thuật rất nhiều
Học viên: "Thứ giỏi nhất thường sẽ trở thành điểm yếu trong sự phát triển của một người! Vi dụ như năng lực cạnh tranh cốt lõi của tôi là làm đồ nướng, tôi ngày nào cũng làm đồ nướng, cực kỳ quen thuộc. Nhưng muốn mỗi ngày đều có tiến bộ, nâng cao thu nhập, gần như là không thể."
Trả lời: "Muốn học kỹ thuật, hãy liên tục đi thử những quán đồ nướng có tỷ lệ đánh giá cao nhất trong nước, trải nghiệm từng quán một, sau đó bắt chước, cuối cùng vượt qua họ. Tất nhiên, điều lợi hại nhất, nên là tư tưởng tiên tiến. Trên cơ sở kỹ thuật rất tốt, không ngừng học hỏi mô hình kinh doanh tiên tiến, và không ngừng thực hành. Không ngừng học hỏi tư duy marketing tiên tiến, phương pháp kiếm tiền, mới có thể không ngừng nâng cao thu nhập.
10. 6. Kiếm tiền là trò chơi nâng cao
Học viên: "Tôi tin vào quy luật 10.000 giờ, nhưng nếu một người giống như công nhân trên dây chuyển sản xuất, làm một việc gì đó một cách máy móc hơn 10.000 giờ, cũng không có ý nghĩa. Nói cách khác, trong 10.000 giờ, liên tục cải tiến và lặp lại, mới có giá trị."
Trả lời: "Kiếm tiền là trò chơi nâng cao, cốt lõi của việc tiến bộ là không ngừng bắt chước bậc thầy, không ngừng nâng cao, không ngừng thay đổi những người thầy giỏi hơn, từng bước đứng lên, đó mới là tư thế đúng đắn. Chỉ lặp lại một cách máy móc, ý nghĩa không lớn."
11. 7. Biết kiếm tiền không bằng khiến bản thân có giá trị hơn
Học viên: "Mặc dù hiện tại kiếm đủ tiền để nuôi sống gia đình, nhưng mỗi ngày đều bị đủ thứ việc vây quanh, thời gian đều tiêu tốn vào việc giao tiếp, họp hành, thăm hỏi, tăng ca, hoàn toàn không có thời gian để dừng lại suy nghĩ."
Trả lời: "Biết kiếm tiền không bằng khiến bản thân có giá trị hơn. Kiếm tiền sẽ ngày càng vất vả, có giá trị lại ngày càng thoải mái. Kiếm tiền là dựa vào hai tay, có giá trị là dùng tên tuổi. Tương lai là thời đại của cá nhân trối dậy, sớm một ngày xây dựng thương hiệu cá nhân, thì sớm một ngày đạt được tự đo. Vấn đề lớn nhất của con người là chỉ nhìn chằm chằm vào thu nhập trước mặt, không muôn đâu tư vào thương hiệu, vì thương hiệu là quá trình xây dựng lâu dài, cân tích lũy lâu dài mới thây được hiệu quả."
12. 8. Lựa chọn nhiều quá sẽ dẫn đến chỗ chết UEAc.store
Học viên: "Tôi thấy thầy nói về việc tập trung, có phải là chỉ được làm một dự án không. Hiện tại tôi đang làm đại lý rượu vang, lại có cửa hàng riêng, lại muốn thử bán một loại mỹ phẩm, phải làm sao bây giờ?"
Trả lời: "Một người chỉ nên chọn một dự án, làm cả đời, cho dù là kẻ ngốc, cũng có thể kiếm tiền, lựa chọn nhiều quá sẽ dẫn đến chỗ chết."
13. 9. Những thứ miễn phí đều có cái giá của nó
Học viên: "Rất nhiều người thích tìm tài liệu miễn phí để học, thực ra rất lãng phí thời gian, tôi thích trả phí trực tiếp, thẳng thắn. Trả phí, không phải để có được bao nhiêu tài liệu, mà là đế kết nối với những người giỏi đẳng sau đó!"
Trả lời: "Vì một cốc cà phê miễn phí mà chờ đợi một tiếng đồng hồ, uống xong cảm thấy mình được lợi rồi tự mãn, những người như vậy rất nhiều.
Những thứ miền phí đều có cái giá của nó, chỉ là rất nhiều người không nhận ra."
14. 10. Đừng dùng tình cảm và đạo đức để ràng buộc, yêu cầu người khác làm việc
Học viên: "Cần chú ý gì khi hợp tác với người khác?"
Trả lời: "Lúc nên chia sẻ lợi ích thì nhất định phải chia sẻ lợi ích, lúc nên trả tiền thì nhất định phải trả tiền, lúc nên tặng quà thì nhất định phải tặng quà.
Đừng dùng tình cảm và đạo đức để ràng buộc, yêu cầu người khác làm việc."
15. 11. Khóa học chia sẻ trong nhóm VIP chính là chuyên môn nâng cao thu nhập và khá năng marketing của một người
Học viên: "Cảm ơn thầy, lúc tôi ở điểm thấp nhất đã được học khóa VIP, lại nhen nhóm mục tiêu nhân sinh, đồng thời, phải nghiêm túc làm theo phương pháp trong khóa VIP đề rèn luyện bản thân, mới có thế liên tục chốt đơn! Cảm ơn sự cống hiến đầy yêu thương của thầy!"
Trả lời: "Khóa học marketing kiếm tiền VIP, chính là chuyên môn nâng cao thu nhập và khả năng marketing cua một người. Lâm việc có quy củ, cỏ nguyên tặc, có phương pháp, tự nhiên sẽ có thu nhập. Sông ngay thăng, có lòng biết ơn, tự nhiên sẽ có thành tựu. Kiên trì, hãy là một người quân tử, một người trưởng thành, một người khôn ngoan."
12. Học thuật ngữ không bằng học bản chất con người
Học viên: "Thầy ơi, em làm sales, có thuật ngữ nào không?"
Trả lời: "Học thuật ngữ không có ý nghĩa lắm, vì nó sẽ mất tác dụng khi tình huống thay đối. Muốn thực sự học nói, vân phải học cách nhìn thấu lòng người, quen thuộc với bản chất con người, đồng thời bản thân cũng phải có kiển thức. Học thuật ngữ không bằng học bản chất con người. Bản chất con người mới là thứ đánh trúng cốt lõi."
13. Đừng luôn đổ lỗi cho người khác không trả phí
Học viên: "Có vài khách hàng, đã nói sẽ mua, nhưng đến lúc trả tiền thì lằng nhằng..."
Trả lời: "Hãy tìm vấn đề của bản thân, đừng luôn đổ lỗi cho người khác không trả phí, hãy nghĩ xem, bản thân đã xuất hiện vấn đề gì."
14. Bất cứ ai có thể tập trung, thu nhập đều tăng gấp N lần
Học viên: "Càng học hỏi sâu, càng muốn thay đổi bản thân. Tập trung, không phải là một câu khẩu hiệu, mà là nền tảng hành động của tôi. Trước đây tôi nghĩ mình có thể làm rất nhiều việc, bây giờ tôi nghĩ mình chỉ có thể làm tốt một việc. Bất cứ lúc nào cũng phải tập trung, chỉ làm một dự án!"
Trả lời: "Trong nhóm VIP, bất cứ ai có thế tập trung, thu nhập đều tăng gấp N lần. Tập trung bao nhiêu, kiểm được bấy nhiêu tiền. Chỉ làm một dự án, thậm chỉ chỉ làm khâu kiếm tiền nhiều nhất là được. Những người có thói quen ăn từ đầu đến đuôi, đều chết."
15. Mọi phương pháp và kỹ thuật đều không bằng sự siêng năng và kiên trì
Học viên: "Trước đây kiểm tiền, đều dựa vào may mắn, vân luôn không thay đổi được tính xấu tự ti lười biếng của người nghèo, tiền đến nhanh, đi cũng nhanh. Vào nhóm VIP rồi, mới bắt đầu thấy căng thẳng, quả thực không thể sống u mê nữa, nhất định phải khiến bản thân mạnh mẽ lên, nếu không, tiền kiếm được nhờ may mắn, sẽ mất đi vì thực lực."
Trả lời: "Hoặc là cứ sống qua ngày, đừng nghĩ đến sự nghiệp. Hoặc là hãy làm việc chăm chỉ, làm việc không màng đến hậu quả. Thực ra đạo lý thành công rất đơn giản, mọi phương pháp và kỹ thuật đều không bằng sự siêng năng và kiên trì, mà mọi sự siêng năng và kiên trì, đều bắt nguồn từ thái độ làm việc và sự tận tâm. Hãy làm việc một cách thực tế, coi công việc như sự tu hành, coi sự nghiệp như sự tu hành, bạn sẽ kiếm được nhiều hơn!"
16. Vượt qua chính mình, thật thoải mái, thật sảng khoái
Học viên: "Tôi căm ghét bản thân yếu đuối trước đây, tôi phải thay đổi, phải trưởng thành, phải lột xác."
Trả lời: "Đừng bao giờ chiếm tiện nghi. Đừng bao giờ giở trò khôn vặt.
Đừng bao giờ tìm cách gian lận. Nhất định phải chọn việc khó nhất. Ngủ nướng không thoải mái, chơi game không thoải mái, đi mua sắm không thoải mái, du lịch cũng không thoải mái. Vượt qua chính mình, thật thoải mái, thật sảng khoái.
Thăng hoa rồi, tự tin hơn rồi, lợi hại hơn rồi. Cảm giác này, người yếu đuối sẽ không bao giờ cảm nhận được. Sự trưởng thành của một người, tóm lại là, những việc bạn từng sợ hãi, sẽ không còn sợ nữa."
17. Chưa đến 3 năm, bạn có thể hoàn toàn lột xác, thậm chí thay đổi vận mệnh
Học viên: "Thầy ơi, làm sao để nhanh chóng thay đổi bản thân, thay đổi vận mệnh?"
Trả lời: "Hãy làm marketing một cách thực tế, làm việc một cách thực tế.
Bạn không cần phải thay đổi vận mệnh trong một ngày, bạn thậm chí không cần phải tiến bộ 1% mỗi ngày, bạn chỉ cần tiến bộ 0,01% mỗi ngày, 1000 ngày, tức là chưa đến 3 năm, bạn có thể hoàn toàn lột xác, thậm chí thay đổi vận mệnh."
18. Một người kiểm được tiền chính là sự báo đáp tốt nhất cho xã hội
Học viên: "Thầy ợi, xin chào thầy! Thầy dã nói, gặp hất kỳ cảnh dẹp nào cũng phải biến thảnh tiền thật, về diểm này, em phải học hỏi thầy!"
Trà lời: "Tất cả thời gian phải đổi thành tiền, một người kiếm được tiền chính là sự báo đáp tốt nhất cho xã hội, vì bạn có giá trị đối với xã hội. Bạn kiếm được càng nhiều, chứng tỏ giá trị càng lớn. Tất nhiên, đều phải là con đường chân chính. Kiến thức trả phí, chính là con đường chân chính. Đây là điều có thể trường tồn."
19. Người hay de dự không phù hợp đế kinh doanh
Học viên: "Thầy ơi, trong WeChat của em có khách hàng của em, còn cỏ
một sô ông chủ đông nghiệp, còn có họ hàng bạn bè... Em muôn đăng bài lên vòng kết nối hạn bè, em nên chọn lọc xóa người, hay là dăng ký một tài khoăn
WeChat mới ạ?"
Trà lời: "Xóa người. Chặn. Hay là đăng ký một tải khoản mới. Em muốn làm thế nào thì cứ làm thôi, trong lòng em đã có câu trả lời rồi. Người hay do dự không phù hợp để kinh doanh."
20. Tranh thủ từng giây từng phút để tạo lưu lượng truy cập, làm marketing
Học viên: "Thầy ơi, rốt cuộc làm thế nào để kiểm tiền?"
Trà lời: "Tôi cho rằng, cốt lỗi của việc kiếm tiền, chẳng qua chỉ là tranh thủ từng giây từng phút dề tạo lưu lượng truy cập, làm marketing, cống hiển giá trị mà thôi. Nói trắng ra, chính là lúc bắt đầu một mình cày cuốc, thành thạo nghiệp vụ rồi, thì dẫn đắt cả nhóm cày cuốc. Sau đó lợi nhuận sẽ cao."
21. Đối với những người không được, hãy chặn ngay lập tức
Học viên: "Êm kiên quyết không niu kéo những người muốn rời đi, sau khi vào nhóm VIP, em mới hiểu được đạo lý này."
Trá lời: "Đối với những người không được, hãy chặn ngay lập tức, không chấp nhận, chỉ làm ăn với những người cùng tần số, tầng lớp cao, đừng cho bất kỳ ai cơ hội giải thích, điểm này, chi những người trải qua nhiều mới hiểu."
22. Làm được 2 điểm này, có thể vượt mặt rất nhiều người
Học viên: "Thầy ơi, làm thế nào để tặng quà cho người giỏi ạ?'"
Trà lời: "Họ bán gì thì mua nấy; họ nói gì thì làm nấy. Làm được 2 điểm này, có thể vượt mặt rấi nhiều người."

"""

# PHẦN B: KIẾN THỨC DỰ ÁN (Bạn dán thông tin uST, uTerra vào đây)
KIEN_THUC_DU_AN = """
1. Về uST (Unitsky String Technologies):
- Về uST (Unitsky String Technologies): Công nghệ giao thông đường dây trên cao, giải quyết tắc đường và ô nhiễm. Đang thương mại hóa toàn cầu.
- Công nghệ giao thông đường dây trên cao, giải quyết triệt để tắc đường và ô nhiễm.
- Đã được chứng nhận quốc tế, đang thương mại hóa toàn cầu (UAE, Sharjah...).
- Đây là mỏ vàng chưa lộ thiên hoàn toàn, cơ hội sở hữu cổ phần giá rẻ trước khi IPO.
- uST là gì
Giao thông tương lai
KHÁM PHÁ UST: CÔNG NGHỆ GIAO THÔNG CÁCH MẠNG CỦA TƯƠNG LAI!
Chào các nhà đầu tư tiên phong và những người dám nghĩ dám làm!
Bạn có bao giờ tưởng tượng một hệ thống giao thông không ùn tắc, không ô nhiễm và siêu tốc độ? Đó chính xác là những gì UST (Unitsky String Technologies) đang mang đến!
UST là gì?
UST là công nghệ vận tải chuỗi tiên tiến, sử dụng hệ thống đường ray treo cao độc đáo. Sử dụng công nghệ đường ray uST tiên tiến, đưa phương tiện lên cao cách mặt đất 10m – 25m. Tốc độ cao trong đô thị 150km/h, liên tỉnh 500km/h. Thời gian thi công nhanh, gọn, không cần giải phóng mặt bằng, đất đai nhà cửa, chi phí rẻ từ 5- 15 triệu $/km ( phụ thuộc vào nhu cầu) ,tiết kiệm năng lượng , không sử dụng xăng dầu ,an toàn gấp 1000 lần ( 250 trí tuệ nhân tạo AI ) ,thân thiện với môi trường…
Tưởng tượng một chiếc tàu điện trên không, nhưng nhanh hơn, an toàn hơn và thân thiện với môi trường hơn!
🔥 Tại sao UST là cơ hội VÀNG cho nhà đầu tư?

Công nghệ độc quyền: UST nắm giữ hơn 150 bằng sáng chế toàn cầu.
Thị trường khổng lồ: Dự kiến chiếm 50% thị phần vận tải toàn cầu, trị giá 400 tỷ USD! 💰
Đã được kiểm chứng: Thử nghiệm thành công tại Belarus và UAE.
Hỗ trợ quốc tế: Được tài trợ bởi các quỹ LHQ và nhiều quốc gia.
Tiềm năng tăng trưởng: Giá cổ phiếu dự kiến tăng từ 0.01$ lên 3-5$ sau IPO khoảng 2029-2033!
Tầm nhìn của UST:

Giải quyết vấn đề giao thông đô thị
Giảm ô nhiễm môi trường
Kết nối các vùng xa xôi với chi phí thấp
⏰ Đừng bỏ lỡ cơ hội này! UST đang trong giai đoạn cuối huy động vốn trước IPO. Hãy là một trong những người đầu tiên đầu tư vào tương lai giao thông!
Trang Web chính chức :https://ust.inc

- Anatoli Unitsky
Nhà phát minh uST
Anatoli Unitsky : Thiên tài của cuộc cách mạng giao thông thế kỷ 21
Bạn đã bao giờ tự hỏi ai là người có thể thay đổi cách chúng ta di chuyển trong tương lai? Hôm nay, hãy cùng tôi khám phá về Anatoli Unitsky – bộ óc thiên tài đằng sau công nghệ UST đang gây bão! 🌪️
Anatoli Unitsky là ai?
Tiến sĩ Anatoli Unitsky sinh ngày 16-04-1949 là một kỹ sư, nhà phát minh người, doanh nhân người Belarus.
Nhà khoa học, kỹ sư và nhà phát minh người Belarus 🇧🇾
Tác giả của hơn 150 phát minh được cấp bằng sáng chế 📜
Thành viên của Liên đoàn Vũ trụ Quốc tế 🚀
Cha đẻ của công nghệ vận tải chuỗi UST 🛤️
Giám đốc của hai dự án của Liên Hiệp Quốc.
Tác giả của 150 dự án và 200 phát minh
18 chuyên khảo và hơn 200 bài báo khoa học
Người được nhận giả thưởng hòa bình quốc tế Slovakia
Nằm trong sách đỏ thuộc Top 100 nhà lãnh đạo xuất sắc thiên nhiên kỷ
Chủ tịch Hội đồng quản trị, Nhà thiết kế chung của Unitsky String Technologies.

Tại sao Anatoli Unitsky là chìa khóa cho sự thành công của UST?
Tầm nhìn đột phá: Ông đã nghiên cứu và phát triển công nghệ UST trong hơn 40 năm!
Kinh nghiệm đa dạng: Từ vũ trụ đến giao thông mặt đất, ông áp dụng kiến thức liên ngành vào UST.
Giải pháp toàn diện: UST không chỉ là giao thông, mà còn là giải pháp cho vấn đề môi trường và đô thị hóa.
Được công nhận quốc tế: Dự án của ông được UNESCO và Liên Hợp Quốc hỗ trợ.
Đam mê không giới hạn: Ở tuổi 77, ông vẫn tiếp tục sáng tạo và phát triển UST!
- 3. Pháp lý & Dự án
Các dự án thương mại
UST: PHÁP LÝ VỮNG CHẮC, TIỀM NĂNG BÙNG NỔ – CƠ HỘI VÀNG CHO NHÀ ĐẦU TƯ TIÊN PHONG! 💎
Bạn đã sẵn sàng cho một cơ hội đầu tư có thể thay đổi cuộc đời? Hãy cùng tôi điểm qua những thông tin NÓNG HỔI về pháp lý và tiềm năng của UST! 📊
Pháp lý uST chuẩn mực quốc tế:
Được cấp phép bởi BVI-FSC (Ủy ban Dịch vụ Tài chính Quần đảo Virgin thuộc Anh) 🏛️
Kiểm toán tài chính bởi BDO – Top 5 công ty kiểm toán toàn cầu 🌐
Định giá công nghệ uST khổng lồ:
Công nghệ UST được định giá 400 TỶ USD! 💰
Dự án thương mại uST đang bùng nổ:
🇮🇳 Ấn Độ: Dự án tại Bihar – tiểu bang 100 triệu dân
🇮🇩 Indonesia: Kết nối các đảo với chi phí thấp
🇷🇺 Nga: Giải quyết vấn đề giao thông tại Moscow
🇺🇸 Hoa Kỳ: Đàm phán dự án tại nhiều bang
🇦🇪 UAE: Trung tâm thử nghiệm và chứng nhận tại Sharjah
GTI tuyên bố cổ tức của nhà đầu tư : https://hovanloi.net/gti-tuyen-bo-co-tuc-cua-nha-dau-tu/
Công ty GTI xác nhận nghĩa vụ trả cổ tức với nhà đầu tư. Trước đây, chúng tôi xem xét phương án phù hợp nhất, trong đó cổ tức sẽ được trả từ lợi nhuận của các công ty phân phối tổ hợp cơ sở hạ tầng và vận tải uST cũng như giấy phép cho công nghệ chuỗi uST.

- Tương lai: Mục tiêu IPO, cổ tức và tự do tài chính cho nhà đầu tư.

2. Về uTerra:
- Dự án nông nghiệp sinh học, sản xuất mùn vi sinh và thực phẩm sạch.
- Về uTerra: Dự án nông nghiệp sinh học, cải tạo đất mùn, sản xuất thực phẩm sạch. Một phần quan trọng trong hệ sinh thái.
- Một mảnh ghép quan trọng trong hệ sinh thái của ngài Anatoli Unitsky.
- Tiềm năng tăng trưởng lớn khi thế giới ngày càng cần thực phẩm sạch.
Website
- Belarus : uterra.by
- UAE : uterra.ae
- Việt Nam : uterravietnam.com

3. Về SWC (Sky World Community): Hệ sinh thái mạo hiểm-nhân ái, Trở thành đồng sở hữu các công nghệ thân thiện với môi trường được săn đón trong thời đại chúng ta, 
- Nền tảng gây quỹ cộng đồng uy tín, cầu nối đưa nhà đầu tư đến với uST.
- Chúng tôi chuyên tài trợ cho các công nghệ green-tech («xanh»)
- Về SWC (Sky World Community): Nền tảng gây quỹ cộng đồng, giúp nhà đầu tư sở hữu cổ phần Pre-IPO của công nghệ.
- Giúp người bình thường cũng có thể trở thành đồng sở hữu công nghệ giao thông tiên tiến nhất.
Wevsite : swc.capital
Mục Tiêu SWC
Tạo và tài trợ cho các công nghệ tiên tiến nhằm cải thiện cuộc sống — từ hạnh phúc cá nhân và độc lập tài chính đến phúc lợi môi trường toàn cầu và thay đổi tích cực trong cộng đồng toàn cầu.


Những con số về Sky World Community một nền tảng mà qua đó bất kỳ ai cũng có thể tài trợ cho các dự án đổi mới
 10+ năm năm thu hút vốn thành công
 180+ nước thành viên tham gia
 25+ nhóm ngôn ngữ
 Gần  1 000 000+ nhà đầu tư & đối tác trên toàn thế giới
- Cấu trúc : Hệ sinh thái Sky World Community bao gồm ba thành phần:
 + Định hướng tài chính (FinTech) : Định hướng tài chính-kỹ thuật. Sky World Community thúc đẩy việc thực hiện các dự án định hướng thân thiện với môi trường đầy hứa hẹn. Bất chấp sự biến động của thị trường, SWC đã thực hiện kế hoạch thu hút vốn một cách liên tục, thể hiện mình là một đối tác tốt, đáng tin cậy. Nền tảng đầu tư cộng đồng hiện đại của chúng tôi mang đến cho các thành viên của cộng đồng cơ hội trở thành một phần của các dự án quốc tế và kiếm được thu nhập xứng đáng trên cơ sở hợp tác đôi bên cùng có lợi.
 + Edtech : Định hướng giáo dục. Sky World Community nỗ lực hướng tới sự phát triển liên tục. Chúng tôi chia sẻ kiến ​​thức cần thiết và được yêu cầu với những ai muốn đạt được nhu cầu cao nhất theo năng lực của mình. Chúng tôi đã phát triển các chiến lược đào tạo hiệu quả của riêng mình, trên cơ sở đó chúng tôi đã tạo ra một trường Đại học trực tuyến cho các ngành nghề tương lai – nó sẽ giúp bạn đạt được mục tiêu của mình. Tại đây mọi người đều có thể nhận được sự cố vấn, hỗ trợ, học các chuyên ngành mới và phát triển các kỹ năng hiện có. 
 + Socialtech : Định hướng cộng đồng-xã hội. Chúng tôi thực hiện cách tiếp cận toàn diện để tạo ra một cộng đồng quốc tế gồm những người hướng tới một tương lai tươi sáng và thoải mái. Chúng tôi đã tích lũy được nguồn vốn xã hội khổng lồ và chúng tôi tự hào về cộng đồng thân thiện của mình, nơi mọi người có thể tin tưởng vào sự chấp nhận và hỗ trợ. Sky World Community trải rộng trên 5 châu lục, hơn 180 quốc gia và 20 nhóm ngôn ngữ trên toàn cầu. Tầm quan trọng và mức độ phù hợp của các dự án của chúng tôi đã thu hút hơn 600 nghìn người có quan điểm và giá trị tương tự.

Nhà Sáng Lập
1. Evgeniy Kudryashov, là người sáng lập hệ sinh thái mạo hiểm-nhân ái Sky World Community, diễn giả quốc tế, chuyên gia trong lĩnh vực góp vốn cộng đồng và là nhà đầu tư tư nhân thành đạt Evgeniy đến với lĩnh vực vận tải đường dây vào năm 2014, sau khi tham gia webinar trực tuyến của Anatoli Unitsky. Evgeniy là người khởi xướng việc thành lập hệ sinh thái Sky World Community và tích cực tham gia vào quá trình phát triển chiến lược của công ty: ông đã xây dựng cơ cấu tổ chức và áp dụng các công cụ quản lý mới.  Evgeniy trở thành người đứng sau những sản phẩm thành công của hệ sinh thái như nền tảng Smart và SWC Pay. Ông vẫn tập trung vào những ý tưởng và chiến lược mới giúp SWC tiến lên và đạt được các mục tiêu đã đề ra.
2. Alexey Sukhodoev, là chuyên gia về tài chính và đầu tư mạo hiểm, nhờ kinh nghiệm sâu rộng của mình, ông đã củng cố đáng kể vị thế của công ty Sky World Community (SWC). Dưới sự lãnh đạo của ông, hoạt động đào tạo các đội ngũ nội bộ đã được triển khai, góp phần tạo nên hệ thống truyền thông hiệu quả và tăng trưởng đáng kể hiệu quả tài chính của công ty. Alexey tích cực tham gia các diễn đàn kinh doanh và cuộc marathon trực tuyến, nâng cao độ nhận diện của SWC, và những nỗ lực của ông trong việc điều phối các dự án thương mại và tương tác với các chuyên gia toàn cầu tiếp tục đóng góp vào sự phát triển toàn diện của SWC.

Chương trình đối tác Sky World Community để thúc đẩy công nghệ sinh thái hiện đại
- Hàng nghìn người trên khắp thế giới đã ủng hộ các dự án của tập đoàn UST và UTerra Middle East Agro Industries. Sky World Community đang mang đến một cơ hội độc nhất vô nhị, không chỉ hỗ trợ tài chính cho các dự án đổi mới sáng tạo, mà còn trở thành một phần của cộng đồng quốc tế giúp thay đổi chất lượng cuộc sống của mỗi thành viên
- Về chương trình đối tác. Chương trình đối tác SWC là gì? Một công cụ tài chính cho phép bạn được tỷ lệ phần trăm từ nguồn tài trợ thu hút được cho các dự án và startup thân thiện với môi trường. Chúng tôi lựa chọn cẩn thận các khoản đầu tư của mình và cho phép các đối tác của cộng đồng được hưởng lợi về mặt tài chính bằng tiền thực




"""


FULL_KNOWLEDGE = f"""
KIẾN THỨC TÀI CHÍNH (LUẬT NGẦM):
{KIEN_THUC_TAI_CHINH}

KIẾN THỨC DỰ ÁN SWC/uST:
{KIEN_THUC_DU_AN}

(Dựa vào kiến thức trên để trả lời người dùng)
"""


# --- WEB SERVER ---
app_web = Flask('')
@app_web.route('/')
def home(): return "Bot SWC Debug Mode Ready!"
def run_web(): app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): t = Thread(target=run_web); t.start()

# --- XỬ LÝ GOOGLE SHEET ---
async def get_data_from_sheet(user_text):
    try:
        json_content = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not json_content: return None
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_content), ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        data = sheet.get_all_values()
        clean_user_text = re.sub(r'[^\w\s]', ' ', user_text).lower()
        for row in data[1:]:
            while len(row) < 5: row.append("")
            keywords = row[0].lower().split(',')
            for key in keywords:
                key = key.strip()
                if not key: continue
                pattern = r'(^|\s)' + re.escape(key) + r'(\s|$)'
                if re.search(pattern, clean_user_text):
                    return {"msg1": row[1], "msg2": row[2], "link": row[3], "img": row[4]}
        return None
    except Exception as e:
        print(f"Lỗi Sheet: {e}")
        return None

# --- XỬ LÝ AI ---
async def ask_ai(user_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return "⚠️ Admin chưa nhập Key AI!"
    genai.configure(api_key=api_key)
    now = datetime.now().strftime("%d/%m/%Y")
    full_input = f"{SYSTEM_PROMPT}\n\nHÔM NAY LÀ: {now}\n\n{FULL_KNOWLEDGE}\n\nNgười dùng nói: {user_text}\n(Lưu ý: Không in 'Đoạn 1'. Nếu ngắn thì không dùng '|||'.):"
    for model_name in AI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_input)
            clean_text = response.text
            for tag in ["**Đoạn 1:**", "Đoạn 1:", "Bước 1:", "**Đoạn 2:**", "Đoạn 2:", "Bước 2:", "**Đoạn 3:**", "Đoạn 3:", "Bước 3:"]:
                clean_text = clean_text.replace(tag, "")
            return clean_text
        except: continue 
    return "Bot đang bận đếm cổ phần (Hệ thống quá tải) 😭"

# --- HÀM GỬI TIN THÔNG MINH ---
async def send_smart_messages(update, context, text):
    chat_id = update.effective_chat.id
    global MESSAGE_COUNTER
    MESSAGE_COUNTER += 1 
    if "|||" not in text:
        final_msg = text
        if MESSAGE_COUNTER % 20 == 0: final_msg += f"\n{SIGNATURE}"
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
        await asyncio.sleep(2)
        await update.message.reply_text(final_msg)
        return
    chunks = [c.strip() for c in text.split('|||') if c.strip()]
    for i, chunk in enumerate(chunks):
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
        await asyncio.sleep(3)
        final_msg = chunk
        if i == len(chunks) - 1: 
            if MESSAGE_COUNTER % 20 == 0: final_msg += f"\n{SIGNATURE}"
        await update.message.reply_text(final_msg)

# ==============================================================================
# TÍNH NĂNG 1: SEEDING
# ==============================================================================
async def handle_seeding_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    post_content = msg.text or msg.caption or "Tin tức hình ảnh"
    seed_prompt = f"Hãy đóng vai nhà đầu tư lão luyện, viết bình luận ngắn (dưới 40 từ) hài hước về tin này: '{post_content}'"
    comment = await ask_ai(seed_prompt)
    try:
        await msg.reply_text(f"🔥 {comment}")
    except Exception as e: print(f"❌ Lỗi Seeding: {e}")

# ==============================================================================
# TÍNH NĂNG 2: ADMIN & CSKH (CÓ LOG CHI TIẾT)
# ==============================================================================
async def notify_admin_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Báo cho Admin biết có khách nhắn tin riêng"""
    user = update.effective_user
    text = update.message.text
    
    print(f"🔔 Đang cố gắng báo tin từ {user.full_name} cho Admin...") # <--- LOG KIỂM TRA

    notification = (
        f"📩 **CÓ KHÁCH HÀNG MỚI!**\n"
        f"👤 Tên: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💬 Nội dung: {text}\n"
        f"👉 Copy ID trên và dùng lệnh: `/gui {user.id} <Câu trả lời>`"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
            print(f"✅ Đã gửi báo cáo thành công cho Admin {admin_id}") # <--- LOG THÀNH CÔNG
        except Exception as e:
            print(f"❌ LỖI: Không gửi được cho Admin {admin_id}. Lý do: {e}") # <--- LOG LỖI (Quan trọng)

async def admin_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ Cách dùng: `/gui 123456789 Chào bạn...`")
        return
    target_id = context.args[0]
    msg = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=target_id, text=msg)
        await update.message.reply_text(f"✅ Đã gửi tới `{target_id}`")
    except Exception as e: await update.message.reply_text(f"❌ Lỗi: {e}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 ID: `{update.effective_chat.id}`", parse_mode='Markdown')

# ==============================================================================
# CHÀO MỪNG
# ==============================================================================
async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # (Giữ nguyên logic chào mừng cũ)
    for member in update.message.new_chat_members:
        if member.id == context.bot.id: continue
        welcome_text = f"Chào mừng {member.full_name} gia nhập SWC Việt Nam!"
        try: await update.message.reply_text(welcome_text)
        except: pass

# --- MAIN HANDLER (ĐIỀU PHỐI) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return

    # 1. Seeding
    if update.message.is_automatic_forward:
        await handle_seeding_in_group(update, context)
        return

    if not update.message.text: return
    
    # 2. XỬ LÝ TIN NHẮN RIÊNG (CSKH) - CÓ LOG KIỂM TRA
    if update.effective_chat.type == constants.ChatType.PRIVATE:
        user_id = update.message.from_user.id
        print(f"👀 Có tin nhắn riêng từ ID: {user_id}") # <--- LOG XEM AI NHẮN
        
        if user_id not in ADMIN_IDS:
            print("👉 Đây là Khách Hàng! Đang gọi hàm báo Admin...")
            await notify_admin_dm(update, context)
        else:
            print("👉 Đây là Admin ( SWC ). Không báo cáo.")

    # 3. Chặn Admin trong nhóm
    if update.effective_chat.type != constants.ChatType.PRIVATE:
        if update.message.from_user.id in ADMIN_IDS: return 

    user_text = update.message.text.lower()
    
    # 4. Sheet & AI
    data = await get_data_from_sheet(user_text) if len(user_text) < 60 else None
    if data:
        global MESSAGE_COUNTER
        MESSAGE_COUNTER += 1
        msg = data['msg1']
        if data['link']: msg += f"\n👉 Link: {data['link']}"
        if MESSAGE_COUNTER % 20 == 0: msg += f"\n{SIGNATURE}"
        try: await update.message.reply_text(msg)
        except: pass
    else:
        await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
        ans = await ask_ai(user_text)
        if ans: await send_smart_messages(update, context, ans)

if __name__ == '__main__':
    keep_alive()
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if TOKEN:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("id", get_id))
        app.add_handler(CommandHandler("gui", admin_send_message))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_chat_members))
        app.add_handler(MessageHandler(filters.ALL, handle_message))
        print("Bot SWC Debug Version Ready...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
