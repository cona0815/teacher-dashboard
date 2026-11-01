const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const projectRoot = path.resolve(__dirname, "..");
const codePath = path.join(projectRoot, "Code.gs");
const source = fs.readFileSync(codePath, "utf8");
const context = vm.createContext({});

vm.runInContext(
  `${source}
globalThis.__exports = {
  APP_CONFIG,
  TASK_HEADERS,
  COMMON_OPTION_LISTS,
  WORK_AXIS_CATEGORY_MAP,
  EMERGENCY_CATEGORIES,
  OFFICE_PROFILES,
  TEACHER_WORKSPACE_PROFILE,
  getOfficeProfile_,
  getOfficeProfileCatalog_,
  getOptionLists_,
  migrateLegacyRow_,
  priorityForCategory_
};`,
  context,
  { filename: "Code.gs" },
);

const {
  APP_CONFIG,
  TASK_HEADERS,
  COMMON_OPTION_LISTS,
  WORK_AXIS_CATEGORY_MAP,
  EMERGENCY_CATEGORIES,
  OFFICE_PROFILES,
  TEACHER_WORKSPACE_PROFILE,
  getOfficeProfile_,
  getOfficeProfileCatalog_,
  getOptionLists_,
  migrateLegacyRow_,
  priorityForCategory_,
} = context.__exports;

assert.equal(TASK_HEADERS.length, 23, "任務資料契約必須維持 23 欄");
assert.deepEqual(
  Array.from(TASK_HEADERS.slice(-4)),
  ["專案ID", "上層任務ID", "任務層級", "工作主軸"],
  "專案階層與工作主軸欄位必須附加在既有任務欄位之後",
);
assert.equal(Object.keys(OFFICE_PROFILES).length, 7, "應提供六個校務處室與六年級學年 profile");
assert.equal(
  JSON.stringify(TEACHER_WORKSPACE_PROFILE.roles.map((role) => role[1])),
  JSON.stringify(["教師", "導師", "學年主任", "行政"]),
  "教師工作台應保留四種工作身分，包含行政",
);
assert.equal(
  JSON.stringify(Array.from(TEACHER_WORKSPACE_PROFILE.categories)),
  JSON.stringify(Array.from(new Set(Object.values(WORK_AXIS_CATEGORY_MAP).flat()))),
  "教師工作台細項應由四大工作主軸組成",
);
assert.ok(OFFICE_PROFILES.sixth_grade.categories.length >= 60, "六年級工作細項應涵蓋常見教師工作");
for (const category of OFFICE_PROFILES.sixth_grade.categories) {
  const axes = Object.entries(WORK_AXIS_CATEGORY_MAP)
    .filter(([, categories]) => categories.includes(category))
    .map(([axis]) => axis);
  assert.equal(axes.length, 1, `細項「${category}」必須且只能屬於一個工作分類`);
}
for (const category of EMERGENCY_CATEGORIES) {
  assert.ok(OFFICE_PROFILES.sixth_grade.categories.includes(category), `緊急分類「${category}」必須出現在細項清單`);
  assert.equal(priorityForCategory_(category, "低"), "高", `緊急分類「${category}」必須強制為最高優先級`);
}

const legacyHeaders = Array.from(TASK_HEADERS.slice(0, -1));
const legacyRow = Array(legacyHeaders.length).fill("");
legacyRow[legacyHeaders.indexOf("任務ID")] = "P-001-01";
legacyRow[legacyHeaders.indexOf("任務名稱")] = "畢旅行程確認";
legacyRow[legacyHeaders.indexOf("類型")] = "戶外教育與畢旅";
legacyRow[legacyHeaders.indexOf("專案ID")] = "P-001";
legacyRow[legacyHeaders.indexOf("上層任務ID")] = "P-001";
legacyRow[legacyHeaders.indexOf("任務層級")] = "子任務";
const migratedRow = migrateLegacyRow_(legacyHeaders, legacyRow);
assert.equal(migratedRow[TASK_HEADERS.indexOf("專案ID")], "P-001", "升級欄位時必須保留專案ID");
assert.equal(migratedRow[TASK_HEADERS.indexOf("上層任務ID")], "P-001", "升級欄位時必須保留父任務");
assert.equal(migratedRow[TASK_HEADERS.indexOf("任務層級")], "子任務", "升級欄位時必須保留任務層級");
assert.equal(migratedRow[TASK_HEADERS.indexOf("工作主軸")], "學年主任", "舊分類應自動推導工作主軸");

for (const [officeKey, profile] of Object.entries(OFFICE_PROFILES)) {
  assert.match(officeKey, /^[a-z_]+$/, `${officeKey} 應使用穩定英文代碼`);
  assert.ok(profile.name, `${officeKey} 缺少處室名稱`);
  assert.ok(profile.description, `${officeKey} 缺少用途說明`);
  assert.ok(profile.categories.includes("其他"), `${profile.name} 類型必須包含「其他」`);
  assert.equal(
    new Set(profile.categories).size,
    profile.categories.length,
    `${profile.name} 有重複任務類型`,
  );
  assert.ok(profile.roles.length > 0, `${profile.name} 至少需要一個職務`);
  assert.equal(
    new Set(profile.roles.map((role) => role[0])).size,
    profile.roles.length,
    `${profile.name} 有重複職務代碼`,
  );
  for (const sample of profile.samples) {
    assert.equal(sample.length, 5, `${profile.name} 範例任務格式錯誤`);
    assert.ok(profile.categories.includes(sample[1]), `${profile.name} 範例使用無效類型`);
    assert.ok(COMMON_OPTION_LISTS.狀態.includes(sample[2]), `${profile.name} 範例使用無效狀態`);
    assert.ok(COMMON_OPTION_LISTS.優先級.includes(sample[3]), `${profile.name} 範例使用無效優先級`);
  }
}

assert.equal(getOfficeProfile_("academic_affairs").name, "教務處");
assert.throws(() => getOfficeProfile_("not_an_office"), /無效的處室選擇/);

const catalog = getOfficeProfileCatalog_();
assert.equal(catalog.length, 1, "安裝介面只應公開單一教師工作台，不公開細部處室");
assert.equal(catalog[0].key, "teacher_workspace");
assert.equal(
  JSON.stringify(catalog[0].roles.map((role) => role.name)),
  JSON.stringify(["教師", "導師", "學年主任", "行政"]),
);

const fakeTaskSheet = {
  getLastRow: () => 3,
  getLastColumn: () => TASK_HEADERS.length,
  getRange: (row, column, rowCount, columnCount) => ({
    getDisplayValues: () => {
      if (row === APP_CONFIG.HEADER_ROW) return [Array.from(TASK_HEADERS)];
      assert.equal(column, 3);
      assert.equal(rowCount, 2);
      assert.equal(columnCount, 1);
      return [["舊制自訂類型"], ["課程教學"]];
    },
  }),
};
const options = getOptionLists_(OFFICE_PROFILES.academic_affairs, fakeTaskSheet);
assert.deepEqual(
  Array.from(options.工作主軸),
  ["教學", "行政", "學年主任", "導師"],
  "工作主軸應固定為四大項目",
);
assert.ok(options.類型.includes("舊制自訂類型"), "切換處室時應保留既有任務類型");
assert.equal(options.類型.filter((value) => value === "課程教學").length, 1);

for (const htmlName of ["Installer.html", "Index.html", "Board.html", "Morning.html", "Install.html", "Studio.html"]) {
  const html = fs.readFileSync(path.join(projectRoot, htmlName), "utf8");
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((match) => match[1]);
  assert.ok(scripts.length > 0, `${htmlName} 缺少前端程式`);
  scripts.forEach((script) => new Function(script));
}

const installerHtml = fs.readFileSync(path.join(projectRoot, "Installer.html"), "utf8");
assert.doesNotMatch(installerHtml, /id="office"|data\.offices|let offices/, "安裝介面不應再要求選擇處室");
assert.match(installerHtml, /主要工作身分/, "安裝介面應改為選擇教師工作身分");

