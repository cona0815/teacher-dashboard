"""產生 assets/art/art_spec.json：教師工作台介面美術（大屏提示插圖、安靜偵測、介面圖示）的清單與規格。

python tools/make_art_spec.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'art' / 'art_spec.json'

GREEN, BLUE, ORANGE, PURPLE = '#1f7a52', '#2457e6', '#d0631a', '#7b4fb8'

# 大屏提示：每一句一張插圖（文字由系統疊在圖上方，圖裡不能有字）
PROMPTS = [
    # 上課秩序（綠）
    ('focus_teacher', '上課囉！眼睛看老師', GREEN, 'lamb, cat, dog, robot',
     '四隻並排坐在小課桌後面，全部抬頭、眼睛直直看向觀眾（老師的方向），lamb 在正中間最大、雙前蹄放桌上'),
    ('sit_up', '坐姿端正，抬頭挺胸', GREEN, 'lamb（主）, cat',
     'lamb 坐在椅子上挺胸、背打直、雙蹄放膝上，表情驕傲；旁邊 cat 正在把背挺直跟著學；身後一條淡綠色直線光暈強調「直」'),
    ('sit_fast', '動作快，三秒內坐好', GREEN, 'dog（主）',
     'dog 一個箭步衝向椅子、身體有速度線，屁股快要坐到椅子上；頭上方三顆圓燈（兩顆亮、一顆暗）表示倒數，不可用數字'),
    ('raise_hand', '發言請舉手，輪流說', GREEN, 'cat（主）, dog, robot',
     'cat 坐在座位上高高舉起前腳、嘴巴閉著等待；後面 dog 和 robot 也舉手但安靜等待輪到自己'),
    ('quiet_zero', '安靜！音量零級', GREEN, 'lamb（主）',
     'lamb 正面大特寫（半身），一隻前蹄豎在嘴前做「噓」，眼睛溫柔；旁邊一個圓形音量表指針停在最左邊（只用圖形，不要刻度數字）'),
    ('whisper', '輕聲討論，別吵到隔壁組', GREEN, 'cat, dog',
     'cat 和 dog 頭靠在一起小聲說話，前腳擋在嘴邊，周圍只有很小很淡的聲波弧線；畫面另一側有一張空桌子保持距離感'),
    # 作業與學習（藍）
    ('hand_in', '收作業囉，交給小組長', BLUE, 'dog, lamb',
     'dog 雙手捧一疊作業本交出去，lamb 手臂戴藍色臂章（組長，不寫字）伸手接過，兩隻都笑'),
    ('correction', '訂正完拿給老師檢查', BLUE, 'cat（主）',
     'cat 雙手把一本攤開的作業本往前遞（朝觀眾），本子上看得到紅筆訂正的線條和勾勾（線條，不是文字）'),
    ('self_check', '寫完的同學自己再檢查一遍', BLUE, 'robot（主）',
     'robot 坐在桌前，一手拿放大鏡仔細看自己的作業本，螢幕臉表情專心，胸口晶片亮著'),
    ('reading', '閱讀時間，安靜看書', BLUE, 'lamb（主）',
     'lamb 坐在小地墊上捧著一本打開的書看得入迷，書頁透出柔和光；旁邊疊兩本書'),
    ('self_study', '自習時間，完成自己的進度', BLUE, 'robot, cat',
     'robot 和 cat 各自在自己的桌子寫作業，低頭專心；桌角各有一個小沙漏'),
    ('circle_question', '不會的先圈起來，等一下問', BLUE, 'dog（主）',
     'dog 拿鉛筆在作業本上畫一個大圓圈，頭上冒出一個圓形泡泡、裡面是問號形狀（問號是符號，可以）'),
    # 生活作息（橘）
    ('drink_toilet', '下課先喝水、上廁所', ORANGE, 'dog（主）, cat',
     'dog 仰頭用水壺喝水；後方 cat 走向一扇有水滴圖示的門（不可寫 WC 或任何字）'),
    ('lunch', '吃飯不說話，細嚼慢嚥', ORANGE, 'lamb, cat, dog, robot',
     '四隻圍著桌子吃營養午餐（不鏽鋼分格餐盤），嘴巴閉著咀嚼、表情滿足；robot 的盤子裡放電池形狀的食物'),
    ('nap', '午休時間，趴下休息', ORANGE, 'lamb, cat, dog, robot',
     '四隻趴在課桌上睡覺，臉頰壓在前腳上，頭上飄著圓形 zzz 泡泡（只用圓形，不用字母）；robot 螢幕表情是閉眼'),
    ('cleaning', '打掃時間，責任區掃乾淨', ORANGE, 'lamb, robot, cat',
     'lamb 拿掃把、cat 拿畚箕、robot 拿拖把，三隻一起打掃，地板亮晶晶的閃光'),
    ('tidy_bag', '整理書包，檢查抽屜', ORANGE, 'cat（主）',
     'cat 把課本放進打開的書包，旁邊課桌抽屜拉開、裡面整整齊齊'),
    # 集合與移動（紫）
    ('line_up', '排隊囉！快、靜、齊', PURPLE, 'lamb, cat, dog, robot',
     '四隻排成一直線（側面 3/4 角度，由前到後），每隻雙手放身體兩側、嘴巴閉著、間距一樣'),
    ('hallway', '到走廊排隊，不推不擠', PURPLE, 'cat, dog, lamb',
     '三隻在走廊上排隊往前走，彼此保持一個手臂的距離，地上有淡淡的排隊腳印標記'),
    ('stairs', '上下樓梯靠右走、不奔跑', PURPLE, 'lamb, dog',
     '一段樓梯，lamb 和 dog 靠樓梯右側扶手一步一步慢慢走，右側扶手明顯；左側空著'),
    ('special_room', '專科教室集合，帶課本鉛筆盒', PURPLE, 'robot, cat, lamb',
     '三隻排隊往前走，每隻都抱著課本和鉛筆盒，表情期待'),
    ('go_home', '準備放學：桌面清空、帶齊物品', PURPLE, 'lamb, cat, dog, robot',
     '四隻背好書包站在乾淨的空桌子旁邊揮手說再見，背景一道夕陽色的柔光圓'),
    # 自訂提示的預設圖
    ('custom_default', '（老師自訂的提示）', GREEN, 'lamb（主）',
     'lamb 站著，一隻前蹄往上指（指向圖上方系統顯示的文字），另一隻扠腰，表情自信；適合任何提醒'),
]

QUIET = [
    ('quiet_super', '超安靜（遠低於門檻）', GREEN, 'lamb',
     'lamb 閉眼微笑、雙蹄合十放胸前，周圍飄著幾顆小星星，很平靜'),
    ('quiet_good', '安靜（低於門檻）', GREEN, 'cat',
     'cat 一隻前腳豎在嘴前「噓」，眼睛眨一隻，表情俏皮'),
    ('quiet_warn', '有點聲音（接近門檻）', ORANGE, 'dog',
     'dog 耳朵往後壓、雙前腳摀住一邊耳朵，表情有點擔心，頭旁邊冒一滴汗'),
    ('quiet_loud', '太吵了（超過門檻）', '#cf4433', 'lamb, cat, dog, robot',
     '四隻同時摀住耳朵、表情崩潰（眼睛變成螺旋或 >< 形狀），周圍很多鋸齒狀聲波，robot 螢幕顯示雜訊；這是唯一一張「錯誤示範」'),
]

# 介面圖示：小綿助家族風格的「物件」；角色只用在身分圖示
ICONS = [
    # 晨間大屏分頁
    ('tab_rollcall', '點名', 'Morning.html 分頁', '點名板夾著一張打勾名單、上面一個小鈴鐺'),
    ('tab_homework', '作業繳交', 'Morning.html 分頁', '打開的書包露出作業本'),
    ('tab_makeup', '作業補交', 'Morning.html 分頁', '作業本旁邊一個沙漏'),
    ('tab_correct', '作業訂正', 'Morning.html 分頁', '紅筆斜放在打勾的作業本上'),
    ('tab_query', '查詢統計', 'Morning.html 分頁', '放大鏡壓在長條圖上'),
    ('tab_tools', '班級工具', 'Morning.html 分頁', '打開的工具箱，裡面露出骰子和碼錶'),
    ('tab_setup', '設定', 'Morning.html 分頁', '圓圓的齒輪，中間一顆鈕扣'),
    ('contact_book', '聯絡本', 'Morning.html 聯絡本標題、Index.html 聯絡本', '一本綠色封面的聯絡簿，夾著鉛筆'),
    # 班級工具八個圖磚
    ('tool_lottery', '抽籤機', 'Morning.html 班級工具', '彩色轉盤加一根紅色指針'),
    ('tool_check', '檢核板', 'Morning.html 班級工具', '板夾上三格勾勾'),
    ('tool_score', '計分板', 'Morning.html 班級工具', '金色獎盃'),
    ('tool_group', '隨機分組', 'Morning.html 班級工具', '三顆不同顏色的小球分成兩堆'),
    ('tool_quiet', '安靜偵測', 'Morning.html 班級工具', '麥克風旁邊一條平平的聲波'),
    ('tool_exam', '定評小幫手', 'Morning.html 班級工具', '考卷加一支鉛筆和小時鐘'),
    ('tool_tomato', '番茄鐘', 'Morning.html 班級工具', '番茄形狀的計時器'),
    ('tool_prompt', '大屏提示', 'Morning.html 班級工具', '大聲公（擴音器）'),
    # 工作台摘要卡
    ('sum_todo', '待辦總數', 'Index.html 摘要卡', '一疊便條紙，最上面一張有三條線'),
    ('sum_weekly', '本週重點', 'Index.html 摘要卡', '一顆金色星星'),
    ('sum_waiting', '等待回覆', 'Index.html 摘要卡、Board.html', '沙漏'),
    ('sum_duetoday', '今日截止', 'Index.html 摘要卡、Board.html', '鬧鐘'),
    ('sum_overdue', '逾期追蹤', 'Index.html 摘要卡', '搖晃中的手搖鈴'),
    ('sum_done', '本期完成', 'Index.html 摘要卡、Board.html', '起飛的小火箭'),
    ('sum_urgent', '高優先', 'Board.html KPI', '紅色旗子插在文件上'),
    # 工作台面板標題
    ('panel_toolbox', '教師工具箱', 'Index.html', '手提工具箱'),
    ('panel_progress', '教學與評量進度', 'Index.html', '指南針'),
    ('panel_ai', 'AI 行政助理', 'Index.html', '機器人頭（用 robot 角色的頭，正面）'),
    ('panel_line_inbox', 'LINE 收件匣', 'Index.html', '綠色對話框形狀的信箱（不可用 LINE 商標）'),
    ('panel_message_hub', '訊息整合站', 'Index.html', '郵筒'),
    ('panel_filter', '篩選任務', 'Index.html', '漏斗'),
    ('panel_tasks', '任務清單', 'Index.html、小綿助圖片載入失敗時的備用圖', '鉛筆加一張打勾清單'),
    # 身分（角色當代表）
    ('role_grade_lead', '學年主任', 'Index.html 身分切換、Board.html 標題', 'dog 半身，拿著板夾和小擴音器'),
    ('role_admin', '行政', 'Index.html 身分切換', 'robot 半身，抱著一疊公文夾'),
    ('role_homeroom', '導師', 'Index.html 身分切換', 'lamb 半身，戴項圈獎牌、身旁一面小班旗（無字）'),
    ('role_teacher', '教師', 'Index.html 身分切換', 'cat 半身，抱著課本'),
]

spec = {
    'version': 1,
    'reference': {
        'characters': 'assets/pet/v4/reference/<lamb|cat|dog|robot>/<姿勢>.png',
        'note': '老師自己的正式角色美術（小綿助家族）。所有插圖的角色外表、配色、筆觸都以此為準。'
    },
    'style': [
        '角色只用小綿助家族：lamb（小綿羊）、cat（橘虎斑貓）、dog（薩摩耶）、robot（藍白懸浮機器人），外表照 reference，項圈獎牌、配色、頭身比都不能變',
        '不畫人類（沒有學生、沒有老師人物），角色就是班上的學生',
        '筆觸照 reference：柔和漸層陰影、毛絨毛邊、暖棕色描邊（不是黑線）、腮紅、眼睛兩點高光',
        '光源統一在左上；地面只畫一個柔和的橢圓影子，不畫整片背景',
        '圖裡不可以有任何文字、數字、字母、商標；系統會在圖的上方顯示大字',
        '示範正確行為（quiet_loud 是唯一的錯誤示範）；不要危險動作',
        '台灣國小教室的物件：單人課桌椅、聯絡簿、不鏽鋼分格餐盤、掃把畚箕、樓梯扶手',
        '每張插圖用該分類的強調色點綴（道具、光暈），但角色本身的顏色不變'
    ],
    'formats': {
        'prompt': {'master': [1920, 1440], 'web': [960, 720], 'web_format': 'webp', 'web_max_kb': 160, 'background': 'transparent',
                   'display': '晨間大屏「大屏提示」：文字在上、圖在下，投影全螢幕時圖高約 38vh（1080p 約 410px），要在教室後排 8 公尺外看懂',
                   'safe_area': '主體外框（不透明像素）落在畫布 6%–94% 之內，不要貼邊'},
        'quiet': {'master': [1600, 1600], 'web': [800, 800], 'web_format': 'webp', 'web_max_kb': 120, 'background': 'transparent',
                  'display': '「安靜偵測」中間的角色，平常高 230px、投影時放大；系統會加上漂浮、搖晃動畫',
                  'safe_area': '主體外框落在 6%–94% 之內'},
        'icon': {'master': [1024, 1024], 'web': [256, 256], 'web_format': 'webp', 'web_max_kb': 30, 'background': 'transparent',
                 'display': '介面圖示，實際顯示 22–80px；系統會自己加圓角色塊底，圖示本身不要畫底色方塊',
                 'safe_area': '主體外框落在 8%–92% 之內，置中',
                 'rules': '一個圖示一個主物件、輪廓粗而清楚，縮到 22px 還認得出來；物件可以有小小的臉（點點眼＋腮紅）讓它可愛，但不要細節雜訊'}
    },
    'paths': {
        'web': 'assets/art/<kind>/<id>.webp（kind = prompt、quiet、icon）',
        'master': 'assets/art/_masters/<kind>/<id>.png（不 commit）',
        'review': 'assets/art/_review/（check_art.py --review 產生，不 commit）'
    },
    'prompt': [{'id': i, 'text': t, 'accent': a, 'cast': c, 'scene': d} for i, t, a, c, d in PROMPTS],
    'quiet': [{'id': i, 'state': t, 'accent': a, 'cast': c, 'scene': d} for i, t, a, c, d in QUIET],
    'icon': [{'id': i, 'label': l, 'used_in': u, 'subject': d} for i, l, u, d in ICONS],
    'first_batch': ['prompt/focus_teacher', 'prompt/nap', 'prompt/line_up', 'quiet/quiet_good',
                    'icon/tab_rollcall', 'icon/tool_lottery', 'icon/tool_tomato', 'icon/role_homeroom']
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(len(PROMPTS), 'prompt', len(QUIET), 'quiet', len(ICONS), 'icon')
