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

for (const htmlName of ["Installer.html", "Index.html", "Board.html", "Morning.html", "Install.html"]) {
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
assert.match(indexHtml, /github\.com\/cona0815\/teacher-dashboard\/releases\/download\/xiaomianzhu-v1\.6\/xiaomianzhu-windows-portable\.zip/, "小綿助設定頁應提供免 Python 可攜版下載入口");
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
assert.match(
  indexHtml,
  /raw\.githubusercontent\.com\/cona0815\/teacher-dashboard\/main\/assets\/pet\//,
  "正式環境的小綿助素材應由本專案 repository 提供",
);
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
assert.doesNotMatch(desktopSecretary, /urllib\.request\.urlopen/, "桌面小綿助不應再依賴 GAS 網址同步");
assert.doesNotMatch(desktopSecretary, /GAS \/exec|同步金鑰/, "桌面小綿助不應再顯示 GAS 同步欄位");
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
