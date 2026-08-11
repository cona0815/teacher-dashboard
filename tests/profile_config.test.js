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
assert.equal(catalog.length, 7);
assert.ok(catalog.every((office) => office.roles.every((role) => role.key && role.name)));

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

for (const htmlName of ["Installer.html", "Index.html", "Board.html"]) {
  const html = fs.readFileSync(path.join(projectRoot, htmlName), "utf8");
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((match) => match[1]);
  assert.ok(scripts.length > 0, `${htmlName} 缺少前端程式`);
  scripts.forEach((script) => new Function(script));
}

const indexHtml = fs.readFileSync(path.join(projectRoot, "Index.html"), "utf8");
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
const desktopSecretary = fs.readFileSync(path.join(projectRoot, "desktop_pet_secretary.py"), "utf8");
for (const secretaryFeature of ["今日簡報", "今日重要", "已逾期", "待追蹤", "健康管理", "快速交代"]) {
  assert.match(desktopSecretary, new RegExp(secretaryFeature), `桌面小綿助缺少「${secretaryFeature}」`);
}
assert.match(desktopSecretary, /ImageGrab\.grabclipboard\(\)/, "桌面小綿助必須支援貼上圖片或檔案");

assert.doesNotMatch(source, /\b1[A-Za-z0-9_-]{30,}\b/, "公開版本不得含固定 Google 資源 ID");
assert.match(source, /BOUND_SPREADSHEET_ID/, "安裝後應以 Script Properties 定位試算表");
assert.match(source, /verifyCsrfToken_/, "寫入流程必須保留 CSRF 驗證");
assert.match(source, /verifyInstallToken_\(installToken\)/, "安裝寫入必須驗證安裝憑證");
assert.match(source, /assertSpreadsheetUiContext_\(\)/, "安裝端點必須限制在試算表 UI");
assert.match(source, /LockService/, "共享寫入必須保留鎖");

console.log("profile_config.test.js: all checks passed");
