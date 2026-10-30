"""產生 assets/art/art_spec.json：教師工作台介面美術（三套可切換風格 × 大屏提示插圖、安靜偵測、介面圖示）。

python tools/make_art_spec.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'art' / 'art_spec.json'

GREEN, BLUE, ORANGE, PURPLE, RED = 'order', 'study', 'life', 'move', 'alert'

# 三套風格：同一份清單、同一個檔名，各畫一次；網頁切換風格時整套換掉
THEMES = [
    {'id': 'tech', 'name': '科技',
     'mood': '未來教室、資訊看板：深藍夜色、青與紫的霓虹光、玻璃質感、細網格',
     'palette': {'bg': '#0b1020', 'surface': '#141c36', 'ink': '#e6f0ff', 'muted': '#8a98bd', 'primary': '#22d3ee', 'accent': '#a78bfa',
                 'order': '#34d399', 'study': '#38bdf8', 'life': '#fbbf24', 'move': '#c084fc', 'alert': '#f87171'},
     'icon': '線框發光圖示：等粗圓角線條（256px 畫布約 10px 粗）、主色青 #22d3ee、局部一個強調色、外面一圈柔和光暈；把光暈拿掉後剪影仍然認得出來',
     'illustration': '等角（isometric）視角的光滑 3D 場景：物件是半透明玻璃＋發光邊；人物是無五官的圓頭全息人偶（青色半透明、身體簡化成膠囊形）；少量發光粒子點綴',
     'figure': '無五官圓頭全息人偶',
     'avoid': '不要真實照片感、不要複雜電路板花紋、不要駭客綠字雨'},
    {'id': 'minimal', 'name': '簡潔',
     'mood': '像交通標誌與瑞士海報：白底、大量留白、一眼看懂、零裝飾',
     'palette': {'bg': '#ffffff', 'surface': '#f4f5f7', 'ink': '#1f2328', 'muted': '#6b7280', 'primary': '#2563eb', 'accent': '#111827',
                 'order': '#15803d', 'study': '#2563eb', 'life': '#ea580c', 'move': '#7c3aed', 'alert': '#dc2626'},
     'icon': '雙色調圖示：以 24 格為基準的幾何線條（256px 畫布約 21px 粗、圓角轉折）＋一塊淡色填色；只用該分類主色與一個淡色，沒有陰影、沒有漸層',
     'illustration': '扁平幾何插畫：人物是 pictogram 式（圓頭無五官、身體用圓角矩形、四肢是粗圓角線），2–3 個顏色、不陰影、不漸層、不描邊',
     'figure': 'pictogram 圓頭人形',
     'avoid': '不要質感、不要陰影、不要多於 3 個顏色、不要裝飾小物'},
    {'id': 'cozy', 'name': '動森風',
     'mood': '悠閒小島生活的手作溫暖感：奶油色、草綠、天空藍、木頭棕；圓滾滾、柔和陰影、像貼紙或繪本',
     'palette': {'bg': '#fbf5e6', 'surface': '#fffaf0', 'ink': '#5b4636', 'muted': '#9c8a74', 'primary': '#6cbf5b', 'accent': '#5ab4e5',
                 'order': '#6cbf5b', 'study': '#5ab4e5', 'life': '#f2a541', 'move': '#b58ad6', 'alert': '#e86a5a'},
     'icon': '圓胖的實心物件貼紙：粗的深棕描邊（256px 畫布約 12px）、柔和高光、外圍一圈白邊像貼紙；大尺寸時旁邊可以點綴一片小葉子或小花（22px 看不到也沒關係）',
     'illustration': '手繪繪本感：柔和水彩紋理、圓潤輪廓、深棕描邊；人物是原創 Q 版學生（2.5 頭身、圓臉、點點眼、腮紅、短手短腳）；場景點綴草地、小花、空白木牌',
     'figure': '原創 Q 版學生（2.5 頭身）',
     'avoid': '這是「風格」不是同人圖：不可出現任天堂或《集合啦！動物森友會》的任何角色（狸克、西施惠、豆狸粒狸、傅達等）、葉子標誌、NookPhone、遊戲字型或介面元件；也不要畫成動物村民'},
]

# 大屏提示：每一句一張插圖（文字由系統疊在圖上方，圖裡不能有字）
PROMPTS = [
    ('focus_teacher', '上課囉！眼睛看老師', GREEN, '三位學生並排坐在課桌後面，全部抬頭、眼睛（或臉）朝向觀眾，雙手放桌上'),
    ('sit_up', '坐姿端正，抬頭挺胸', GREEN, '一位學生側面坐在椅子上，背打直、雙腳平放、雙手放腿上；背後一條直線強調「直」'),
    ('sit_fast', '動作快，三秒內坐好', GREEN, '一位學生快步走向椅子、身後有速度線；上方三顆圓燈（兩顆亮、一顆暗）表示倒數，不可用數字'),
    ('raise_hand', '發言請舉手，輪流說', GREEN, '一位學生坐著高高舉手、嘴巴閉著等待；旁邊兩位也舉手但安靜等'),
    ('quiet_zero', '安靜！音量零級', GREEN, '一位學生半身大特寫，食指豎在嘴前做「噓」；旁邊一個圓形音量表指針停在最左邊（只用圖形，沒有刻度數字）'),
    ('whisper', '輕聲討論，別吵到隔壁組', GREEN, '兩位學生頭靠在一起小聲說話、手擋在嘴邊，周圍只有很小的聲波弧線；畫面另一邊一張保持距離的空桌'),
    ('hand_in', '收作業囉，交給小組長', BLUE, '一位學生雙手把一疊作業本交給另一位戴臂章（不寫字）的小組長'),
    ('correction', '訂正完拿給老師檢查', BLUE, '一位學生雙手把攤開的作業本往前遞（朝觀眾），本子上看得到紅色訂正線與勾勾（線條，不是文字）'),
    ('self_check', '寫完的同學自己再檢查一遍', BLUE, '一位學生坐在桌前，拿放大鏡仔細看自己的作業本'),
    ('reading', '閱讀時間，安靜看書', BLUE, '一位學生坐著捧一本打開的書看得入迷，旁邊疊兩本書'),
    ('self_study', '自習時間，完成自己的進度', BLUE, '兩位學生各自在自己的桌子低頭寫作業，桌角各有一個小沙漏'),
    ('circle_question', '不會的先圈起來，等一下問', BLUE, '一支鉛筆在作業本上畫一個大圓圈，旁邊一個問號形狀的泡泡（問號是符號，可以）'),
    ('drink_toilet', '下課先喝水、上廁所', ORANGE, '一位學生仰頭用水壺喝水；後面一扇門上有水滴圖示（不可寫 WC 或任何字）'),
    ('lunch', '吃飯不說話，細嚼慢嚥', ORANGE, '三位學生圍著桌子吃營養午餐（不鏽鋼分格餐盤），嘴巴閉著咀嚼'),
    ('nap', '午休時間，趴下休息', ORANGE, '兩三位學生趴在課桌上睡覺，上方飄著圓形泡泡（不要寫 Z）'),
    ('cleaning', '打掃時間，責任區掃乾淨', ORANGE, '三位學生分別拿掃把、畚箕、拖把打掃，地板有乾淨的閃光'),
    ('tidy_bag', '整理書包，檢查抽屜', ORANGE, '一個打開的書包正放進課本，旁邊課桌抽屜拉開、裡面整整齊齊'),
    ('line_up', '排隊囉！快、靜、齊', PURPLE, '四位學生排成一直線（3/4 側面、由前到後），雙手放兩側、間距一樣'),
    ('hallway', '到走廊排隊，不推不擠', PURPLE, '三位學生在走廊排隊往前走，彼此保持一個手臂的距離，地上有排隊腳印標記'),
    ('stairs', '上下樓梯靠右走、不奔跑', PURPLE, '一段樓梯，兩位學生靠右側扶手一步一步慢慢走；右側扶手明顯、左側空著'),
    ('special_room', '專科教室集合，帶課本鉛筆盒', PURPLE, '三位學生排隊往前走，每人抱著課本和鉛筆盒'),
    ('go_home', '準備放學：桌面清空、帶齊物品', PURPLE, '兩位學生背好書包站在乾淨的空桌子旁揮手再見'),
    ('custom_default', '（老師自訂的提示）', GREEN, '一個大大的擴音器（大聲公）往右上方發出聲波，適合任何提醒'),
]

QUIET = [
    ('quiet_super', '超安靜（遠低於門檻）', GREEN, '一位學生閉眼微笑、雙手合十，周圍幾顆小星星，很平靜'),
    ('quiet_good', '安靜（低於門檻）', GREEN, '一位學生食指豎在嘴前「噓」，眨一隻眼'),
    ('quiet_warn', '有點聲音（接近門檻）', ORANGE, '一位學生摀住一邊耳朵、表情擔心，旁邊一滴汗'),
    ('quiet_loud', '太吵了（超過門檻）', RED, '三位學生同時摀住耳朵、表情崩潰，周圍很多鋸齒狀聲波；唯一一張「錯誤示範」'),
]

# 介面圖示：一個主物件；身分圖示才畫人物
ICONS = [
    ('tab_rollcall', '點名', 'Morning.html 分頁', '板夾夾著一張打勾名單'),
    ('tab_homework', '作業繳交', 'Morning.html 分頁', '打開的書包露出作業本'),
    ('tab_makeup', '作業補交', 'Morning.html 分頁', '作業本旁邊一個沙漏'),
    ('tab_correct', '作業訂正', 'Morning.html 分頁', '紅筆斜放在打勾的作業本上'),
    ('tab_query', '查詢統計', 'Morning.html 分頁', '放大鏡壓在長條圖上'),
    ('tab_tools', '班級工具', 'Morning.html 分頁', '打開的工具箱'),
    ('tab_setup', '設定', 'Morning.html 分頁', '齒輪'),
    ('contact_book', '聯絡本', 'Morning.html 聯絡本標題、Index.html 聯絡本', '一本聯絡簿夾著鉛筆'),
    ('tool_lottery', '抽籤機', 'Morning.html 班級工具', '轉盤加一根指針'),
    ('tool_check', '檢核板', 'Morning.html 班級工具', '板夾上三格勾勾'),
    ('tool_score', '計分板', 'Morning.html 班級工具', '獎盃'),
    ('tool_group', '隨機分組', 'Morning.html 班級工具', '幾顆小球分成兩堆'),
    ('tool_quiet', '安靜偵測', 'Morning.html 班級工具', '麥克風旁邊一條平平的聲波'),
    ('tool_exam', '定評小幫手', 'Morning.html 班級工具', '考卷加一支鉛筆'),
    ('tool_tomato', '番茄鐘', 'Morning.html 班級工具', '番茄形狀的計時器'),
    ('tool_prompt', '大屏提示', 'Morning.html 班級工具', '擴音器（大聲公）'),
    ('sum_todo', '待辦總數', 'Index.html 摘要卡', '一疊便條紙'),
    ('sum_weekly', '本週重點', 'Index.html 摘要卡', '星星'),
    ('sum_waiting', '等待回覆', 'Index.html 摘要卡、Board.html', '沙漏'),
    ('sum_duetoday', '今日截止', 'Index.html 摘要卡、Board.html', '鬧鐘'),
    ('sum_overdue', '逾期追蹤', 'Index.html 摘要卡', '搖晃的手搖鈴'),
    ('sum_done', '本期完成', 'Index.html 摘要卡、Board.html', '起飛的火箭'),
    ('sum_urgent', '高優先', 'Board.html KPI', '旗子插在文件上'),
    ('panel_toolbox', '教師工具箱', 'Index.html', '手提工具箱'),
    ('panel_progress', '教學與評量進度', 'Index.html', '指南針'),
    ('panel_ai', 'AI 行政助理', 'Index.html', '簡單的機器人頭（原創，不是小綿助家族的機器人）'),
    ('panel_line_inbox', 'LINE 收件匣', 'Index.html', '對話框形狀的信箱（不可用 LINE 商標）'),
    ('panel_message_hub', '訊息整合站', 'Index.html', '郵筒'),
    ('panel_filter', '篩選任務', 'Index.html', '漏斗'),
    ('panel_tasks', '任務清單', 'Index.html', '鉛筆加一張打勾清單'),
    ('role_grade_lead', '學年主任', 'Index.html 身分切換、Board.html 標題', '一位老師半身，拿板夾和小擴音器'),
    ('role_admin', '行政', 'Index.html 身分切換', '一位老師半身，抱一疊公文夾'),
    ('role_homeroom', '導師', 'Index.html 身分切換', '一位老師半身，身旁一面小班旗（無字）'),
    ('role_teacher', '教師', 'Index.html 身分切換', '一位老師半身，抱著課本'),
]

spec = {
    'version': 2,
    'themes': THEMES,
    'style': [
        '三套風格（tech、minimal、cozy）各畫一整套，同一個 id 的三張畫的是同一件事，只有畫風不同',
        '同一套風格裡的所有圖要像同一個設計師畫的：線條粗細、顏色、光源、人物比例一致',
        '不可以出現小綿助家族（綿羊、橘貓、薩摩耶、藍白機器人）或任何像牠們的角色；系統美術和桌寵要明顯不同',
        '人物用各風格的 figure 設定；學生男女都有、穿一般便服或運動服，不畫特定學校制服或校徽',
        '圖裡不可以有任何文字、數字、字母、商標；系統會在圖的上方顯示大字',
        '示範正確行為（quiet_loud 是唯一的錯誤示範）；不要危險動作',
        '台灣國小教室的物件：單人課桌椅、聯絡簿、不鏽鋼分格餐盤、掃把畚箕、樓梯扶手',
        '每張圖用它分類的顏色（themes[].palette 的 order／study／life／move／alert）當主色',
        '不可使用第三方角色、插圖、圖示、商標；不要參考いらすとや、IP as Logo、Koboyo 的畫面'
    ],
    'formats': {
        'prompt': {'master': [1920, 1440], 'web': [960, 720], 'web_format': 'webp', 'web_max_kb': 160, 'background': 'transparent',
                   'display': '晨間大屏「大屏提示」：文字在上、圖在下，投影全螢幕時圖高約 38vh（1080p 約 410px），要在教室後排 8 公尺外看懂',
                   'safe_area': '主體外框（不透明像素）落在畫布 6%–94% 之內'},
        'quiet': {'master': [1600, 1600], 'web': [800, 800], 'web_format': 'webp', 'web_max_kb': 120, 'background': 'transparent',
                  'display': '「安靜偵測」中間的人物，平常高 230px、投影時放大；系統會加上漂浮、搖晃動畫',
                  'safe_area': '主體外框落在 6%–94% 之內'},
        'icon': {'master': [1024, 1024], 'web': [256, 256], 'web_format': 'webp', 'web_max_kb': 30, 'background': 'transparent',
                 'display': '介面圖示，實際顯示 22–80px；系統會自己加圓角色塊底，圖示本身不要畫底色方塊',
                 'safe_area': '主體外框落在 8%–92% 之內，置中',
                 'rules': '一個圖示一個主物件、剪影清楚，縮到 22px 還認得出來'}
    },
    'paths': {
        'web': 'assets/art/<風格>/<類別>/<id>.webp（風格 = tech、minimal、cozy；類別 = prompt、quiet、icon）',
        'master': 'assets/art/_masters/<風格>/<類別>/<id>.png（不 commit）',
        'review': 'assets/art/_review/<風格>/（check_art.py --review 產生，不 commit）'
    },
    'prompt': [{'id': i, 'text': t, 'category': c, 'scene': d} for i, t, c, d in PROMPTS],
    'quiet': [{'id': i, 'state': t, 'category': c, 'scene': d} for i, t, c, d in QUIET],
    'icon': [{'id': i, 'label': l, 'used_in': u, 'subject': d} for i, l, u, d in ICONS],
    'first_batch': ['prompt/focus_teacher', 'prompt/line_up', 'quiet/quiet_good',
                    'icon/tab_rollcall', 'icon/tool_lottery', 'icon/tool_tomato', 'icon/sum_done', 'icon/role_homeroom']
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
n = len(PROMPTS) + len(QUIET) + len(ICONS)
print(f'{len(THEMES)} 套風格 × {n} 張 = {len(THEMES) * n} 張（prompt {len(PROMPTS)}、quiet {len(QUIET)}、icon {len(ICONS)}）')