const indexHtml = fs.readFileSync(path.join(projectRoot, "Index.html"), "utf8");
assert.match(indexHtml, /#apiEndpointField\[hidden\] \{ display: none !important; \}/, "Gemini 預設端點應隱藏，只有自訂服務才顯示端點欄位");
assert.match(indexHtml, /github\.com\/cona0815\/teacher-dashboard\/releases\/download\/xiaomianzhu-v2\.3\/xiaomianzhu-windows-portable\.zip/, "小綿助設定頁應提供免 Python 可攜版下載入口");
assert.doesNotMatch(indexHtml, /先安裝 Python 3/, "一般老師的小綿助下載說明不應要求安裝 Python");
assert.match(indexHtml, /id="checkPetDownloadBridgeButton"/, "小綿助下載卡片應提供本機連線檢查");
assert.match(indexHtml, /let previewTasks = loadLocalPreviewTasks\(\)/, "公開版第一次開啟應載入空白本機任務，而非示範任務");
assert.match(indexHtml, /isLegacyPreviewDemoTask/, "更新後應自動辨識並移除舊版內建示範任務");
assert.match(indexHtml, /tasks, \[\]/, "本機任務找不到已存資料時應使用空陣列");
assert.doesNotMatch(indexHtml, /readLocalPreviewArray\(LOCAL_PREVIEW_STORAGE_KEYS\.tasks, previewSeedTasks\)/, "不得再將內建示範任務顯示給新使用者");
assert.match(indexHtml, /body \.deskpet, body \.deskpet-panel \{ display: none !important; \}/, "小綿助是桌面程式，不應顯示在網頁內");
assert.match(indexHtml, /id="schoolHolidayList"/, "學校自訂假日應使用可新增的列式編輯器");
assert.match(indexHtml, /type="date" data-school-holiday-field="date"/, "每筆學校自訂假日應使用日期選擇器");
assert.match(indexHtml, /data-school-holiday-field="reason"/, "每筆學校自訂假日應可自行填寫原因");
assert.doesNotMatch(indexHtml, /id="schoolHolidayDates"/, "不應再要求教師手動輸入日期分隔格式");
assert.match(indexHtml, /data-settings-tab="license"/, "系統設定應提供授權分頁");
assert.match(indexHtml, /本專案採 MIT 開源授權/, "授權分頁應清楚強調 MIT 開源授權");
assert.match(indexHtml, /github\.com\/mihozip\/school-admin-daily-dashboard/, "授權分頁應連結原始校務系統");
assert.match(indexHtml, /facebook\.com\/albert\.peng\.56/, "授權分頁應標示原作者 Facebook");
assert.match(indexHtml, /github\.com\/mihozip\/DeskPet/, "授權分頁應標示 DeskPet 流程參考來源");
assert.match(indexHtml, /本修改版介面插圖/, "授權分頁應記錄本修改版介面插圖來源");
// 2026-09-04 契約反轉：Netlify 上本站就有 assets/pet/，外連 GitHub 會被
// CSP img-src 'self' 擋下刷 console 錯誤——素材一律走本站相對路徑。
assert.doesNotMatch(indexHtml, /raw\.githubusercontent\.com/, "小綿助素材不得外連 GitHub（CSP 只允許本站圖片）");
assert.match(indexHtml, /deskpetAssetRoot = 'assets\/pet\/'/, "小綿助素材應使用本站相對路徑");
assert.match(indexHtml, /project-child \.task-name\.is-completed/, "完成的子任務應以刪除線標示該項目");
assert.match(indexHtml, /子任務.*已完成；主任務狀態維持不變/, "完成子任務時應保留主任務狀態");
assert.match(indexHtml, /主任務與下面的 .*項子任務/, "封存主任務前應明確提示會連同子任務處理");
assert.match(indexHtml, /data-theme-choice="minimal"/, "介面配色應提供低彩度極簡選項");
assert.match(indexHtml, /INTERFACE_THEMES = \['forest', 'apricot', 'lavender', 'tech', 'minimal'\]/, "主題清單應包含極簡配色");
assert.match(indexHtml, /id="teachingProgressBody" hidden/, "教學進度首次進入應預設收合");
assert.match(indexHtml, /id="progressUnitList"/, "教學進度應提供逐單元編輯清單");
assert.match(indexHtml, /data-unit-step="1"/, "每個單元應可單獨增加教學節數");
assert.match(indexHtml, /data-unit-step="-1"/, "每個單元應可單獨減少教學節數");
assert.match(indexHtml, /Math\.ceil\(totalPeriods \/ weeklyPeriods\)/, "單元總節數應依每週實際節數估算所需週數");
assert.match(indexHtml, /updateTeachingUnitCapacity\(\)/, "調整每週節數後應同步更新單元容量提示");
assert.match(indexHtml, /function buildTeachingDays\(/, "排程應把每週容量拆成實際上課日");
assert.match(indexHtml, /startDate: day\.date, endDate: day\.date, type: 'teaching'/, "一般課程應寫入實際授課日而非整週日期範圍");
assert.match(indexHtml, /reservedReviewPeriods\.get\(day\.date\)/, "評量複習也應依每日課量保留節數");
assert.match(indexHtml, /startDate: allocation\.date, endDate: allocation\.date, type: 'review'/, "評量複習應分散到實際上課日");
assert.match(indexHtml, /id="taskPanelNewTaskButton">＋ 新增任務/, "任務清單標題旁應提供新增任務入口");
assert.match(indexHtml, /data-action="archive"/, "已完成任務列應提供直接封存入口");
assert.match(source, /隨主任務封存子任務/, "GAS 封存主任務時應留下子任務連帶封存紀錄");
assert.doesNotMatch(
  indexHtml,
  /raw\.githubusercontent\.com\/mihozip\/school-admin-daily-dashboard\/main\/assets\/pet\//,
  "不得再從原作者 repository 讀取小綿助素材",
);
const thirdPartyNotices = fs.readFileSync(path.join(projectRoot, "THIRD_PARTY_NOTICES.md"), "utf8");
for (const projectOwnedAsset of [
  "assets/grade-leader-fun.png",
  "assets/marker-homeroom.webp",
  "assets/marker-graduation.webp",
  "assets/marker-grade-team.webp",
  "assets/marker-checklist.webp",
  "assets/pet/",
]) {
  assert.match(thirdPartyNotices, new RegExp(projectOwnedAsset.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), `素材聲明缺少 ${projectOwnedAsset}`);
}
const desktopSecretary = fs.readFileSync(path.join(projectRoot, "desktop_pet_secretary.py"), "utf8");
for (const secretaryFeature of ["今日簡報", "今日重要", "已逾期", "待追蹤", "健康管理", "快速交代"]) {
  assert.match(desktopSecretary, new RegExp(secretaryFeature), `桌面小綿助缺少「${secretaryFeature}」`);
}
assert.match(desktopSecretary, /ImageGrab\.grabclipboard\(\)/, "桌面小綿助必須支援貼上圖片或檔案");
assert.match(desktopSecretary, /BRIDGE_HOST = "127\.0\.0\.1"/, "桌面小綿助橋接只能綁定本機回環位址");
assert.match(desktopSecretary, /BRIDGE_MAX_BODY = 5 \* 1024 \* 1024/, "桌面小綿助橋接應限制請求大小");
assert.match(desktopSecretary, /ThreadingHTTPServer/, "桌面小綿助應提供本機橋接服務");
assert.match(desktopSecretary, /目前還沒有任務/, "桌面小綿助在空白資料時應顯示清楚的空狀態");
assert.match(desktopSecretary, /box\.pack\(fill="x", expand=False\)/, "桌面清單不應在高 DPI 畫面撐成大片空白");
assert.match(desktopSecretary, /bridge_origin_allowed/, "桌面小綿助應限制可存取的網頁來源");
assert.match(desktopSecretary, /temporary\.replace\(DATA_FILE\)/, "桌面資料應以暫存檔原子替換保存");
// 2026-09-04 契約改版（使用者核定小綿助 v2.0「方案 B」）：桌寵可直連老師自己的
// Apps Script，但只能透過 desktop_pet_cloud 模組、只允許 script.google.com 網域、只讀＋prompt_set。
assert.doesNotMatch(desktopSecretary, /urllib\.request\.urlopen/, "桌寵主程式不得自行開網路連線，一律經 desktop_pet_cloud");
assert.match(desktopSecretary, /from desktop_pet_cloud import CloudLink/, "桌寵應透過 CloudLink 模組連雲端");
const desktopCloud = fs.readFileSync(path.join(projectRoot, "desktop_pet_cloud.py"), "utf8");
assert.match(desktopCloud, /ALLOWED_HOSTS = \("script\.google\.com", "script\.googleusercontent\.com"\)/, "雲端模組只允許 Google Apps Script 網域");
assert.match(desktopCloud, /READ_ACTIONS = \("ping", "snapshot_get", "pull", "prompt_get"\)/, "雲端模組的讀取動作應為固定白名單");
assert.match(desktopCloud, /PROMPT_SET_ACTION = "prompt_set"/, "桌寵唯一的寫入動作是大屏提示遙控");
assert.doesNotMatch(desktopCloud, /ImageGrab|screenshot|grab\(/i, "專注偵測不得截圖");
for (const v2Feature of ["☁️ 雲端連線", "🍅 專注小綿助", "📣 大屏提示遙控", "這是備課用", "只讀作用中視窗標題、不截圖、不上傳"]) {
  assert.match(desktopSecretary, new RegExp(v2Feature), `小綿助 v2.0 秘書頁缺少「${v2Feature}」`);
}
assert.match(fs.readFileSync(path.join(projectRoot, "LineBot.gs"), "utf8"), /action === 'snapshot_get'/, "GAS 應提供桌寵讀取工作台快照的動作");
assert.match(indexHtml, /const PET_BRIDGE_URL = 'http:\/\/127\.0\.0\.1:8767'/, "網頁應自動連接本機小綿助");
assert.match(indexHtml, /data-settings-panel="security"/, "網頁應提供資料與資安說明");
assert.match(indexHtml, /Content-Security-Policy/, "網頁應宣告內容安全政策");

// LINE 小幫手（選用雲端模組）契約
const lineBotSource = fs.readFileSync(path.join(projectRoot, "LineBot.gs"), "utf8");
new Function(lineBotSource);
assert.match(lineBotSource, /function setupLineBot\(\)/, "LineBot.gs 應提供一鍵初始化");
assert.match(lineBotSource, /LINE_WEBHOOK_TOKEN/, "LINE Webhook 必須以亂數參數驗證");
assert.match(lineBotSource, /LINE_SYNC_TOKEN/, "工作台同步必須驗證同步金鑰");
assert.match(lineBotSource, /LINE_ALLOWED_USER_IDS/, "應支援鎖定只回應老師本人的 userId");
assert.doesNotMatch(lineBotSource, /\b1[A-Za-z0-9_-]{30,}\b/, "LineBot.gs 不得含固定 Google 資源 ID");
assert.match(indexHtml, /data-settings-tab="linebot"/, "系統設定應提供 LINE 小幫手分頁");
assert.match(indexHtml, /id="lineInboxSection"/, "工作台應提供 LINE 收件匣");
assert.match(indexHtml, /grade6LineInbox/, "LINE 收件匣應保存於瀏覽器本機");
assert.match(indexHtml, /https:\/\/script\.google\.com/, "CSP 應允許連線老師自己的 Apps Script");
assert.match(indexHtml, /lineInbox: lineInboxItemsForPet\(\)/, "本機橋接應把 LINE 待整理清單帶給桌面小綿助");
assert.doesNotMatch(
  JSON.stringify(indexHtml.match(/function buildBackupPayload\(\) \{[\s\S]*?\n    \}/)?.[0] || ""),
  /grade6LineSyncToken|lineSyncToken|lineGasUrl/,
  "JSON 備份不得包含 LINE 同步金鑰或 GAS 網址",
);
assert.match(desktopSecretary, /line_inbox/, "桌面小綿助應保存 LINE 待整理鏡像");
assert.match(desktopSecretary, /LINE 待整理/, "桌面小綿助面板應顯示 LINE 待整理");
assert.match(desktopSecretary, /sanitize_line_inbox/, "LINE 清單必須經過欄位淨化");

// 晨間大屏（模組 B）契約
assert.match(lineBotSource, /CLASSROOM_TOKEN/, "大屏應使用獨立教室金鑰");
assert.match(lineBotSource, /rollcall_submit/, "GAS 應提供點名回報動作");
assert.match(lineBotSource, /rollcall_query/, "GAS 應提供歷史區間查詢（老師金鑰限定）");
assert.match(lineBotSource, /date !== lineBotToday_\(\)/, "教室金鑰只能回報今天的紀錄");
assert.match(lineBotSource, /點名紀錄/, "GAS 應建立點名紀錄表");
assert.match(lineBotSource, /作業紀錄/, "GAS 應建立作業紀錄表");
const morningHtml = fs.readFileSync(path.join(projectRoot, "Morning.html"), "utf8");
for (const feature of ["病假", "事假", "遲到", "未到", "補交", "缺交", "全班繳交", "聯絡簿", "倒數", "座號"]) {
  assert.match(morningHtml, new RegExp(feature), `晨間大屏缺少「${feature}」`);
}
assert.match(morningHtml, /https:\/\/script\.google\.com/, "晨間大屏 CSP 應允許連線 Apps Script");
assert.match(morningHtml, /rollcall_submit/, "晨間大屏應以教室金鑰回報");
// 大屏 v2 契約
assert.match(morningHtml, /空號/, "設定應支援空號");
assert.match(morningHtml, /作業補交/, "應有作業補交分頁");
assert.match(morningHtml, /classroom_missing/, "補交分頁應讀取近期缺交清單");
assert.match(morningHtml, /homework_resubmit/, "補交完成應回寫雲端");
assert.match(morningHtml, /作業名稱/, "收件版面應含作業名稱");
assert.match(morningHtml, /未填/, "點名預設應為未填空白");
assert.match(morningHtml, /遲到只有老師/, "遲到只給老師看，大屏不顯示");
assert.match(lineBotSource, /classroom_missing/, "GAS 應提供近期缺交查詢（教室金鑰）");
assert.match(lineBotSource, /markHomeworkResubmitted_/, "GAS 應提供缺交轉補交（僅此一種歷史寫入）");
assert.match(lineBotSource, /sendRollcallReminder/, "GAS 應提供未點名雲端提醒備援");
assert.match(lineBotSource, /作業名稱/, "作業紀錄表應含作業名稱欄");
assert.match(lineBotSource, /sendWeeklyHomeworkAlerts/, "GAS 應提供每週缺交達門檻的家長訊息草稿");
assert.match(lineBotSource, /WEEKLY_ALERT_THRESHOLD/, "每週關懷門檻應可由指令碼屬性調整");
assert.match(lineBotSource, /家長聯繫/, "家長訊息草稿應帶家長聯繫標籤進工作台收件匣");
// 聯絡本（大屏黑板 ⇄ 工作台管理）契約
assert.match(lineBotSource, /contactbook_get/, "GAS 應提供聯絡本讀取");
assert.match(lineBotSource, /contactbook_save/, "GAS 應提供聯絡本儲存");
assert.match(lineBotSource, /教室端只能編輯今天的聯絡本/, "教室金鑰只能讀寫今天的聯絡本");
assert.match(morningHtml, /chalkboard/, "大屏應提供黑板風聯絡本");
assert.match(morningHtml, /contactbook_get/, "大屏開啟應載入今日聯絡本");
assert.match(morningHtml, /投影模式/, "大屏應提供聯絡本投影模式");
assert.match(morningHtml, /exportQueryCsv/, "查詢統計應可匯出 Excel（CSV）");
assert.match(lineBotSource, /function setupTriggers\(\)/, "GAS 應提供一鍵設定觸發器");
assert.match(indexHtml, /assets\/ipas\//, "介面圖示應使用本地化的 IP as Logo 素材");
assert.match(thirdPartyNotices, /ipaslogo\.com/, "素材聲明應記錄 IP as Logo 來源與授權");
assert.match(morningHtml, /data:image\/webp;base64,/, "大屏圖示應內嵌以維持單檔可攜");
assert.match(morningHtml, /BpmfIansui/, "大屏聯絡本應提供注音體選項");
assert.match(thirdPartyNotices, /bpmfvs/, "素材聲明應記錄注音字型來源與 OFL 授權");
const installHtml = fs.readFileSync(path.join(projectRoot, "Install.html"), "utf8");
for (const guideFeature of ["setupLineBot", "setupTriggers", "指令碼屬性", "Webhook", "教室大屏金鑰", "疑難排解", "shell:startup"]) {
  assert.match(installHtml, new RegExp(guideFeature), `新手安裝教學缺少「${guideFeature}」`);
}
assert.match(indexHtml, /Install\.html/, "工作台應連結新手安裝教學");
assert.match(morningHtml, /Install\.html/, "大屏應連結新手安裝教學");
assert.ok(fs.existsSync(path.join(projectRoot, "assets", "fonts", "BpmfIansui-Regular.ttf")), "注音字型檔應存在於 assets/fonts");
assert.match(lineBotSource, /writeContactBookFromLine_/, "LINE 應可直接寫入當天聯絡本");
assert.match(lineBotSource, /contactbook/, "分類應支援聯絡本類型");
assert.match(indexHtml, /id="contactBookSection"/, "工作台應提供聯絡本管理版面");
assert.match(indexHtml, /contactbook_save/, "工作台應可依日期儲存聯絡本");
assert.match(morningHtml, /只使用座號/, "晨間大屏應聲明只使用座號");
assert.doesNotMatch(morningHtml, /placeholder="[^"]*姓名/, "晨間大屏不得出現要求輸入姓名的欄位");
assert.match(indexHtml, /grade6RollcallStats/, "工作台應保存大屏統計快取");
assert.match(indexHtml, /rollcallBadgeFor\(key\)/, "工作台日曆應顯示出缺與缺交摘要");

// 班級工具（純本機）與說明頁契約
for (const tool of ["抽籤機", "檢核板", "計分板", "隨機分組", "安靜偵測", "定評小幫手", "排除今日缺席"]) {
  assert.match(morningHtml, new RegExp(tool), `班級工具缺少「${tool}」`);
}
// 純本機原則的唯一例外：大屏提示的唯讀輪詢 prompt_get（使用者 2026-09-04 核定的遠端切換功能）
const toolsScriptSlice = morningHtml
  .slice(morningHtml.indexOf("班級工具（純本機）＋顯示縮放"))
  .replace(/callGas\(\{ action: 'prompt_get'[^}]*\}\)/g, "");
assert.doesNotMatch(toolsScriptSlice, /callGas\(/, "班級工具除 prompt_get 輪詢外不得呼叫雲端");
const aboutHtml = fs.readFileSync(path.join(projectRoot, "About.html"), "utf8");
for (const aboutFeature of ["使用情境", "授權逐條", "LINE小幫手備份", "只用座號", "DRIVE_BACKUP_TYPES", "金鑰權限邊界"]) {
  assert.match(aboutHtml, new RegExp(aboutFeature), `說明頁缺少「${aboutFeature}」`);
}
assert.match(indexHtml, /About\.html/, "工作台資安分頁應連到說明頁");
assert.match(morningHtml, /About\.html/, "大屏設定應連到說明頁");

// 重複紀錄修復與安裝中心契約
assert.match(lineBotSource, /function cellDate_/, "日期儲存格必須正規化後才能比對（重複紀錄修復）");
assert.match(lineBotSource, /cellDate_\(values\[index\]\[0\]\) === date/, "覆蓋刪除必須用正規化日期比對");
assert.match(lineBotSource, /function cleanupDuplicateRecords/, "應提供一次性重複資料清理");
assert.match(lineBotSource, /安裝總表/, "選單應能產生安裝總表");
assert.match(lineBotSource, /menuSetTokenA/, "選單應可直接填入 LINE Token");
assert.match(lineBotSource, /menuSetUserId/, "選單應可直接填入 userId");
const boardHtml = fs.readFileSync(path.join(projectRoot, "Board.html"), "utf8");
assert.match(boardHtml, /grade6PreviewTasks/, "每日看板離線時應讀取工作台真實任務");
assert.doesNotMatch(boardHtml, /（模擬）/, "每日看板不得再顯示模擬資料戳記");

// 教材小工場（Studio.html）
const studioHtml = fs.readFileSync(path.join(projectRoot, "Studio.html"), "utf8");
assert.match(studioHtml, /grade6AssistantApiKey/, "教材小工場應沿用工作台已存的 Gemini 金鑰");
assert.match(studioHtml, /generativelanguage\.googleapis\.com/, "教材小工場應直連 Gemini（不經任何中繼伺服器）");
assert.match(studioHtml, /data-page="ws"/, "教材小工場應有學習單分頁");
assert.match(studioHtml, /差異化雙版本/, "學習單應支援基礎＋進階差異化");
assert.match(studioHtml, /教師解答卷/, "學習單應可附教師解答卷");
assert.match(studioHtml, /家長回條/, "家長通知單應含裁切回條");
assert.match(studioHtml, /data-page="mm"/, "教材小工場應有心智圖分頁");
assert.match(studioHtml, /data-page="cm"/, "教材小工場應有評語小幫手分頁");
assert.match(studioHtml, /data-page="mask"/, "教材小工場應有敏感資料遮蔽分頁");
assert.match(studioHtml, /100% 本機處理，不會上傳/, "遮蔽工具應標明純本機處理");
assert.match(studioHtml, /\[A-Z\]\[12\]\\d\{8\}/, "文字遮蔽應能辨識身分證字號");
assert.match(studioHtml, /data-page="poster"/, "教材小工場應有海報宣傳單分頁");
assert.doesNotMatch(studioHtml, /data-page="award"/, "獎狀已依使用者指示移除");
assert.match(studioHtml, /data-page="seat"/, "教材小工場應有座位表分頁");
assert.match(studioHtml, /island4/, "座位表應支援小組島排法（分組座位）");
assert.match(studioHtml, /兩人一組（雙併桌）/, "座位表應支援兩人雙併排法");
assert.match(indexHtml, /href="Studio\.html"/, "教師工具箱應有教材小工場入口");
assert.match(indexHtml, /toolbox-button" href="Studio\.html"/, "教材小工場應放在教師工具箱按鈕列");

// Google 生態整合：日曆方案①、記事↔Tasks、表單產生器
assert.match(indexHtml, /calendar\.google\.com\/calendar\/render\?action=TEMPLATE/, "任務應提供免授權的 Google 日曆預填連結");
assert.match(indexHtml, /data-action="gcal"/, "有期限的任務列應有加入日曆按鈕");
assert.match(indexHtml, /id="syncGoogleTasksButton"/, "記事區應有 Google Tasks 同步按鈕");
assert.match(indexHtml, /gtaskId: String\(note\.gtaskId/, "記事正規化應保留 gtaskId 對應");
assert.match(lineBotSource, /notes_tasks_sync/, "GAS 應提供記事與 Google Tasks 雙向同步動作");
assert.match(lineBotSource, /function createGoogleForm_/, "GAS 應提供建立 Google 表單動作");
assert.match(lineBotSource, /function lineBotFormSubmitCopy/, "表單提交後應能寄回覆副本給填表者");
assert.match(lineBotSource, /尚未啟用 Tasks 服務/, "未啟用 Tasks 服務時應回傳友善的啟用教學");
assert.match(studioHtml, /data-page="gform"/, "教材小工場應有 Google 表單產生器分頁");
assert.match(studioHtml, /form_create/, "表單產生器應透過 GAS form_create 建立");
assert.match(studioHtml, /https:\/\/script\.google\.com/, "Studio CSP 應放行 GAS 連線");

// 2026-09-04 驗收前批次：作文批改、圖文選單、座位表升級、文件匯出、提示遙控
assert.match(studioHtml, /data-page="essay"/, "教材小工場應有作文批改分頁");
assert.match(studioHtml, /data-page="guide"/, "教材小工場應有作文引導單分頁");
assert.match(studioHtml, /function buildMindmapSvg/, "心智圖繪製應為共用函式（引導單重用）");
assert.match(studioHtml, /四格情境漫畫/, "作文引導單應含四格情境漫畫頁");
assert.match(studioHtml, /段落鷹架|段落設計圖/, "作文引導單應含段落鷹架");
assert.match(studioHtml, /名言佳句/, "作文引導單應含名言佳句");
assert.match(studioHtml, /data-page="richmenu"/, "教材小工場應有 LINE 圖文選單分頁");
assert.match(studioHtml, /richmenu_apply/, "圖文選單應透過 GAS richmenu_apply 套用");
assert.match(studioHtml, /data-page="cm" hidden/, "評語小幫手分頁暫時收起（使用者指示先不用）");
assert.match(studioHtml, /function downloadPreview/, "文件產出應可下載 Word／Excel");
assert.match(studioHtml, /id="stNames"/, "座位表應支援自訂名單");
assert.match(studioHtml, /id="stDirection"/, "座位表應支援排列方向");
assert.match(studioHtml, /dragstart/, "座位表應支援拖拉移動座位");
assert.match(lineBotSource, /handleScreenPromptCommand_/, "LINE 應可用「提示 ○○」切換大屏提示");
assert.match(lineBotSource, /applyRichMenu_/, "GAS 應可建立並套用 LINE 圖文選單");
assert.ok((lineBotSource.match(/key: '/g) || []).length >= 20, "大屏提示內建句至少 20 句");
assert.match(morningHtml, /data-tool="prompt"/, "班級工具應含大屏提示分頁");
assert.match(morningHtml, /prompt_get/, "大屏提示應輪詢 GAS 取得遠端指令");
assert.match(morningHtml, /assets\/irasutoya\//, "大屏應使用本機 irasutoya 插圖（CSP 不允許外連圖）");
assert.match(morningHtml, /function rollcallTaken\(\)/, "抽籤／分組排除缺席前要先判斷今天有沒有真的點名");
assert.match(morningHtml, /status === '未到' && countMissing/, "沒點名時自動轉「未到」不可把全班排出抽籤池（2026-11-01 回報）");
assert.match(morningHtml, /function seatPoolNote/, "抽籤狀態列應寫出座號範圍與排除名單");
assert.match(morningHtml, /config\.promptSchedules/, "大屏提示應可設定定時自動跳出");
assert.match(morningHtml, /mode: 'breaks'/, "定時提示應支援「每節下課」");
assert.match(morningHtml, /day\.promptFired/, "同一天同一時間只跳一次（重新整理不重跳）");
assert.match(morningHtml, /飯後潔牙/, "大屏提示應含飯後潔牙");
assert.match(morningHtml, /\.prompt-img \{ width: auto; height: auto; align-self: center; object-fit: contain; \}/, "全螢幕時提示插圖不可被拉變形");
assert.match(morningHtml, /PROMPT_ART_DIR = 'assets\/art\/cozy\/prompt\/'/, "新插圖（動森風）放在 assets/art/cozy/prompt/");
assert.match(morningHtml, /tomatoBreathe/, "番茄鐘跑動時應有呼吸動畫");
assert.match(morningHtml, /youtube-nocookie\.com/, "番茄鐘音樂角應支援 YouTube 內嵌");
assert.match(morningHtml, /config\.scores/, "計分板分數應永久保存（只有手動歸零）");
assert.doesNotMatch(morningHtml, /分數隔天自動歸零/, "計分板不得再自動歸零");
const noticesText = fs.readFileSync(path.join(projectRoot, "THIRD_PARTY_NOTICES.md"), "utf8");
assert.match(noticesText, /irasutoya/i, "第三方聲明應記錄いらすとや授權");

// 第 2 版文件同步：安裝教學更新指南、About 新情境、Intro 介紹
assert.match(installHtml, /id="partv2"/, "安裝教學應有第 2 版更新指南分頁");
assert.match(installHtml, /管理部署 → ✏️ 編輯 → 版本選「新版本」/, "更新指南應強調管理部署而非新增部署");
assert.match(installHtml, /重新授權一次/, "更新指南應預告新權限的重新授權");
assert.match(installHtml, /Tasks API/, "更新指南應說明 Tasks 服務選配啟用");
assert.match(aboutHtml, /教材小工場一條龍/, "About 應新增備課夜情境");
assert.match(aboutHtml, /會考寫作六級分規準/, "About 應說明作文批改採會考規準");
assert.match(aboutHtml, /提示 排隊/, "About 應示範大屏提示 LINE 遙控");
const introHtml = fs.readFileSync(path.join(projectRoot, "Intro.html"), "utf8");
assert.match(introHtml, /教材小工場（第 2 版新登場）/, "Intro 應介紹教材小工場");
assert.match(introHtml, /大屏提示/, "Intro 班級工具應含大屏提示");
assert.match(introHtml, /教材小工場一站生成/, "Intro 轉貼文案應含第 2 版痛點");
assert.match(installHtml, /copyLineBotButton/, "更新指南應提供一鍵複製最新程式碼（不依賴分享包）");

// 📎 PDF 工具（pdf-lib 純本機）
assert.match(studioHtml, /data-page="pdf"/, "教材小工場應有 PDF 工具分頁");
assert.match(studioHtml, /assets\/vendor\/pdf-lib\.min\.js/, "PDF 工具應載入本站自帶的 pdf-lib");
assert.ok(fs.existsSync(path.join(projectRoot, "assets", "vendor", "pdf-lib.min.js")), "pdf-lib 函式庫檔案應存在");
assert.match(studioHtml, /setCropBox/, "PDF 工具應支援裁切");
assert.match(noticesText, /pdf-lib/, "第三方聲明應記錄 pdf-lib");
assert.match(morningHtml, /data-tool="tomato"/, "班級工具應含番茄鐘分頁");
assert.match(morningHtml, /tomatoFullscreenButton/, "番茄鐘應支援全螢幕播放");
// 2026-10 班級工具動畫大升級：吉祥物內嵌、投影模式、hidden 不被樣式蓋掉
assert.match(morningHtml, /const SHEEP = \{\s*idle: 'data:image\/webp;base64,/, "小綿羊吉祥物應內嵌為 WebP（大屏維持單檔可攜）");
for (const tool of ["lottery", "check", "score", "group", "quiet"]) {
  assert.match(morningHtml, new RegExp(`data-fs-panel="${tool}"`), `班級工具「${tool}」應有投影模式`);
}
assert.match(morningHtml, /\.tool-opts\[hidden\], \.tomato-edit\[hidden\]/, "有 hidden 的編輯列與番茄鐘編輯框必須真的藏起來");
for (const fx of ["lot-bulbs", "check-ring", "score-crown", "group-pool", "quietNeedle", "tomatoRing", "promptTiles"]) {
  assert.match(morningHtml, new RegExp(fx), `班級工具動畫元件缺少「${fx}」`);
}

const netlifyConfig = fs.readFileSync(path.join(projectRoot, "netlify.toml"), "utf8");
for (const header of ["Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]) {
  assert.match(netlifyConfig, new RegExp(header), `Netlify 應設定 ${header}`);
}
assert.match(netlifyConfig, /https:\/\/script\.google\.com https:\/\/script\.googleusercontent\.com/, "Netlify CSP 也要允許 Apps Script 同步");

assert.doesNotMatch(source, /\b1[A-Za-z0-9_-]{30,}\b/, "公開版本不得含固定 Google 資源 ID");
assert.match(source, /BOUND_SPREADSHEET_ID/, "安裝後應以 Script Properties 定位試算表");
assert.match(source, /verifyCsrfToken_/, "寫入流程必須保留 CSRF 驗證");
assert.match(source, /verifyInstallToken_\(installToken\)/, "安裝寫入必須驗證安裝憑證");
assert.match(source, /assertSpreadsheetUiContext_\(\)/, "安裝端點必須限制在試算表 UI");
assert.match(source, /LockService/, "共享寫入必須保留鎖");

console.log("profile_config.test.js: all checks passed");

// 2026-09-06 資安審查修正契約
assert.match(lineBotSource, /還沒設定「允許的使用者」/, "LINE 允許名單為空時應拒絕指令並引導填 userId");
assert.doesNotMatch(lineBotSource, /allowedUsers\.length && allowedUsers\.indexOf/, "不得再有『名單為空即放行』的邏輯");
assert.match(lineBotSource, /function lineBotFormCopySweep/, "表單副本應改為單一時間觸發器掃描");
assert.doesNotMatch(lineBotSource, /forForm\(form\)\.onFormSubmit\(\)\.create\(\)/, "不得再為每張表單各建一個觸發器（20 個上限）");
assert.match(lineBotSource, /safeImg = \/\^\[a-z_\]\+\\\.png\$\//, "大屏提示圖片名稱應白名單驗證");
for (const [name, html] of [["Index.html", indexHtml], ["Studio.html", studioHtml]]) {
  assert.doesNotMatch(html, /generateContent\?key=/, `${name} 不得把 Gemini 金鑰放在網址`);
  assert.match(html, /'x-goog-api-key'/, `${name} 應以標頭傳送 Gemini 金鑰`);
}
assert.match(studioHtml, /async function shrinkImageForAi/, "作文批改上傳前應自動縮圖");
assert.match(desktopSecretary, /def _is_local_origin/, "桌寵面板端點應限制本機來源");
assert.match(desktopSecretary, /換了網址就作廢舊金鑰/, "桌寵換雲端網址時應清空舊金鑰");

// 2026-09-06 模擬資料清查：工作台建立 Google 表單必須走真的 GAS form_create
assert.doesNotMatch(indexHtml, /serverCall\('createGoogleForm'/, "工作台不得再用 google.script.run 建立表單（Netlify 上不存在）");
assert.match(indexHtml, /callLineBridge\('form_create'/, "工作台建立表單應透過 LINE 小幫手 GAS");
assert.doesNotMatch(indexHtml, /模擬建立成功|模擬備份|模擬版會還原|模擬產生|模擬檔/, "工作台不得殘留『模擬』功能文案");

// 2026-09-06 模擬資料清查（第二輪）：日曆、教學進度同步、Drive 檔案改走真 GAS
for (const action of ["calendar_event_create", "calendar_sync_progress", "drive_upload", "drive_list"]) {
  assert.match(fs.readFileSync(path.join(projectRoot, "LineBot.gs"), "utf8"), new RegExp(`action === '${action}'`), `GAS 應提供 ${action}`);
  assert.match(indexHtml, new RegExp(`cloudCall\\('${action}'`), `工作台 ${action} 應經 LINE 小幫手 GAS`);
}
for (const fake of ["createGoogleCalendarEvent:", "syncTeachingProgressCalendar:", "createGoogleForm:", "uploadWorkspaceFile:", "listWorkspaceFiles:"]) {
  assert.doesNotMatch(indexHtml, new RegExp(fake.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), `本機 shim 不得再提供假的 ${fake}`);
}
assert.doesNotMatch(indexHtml, /serverCall\('(createGoogleCalendarEvent|syncTeachingProgressCalendar|uploadWorkspaceFile|listWorkspaceFiles)'/, "雲端功能不得再走 google.script.run");

// 2026-09-06 文件同步契約：小綿助 v2.0、雲端功能改真、PDF 工具、作文批改不限張數、允許名單新行為
assert.match(installHtml, /小綿助 v2\.\d/, "安裝更新指南應介紹小綿助 v2.x 與升級步驟");
// 2026-09-28 小綿助 v2.3 新畫風：文件要講到新畫風與投影時睡覺；網頁版動畫也換新（新檔每個 < 200KB）
{
  const aboutText = fs.readFileSync(path.join(projectRoot, "About.html"), "utf8");
  const introText = fs.readFileSync(path.join(projectRoot, "Intro.html"), "utf8");
  assert.match(aboutText, /新畫風[\s\S]{0,400}全螢幕/, "About 應介紹 v2.3 新畫風與投影／全螢幕時睡覺");
  assert.match(introText, /新畫風（v2\.3 新）/, "Intro 應列出 v2.3 新畫風");
  assert.match(installHtml, /投影或全螢幕<\/strong>時牠會自己睡覺/, "安裝教學應提醒投影時小綿助會睡覺");
  for (const state of ["drag", "idle", "listen", "sleep", "success", "think", "walk_left", "walk_right", "warning"]) {
    const size = fs.statSync(path.join(projectRoot, "assets", "pet", `pet_${state}.webp`)).size;
    assert.ok(size < 200000, `網頁版 pet_${state}.webp 應為 v3 新畫風（舊版約 600KB）`);
  }
  assert.ok(fs.existsSync(path.join(projectRoot, "assets", "pet", "v3", "CODEX_HANDOFF.md")), "v3 動作圖交接手冊應保留在 repo");
  // 2026-09-29 介紹頁：48 秒宣傳影片＋「在家就能寫聯絡本」亮點
  assert.match(introText, /<video[^>]+src="assets\/video\/teacher-dashboard-48s\.mp4"/, "Intro 應嵌入 48 秒宣傳影片");
  assert.ok(fs.statSync(path.join(projectRoot, "assets", "video", "teacher-dashboard-48s.mp4")).size < 15 * 1024 * 1024, "宣傳影片應壓縮在 15MB 以內");
  assert.ok(fs.existsSync(path.join(projectRoot, "assets", "video", "teacher-dashboard-48s.jpg")), "宣傳影片應有封面圖");
  assert.match(introText, /不用到學校：LINE 或工作台寫好，隔天大屏黑板自動出現/, "Intro 應把在家寫聯絡本列為亮點");
}
assert.match(installHtml, /寫入 Google 日曆、存檔到雲端硬碟/, "更新指南授權說明應含日曆與雲端硬碟");
assert.match(installHtml, /以前只是模擬/, "更新指南應說明雲端功能已改為真實寫入");
assert.match(installHtml, /📎 PDF 工具/, "更新指南應列出 PDF 工具");
assert.match(installHtml, /不會執行任何指令/, "安裝教學應說明允許名單未填時的新行為");
assert.match(aboutHtml, /不限張數/, "About 作文批改應更新為不限張數");
assert.match(aboutHtml, /桌面小綿助會看我的螢幕嗎/, "About 應回答桌寵螢幕隱私問題");
assert.match(aboutHtml, /桌面小綿助 v2\.0 陪你專注/, "About 應有桌寵 v2.0 情境");
assert.match(aboutHtml, /XiaoMianZhuSecretary/, "About 資料存放表應含桌寵資料位置");
assert.match(introHtml, /小綿助 v2\.[01]「(專注|會聽的)小綿助」/, "Intro 應有小綿助 v2.x 功能卡");
assert.match(introHtml, /PDF 工具/, "Intro 教材小工場卡應含 PDF 工具");

// 2026-09-07 教材小工場 v3：拍照／貼上元件、真 PDF 下載、海報改 Gemini 生圖與風格庫
assert.match(studioHtml, /function attachZone/, "每個檔案輸入都應有拍照／貼上元件");
assert.match(studioHtml, /\['wsImage', 'ntImage', 'mmImage'\]\.forEach\(id => attachZone\(id\)\)/, "學習單／通知單／心智圖的檔案輸入應掛上拍照／貼上");
for (const zoneId of ["esImages", "pdfFiles", "maskImageInput"]) {
  assert.ok(studioHtml.includes(`attachZone('${zoneId}'`), `${zoneId} 應掛上拍照／貼上`);
}
assert.match(studioHtml, /assets\/vendor\/html2pdf\.bundle\.min\.js/, "應載入本站自帶的 html2pdf");
assert.ok(fs.existsSync(path.join(projectRoot, "assets", "vendor", "html2pdf.bundle.min.js")), "html2pdf 函式庫應存在");
assert.ok((studioHtml.match(/downloadPdfFromHost\('/g) || []).length >= 6, "各文件工具都應有 PDF 下載");
assert.match(studioHtml, /responseModalities: \['IMAGE', 'TEXT'\]/, "海報應呼叫 Gemini 生圖模型");
{
  const stylesBlock = studioHtml.slice(studioHtml.indexOf("const PO_STYLES = ["), studioHtml.indexOf("];", studioHtml.indexOf("const PO_STYLES = [")));
  assert.ok((stylesBlock.match(/^\s+\['[a-z]+', '/gm) || []).length >= 12, "海報風格庫至少 12 種");
}
assert.doesNotMatch(studioHtml, /PO_THEMES/, "海報不再使用配色版型");
assert.match(studioHtml, /name="poTextMode"/, "海報應可選文字疊圖或 AI 畫進圖");
assert.match(fs.readFileSync(path.join(projectRoot, "THIRD_PARTY_NOTICES.md"), "utf8"), /html2pdf/, "第三方聲明應記錄 html2pdf");

// 家長通知單升級：與宣傳單同套插圖介面，內容可微調
assert.match(studioHtml, /id="ntStyle"/, "通知單應可選插圖風格");
assert.match(studioHtml, /async function makeNoticeBanner/, "通知單應能產生 AI 插圖橫幅");
assert.match(studioHtml, /id="ntPngButton"/, "通知單應可下載 PNG");
assert.ok((studioHtml.match(/contenteditable="true" spellcheck="false"/g) || []).length >= 8, "通知單與海報文字應可直接點著修改");

// LINE 圖文選單：Gemini 生背景＋疊按鈕
assert.match(studioHtml, /async function makeMenuBackground/, "圖文選單應能用 Gemini 產生背景圖");
assert.match(studioHtml, /id="rmStyle"/, "圖文選單應可選插圖風格");
assert.match(studioHtml, /id="rmPngButton"/, "圖文選單應可下載 PNG");

// 作文引導單第二版型：感官觀察四頁組
assert.match(studioHtml, /id="gdFormat"/, "作文引導單應可選版型");
assert.match(studioHtml, /async function runSenseWorksheet/, "應有感官觀察四頁組產生流程");
assert.match(studioHtml, /我可以先這樣說/, "感官學習單應含句型起手式區");

// 學習單生動版式：暖身／挑戰／自評／線稿插圖
assert.match(studioHtml, /id="wsArt"/, "學習單應可附 AI 線稿插圖");
assert.match(studioHtml, /🔥 暖身/, "學習單應有暖身區");
assert.match(studioHtml, /🌟 挑戰題/, "學習單應有挑戰題");
assert.match(studioHtml, /我的自我評量/, "學習單應有自我評量");
assert.match(studioHtml, /例：中秋節/, "作文引導示範主題應為中秋節");

// 段考複習講義／閱讀分級改寫
assert.match(studioHtml, /data-page="review"/, "教材小工場應有段考複習講義分頁");
assert.match(studioHtml, /data-page="reading"/, "教材小工場應有閱讀分級改寫分頁");
assert.match(studioHtml, /易錯/, "複習講義應含易錯提醒");
assert.match(studioHtml, /🟢 基礎/, "閱讀分級應有三級版本選項");
assert.ok(studioHtml.includes("attachZone('rvImages'") && studioHtml.includes("attachZone('rdImages'"), "兩個新工具的檔案輸入應掛上拍照／貼上");

// 閱讀分級：即時國際時事（搜尋接地＋兒童安全過濾）
assert.match(studioHtml, /google_search: \{\}/, "找時事應使用 Gemini Google 搜尋接地");
assert.match(studioHtml, /const NEWS_BLOCKLIST = \/政治\|選舉/, "時事應有程式端兒童安全關鍵字過濾");
assert.match(studioHtml, /絕對排除\*\*：政治、選舉/, "時事提示詞應明確排除政治、暴力、色情");

// LINE 圖文選單：附小幫手可用指令參考表
assert.match(studioHtml, /LINE 小幫手聽得懂的指令/, "圖文選單應附可用指令參考表");
for (const cmd of ["說明", "今日點名", "缺交統計", "推播設定", "代課包", "提示 排隊", "撤回"]) {
  assert.ok(studioHtml.includes(`data-cmd="${cmd}"`), `指令表應含「${cmd}」`);
}

// 作文批改：段落修改指引＋評語 2 正向 1 待改進
assert.match(studioHtml, /段落修改指引（這一段要怎麼修）/, "批改單應逐段指出要修改處");
assert.match(studioHtml, /praise 兩條/, "評語應固定兩條正向");
assert.match(studioHtml, /improve 一條/, "評語應固定一條待改進");

// 2026-09-07 工作台：清單分任務／記事＋帶時間、任務拖曳分主子、訊息整合站
assert.match(indexHtml, /"kind": "task 或 note/, "AI 清單應標示每項是任務或記事");
assert.match(indexHtml, /id="aiAdviceApplyAll"/, "應有依建議一鍵建立全部");
assert.match(indexHtml, /function safeTimeString/, "應能擷取原文時間到任務欄位");
assert.match(indexHtml, /draggable="true" data-task-row=/, "任務列應可拖曳");
assert.match(indexHtml, /async function nestTask/, "應能拖曳設定／解除主子任務");
assert.match(indexHtml, /id="taskUnnestZone"/, "應有解除子任務的拖放區");
assert.match(indexHtml, /id="aiDraftBoard"/, "AI 行政助理應有任務草稿板");
assert.match(indexHtml, /function nestDraft/, "草稿板應可拖曳設定／解除主子");
assert.match(indexHtml, /taskType: kids\.length \? '主任務' : '一般任務'/, "確認建立時依草稿板關係寫入主／子任務並經 saveTask 持久化");
assert.match(indexHtml, /parentTaskId, projectId: parentTaskId, taskType: parentTaskId \? '子任務'/, "子任務應掛在剛建立的主任務底下");
assert.doesNotMatch(indexHtml, /建立主任務與 \$\{analysis\.children\.length\} 個子任務/, "不得再自動建立主／子任務");
assert.match(indexHtml, /id="messageHubSection"/, "應有訊息整合站版面");
assert.match(indexHtml, /data-toolbox-target="messageHubSection"/, "教師工具箱應有訊息整合站入口");
assert.match(indexHtml, /轉達學生', '轉達家長', '轉達科任', '自己待辦', '略過'/, "訊息整合站應有五種分類");

// 🖼 圖像簡報：先確認大綱→樣張→逐頁生圖（風格錨定）→單一 PDF
assert.match(studioHtml, /data-page="deck"/, "應有圖像簡報分頁");
assert.match(studioHtml, /async function dkGenerateSlide/, "應有逐頁生圖流程");
assert.match(studioHtml, /style-anchor\.png/, "後續頁應以樣張為風格參考");
assert.match(studioHtml, /ABSOLUTELY NO text, letters, numbers, logos or signs anywhere\. Keep \$\{calm\}/, "疊字模式生圖不得含文字並預留文字區");
assert.match(studioHtml, /pdf\.addPage\(\[1120, 630\], 'landscape'\)/, "PDF 應為 16:9 橫式、每頁一張逐頁加入");

// 任務／清單／整合站附超連結（來自原文或附件，寫入 detailUrl）
assert.match(indexHtml, /"link": "原文或附件中對應這件事的網址/, "AI 清單項目應抽出對應網址");
assert.match(indexHtml, /function safeUrl/, "網址應經 http(s) 驗證");
assert.match(indexHtml, /data-draft-link=/, "草稿板每項應可填連結");
assert.match(indexHtml, /draft\.detailUrl = item\.link \|\| ''/, "建立任務時連結應寫入 detailUrl");
assert.match(indexHtml, /rel="noopener" title="\$\{escapeHtml\(task\.detailUrl\)\}">🔗 連結<\/a>/, "任務清單應顯示連結按鈕");

// 任務說明彈窗：點名稱看完整說明、連結、來源附件
assert.match(indexHtml, /function openTaskDetail/, "應有任務說明彈窗");
assert.match(indexHtml, /data-task-detail=/, "任務名稱與下一步應可點開說明");
assert.match(indexHtml, /📎 來源附件：/, "AI 建立的任務應記錄來源附件");

// 版本標記：LineBot.gs BOT_VERSION、各頁 assets/version.js（發布時要一起更新日期）
assert.match(lineBotSource, /var BOT_VERSION = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}'/, "LineBot.gs 應有 BOT_VERSION 日期時間");
assert.match(lineBotSource, /botVersion: BOT_VERSION/, "ping 應回傳程式版本");
assert.match(lineBotSource, /\(版本\|程式版本\)/, "LINE 應支援「版本」指令");
assert.match(fs.readFileSync(path.join(__dirname, '..', 'assets', 'version.js'), 'utf8'), /TD_VERSION = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}'/, "assets/version.js 應有網站版本");
['Index.html', 'Studio.html', 'Morning.html', 'Install.html'].forEach(name => assert.match(fs.readFileSync(path.join(__dirname, '..', name), 'utf8'), /assets\/version\.js/, name + ' 應載入版本標記'));

// 使用說明選單：部署方法／系統使用方法／網頁介紹
assert.match(indexHtml, /id="helpMenuButton"/, "工作台應有使用說明按鈕");
['Install.html', 'About.html', 'Intro.html'].forEach(name => assert.match(indexHtml, new RegExp('class="help-card" href="' + name.replace('.', '\.') + '"'), '使用說明應連到 ' + name));

// 2026-09-28 減重版版面：標頭降高、指標列、工具箱分組、篩選預設收合、緊湊模式、小字 ≥ 11px
assert.match(indexHtml, /class="toolbox-group-label">溝通</, "工具箱應分組");
assert.match(indexHtml, /function setFilterPanelOpen/, "篩選欄應可收合並記住狀態");
assert.match(indexHtml, /id="compactToggleButton"/, "應有緊湊模式");
assert.doesNotMatch(indexHtml.slice(indexHtml.indexOf('<style>'), indexHtml.indexOf('</style>')), /font-size:\s*(?:9|10|10\.5)px/, "樣式表不得再有 9–10.5px 小字");

// 2026-09-28 安裝教學重寫：三種難度＋每關 SVG 操作示意圖；選單名稱與 GAS 一致
for (const id of ["tier1", "tier2", "tier3", "part2", "part3", "pet", "part5", "part6", "partv2", "part7"]) {
  assert.match(installHtml, new RegExp(`id="${id}"`), `安裝教學應有錨點 #${id}`);
}
assert.ok((installHtml.match(/class="diagram steps"/g) || []).length >= 7, "安裝教學每個難度都應附 SVG 操作示意圖");
assert.doesNotMatch(installHtml, /② 顯示我的金鑰/, "選單沒有「② 顯示我的金鑰」，應為「🔑 顯示我的金鑰」");
for (const menu of ["② 填入 LINE Token", "③ 填入我的 LINE userId", "④ 填入 Gemini 金鑰", "⑤ 設定自動化排程", "🔑 顯示我的金鑰", "📋 更新安裝總表"]) {
  assert.match(installHtml, new RegExp(menu.replace(/[()]/g, "\\$&")), `安裝教學應使用實際選單名稱「${menu}」`);
  assert.match(lineBotSource, new RegExp(menu.replace(/[()]/g, "\\$&")), `GAS 選單應有「${menu}」`);
}
assert.match(installHtml, /🔑B（Webhook 驗證參數）先不用管/, "難度 1 應說明 🔑B 先不用");
assert.match(lineBotSource, /【難度 1：雲端大腦】現在就要用這兩把/, "初始化彈窗應依難度分段");
assert.match(lineBotSource, /BOT_VERSION = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}'/, "GAS 版本日期");

// 2026-09-28 小白視角第二輪：授權四畫面、大屏密碼、下載 .bat、SmartScreen、金鑰記錄表
assert.ok((installHtml.match(/class="diagram steps"/g) || []).length >= 16, "每一關都應有 SVG 操作示意圖");
assert.match(installHtml, /選取全部/, "授權步驟應提醒勾「選取全部」");
assert.match(installHtml, /預設 <code>1234<\/code>/, "大屏設定應提醒設定頁密碼");
assert.match(installHtml, /data-kiosk="edge"/, "應可直接下載開機啟動 .bat");
assert.match(installHtml, /其他資訊<\/strong>」→「<strong>仍要執行/, "小綿助應說明 SmartScreen");
assert.match(installHtml, /id="keyNotes"/, "應提供金鑰記錄表範本");
assert.doesNotMatch(installHtml, /📤 送出/, "大屏按鈕是「💾 存到雲端」，不是「📤 送出」");

// ===== 組B 行政文書 =====
// 2026-11-01 升級規格書組 B：教材小工場「🗂 行政文書」分頁群
const groupBPage = id => {
  const start = studioHtml.indexOf(`id="page-${id}"`);
  assert.ok(start > 0, `Studio 應有 page-${id}`);
  return studioHtml.slice(start, studioHtml.indexOf("</section>", start));
};
assert.match(studioHtml, /<span class="tab-group">🗂 行政文書<\/span>/, "應有行政文書分頁群");
assert.match(studioHtml, /不得出現任何學生姓名/, "行政文書 AI 規範應禁止學生姓名");
assert.match(studioHtml, /不要猜任何數字：人次、人數、金額/, "行政文書 AI 不得猜數字");
assert.match(studioHtml, /AI 協助草擬，內容已由老師核對/, "勾核對後才出現的署名");
assert.match(studioHtml, /function docApplyConfirm\(prefix\)/, "應有核對切換");
assert.match(studioHtml, /clone\.querySelectorAll\('\[data-export-hide="1"\]'\)/, "Word／Excel 匯出應拿掉畫面專用標記");
assert.match(studioHtml, /if \(Array\.isArray\(imagePart\)\) parts\.push\(\.\.\.imagePart\)/, "callGemini 應支援多個附件");
// G1 📑 成果報告
assert.match(studioHtml, /data-page="report">📑 成果報告/, "應有成果報告分頁");
{
  const page = groupBPage("report");
  for (const id of ["rpName", "rpDate", "rpTarget", "rpUnit", "rpPlan", "rpPlanFiles", "rpExec", "rpPhotos", "rpChecked"]) assert.match(page, new RegExp(`id="${id}"`), `成果報告應有 #${id}`);
  assert.match(page, /downloadPreview\('rpPreview','成果報告','doc'\)/, "成果報告應可下載 Word");
  assert.match(page, /downloadPdfFromHost\('rpPreview','成果報告',false\)/, "成果報告應可下載 PDF");
}
for (const title of ["'依據'", "'目的'", "'辦理情形'", "'參與人次'", "'成效與檢討'", "'活動照片'"]) assert.ok(studioHtml.includes(`docSection(`) && studioHtml.includes(title), `成果報告應有 ${title} 段`);
assert.match(studioHtml, /\[\['學生', ''\], \['教職員', ''\], \['家長及來賓', ''\], \['合計', ''\]\]/, "參與人次欄留空給老師填");
assert.match(studioHtml, /function docPhotoTable/, "活動照片應以 2×2 表格排版");
// G2 📋 計畫書
assert.match(studioHtml, /data-page="plan">📋 計畫書/, "應有計畫書分頁");
{
  const page = groupBPage("plan");
  for (const t of ["校內活動", "社團", "教師研習", "校外教學", "競賽"]) assert.match(page, new RegExp(`<option value="${t}">`), `計畫書應有「${t}」類型`);
  for (const id of ["plName", "plTarget", "plDate", "plPlace", "plIdea", "plBudget", "plChecked"]) assert.match(page, new RegExp(`id="${id}"`), `計畫書應有 #${id}`);
}
for (const title of ["'活動流程表'", "'工作分配表'", "'經費概算表'", "'預期效益'", "'注意事項'"]) assert.ok(studioHtml.includes(title), `計畫書應有 ${title}`);
assert.match(studioHtml, /\[r\.item \|\| '', r\.unit \|\| '', r\.qty \|\| '', '', '', r\.note \|\| ''\]/, "經費表單價、金額一律留空");
assert.match(studioHtml, /const PL_TRIP_INSURANCE = /, "校外教學應固定加保險段落");
assert.match(studioHtml, /const PL_TRIP_CONSENT = /, "校外教學應固定加家長同意書提醒");
// G3 🗒 會議紀錄
assert.match(studioHtml, /data-page="minutes">🗒 會議紀錄/, "應有會議紀錄分頁");
{
  const page = groupBPage("minutes");
  for (const id of ["mtName", "mtTime", "mtPlace", "mtChair", "mtAttend", "mtAudio", "mtText", "mtPhotos", "mtTodoCopy", "mtChecked"]) assert.match(page, new RegExp(`id="${id}"`), `會議紀錄應有 #${id}`);
  assert.match(page, /accept="audio\/\*,\.m4a,\.mp3,\.webm/, "錄音檔應接受 m4a／mp3／webm");
}
assert.match(studioHtml, /m4a: 'audio\/mp4'/, "m4a 應以 audio/mp4 送 Gemini");
assert.match(studioHtml, /audio\.size > 15 \* 1024 \* 1024/, "錄音檔應有 15MB 上限提示");
assert.match(studioHtml, /\[\{ label: '事項' \}, \{ label: '負責', width: '24%' \}, \{ label: '期限', width: '22%' \}\]/, "待辦表應有事項、負責、期限欄");
for (const title of ["'主席報告'", "'討論事項'", "'臨時動議'", "'待辦事項'", "'下次會議'"]) assert.ok(studioHtml.includes(title), `會議紀錄應有 ${title}`);
// G4 📘 教案與觀議課
assert.match(studioHtml, /data-page="lesson">📘 教案與觀議課/, "應有教案與觀議課分頁");
{
  const page = groupBPage("lesson");
  for (const id of ["lpMode", "lpGrade", "lpSubject", "lpUnit", "lpPeriods", "lpImages", "lpFormat", "lpBullets", "lpChecked", "lpCodeHint"]) assert.match(page, new RegExp(`id="${id}"`), `教案頁應有 #${id}`);
  assert.match(page, /代碼是 AI 寫的，請對照課綱核對/, "教案畫面應固定提示代碼請核對");
}
assert.match(studioHtml, /\[\{ label: '時間', width: '10%' \}, \{ label: '教師活動' \}, \{ label: '學生活動' \}, \{ label: '評量', width: '16%' \}, \{ label: '資源', width: '14%' \}\]/, "教案應有每節教學活動流程表");
for (const title of ["'單元目標'", "'學習表現'", "'學習內容'", "'核心素養'", "'差異化教學'", "'評量方式'", "'觀課紀錄'", "'議課紀錄'"]) assert.ok(studioHtml.includes(title), `教案／觀議課應有 ${title}`);
assert.match(studioHtml, /strengths 議課的優點恰好 3 項；suggestions 具體可行的建議恰好 2 項。教學者回應不要寫/, "議課紀錄：優點 3、建議 2、教學者回應留白");
assert.match(studioHtml, /customFields 依序對每個欄位寫內容/, "教案可套學校欄位");
// ===== 組B 行政文書 end =====

// ===== 組A 行政文書 =====
// G7 文書情境包：AI 行政助理「📝 行政文書」五種情境、固定格式、可編輯可複製、沒金鑰提示、不自動建任務
{
  const docsStart = indexHtml.indexOf("// ===== 📝 行政文書（G7/G9）");
  const docsEnd = indexHtml.indexOf("// ===== 📝 行政文書 END =====");
  assert.ok(docsStart > 0 && docsEnd > docsStart, "工作台應有行政文書程式區塊");
  const docsJs = indexHtml.slice(docsStart, docsEnd);
  assert.match(indexHtml, /<details class="ai-docs" id="aiDocsPanel">/, "AI 行政助理應有「📝 行政文書」區");
  for (const [value, label] of [["memo", "簽呈"], ["notice", "校內公告"], ["reflection", "研習心得"], ["news", "活動新聞稿／學校臉書貼文"], ["parentLetter", "致家長信（活動通知・LINE 純文字版）"]]) {
    assert.ok(indexHtml.includes(`<option value="${value}">${label}</option>`), `行政文書情境應有「${label}」`);
    assert.match(docsJs, new RegExp(`\\n      ${value}: \\{`), `ADMIN_DOC_TYPES 應定義 ${value}`);
  }
  for (const heading of ["主旨：", "一、依據：", "二、緣由：", "三、內容：", "擬辦：", "'敬陳'"]) assert.ok(docsJs.includes(heading), `簽呈格式應有 ${heading}`);
  for (const heading of ["【公告】", "對象：", "重點：", "時間地點：", "聯絡窗口："]) assert.ok(docsJs.includes(heading), `校內公告格式應有 ${heading}`);
  for (const heading of ["研習名稱：", "研習時間：", "一、內容摘要", "二、心得與應用", "三、對教學的改變"]) assert.ok(docsJs.includes(heading), `研習心得格式應有 ${heading}`);
  assert.match(docsJs, /正文 100 到 200 字/, "新聞稿應要求 100–200 字");
  assert.match(docsJs, /function docHashtags[\s\S]*?slice\(0, 3\)[\s\S]*?while \(tags\.length < 3\)/, "新聞稿 hashtag 應固定三個");
  assert.match(docsJs, /要能直接貼到 LINE：不要用 markdown 符號/, "致家長信應為可貼 LINE 的純文字");
  assert.match(docsJs, /繁體中文與臺灣學校公文/, "prompt 應要求繁體中文與臺灣公文慣用語");
  assert.match(docsJs, /不得出現任何學生姓名/, "prompt 應禁止學生姓名");
  assert.match(docsJs, /redactSensitiveText\(raw\)/, "送 AI 前應先去識別化");
  assert.match(indexHtml, /id="aiDocOutput" contenteditable="true"/, "結果應放在可編輯區");
  assert.match(indexHtml, /id="aiDocCopyButton">📋 複製</, "結果應可複製");
  assert.match(indexHtml, /草稿，請核對/, "結果應標草稿請核對");
  assert.match(docsJs, /請先到設定填 \$\{name\} 金鑰/, "沒金鑰應提示先到設定填 Gemini 金鑰");
  assert.match(indexHtml, /id="aiDocRetryButton" hidden>🔁 重試 AI</, "AI 失敗應可重試");
  assert.doesNotMatch(docsJs, /serverCall\(|saveTask|applyTaskResult|taskDraft|renderTaskSuggestion/, "行政文書不得自動建任務");
}
// G9 晨會／升旗宣導稿：主題＋年級＋時長 → 講稿＋三句重點；推到大屏提示要確認、走既有 prompt_set
{
  const docsJs = indexHtml.slice(indexHtml.indexOf("// ===== 📝 行政文書（G7/G9）"), indexHtml.indexOf("// ===== 📝 行政文書 END ====="));
  assert.ok(indexHtml.includes('<option value="speech">晨會／升旗宣導稿</option>'), "行政文書應有晨會／升旗宣導稿");
  for (const id of ["aiDocSpeechTopic", "aiDocSpeechGrade", "aiDocSpeechMinutes", "aiDocPushButton", "aiDocPushHint"]) assert.match(indexHtml, new RegExp(`id="${id}"`), `宣導稿應有 #${id}`);
  for (const topic of ["防災演練", "交通安全", "品德教育", "節慶由來", "反霸凌"]) assert.ok(indexHtml.includes(`<option value="${topic}">`), `宣導主題建議應有 ${topic}`);
  for (const minutes of ["1", "2", "3"]) assert.match(indexHtml, new RegExp(`<option value="${minutes}"[^>]*>${minutes} 分鐘（約 ${Number(minutes) * 250} 字）`), `時長應有 ${minutes} 分鐘`);
  assert.match(docsJs, /const ADMIN_SPEECH_CHARS_PER_MINUTE = 250;/, "講稿字數以每分鐘 250 字計");
  assert.match(docsJs, /targetChars: minutes \* ADMIN_SPEECH_CHARS_PER_MINUTE/, "講稿目標字數 = 分鐘 × 250");
  assert.match(docsJs, /"keyPoints":\["重點一","重點二","重點三"\]/, "宣導稿應回三句重點");
  assert.match(docsJs, /'三句重點：',\s*\.\.\.docList\(d\.keyPoints, 3, docNumber, true\)/, "講稿下方固定列三句重點");
  assert.match(docsJs, /async function pushAdminDocPoint\(\)[\s\S]*?if \(!window\.confirm\(`確定要把這句送到教室大屏提示嗎？[\s\S]*?「\$\{text\}」[\s\S]*?return;[\s\S]*?await callLineBridge\('prompt_set', \{ text, img: 'class_focus\.png' \}\)/, "推到大屏要先確認並顯示句子，確認後才走 prompt_set");
  assert.match(docsJs, /\$\('aiDocPushButton'\)\.hidden = !ready;/, "沒有 LINE／GAS 設定時隱藏推送按鈕");
}

// ===== 組C 多班模式 =====
// G10 大屏多班模式（科任）：第一個班沿用舊 key，其他班 key 後加「:班級」；點名、聯絡本仍屬第一個班
{
  const mh = fs.readFileSync(path.join(projectRoot, "Morning.html"), "utf8");
  assert.match(mh, /id="setupClasses"/, "設定頁應有「我教的班級」欄");
  assert.match(mh, /我教的班級/, "設定頁欄位名稱應為「我教的班級」");
  assert.match(mh, /座號範圍與空號各班共用/, "設定頁應說明各班共用座號設定");
  assert.match(mh, /id="classSwitch" hidden/, "班級切換鈕預設隱藏（單班＝舊畫面）");
  assert.match(mh, /const CURRENT_CLASS_KEY = 'morningCurrentClass'/, "目前班應存在 morningCurrentClass");
  assert.match(mh, /return out\.length >= 2 \? out\.slice\(0, 12\) : \[\]/, "不到兩班時 classes 應為空陣列（行為與單班相同）");
  assert.match(mh, /return !isMultiClass\(\) \|\| cls === state\.settings\.classes\[0\] \? '' : ':' \+ cls;/, "第一個班沿用舊 key，其他班加「:班級」");
  assert.match(mh, /const SETTINGS_KEY = 'morningBoardSettings'/, "設定 key 不可改名");
  assert.match(mh, /const STATE_PREFIX = 'morningBoardState:'/, "當日狀態 key 不可改名");
  assert.match(mh, /const CONFIG_KEY = 'morningToolsConfig'/, "班級工具設定 key 不可改名");
  assert.match(mh, /const DAY_PREFIX = 'morningToolsDay:'/, "班級工具當日 key 不可改名");
  assert.match(mh, /const CLASS_CONFIG_FIELDS = \['scores', 'teamNames', 'teamCount'\]/, "計分板分數與隊名每班一份");
  assert.match(mh, /const CLASS_DAY_FIELDS = \['drawn', 'boards', 'groups'\]/, "已抽名單、檢核板、分組結果每班一份");
  assert.match(mh, /localStorage\.setItem\(STATE_PREFIX \+ todayKey\(\) \+ suffix, JSON\.stringify\(\{ boards: state\.boards \}\)\)/, "作業繳交版面每班一份，別班只存 boards");
  assert.match(mh, /JSON\.stringify\(\{ attendance: state\.attendance, boards: firstBoards, flags: state\.flags \}\)/, "別班畫面改點名仍寫回第一個班、不蓋掉第一個班的版面");
  assert.match(mh, /const target = cls \|\| \(push !== 'none' \? firstClass\(\) : currentClass\(\)\)/, "推播只送第一個班，一般存檔送目前的班");
  assert.match(mh, /const attendance = \(isFirst \? Object\.entries\(state\.attendance\) : \[\]\)/, "點名只屬第一個班");
  assert.match(mh, /date: todayKey\(\), className: cls, attendance, homework, push/, "送出雲端的 className 用指定班");
  assert.doesNotMatch(mh, /action: 'classroom_missing', token: state\.settings\.classroomToken, className: state\.settings\.className/, "補交／訂正應讀目前的班");
  assert.match(mh, /action: 'contactbook_get', token: state\.settings\.classroomToken, className: state\.settings\.className/, "聯絡本仍屬第一個班");
  assert.match(mh, /new CustomEvent\('morning:classchange'/, "切班要通知班級工具重新載入");
  assert.match(mh, /if \(lotteryBusy\) event\.preventDefault\(\)/, "抽籤進行中不可切班");
  assert.match(mh, /if \(toolsClassSuffix\(\)\) return absent;/, "別班沒有點名資料，抽籤分組不排除第一個班的缺席");
}
// G8 填報截止橫幅：任務可標「📋 填報／繳交」（存在下一步行動開頭的 [填報]，不改試算表契約）；到期前 3 天出現、逾期變紅、點了套用篩選
{
  assert.match(indexHtml, /<input type="checkbox" id="taskFilingFlag">📋 填報／繳交/, "任務表單應可勾「📋 填報／繳交」");
  assert.doesNotMatch(indexHtml, /id="taskFilingFlag"[^>]*name=/, "填報勾選框不可帶 name，避免變成新欄位送進試算表");
  assert.match(indexHtml, /const FILING_MARK = '\[填報\]';/, "填報標記為下一步行動開頭的 [填報]");
  assert.match(indexHtml, /const FILING_WINDOW_DAYS = 3;/, "到期前 3 天出現在橫幅");
  assert.match(indexHtml, /payload\.nextAction = applyFilingMark\(payload\.nextAction, \$\('taskFilingFlag'\)\.checked\);/, "存檔時把勾選轉成下一步行動前綴");
  assert.match(indexHtml, /\$\('taskFilingFlag'\)\.checked = isFilingTask\(values\);\s*\$\('nextAction'\)\.value = stripFilingMark\(values\.nextAction\);/, "編輯時帶出勾選、文字框不顯示標記");
  assert.match(indexHtml, /<button class="filing-banner" type="button" id="filingBanner" hidden><\/button>/, "任務清單上方應有填報橫幅");
  assert.match(indexHtml, /\.filing-banner\[hidden\] \{ display: none; \}/, "橫幅隱藏時不可被 display:flex 蓋掉");
  assert.match(indexHtml, /本週要交的填報/, "橫幅標題為「本週要交的填報」");
  assert.match(indexHtml, /banner\.classList\.toggle\('is-overdue', overdue > 0\)/, "有逾期時橫幅變紅");
  assert.match(indexHtml, /<option value="filing">📋 本週要交的填報<\/option>/, "期限篩選應有「本週要交的填報」");
  assert.match(indexHtml, /if \(due === 'filing' && !isFilingDueSoon\(task\)\) return false;/, "篩選只留本週要交的填報");
  assert.match(indexHtml, /\$\('filingBanner'\)\.addEventListener\('click', \(\) => \{\s*\$\('dueFilter'\)\.value = 'filing';\s*applyFilters\(\);/, "點橫幅套用篩選");
  assert.ok(Array.from(TASK_HEADERS).includes("下一步行動"), "填報標記沿用既有「下一步行動」欄位，不新增試算表欄位");
}
