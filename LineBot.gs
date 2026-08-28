/**
 * LINE 小幫手（選用雲端模組）
 *
 * 這是教師工作台的「選用」LINE Bot 後端：每位老師部署到自己的 Google Apps Script，
 * 搭配自己的 Google 試算表與 LINE 官方帳號。試算表只作為「雲端轉運信箱」：
 * LINE 傳入的訊息暫存在這裡，等教師在工作台網頁確認後轉為任務或記事；
 * 資料正本永遠保存在教師瀏覽器的 localStorage。
 *
 * 不安裝本模組時，教師工作台與桌面小綿助完全不受影響。
 *
 * 安裝步驟請見 LINE_BOT_INSTALL.md。
 * 授權：MIT（同本專案）。
 */

var LINE_BOT_CONFIG = {
  INBOX_SHEET: 'LINE收件匣',
  SNAPSHOT_SHEET: '工作台快照',
  ROLLCALL_SHEET: '點名紀錄',
  HOMEWORK_SHEET: '作業紀錄',
  CONTACTBOOK_SHEET: '聯絡本',
  CONTACTBOOK_HEADERS: ['日期', '班級', '內容', '更新時間', '來源'],
  FILES_SHEET: '檔案備份',
  FILES_HEADERS: ['日期', '類型', '分類', '標題', '檔名', '雲端連結'],
  INBOX_HEADERS: ['編號', '建立時間', '類型', '原文', '整理標題', '到期日', '工作主軸', '狀態', '來源使用者', '補充JSON'],
  ROLLCALL_HEADERS: ['日期', '班級', '座號', '狀態'],
  HOMEWORK_HEADERS: ['日期', '班級', '科目', '作業名稱', '座號', '狀態'],
  ATTENDANCE_STATUSES: ['病假', '事假', '遲到', '未到'],
  HOMEWORK_STATUSES: ['缺交', '補交'],
  MAX_TEXT_LENGTH: 3000,
  MAX_PULL_ROWS: 200,
  MAX_INBOX_ROWS: 1000,
  REPLY_ENDPOINT: 'https://api.line.me/v2/bot/message/reply',
  PUSH_ENDPOINT: 'https://api.line.me/v2/bot/message/push',
  GEMINI_ENDPOINT: 'https://generativelanguage.googleapis.com/v1beta/models/',
  DEFAULT_GEMINI_MODEL: 'gemini-2.5-flash',
  WORK_AXES: ['教學', '行政', '學年主任', '導師'],
  NOTE_TAGS: ['家長聯繫', '學生概況', '作業缺交', '備課靈感', '生活雜事']
};

/** 第一次安裝時於 Apps Script 編輯器手動執行：建立資料表並產生金鑰。 */
function setupLineBot() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  if (!spreadsheet) throw new Error('請先把這份指令碼綁定到一份 Google 試算表（擴充功能 → Apps Script）。');
  ensureLineBotSheets_(spreadsheet);
  var properties = PropertiesService.getScriptProperties();
  if (!properties.getProperty('LINE_WEBHOOK_TOKEN')) {
    properties.setProperty('LINE_WEBHOOK_TOKEN', Utilities.getUuid().replace(/-/g, ''));
  }
  if (!properties.getProperty('LINE_SYNC_TOKEN')) {
    properties.setProperty('LINE_SYNC_TOKEN', Utilities.getUuid().replace(/-/g, ''));
  }
  if (!properties.getProperty('CLASSROOM_TOKEN')) {
    properties.setProperty('CLASSROOM_TOKEN', Utilities.getUuid().replace(/-/g, ''));
  }
  var summary = [
    '✅ LINE 小幫手初始化完成。',
    '',
    '請接著在「專案設定 → 指令碼屬性」確認／填入：',
    '1. LINE_CHANNEL_ACCESS_TOKEN：LINE Developers 的 Channel access token（必填）。',
    '2. LINE_ALLOWED_USER_IDS：你自己的 LINE userId（強烈建議，鎖定只回應你本人；多個以逗號分隔）。',
    '3. GEMINI_API_KEY：Gemini 金鑰（選填；沒填時改用「任務：」「記：」等前綴規則）。',
    '',
    'Webhook 網址（貼到 LINE Developers 的 Webhook URL）：',
    '  <部署後的 /exec 網址>?hook=' + properties.getProperty('LINE_WEBHOOK_TOKEN'),
    '',
    '工作台同步金鑰（貼到教師工作台「系統設定 → LINE 小幫手」）：',
    '  ' + properties.getProperty('LINE_SYNC_TOKEN'),
    '',
    '教室大屏金鑰（貼到 Morning.html 大屏頁的設定；權限只限當日點名與作業回報）：',
    '  ' + properties.getProperty('CLASSROOM_TOKEN')
  ].join('\n');
  Logger.log(summary);
  return summary;
}

function ensureLineBotSheets_(spreadsheet) {
  var inbox = spreadsheet.getSheetByName(LINE_BOT_CONFIG.INBOX_SHEET);
  if (!inbox) {
    inbox = spreadsheet.insertSheet(LINE_BOT_CONFIG.INBOX_SHEET);
    inbox.getRange(1, 1, 1, LINE_BOT_CONFIG.INBOX_HEADERS.length).setValues([LINE_BOT_CONFIG.INBOX_HEADERS]);
    inbox.setFrozenRows(1);
  }
  var snapshot = spreadsheet.getSheetByName(LINE_BOT_CONFIG.SNAPSHOT_SHEET);
  if (!snapshot) {
    snapshot = spreadsheet.insertSheet(LINE_BOT_CONFIG.SNAPSHOT_SHEET);
    snapshot.getRange(1, 1, 1, 2).setValues([['更新時間', '快照JSON']]);
    snapshot.setFrozenRows(1);
  }
  var rollcall = spreadsheet.getSheetByName(LINE_BOT_CONFIG.ROLLCALL_SHEET);
  if (!rollcall) {
    rollcall = spreadsheet.insertSheet(LINE_BOT_CONFIG.ROLLCALL_SHEET);
    rollcall.getRange(1, 1, 1, LINE_BOT_CONFIG.ROLLCALL_HEADERS.length).setValues([LINE_BOT_CONFIG.ROLLCALL_HEADERS]);
    rollcall.setFrozenRows(1);
  }
  var homework = spreadsheet.getSheetByName(LINE_BOT_CONFIG.HOMEWORK_SHEET);
  if (!homework) {
    homework = spreadsheet.insertSheet(LINE_BOT_CONFIG.HOMEWORK_SHEET);
    homework.getRange(1, 1, 1, LINE_BOT_CONFIG.HOMEWORK_HEADERS.length).setValues([LINE_BOT_CONFIG.HOMEWORK_HEADERS]);
    homework.setFrozenRows(1);
  } else if (String(homework.getRange(1, 4).getValue()) === '座號') {
    // v2 遷移：舊版第 4 欄是座號，插入「作業名稱」欄，既有資料不動。
    homework.insertColumnBefore(4);
    homework.getRange(1, 4).setValue('作業名稱');
  }
  var contactbook = spreadsheet.getSheetByName(LINE_BOT_CONFIG.CONTACTBOOK_SHEET);
  if (!contactbook) {
    contactbook = spreadsheet.insertSheet(LINE_BOT_CONFIG.CONTACTBOOK_SHEET);
    contactbook.getRange(1, 1, 1, LINE_BOT_CONFIG.CONTACTBOOK_HEADERS.length).setValues([LINE_BOT_CONFIG.CONTACTBOOK_HEADERS]);
    contactbook.setFrozenRows(1);
  }
  var files = spreadsheet.getSheetByName(LINE_BOT_CONFIG.FILES_SHEET);
  if (!files) {
    files = spreadsheet.insertSheet(LINE_BOT_CONFIG.FILES_SHEET);
    files.getRange(1, 1, 1, LINE_BOT_CONFIG.FILES_HEADERS.length).setValues([LINE_BOT_CONFIG.FILES_HEADERS]);
    files.setFrozenRows(1);
  }
  return { inbox: inbox, snapshot: snapshot, rollcall: rollcall, homework: homework, contactbook: contactbook, files: files };
}

/**
 * 一鍵設定全部自動觸發器：在編輯器選擇本函式按「執行」一次即可。
 * 重複執行會先清掉舊的再重建，不會疊加。
 * 1. sendLineDailyBriefing　每天 8–9 點：每日簡報（點名回報＋作業＋今日任務＋逾期清單）
 * 2. sendRollcallReminder　每天 9–10 點：當天還沒點名回報時提醒（排在自動回報之後檢查）
 * 3. sendWeeklyHomeworkAlerts　每週五 15–16 點：缺交達門檻的家長訊息草稿
 */
function setupTriggers() {
  var handlers = ['sendLineDailyBriefing', 'sendRollcallReminder', 'sendWeeklyHomeworkAlerts', 'sendAfternoonBriefing'];
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (handlers.indexOf(trigger.getHandlerFunction()) !== -1) ScriptApp.deleteTrigger(trigger);
  });
  ScriptApp.newTrigger('sendLineDailyBriefing').timeBased().everyDays(1).atHour(8).create();
  ScriptApp.newTrigger('sendRollcallReminder').timeBased().everyDays(1).atHour(8).create();
  ScriptApp.newTrigger('sendAfternoonBriefing').timeBased().everyDays(1).atHour(16).create();
  ScriptApp.newTrigger('sendWeeklyHomeworkAlerts').timeBased().onWeekDay(ScriptApp.WeekDay.FRIDAY).atHour(15).create();
  var summary = [
    '✅ 已設定 4 個自動觸發器（實際會不會發送，由「推播設定」決定）：',
    '・每日簡報備援（每天 8–9 點）— 預設關閉，因為點名推播已含相同內容',
    '・未點名提醒（8:20 起智慧檢查，僅在當天沒回報時發送）— 預設開啟',
    '・下午整合推播（16–17 點：放學小結／早期缺交預警／到期前提醒）— 三項皆預設關閉，開幾項都只用 1 則額度',
    '・每週家長關懷（每週五下午 3–4 點）— 預設開啟',
    '',
    '在 LINE 傳「推播設定」可查看目前開關與本月用量，傳「開啟 放學小結」「關閉 作業推播」即可切換。',
    '有開大屏的日子，08:08 點名推播會一併帶上今日課程、任務、記事與逾期；08:40 再補一則作業繳交情況。'
  ].join('\n');
  Logger.log(summary);
  return summary;
}

function lineBotProperty_(key) {
  return String(PropertiesService.getScriptProperties().getProperty(key) || '').trim();
}

var MORNING_BRIEF_FLAG = 'MORNING_BRIEF_SENT_DATE';

/**
 * 取得「今日重點」段落（今日課程／任務／記事／逾期），同一天只回傳一次。
 * 大屏的點名推播與每日簡報共用這個旗標，先送到的那一則帶上，另一則就不再重複。
 */
function morningBriefSectionOnce_(date) {
  var props = PropertiesService.getScriptProperties();
  if (String(props.getProperty(MORNING_BRIEF_FLAG) || '') === date) return '';
  if (!readWorkspaceSnapshot_()) return '';   // 工作台還沒同步過快照就先不附，避免推一段沒內容的提示
  props.setProperty(MORNING_BRIEF_FLAG, date);
  return buildSnapshotReply_();
}

// ---------------------------------------------------------------------------
// 推播設定與 LINE 額度保護
// 只有「主動推播」會用到 LINE 免費額度；老師問、小幫手答（reply）完全免費，
// 因此這裡只管理 4+1 項主動推播，老師可用 LINE 指令隨時開關。
// ---------------------------------------------------------------------------

var PUSH_SETTINGS_KEY = 'PUSH_SETTINGS';
var QUOTA_CACHE_KEY = 'LINE_QUOTA_CACHE';
var QUOTA_SAFETY_MARGIN = 20;   // 距離上限剩這麼多則時，只保留最重要的點名推播

var PUSH_ITEMS = [
  { key: 'rollcall', name: '點名推播', desc: '早上出缺＋今日課程／任務／記事／逾期', def: true },
  { key: 'homework', name: '作業推播', desc: '收完作業後的點名＋各科繳交情況', def: true },
  { key: 'reminder', name: '未點名提醒', desc: '當天沒收到大屏回報才發', def: true },
  { key: 'weekly', name: '週五家長關懷', desc: '缺交達門檻的家長訊息草稿', def: true },
  { key: 'dailyBrief', name: '每日簡報備援', desc: '沒在用大屏的人才需要；點名推播已含相同內容', def: false },
  { key: 'missingAlert', name: '早期缺交預警', desc: '同一科連續缺交就提早通知', def: false },
  { key: 'dueTomorrow', name: '到期前一天提醒', desc: '明天到期的任務先提醒', def: false },
  { key: 'dayEnd', name: '放學小結', desc: '下午回顧今天並提醒明天', def: false }
];

function pushSettings_() {
  var saved = {};
  try { saved = JSON.parse(lineBotProperty_(PUSH_SETTINGS_KEY) || '{}') || {}; } catch (error) {}
  var result = {};
  PUSH_ITEMS.forEach(function (item) {
    result[item.key] = typeof saved[item.key] === 'boolean' ? saved[item.key] : item.def;
  });
  return result;
}

function savePushSettings_(settings) {
  PropertiesService.getScriptProperties().setProperty(PUSH_SETTINGS_KEY, JSON.stringify(settings));
}

/** 向 LINE 查詢本月推播用量；查不到時回 null（例如金鑰未設定或網路異常）。 */
function lineQuotaUsage_() {
  var token = lineBotProperty_('LINE_CHANNEL_ACCESS_TOKEN');
  if (!token) return null;
  try {
    var options = { method: 'get', muteHttpExceptions: true, headers: { Authorization: 'Bearer ' + token } };
    var quotaResponse = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/quota', options);
    var usageResponse = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/quota/consumption', options);
    if (quotaResponse.getResponseCode() !== 200 || usageResponse.getResponseCode() !== 200) return null;
    var quota = JSON.parse(quotaResponse.getContentText() || '{}');
    var usage = JSON.parse(usageResponse.getContentText() || '{}');
    return {
      limit: String(quota.type) === 'limited' ? Number(quota.value || 0) : 0,
      used: Number(usage.totalUsage || 0)
    };
  } catch (error) {
    return null;
  }
}

/** 每天只實際查詢一次，避免每則推播都多打兩次 API。 */
function cachedQuotaUsage_() {
  var props = PropertiesService.getScriptProperties();
  var today = lineBotToday_();
  try {
    var cache = JSON.parse(props.getProperty(QUOTA_CACHE_KEY) || 'null');
    if (cache && cache.date === today) return cache;
  } catch (error) {}
  var live = lineQuotaUsage_();
  var record = { date: today, limit: live ? live.limit : 0, used: live ? live.used : 0 };
  props.setProperty(QUOTA_CACHE_KEY, JSON.stringify(record));
  return record;
}

/**
 * 這一項推播現在可不可以發：老師關掉的不發；額度快用完時，
 * 只保留最重要的點名推播，其餘自動暫停到下個月。
 */
function pushAllowed_(key) {
  if (!pushSettings_()[key]) return false;
  if (key === 'rollcall') return true;
  var quota = cachedQuotaUsage_();
  if (quota.limit && quota.used >= quota.limit - QUOTA_SAFETY_MARGIN) return false;
  return true;
}

function buildPushSettingsReply_() {
  var settings = pushSettings_();
  var quota = lineQuotaUsage_();
  var lines = ['📢 推播設定'];
  if (quota && quota.limit) {
    lines.push('本月推播已用 ' + quota.used + '／' + quota.limit + ' 則');
    if (quota.used >= quota.limit - QUOTA_SAFETY_MARGIN) {
      lines.push('⚠️ 已接近上限，除了點名推播外會自動暫停到下個月。');
    }
  } else if (quota) {
    lines.push('本月推播已用 ' + quota.used + ' 則（目前方案沒有則數上限）');
  }
  lines.push('');
  PUSH_ITEMS.forEach(function (item) {
    lines.push((settings[item.key] ? '✅ ' : '⬜ ') + item.name + '｜' + item.desc);
  });
  lines.push('');
  lines.push('切換方式：傳「開啟 放學小結」或「關閉 作業推播」。');
  lines.push('只有以上項目會用到 LINE 額度；你問我答（今日點名、缺交統計、座號查詢、代課包…）完全免費。');
  return lines.join('\n');
}

function togglePushSetting_(action, name) {
  var keyword = String(name || '').trim();
  var target = null;
  PUSH_ITEMS.forEach(function (item) {
    if (target) return;
    if (item.name === keyword || item.name.indexOf(keyword) !== -1 || (keyword && keyword.indexOf(item.name) !== -1)) target = item;
  });
  if (!target) return '找不到「' + keyword + '」這項推播。\n傳「推播設定」可以看全部可切換的項目。';
  var settings = pushSettings_();
  settings[target.key] = action === '開啟';
  savePushSettings_(settings);
  return (action === '開啟' ? '✅ 已開啟「' : '⬜ 已關閉「') + target.name + '」\n\n' + buildPushSettingsReply_();
}

/**
 * 入口：同一個 doPost 同時服務 LINE Webhook 與教師工作台同步 API。
 * - LINE Webhook：網址需帶 ?hook=<LINE_WEBHOOK_TOKEN>（GAS 收不到 LINE 簽章標頭，以此補償）。
 * - 同步 API：JSON body 帶 { action, token, ... }，token 需等於 LINE_SYNC_TOKEN。
 */
function doPost(e) {
  var body = {};
  try {
    body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
  } catch (error) {
    return lineBotJson_({ ok: false, error: '無法解析請求內容' });
  }
  if (body && Array.isArray(body.events)) {
    return handleLineWebhook_(e, body);
  }
  return handleLineSyncApi_(body);
}

function doGet() {
  return lineBotJson_({ ok: true, service: 'teacher-dashboard-line-bot', hint: '請以 POST 使用本服務。' });
}

function lineBotJson_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}

// ---------------------------------------------------------------------------
// 教師工作台同步 API
// ---------------------------------------------------------------------------

function handleLineSyncApi_(body) {
  var action = String(body.action || '');
  var provided = String(body.token || '');
  var teacherToken = lineBotProperty_('LINE_SYNC_TOKEN');
  var classroomToken = lineBotProperty_('CLASSROOM_TOKEN');
  var isTeacher = Boolean(teacherToken) && provided === teacherToken;
  var isClassroom = Boolean(classroomToken) && provided === classroomToken;
  // 教室金鑰權限受限：只能回報與讀取「當日」的點名與作業；歷史查詢需要老師金鑰。
  var classroomActions = ['ping', 'rollcall_submit', 'classroom_today', 'classroom_missing', 'homework_resubmit', 'contactbook_get', 'contactbook_save'];
  if (!isTeacher && !(isClassroom && classroomActions.indexOf(action) !== -1)) {
    return lineBotJson_({ ok: false, error: '金鑰不正確或權限不足' });
  }
  try {
    if (action === 'ping') {
      return lineBotJson_({ ok: true, service: 'teacher-dashboard-line-bot', version: 1, role: isTeacher ? 'teacher' : 'classroom', time: new Date().toISOString() });
    }
    if (action === 'pull') return lineBotJson_(pullLineInbox_());
    if (action === 'ack') return lineBotJson_(ackLineInbox_(body));
    if (action === 'snapshot') return lineBotJson_(saveWorkspaceSnapshot_(body));
    if (action === 'rollcall_submit') return lineBotJson_(submitRollcall_(body));
    if (action === 'classroom_today') return lineBotJson_(readRollcallRange_(lineBotToday_(), lineBotToday_(), String(body.className || '')));
    if (action === 'classroom_missing') return lineBotJson_(readClassroomMissing_(body));
    if (action === 'homework_resubmit') return lineBotJson_(markHomeworkResubmitted_(body));
    if (action === 'rollcall_query') return lineBotJson_(readRollcallRange_(String(body.from || ''), String(body.to || ''), String(body.className || '')));
    if (action === 'contactbook_get') return lineBotJson_(getContactBook_(body, isTeacher));
    if (action === 'contactbook_save') return lineBotJson_(saveContactBook_(body, isTeacher));
    if (action === 'contactbook_list') {
      if (!isTeacher) return lineBotJson_({ ok: false, error: '歷史清單需要老師金鑰' });
      return lineBotJson_(listContactBook_(body));
    }
    return lineBotJson_({ ok: false, error: '未知的動作：' + action });
  } catch (error) {
    return lineBotJson_({ ok: false, error: String(error && error.message ? error.message : error) });
  }
}

function lineBotToday_() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

// ---------------------------------------------------------------------------
// 晨間大屏：點名與作業回報
// ---------------------------------------------------------------------------

/**
 * 大屏送出當日回報。同一天同一班重送會整批覆蓋。
 * payload: { date, className, attendance: [{seat, status}], homework: [{subject, missing: [], resubmitted: []}], push }
 * push：'none' 只存雲端不推播（大屏按送出、自動存檔用）｜'attendance' 只推點名｜'full' 點名＋作業。
 * 省略時預設 'full'，保留舊版大屏的行為。
 */
function submitRollcall_(body) {
  var date = String(body.date || '');
  if (date !== lineBotToday_()) throw new Error('大屏只能回報今天的紀錄');
  var className = String(body.className || '').trim().slice(0, 20);
  if (!className) throw new Error('缺少班級名稱');
  var attendance = Array.isArray(body.attendance) ? body.attendance : [];
  var homework = Array.isArray(body.homework) ? body.homework : [];
  var pushMode = String(body.push || 'full');
  if (['none', 'attendance', 'full'].indexOf(pushMode) === -1) pushMode = 'full';

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
    deleteRowsByDateClass_(sheets.rollcall, date, className, 1);
    deleteRowsByDateClass_(sheets.homework, date, className, 1);

    var rollcallRows = [];
    attendance.slice(0, 60).forEach(function (entry) {
      var seat = parseInt(entry && entry.seat, 10);
      var status = String((entry && entry.status) || '');
      if (seat >= 1 && seat <= 99 && LINE_BOT_CONFIG.ATTENDANCE_STATUSES.indexOf(status) !== -1) {
        rollcallRows.push([date, className, seat, status]);
      }
    });
    if (rollcallRows.length) {
      sheets.rollcall.getRange(sheets.rollcall.getLastRow() + 1, 1, rollcallRows.length, 4).setValues(rollcallRows);
    }

    var homeworkRows = [];
    homework.slice(0, 20).forEach(function (entry) {
      var subject = String((entry && entry.subject) || '').trim().slice(0, 20);
      if (!subject) return;
      var assignment = String((entry && entry.assignment) || '').trim().slice(0, 20);
      (Array.isArray(entry.missing) ? entry.missing : []).slice(0, 60).forEach(function (seat) {
        seat = parseInt(seat, 10);
        if (seat >= 1 && seat <= 99) homeworkRows.push([date, className, subject, assignment, seat, '缺交']);
      });
      (Array.isArray(entry.resubmitted) ? entry.resubmitted : []).slice(0, 60).forEach(function (seat) {
        seat = parseInt(seat, 10);
        if (seat >= 1 && seat <= 99) homeworkRows.push([date, className, subject, assignment, seat, '補交']);
      });
    });
    if (homeworkRows.length) {
      sheets.homework.getRange(sheets.homework.getLastRow() + 1, 1, homeworkRows.length, 6).setValues(homeworkRows);
    }
  } finally {
    lock.releaseLock();
  }

  // 大屏按「送出」與自動存檔都是 push:'none'：資料存進試算表，但不打擾老師的 LINE。
  if (pushMode === 'none') return { ok: true, pushed: 0, saved: true };
  // 老師可在 LINE 傳「關閉 作業推播」等指令關掉個別推播；關掉時資料照樣存好。
  if (!pushAllowed_(pushMode === 'attendance' ? 'rollcall' : 'homework')) {
    return { ok: true, pushed: 0, saved: true, skipped: 'push-disabled' };
  }

  var summaryText = buildRollcallSummaryText_(
    date, className, attendance, pushMode === 'attendance' ? [] : homework, pushMode);
  // 點名推播同時當成老師的晨間簡報：附上今日課程、任務、記事與逾期提醒。
  // 同一天只附一次，之後 sendLineDailyBriefing 會自動略過，不會重複轟炸。
  if (pushMode === 'attendance') {
    var brief = morningBriefSectionOnce_(date);
    if (brief) summaryText += '\n\n' + brief;
  }
  var users = lineBotProperty_('LINE_ALLOWED_USER_IDS')
    .split(',').map(function (value) { return value.trim(); }).filter(String);
  users.forEach(function (userId) { pushLineMessage_(userId, summaryText); });
  return { ok: true, pushed: users.length, saved: true };
}

function deleteRowsByDateClass_(sheet, date, className, dateColumn) {
  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) return;
  var values = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
  for (var index = values.length - 1; index >= 0; index -= 1) {
    if (String(values[index][0]) === date && String(values[index][1]) === className) {
      sheet.deleteRow(index + 2);
    }
  }
}

function buildRollcallSummaryText_(date, className, attendance, homework, mode) {
  var time = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'M/d HH:mm');
  var title = mode === 'attendance' ? ' 晨間點名回報（' : ' 晨間回報（';
  var lines = ['📋 ' + className + title + time + '）'];
  var byStatus = {};
  (attendance || []).forEach(function (entry) {
    var status = String((entry && entry.status) || '');
    if (LINE_BOT_CONFIG.ATTENDANCE_STATUSES.indexOf(status) === -1) return;
    if (!byStatus[status]) byStatus[status] = [];
    byStatus[status].push(entry.seat + '號');
  });
  var attendanceParts = LINE_BOT_CONFIG.ATTENDANCE_STATUSES
    .filter(function (status) { return byStatus[status] && byStatus[status].length; })
    .map(function (status) { return status + byStatus[status].length + '（' + byStatus[status].join('、') + '）'; });
  lines.push('👥 出缺：' + (attendanceParts.length ? attendanceParts.join('、') : '全班到齊 🎉'));
  var homeworkLines = [];
  (homework || []).forEach(function (entry) {
    var subject = String((entry && entry.subject) || '').trim();
    if (!subject) return;
    var label = subject + (String((entry && entry.assignment) || '').trim() ? '／' + String(entry.assignment).trim() : '');
    var missing = (Array.isArray(entry.missing) ? entry.missing : []).map(function (seat) { return seat + '號'; });
    var resubmitted = (Array.isArray(entry.resubmitted) ? entry.resubmitted : []).map(function (seat) { return seat + '號'; });
    var parts = [];
    if (missing.length) parts.push('缺交' + missing.length + '（' + missing.join('、') + '）');
    if (resubmitted.length) parts.push('補交' + resubmitted.length + '（' + resubmitted.join('、') + '）');
    homeworkLines.push('・' + label + '：' + (parts.length ? parts.join('、') : '全交 ✅'));
  });
  if (homeworkLines.length) {
    lines.push('📚 作業：');
    lines = lines.concat(homeworkLines);
  }
  return lines.join('\n');
}

function readRollcallRange_(from, to, className) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(from) || !/^\d{4}-\d{2}-\d{2}$/.test(to) || from > to) {
    throw new Error('日期區間格式不正確');
  }
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var attendance = [];
  var rollcallLast = sheets.rollcall.getLastRow();
  if (rollcallLast > 1) {
    sheets.rollcall.getRange(2, 1, rollcallLast - 1, 4).getValues().forEach(function (row) {
      var date = row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : String(row[0]);
      if (date < from || date > to) return;
      if (className && String(row[1]) !== className) return;
      if (attendance.length < 5000) attendance.push({ date: date, className: String(row[1]), seat: Number(row[2]), status: String(row[3]) });
    });
  }
  var homework = [];
  var homeworkLast = sheets.homework.getLastRow();
  if (homeworkLast > 1) {
    sheets.homework.getRange(2, 1, homeworkLast - 1, 6).getValues().forEach(function (row) {
      var date = row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : String(row[0]);
      if (date < from || date > to) return;
      if (className && String(row[1]) !== className) return;
      if (homework.length < 5000) homework.push({ date: date, className: String(row[1]), subject: String(row[2]), assignment: String(row[3] || ''), seat: Number(row[4]), status: String(row[5]) });
    });
  }
  return { ok: true, from: from, to: to, attendance: attendance, homework: homework };
}

/** 教室金鑰可用：近 N 天仍為缺交的清單（僅日期、科目、作業名稱、座號）。 */
function readClassroomMissing_(body) {
  var className = String(body.className || '').trim();
  if (!className) throw new Error('缺少班級名稱');
  var days = Math.min(60, Math.max(1, parseInt(body.days, 10) || 30));
  var from = Utilities.formatDate(new Date(new Date().getTime() - (days - 1) * 24 * 3600 * 1000), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var data = readRollcallRange_(from, lineBotToday_(), className);
  var missing = data.homework.filter(function (row) { return row.status === '缺交'; })
    .map(function (row) { return { date: row.date, subject: row.subject, assignment: row.assignment, seat: row.seat }; });
  return { ok: true, from: from, to: lineBotToday_(), missing: missing };
}

/** 教室金鑰可用的唯一歷史寫入：把單筆「缺交」改為「補交」，其他欄位一律不可改。 */
function markHomeworkResubmitted_(body) {
  var className = String(body.className || '').trim();
  var date = String(body.date || '');
  var subject = String(body.subject || '').trim();
  var assignment = String(body.assignment || '').trim();
  var seat = parseInt(body.seat, 10);
  if (!className || !/^\d{4}-\d{2}-\d{2}$/.test(date) || !subject || !(seat >= 1 && seat <= 99)) {
    throw new Error('補交參數不完整');
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
    var lastRow = sheets.homework.getLastRow();
    if (lastRow <= 1) return { ok: true, updated: 0 };
    var values = sheets.homework.getRange(2, 1, lastRow - 1, 6).getValues();
    for (var index = 0; index < values.length; index += 1) {
      var row = values[index];
      var rowDate = row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : String(row[0]);
      if (rowDate === date && String(row[1]) === className && String(row[2]) === subject
        && String(row[3] || '') === assignment && Number(row[4]) === seat && String(row[5]) === '缺交') {
        sheets.homework.getRange(index + 2, 6).setValue('補交');
        return { ok: true, updated: 1 };
      }
    }
    return { ok: true, updated: 0 };
  } finally {
    lock.releaseLock();
  }
}

/**
 * 雲端定時備援（選用）：在 Apps Script「觸發條件」新增時間驅動觸發器，
 * 選擇本函式與每日早上時段（例如 8:00–9:00）。
 * 當天若還沒有任何大屏點名回報，LINE 提醒老師；已回報則不重複打擾。
 */
function sendRollcallReminder() {
  if (!pushAllowed_('reminder')) return;
  var today = lineBotToday_();
  var data = readRollcallRange_(today, today, '');
  if (data.attendance.length || data.homework.length) return; // 已有回報（大屏 8:08 已即時推播）→ 不打擾。
  // Google 觸發器只保證落在整點區間內的隨機分鐘；若醒來時還不到 8:20（回報可能尚未發生），
  // 排一個 20 分鐘後的一次性檢查再判斷，避免誤報又能盡早提醒。
  var now = new Date();
  if (now.getHours() === 8 && now.getMinutes() < 20) {
    ScriptApp.newTrigger('sendRollcallReminder').timeBased().at(new Date(now.getTime() + 20 * 60000)).create();
    return;
  }
  var users = lineBotProperty_('LINE_ALLOWED_USER_IDS')
    .split(',').map(function (value) { return value.trim(); }).filter(String);
  users.forEach(function (userId) {
    pushLineMessage_(userId, '⏰ 提醒：今天還沒有收到晨間大屏的點名回報。若教室電腦未開啟大屏頁，請開啟後完成點名並按「送出」。');
  });
}

function pullLineInbox_() {
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var lastRow = sheets.inbox.getLastRow();
  if (lastRow <= 1) return { ok: true, items: [] };
  var values = sheets.inbox.getRange(2, 1, lastRow - 1, LINE_BOT_CONFIG.INBOX_HEADERS.length).getValues();
  var items = [];
  for (var index = 0; index < values.length && items.length < LINE_BOT_CONFIG.MAX_PULL_ROWS; index += 1) {
    var row = values[index];
    if (String(row[7]) !== 'new') continue;
    var extra = {};
    try { extra = JSON.parse(String(row[9] || '{}')) || {}; } catch (error) { extra = {}; }
    items.push({
      id: String(row[0]),
      createdAt: row[1] instanceof Date ? row[1].toISOString() : String(row[1]),
      type: String(row[2]),
      text: String(row[3]).slice(0, LINE_BOT_CONFIG.MAX_TEXT_LENGTH),
      title: String(row[4]).slice(0, 120),
      dueDate: String(row[5]),
      axis: String(row[6]),
      tag: String(extra.tag || ''),
      medium: String(extra.medium || '')
    });
  }
  return { ok: true, items: items };
}

function ackLineInbox_(body) {
  var ids = Array.isArray(body.ids) ? body.ids.map(String) : [];
  var status = body.status === 'ignored' ? 'ignored' : 'imported';
  if (!ids.length) return { ok: true, updated: 0 };
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var lastRow = sheets.inbox.getLastRow();
  if (lastRow <= 1) return { ok: true, updated: 0 };
  var idRange = sheets.inbox.getRange(2, 1, lastRow - 1, 1).getValues();
  var wanted = {};
  ids.forEach(function (id) { wanted[id] = true; });
  var updated = 0;
  for (var index = 0; index < idRange.length; index += 1) {
    if (wanted[String(idRange[index][0])]) {
      sheets.inbox.getRange(index + 2, 8).setValue(status);
      updated += 1;
    }
  }
  return { ok: true, updated: updated };
}

function saveWorkspaceSnapshot_(body) {
  var snapshot = body.snapshot;
  if (!snapshot || typeof snapshot !== 'object') throw new Error('缺少快照內容');
  var serialized = JSON.stringify(snapshot);
  if (serialized.length > 100000) throw new Error('快照內容過大');
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  sheets.snapshot.getRange(2, 1, 1, 2).setValues([[new Date().toISOString(), serialized]]);
  return { ok: true };
}

function readWorkspaceSnapshot_() {
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  if (sheets.snapshot.getLastRow() < 2) return null;
  var row = sheets.snapshot.getRange(2, 1, 1, 2).getValues()[0];
  try {
    var snapshot = JSON.parse(String(row[1] || 'null'));
    if (snapshot && typeof snapshot === 'object') {
      snapshot.updatedAt = row[0] instanceof Date ? row[0].toISOString() : String(row[0]);
      return snapshot;
    }
  } catch (error) {}
  return null;
}

// ---------------------------------------------------------------------------
// LINE Webhook
// ---------------------------------------------------------------------------

function handleLineWebhook_(e, body) {
  var expectedHook = lineBotProperty_('LINE_WEBHOOK_TOKEN');
  var providedHook = String((e && e.parameter && e.parameter.hook) || '');
  if (!expectedHook || providedHook !== expectedHook) {
    return lineBotJson_({ ok: false, error: 'webhook 驗證失敗' });
  }
  var allowedUsers = lineBotProperty_('LINE_ALLOWED_USER_IDS')
    .split(',').map(function (value) { return value.trim(); }).filter(String);
  body.events.forEach(function (event) {
    try {
      handleLineEvent_(event, allowedUsers);
    } catch (error) {
      // 單一事件失敗不影響其他事件；LINE 需要 200 回應避免重送。
    }
  });
  return lineBotJson_({ ok: true });
}

function handleLineEvent_(event, allowedUsers) {
  if (!event || event.type !== 'message' || !event.message) return;
  var userId = String((event.source && event.source.userId) || '');
  if (allowedUsers.length && allowedUsers.indexOf(userId) === -1) return;
  if (event.message.type !== 'text') {
    handleLineMediaMessage_(event, userId);
    return;
  }
  var text = String(event.message.text || '').trim().slice(0, LINE_BOT_CONFIG.MAX_TEXT_LENGTH);
  if (!text) return;

  if (/^撤回$/.test(text)) {
    replyLineMessage_(event.replyToken, revokeLineInbox_(userId, ''));
    return;
  }
  var deleteMatch = text.match(/^刪除\s*(.+)$/);
  if (deleteMatch) {
    replyLineMessage_(event.replyToken, revokeLineInbox_(userId, deleteMatch[1].trim()));
    return;
  }

  if (/^(說明|幫助|help)$/i.test(text)) {
    replyLineMessage_(event.replyToken, lineBotHelpText_());
    return;
  }
  if (/^(我的\s?id|我的編號|my\s?id)$/i.test(text)) {
    replyLineMessage_(event.replyToken, userId
      ? '你的 LINE userId 是：\n' + userId + '\n\n請把它填入 Apps Script 的指令碼屬性 LINE_ALLOWED_USER_IDS，鎖定只回應你本人。'
      : '目前讀不到 userId，請改用一對一聊天視窗再試一次。');
    return;
  }

  if (/^(今日點名|點名|今日出缺)$/.test(text)) {
    replyLineMessage_(event.replyToken, buildRollcallTodayReply_());
    return;
  }
  if (/^(缺交統計|作業統計)$/.test(text)) {
    replyLineMessage_(event.replyToken, buildHomeworkStatsReply_());
    return;
  }
  if (/^(推播設定|推播|用量|額度)$/.test(text)) {
    replyLineMessage_(event.replyToken, buildPushSettingsReply_());
    return;
  }
  var toggleMatch = text.match(/^(開啟|關閉)\s*(.+)$/);
  if (toggleMatch) {
    replyLineMessage_(event.replyToken, togglePushSetting_(toggleMatch[1], toggleMatch[2]));
    return;
  }
  if (/^(代課包|請假|今天請假|明天請假|代課)$/.test(text) || /^(明天|今天)?請假$/.test(text)) {
    replyLineMessages_(event.replyToken, [
      buildSubstituteKitReply_(text),
      '↑ 長按上面那一則即可轉發給代課老師或學年主任。'
    ]);
    return;
  }
  var seatMatch = text.match(/^(\d{1,2})\s*號?$/);
  if (seatMatch && Number(seatMatch[1]) >= 1 && Number(seatMatch[1]) <= 99) {
    replyLineMessage_(event.replyToken, buildSeatLookupReply_(Number(seatMatch[1])));
    return;
  }
  var fileSearchMatch = text.match(/^(找檔案|找檔|檔案)\s*(.*)$/);
  if (fileSearchMatch) {
    replyLineMessage_(event.replyToken, buildFileSearchReply_(fileSearchMatch[2]));
    return;
  }
  if (/^(照片轉聯絡本|加入聯絡本|存進聯絡本)$/.test(text)) {
    var pending = lineBotProperty_(LAST_MEDIA_SUMMARY_KEY);
    replyLineMessage_(event.replyToken, pending
      ? writeContactBookFromLine_(pending)
      : '目前沒有可轉入的辨識結果。請先傳一張通知單照片，再傳「照片轉聯絡本」。');
    return;
  }

  var classified = classifyLineMessage_(text);
  if (classified.type === 'query') {
    replyLineMessage_(event.replyToken, buildSnapshotReply_());
    return;
  }
  if (classified.type === 'contactbook') {
    replyLineMessage_(event.replyToken, writeContactBookFromLine_(classified.content || ''));
    return;
  }
  if (classified.type === 'contact') {
    replyLineMessages_(event.replyToken, [
      buildContactBookReply_(classified.content || text),
      '↑ 長按上面那一則即可轉發到家長群。轉發前請先確認內容沒有學生姓名等個資。'
    ]);
    return;
  }
  replyLineMessage_(event.replyToken, saveAndConfirm_(classified, text, userId, ''));
}

/** 寫入信箱並組出確認訊息；medium 為 ''（文字）、'voice'、'photo'。 */
function saveAndConfirm_(classified, text, userId, medium) {
  var saved = appendLineInboxRow_(classified, text, userId, medium);
  var label = classified.type === 'task' ? '任務' : '記事';
  var mediumLabel = medium === 'voice' ? '🎤 語音聽寫｜' : medium === 'photo' ? '📷 照片辨識｜' : '';
  var lines = ['已收到，整理成「' + label + '」放進工作台的 LINE 收件匣：', '📌 ' + mediumLabel + (classified.title || text.slice(0, 60))];
  if (classified.dueDate) lines.push('📅 到期日：' + classified.dueDate);
  if (classified.axis) lines.push('🏷️ 工作主軸：' + classified.axis);
  if (classified.tag) lines.push('📂 分類：' + classified.tag);
  lines.push('（開啟教師工作台按「立即同步」，確認後才會正式建立。傳「撤回」可作廢這一筆。）');
  return lines.join('\n');
}

/** 「撤回」與「刪除 關鍵字」：把該使用者最新一筆符合的未處理項目作廢。 */
function revokeLineInbox_(userId, keyword) {
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var lastRow = sheets.inbox.getLastRow();
  if (lastRow <= 1) return '目前沒有可撤回的項目。';
  var values = sheets.inbox.getRange(2, 1, lastRow - 1, LINE_BOT_CONFIG.INBOX_HEADERS.length).getValues();
  for (var index = values.length - 1; index >= 0; index -= 1) {
    var row = values[index];
    if (String(row[7]) !== 'new') continue;
    if (userId && String(row[8]) && String(row[8]) !== userId) continue;
    var haystack = String(row[3]) + ' ' + String(row[4]);
    if (keyword && haystack.indexOf(keyword) === -1) continue;
    sheets.inbox.getRange(index + 2, 8).setValue('ignored');
    return '已作廢這一筆：\n「' + (String(row[4]) || String(row[3]).slice(0, 40)) + '」\n它不會再出現在工作台收件匣。';
  }
  return keyword ? '找不到含「' + keyword + '」的未處理項目。' : '目前沒有可撤回的項目。';
}

// ---------------------------------------------------------------------------
// 語音與照片（需要 Gemini 金鑰）
// ---------------------------------------------------------------------------

var LAST_MEDIA_SUMMARY_KEY = 'LAST_MEDIA_SUMMARY';

function handleLineMediaMessage_(event, userId) {
  var messageType = event.message.type;
  if (['audio', 'image', 'file', 'video'].indexOf(messageType) === -1) {
    replyLineMessage_(event.replyToken, '目前我看得懂文字、語音、照片、影片與檔案；其他訊息類型還在學習中。');
    return;
  }
  var content = fetchLineContent_(String(event.message.id));
  if (!content) {
    replyLineMessage_(event.replyToken, '這則訊息的內容讀取失敗，請再傳一次。');
    return;
  }
  // 先備份再辨識：LINE 的檔案有保存期限，先落地到老師自己的雲端硬碟最保險。
  var backup = backupLineContentToDrive_(String(event.message.id), messageType, String(event.message.fileName || ''), content);

  // 影片與一般檔案不做 AI 辨識，直接記錄檔名並附上備份連結。
  if (messageType === 'file' || messageType === 'video') {
    var fileLabel = String(event.message.fileName || (messageType === 'video' ? '影片' : '檔案'));
    var saved = saveAndConfirm_({ type: 'note', title: fileLabel, tag: '檔案' }, fileLabel, userId, '');
    replyLineMessage_(event.replyToken, saved + driveBackupNote_(backup));
    return;
  }

  var geminiKey = lineBotProperty_('GEMINI_API_KEY');
  if (!geminiKey) {
    replyLineMessage_(event.replyToken,
      '語音與照片辨識需要 Gemini 金鑰。請在 Apps Script「指令碼屬性」設定 GEMINI_API_KEY 後再試。' + driveBackupNote_(backup));
    return;
  }
  if (content.bytes.length > 15 * 1024 * 1024) {
    replyLineMessage_(event.replyToken, '檔案超過 15 MB，暫時無法辨識，請縮短語音或改傳截圖。' + driveBackupNote_(backup));
    return;
  }
  var classified = classifyMediaByGemini_(content, messageType, geminiKey);
  if (!classified) {
    replyLineMessage_(event.replyToken, messageType === 'audio' ? '這段語音我沒有聽清楚，請再試一次或改用文字。' : '這張照片我看不出重點，請再拍清楚一點或改用文字。');
    return;
  }
  if (classified.type === 'query') {
    replyLineMessage_(event.replyToken, buildSnapshotReply_());
    return;
  }
  if (classified.type === 'contactbook') {
    replyLineMessage_(event.replyToken, writeContactBookFromLine_(classified.content || classified.transcript || ''));
    return;
  }
  if (classified.type === 'contact') {
    replyLineMessages_(event.replyToken, [
      buildContactBookReply_(classified.content || classified.transcript || ''),
      '↑ 長按上面那一則即可轉發到家長群。轉發前請先確認內容沒有學生姓名等個資。'
    ]);
    return;
  }
  var sourceText = String(classified.transcript || classified.title || '').slice(0, LINE_BOT_CONFIG.MAX_TEXT_LENGTH);
  if (!sourceText) {
    replyLineMessage_(event.replyToken, '辨識結果是空的，請再試一次。' + driveBackupNote_(backup));
    return;
  }
  // 記住這次的辨識結果，老師接著傳「照片轉聯絡本」就能一鍵寫進今天的黑板。
  PropertiesService.getScriptProperties().setProperty(LAST_MEDIA_SUMMARY_KEY, sourceText.slice(0, 1000));
  // 用 AI 讀出的標題把雲端檔案改成看得懂的名字，並歸到正確的分類資料夾。
  backup = refineDriveBackup_(backup, classified.title || sourceText.slice(0, 30), classified.tag || '');
  var confirmText = saveAndConfirm_(classified, sourceText, userId, messageType === 'audio' ? 'voice' : 'photo');
  if (messageType === 'image') confirmText += '\n（要把重點寫進今天的聯絡本嗎？傳「照片轉聯絡本」即可。）';
  replyLineMessage_(event.replyToken, confirmText + driveBackupNote_(backup));
}

/** 以 LINE Content API 取回語音／照片位元組。 */
function fetchLineContent_(messageId) {
  var accessToken = lineBotProperty_('LINE_CHANNEL_ACCESS_TOKEN');
  if (!accessToken || !messageId) return null;
  try {
    var response = UrlFetchApp.fetch('https://api-data.line.me/v2/bot/message/' + encodeURIComponent(messageId) + '/content', {
      method: 'get',
      muteHttpExceptions: true,
      headers: { Authorization: 'Bearer ' + accessToken }
    });
    if (response.getResponseCode() !== 200) return null;
    var blob = response.getBlob();
    return { bytes: blob.getBytes(), contentType: String(blob.getContentType() || '') };
  } catch (error) {
    return null;
  }
}

function classifyMediaByGemini_(content, messageType, apiKey) {
  var model = lineBotProperty_('GEMINI_MODEL') || LINE_BOT_CONFIG.DEFAULT_GEMINI_MODEL;
  var mimeType = messageType === 'audio'
    ? 'audio/mp4'
    : (content.contentType.indexOf('image/') === 0 ? content.contentType : 'image/jpeg');
  var instruction = messageType === 'audio'
    ? '先把這段臺灣國小老師的語音完整聽寫成繁體中文（放在 transcript），再依聽寫內容分類。'
    : '先把這張照片（可能是通知單、公文、黑板或手寫聯絡簿）的文字與重點整理成繁體中文條列（放在 transcript），再依內容分類。';
  var prompt = [
    '你是臺灣國小教師工作台的訊息分類器。' + instruction,
    '只回傳 JSON，不要其他文字。格式：',
    '{"transcript":"聽寫或辨識出的完整內容","type":"task|note|query|contact|contactbook","title":"20字內標題","dueDate":"yyyy-MM-dd或空字串","axis":"教學|行政|學年主任|導師|空字串","tag":"家長聯繫|學生概況|作業缺交|備課靈感|生活雜事|空字串","content":"若type=contact或contactbook，放項目內容"}',
    '分類原則：要辦的事＝task；純紀錄＝note；詢問進度或今日任務＝query；要產生給家長群的公告＝contact；提到「聯絡本」要記錄當天聯絡本內容＝contactbook。',
    '今天是 ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd') + '。'
  ].join('\n');
  try {
    var response = UrlFetchApp.fetch(LINE_BOT_CONFIG.GEMINI_ENDPOINT + model + ':generateContent?key=' + encodeURIComponent(apiKey), {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      payload: JSON.stringify({
        contents: [{ parts: [
          { text: prompt },
          { inline_data: { mime_type: mimeType, data: Utilities.base64Encode(content.bytes) } }
        ] }],
        generationConfig: { temperature: 0.1 }
      })
    });
    if (response.getResponseCode() !== 200) return null;
    var data = JSON.parse(response.getContentText());
    var answer = String(((data.candidates || [])[0] || {}).content && data.candidates[0].content.parts[0].text || '');
    var jsonMatch = answer.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return null;
    var parsed = JSON.parse(jsonMatch[0]);
    if (['task', 'note', 'query', 'contact', 'contactbook'].indexOf(parsed.type) === -1) return null;
    return {
      type: parsed.type,
      transcript: String(parsed.transcript || '').slice(0, LINE_BOT_CONFIG.MAX_TEXT_LENGTH),
      title: String(parsed.title || '').slice(0, 60),
      dueDate: /^\d{4}-\d{2}-\d{2}$/.test(String(parsed.dueDate || '')) ? String(parsed.dueDate) : '',
      axis: LINE_BOT_CONFIG.WORK_AXES.indexOf(String(parsed.axis || '')) === -1 ? '' : String(parsed.axis),
      tag: LINE_BOT_CONFIG.NOTE_TAGS.indexOf(String(parsed.tag || '')) === -1 ? '' : String(parsed.tag),
      content: String(parsed.content || '')
    };
  } catch (error) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// LINE 檔案自動備份到老師自己的 Google Drive
// LINE 對話裡的檔案有保存期限，這裡在收到當下就抓下來存進老師自己的雲端硬碟。
// 指令碼屬性：DRIVE_BACKUP_TYPES（預設 image,file）、DRIVE_BACKUP_FOLDER_ID、DRIVE_BACKUP_MAX_MB（預設 20）
// ---------------------------------------------------------------------------

var DRIVE_FOLDER_PROP = 'DRIVE_BACKUP_FOLDER_ID';
var DRIVE_TYPES_PROP = 'DRIVE_BACKUP_TYPES';
var DRIVE_MAX_MB_PROP = 'DRIVE_BACKUP_MAX_MB';
var DRIVE_DEFAULT_TYPES = ['image', 'file'];   // 影片與語音預設不備份，避免吃掉雲端容量

function driveBackupTypes_() {
  var raw = lineBotProperty_(DRIVE_TYPES_PROP);
  if (!raw) return DRIVE_DEFAULT_TYPES;
  if (/^(off|none|關閉|停用)$/i.test(raw)) return [];
  return raw.split(/[,，、]/).map(function (value) { return value.trim().toLowerCase(); }).filter(String);
}

function driveBackupFolder_() {
  var props = PropertiesService.getScriptProperties();
  var savedId = String(props.getProperty(DRIVE_FOLDER_PROP) || '').trim();
  if (savedId) {
    try { return DriveApp.getFolderById(savedId); } catch (error) {}   // 資料夾被刪掉就重建
  }
  var name = 'LINE小幫手備份';
  var existing = DriveApp.getFoldersByName(name);
  var folder = existing.hasNext() ? existing.next() : DriveApp.createFolder(name);
  props.setProperty(DRIVE_FOLDER_PROP, folder.getId());
  return folder;
}

function driveMonthFolder_(root, date) {
  var monthName = String(date).slice(0, 7);
  var found = root.getFoldersByName(monthName);
  return found.hasNext() ? found.next() : root.createFolder(monthName);
}

var DRIVE_TYPE_LABELS = { image: '照片', video: '影片', audio: '語音', file: '檔案' };

/** 依關鍵字判斷這份資料屬於哪一類，決定要放進哪個資料夾。 */
var DRIVE_CATEGORY_RULES = [
  { name: '通知單與回條', pattern: /通知單|回條|同意書|報名表|調查表|意願|繳費|收費/ },
  { name: '學生與親師', pattern: /學生|家長|親師|輔導|請假|健康中心|保健室|受傷|跌倒|缺交|出缺席/ },
  { name: '會議與晨會', pattern: /會議|晨會|朝會|報告事項|決議|議程/ },
  { name: '公文與行政', pattern: /公文|來函|行政|處室|校務|人事|研習|考核|評鑑|計畫|方案|實施要點/ },
  { name: '課程與教材', pattern: /教材|學習單|課程|進度|備課|試卷|命題|題目|教案|講義|評量/ },
  { name: '活動與競賽', pattern: /活動|校慶|運動會|畢旅|校外教學|競賽|比賽|表演|展覽|演練/ }
];

/** AI 標籤對應的預設分類；關鍵字沒命中時使用。 */
var DRIVE_TAG_CATEGORY = {
  '家長聯繫': '學生與親師',
  '學生概況': '學生與親師',
  '作業缺交': '學生與親師',
  '備課靈感': '課程與教材',
  '生活雜事': '其他'
};

function driveCategoryFor_(text, tag) {
  var haystack = String(text || '') + ' ' + String(tag || '');
  for (var index = 0; index < DRIVE_CATEGORY_RULES.length; index += 1) {
    if (DRIVE_CATEGORY_RULES[index].pattern.test(haystack)) return DRIVE_CATEGORY_RULES[index].name;
  }
  return DRIVE_TAG_CATEGORY[String(tag)] || '其他';
}

function driveCategoryFolder_(monthFolder, category) {
  var found = monthFolder.getFoldersByName(category);
  return found.hasNext() ? found.next() : monthFolder.createFolder(category);
}

function driveSafeName_(value) {
  return String(value || '').replace(/[\\\/:*?"<>|\r\n]/g, '_').replace(/\s+/g, ' ').trim().slice(0, 60);
}

function driveExtensionFor_(messageType, originalName, contentType) {
  var fromName = String(originalName || '').match(/\.[A-Za-z0-9]{1,6}$/);
  if (fromName) return fromName[0].toLowerCase();
  if (/jpeg|jpg/.test(String(contentType))) return '.jpg';
  if (/png/.test(String(contentType))) return '.png';
  if (/pdf/.test(String(contentType))) return '.pdf';
  if (messageType === 'image') return '.jpg';
  if (messageType === 'video') return '.mp4';
  if (messageType === 'audio') return '.m4a';
  return '';
}

/**
 * 把 LINE 訊息的檔案存進 Drive；回傳 { fileId, name, url, category } 或 null。
 * 收到當下就先落地（LINE 檔案有期限），檔名先用原檔名或類型；
 * 之後 AI 辨識完成再呼叫 refineDriveBackup_ 改成看得懂的名稱並歸到正確分類。
 * 任何失敗都只回 null，不影響原本的訊息處理。
 */
function backupLineContentToDrive_(messageId, messageType, originalName, content) {
  if (driveBackupTypes_().indexOf(String(messageType)) === -1) return null;
  var maxMb = Number(lineBotProperty_(DRIVE_MAX_MB_PROP) || 20);
  try {
    var payload = content || fetchLineContent_(messageId);
    if (!payload || !payload.bytes) return null;
    if (payload.bytes.length > maxMb * 1024 * 1024) return { oversize: true, limitMb: maxMb };
    var date = lineBotToday_();
    var label = DRIVE_TYPE_LABELS[messageType] || '檔案';
    var extension = driveExtensionFor_(messageType, originalName, payload.contentType);
    var baseName = driveSafeName_(String(originalName || '').replace(/\.[A-Za-z0-9]{1,6}$/, '')) || label;
    var category = driveCategoryFor_(originalName, '');
    var monthFolder = driveMonthFolder_(driveBackupFolder_(), date);
    var folder = driveCategoryFolder_(monthFolder, category);
    var fileName = date.slice(5).replace('-', '') + '_' + baseName + extension;
    var blob = Utilities.newBlob(payload.bytes, payload.contentType || 'application/octet-stream', fileName);
    var file = folder.createFile(blob);
    var backup = { fileId: file.getId(), name: file.getName(), url: file.getUrl(), category: category, type: label, date: date };
    recordDriveBackup_(backup, baseName);
    return backup;
  } catch (error) {
    return null;
  }
}

/**
 * AI 辨識完成後，用辨識出的標題重新命名並歸類，讓檔案在雲端硬碟一眼看得懂。
 * 例：0828_通知單與回條/0828_第二次返校日晨會報告事項.jpg
 */
function refineDriveBackup_(backup, title, tag) {
  if (!backup || !backup.fileId || !title) return backup;
  try {
    var cleanTitle = driveSafeName_(title);
    if (!cleanTitle) return backup;
    var file = DriveApp.getFileById(backup.fileId);
    var extension = String(backup.name).match(/\.[A-Za-z0-9]{1,6}$/);
    var newName = String(backup.date).slice(5).replace('-', '') + '_' + cleanTitle + (extension ? extension[0] : '');
    file.setName(newName);
    var category = driveCategoryFor_(title, tag);
    if (category !== backup.category) {
      var monthFolder = driveMonthFolder_(driveBackupFolder_(), backup.date);
      file.moveTo(driveCategoryFolder_(monthFolder, category));
      backup.category = category;
    }
    backup.name = newName;
    updateDriveBackupRecord_(backup, cleanTitle);
    return backup;
  } catch (error) {
    return backup;
  }
}

/** 在「檔案備份」分頁留一筆索引，之後可用「找檔案 關鍵字」搜尋。 */
function recordDriveBackup_(backup, title) {
  try {
    var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
    sheets.files.appendRow([backup.date, backup.type, backup.category, title || '', backup.name, backup.url]);
  } catch (error) {}
}

function updateDriveBackupRecord_(backup, title) {
  try {
    var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
    var lastRow = sheets.files.getLastRow();
    if (lastRow <= 1) return;
    var values = sheets.files.getRange(2, 1, lastRow - 1, LINE_BOT_CONFIG.FILES_HEADERS.length).getValues();
    for (var index = values.length - 1; index >= 0; index -= 1) {
      if (String(values[index][5]) === backup.url) {
        sheets.files.getRange(index + 2, 3, 1, 3).setValues([[backup.category, title, backup.name]]);
        return;
      }
    }
  } catch (error) {}
}

/** 「找檔案 關鍵字」：從備份索引找出符合的檔案並附上連結。 */
function buildFileSearchReply_(keyword) {
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var lastRow = sheets.files.getLastRow();
  if (lastRow <= 1) return '目前還沒有備份任何檔案。傳照片或檔案給我，就會自動存進你的雲端硬碟。';
  var values = sheets.files.getRange(2, 1, lastRow - 1, LINE_BOT_CONFIG.FILES_HEADERS.length).getValues();
  var query = String(keyword || '').trim();
  var matched = values.filter(function (row) {
    if (!query) return true;
    return (String(row[2]) + String(row[3]) + String(row[4])).indexOf(query) !== -1;
  }).slice(-8).reverse();
  if (!matched.length) return '找不到含「' + query + '」的備份檔案。傳「找檔案」可看最近備份的幾筆。';
  var lines = [query ? '📁 含「' + query + '」的備份（最近 ' + matched.length + ' 筆）' : '📁 最近備份的檔案'];
  matched.forEach(function (row) {
    var date = row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : String(row[0]);
    lines.push('');
    lines.push('・' + date.slice(5).replace('-', '/') + '｜' + row[2] + '｜' + (row[3] || row[4]));
    lines.push(String(row[5]));
  });
  return lines.join('\n');
}

/** 組出要附在回覆後面的備份說明；沒有備份就回空字串。 */
function driveBackupNote_(backup) {
  if (!backup) return '';
  if (backup.oversize) return '\n（檔案超過 ' + backup.limitMb + ' MB，未自動備份到雲端硬碟。）';
  return '\n☁️ 已備份到雲端硬碟｜' + backup.category + '\n' + backup.url;
}

// ---------------------------------------------------------------------------
// 代課包：臨時請假時，一則訊息交接完畢
// ---------------------------------------------------------------------------

/** 「請假」「代課包」→ 整理成可直接轉發給代課老師的交接資訊。 */
function buildSubstituteKitReply_(text) {
  var today = lineBotToday_();
  var forTomorrow = /明天|明日/.test(String(text || ''));
  var target = forTomorrow ? shiftLineBotDate_(today, 1) : today;
  var snapshot = readWorkspaceSnapshot_();
  var lines = ['🧳 代課交接包｜' + target.replace(/-/g, '/') + (forTomorrow ? '（明天）' : '（今天）')];

  var courses = snapshot && Array.isArray(forTomorrow ? snapshot.tomorrowCourses : snapshot.todayCourses)
    ? (forTomorrow ? snapshot.tomorrowCourses : snapshot.todayCourses) : [];
  lines.push('');
  lines.push('📚 課程進度');
  if (courses.length) {
    courses.slice(0, 10).forEach(function (course) {
      lines.push('・' + course.subject + '：' + course.content);
    });
  } else {
    lines.push('・工作台目前沒有這天的課程進度紀錄。');
  }

  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var contactRow = findContactBookRow_(sheets.contactbook, target);
  lines.push('');
  lines.push('📝 聯絡本');
  if (contactRow !== -1) {
    var contactText = String(sheets.contactbook.getRange(contactRow, 3).getValue() || '').trim();
    lines.push(contactText || '・（該日聯絡本是空的）');
  } else {
    lines.push('・還沒寫；可傳「聯絡本：……」直接補上。');
  }

  var missing = readRollcallRange_(shiftLineBotDate_(today, -6), today, '').homework
    .filter(function (row) { return row.status === '缺交'; });
  var bySeat = {};
  missing.forEach(function (row) { bySeat[row.seat] = (bySeat[row.seat] || 0) + 1; });
  var seats = Object.keys(bySeat).sort(function (a, b) { return bySeat[b] - bySeat[a]; }).slice(0, 8);
  lines.push('');
  lines.push('📌 近 7 天需要多留意的座號（缺交次數）');
  lines.push(seats.length
    ? seats.map(function (seat) { return seat + '號 ' + bySeat[seat] + ' 次'; }).join('、')
    : '・近期沒有缺交紀錄 🎉');

  var notes = lineBotProperty_('CLASS_NOTES');
  if (notes) {
    lines.push('');
    lines.push('⚠️ 班級注意事項');
    lines.push(notes);
  }

  lines.push('');
  lines.push('（可長按整則轉發給代課老師。班級注意事項請在 Apps Script 指令碼屬性 CLASS_NOTES 自訂。）');
  return lines.join('\n');
}

function shiftLineBotDate_(dateText, days) {
  var parts = String(dateText).split('-');
  var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  date.setDate(date.getDate() + days);
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

// ---------------------------------------------------------------------------
// 座號快查：親師溝通前 30 秒掌握狀況
// ---------------------------------------------------------------------------

function buildSeatLookupReply_(seat) {
  var today = lineBotToday_();
  var from = shiftLineBotDate_(today, -29);
  var data = readRollcallRange_(from, today, '');
  var attendance = data.attendance.filter(function (row) { return row.seat === seat; });
  var homework = data.homework.filter(function (row) { return row.seat === seat; });
  var lines = ['🔍 ' + seat + '號｜近 30 天紀錄（' + from.slice(5).replace('-', '/') + '～' + today.slice(5).replace('-', '/') + '）'];

  lines.push('');
  lines.push('👥 出缺');
  if (attendance.length) {
    var statusCount = {};
    attendance.forEach(function (row) { statusCount[row.status] = (statusCount[row.status] || 0) + 1; });
    lines.push(Object.keys(statusCount).map(function (status) { return status + ' ' + statusCount[status] + ' 次'; }).join('、'));
    lines.push('最近：' + attendance.slice(-5).map(function (row) { return row.date.slice(5).replace('-', '/') + ' ' + row.status; }).join('、'));
  } else {
    lines.push('・全勤，沒有缺席紀錄 🎉');
  }

  var missing = homework.filter(function (row) { return row.status === '缺交'; });
  var resubmitted = homework.filter(function (row) { return row.status === '補交'; });
  lines.push('');
  lines.push('📚 作業');
  if (missing.length || resubmitted.length) {
    var bySubject = {};
    missing.forEach(function (row) { bySubject[row.subject] = (bySubject[row.subject] || 0) + 1; });
    lines.push('缺交 ' + missing.length + ' 次｜補交 ' + resubmitted.length + ' 次');
    if (Object.keys(bySubject).length) {
      lines.push('分科：' + Object.keys(bySubject).map(function (subject) { return subject + ' ' + bySubject[subject] + ' 次'; }).join('、'));
    }
    if (missing.length) {
      lines.push('最近缺交：' + missing.slice(-5).map(function (row) {
        return row.date.slice(5).replace('-', '/') + ' ' + row.subject + (row.assignment ? '／' + row.assignment : '');
      }).join('、'));
    }
  } else {
    lines.push('・沒有缺交紀錄 ✅');
  }

  lines.push('');
  lines.push('（僅供老師參考，請勿轉發；系統只記錄座號，不含姓名。）');
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// 下午推播：放學小結／早期缺交預警／到期前一天提醒
// 三項合併成一則訊息，開幾項都只用 1 則額度。
// ---------------------------------------------------------------------------

/** 找出近期同一科連續缺交達門檻的座號（預設連續 3 個有登記的日子）。 */
function findConsecutiveMissing_(threshold) {
  var today = lineBotToday_();
  var data = readRollcallRange_(shiftLineBotDate_(today, -13), today, '');
  var bySubjectDate = {};
  data.homework.forEach(function (row) {
    var key = row.subject;
    if (!bySubjectDate[key]) bySubjectDate[key] = {};
    if (!bySubjectDate[key][row.date]) bySubjectDate[key][row.date] = { missing: {}, seen: true };
    if (row.status === '缺交') bySubjectDate[key][row.date].missing[row.seat] = true;
  });
  var alerts = [];
  Object.keys(bySubjectDate).forEach(function (subject) {
    var dates = Object.keys(bySubjectDate[subject]).sort();
    var recent = dates.slice(-threshold);
    if (recent.length < threshold) return;
    var seats = Object.keys(bySubjectDate[subject][recent[0]].missing);
    seats.forEach(function (seat) {
      var everyDay = recent.every(function (date) { return bySubjectDate[subject][date].missing[seat]; });
      if (everyDay) alerts.push({ subject: subject, seat: Number(seat), days: threshold });
    });
  });
  return alerts;
}

/**
 * 下午的一則整合推播。三個開關各自控制一個段落；全關就不發。
 * 由 setupTriggers 建立的每日觸發器呼叫。
 */
function sendAfternoonBriefing() {
  var users = lineBotProperty_('LINE_ALLOWED_USER_IDS')
    .split(',').map(function (value) { return value.trim(); }).filter(String);
  if (!users.length) return;
  var today = lineBotToday_();
  var sections = [];

  if (pushAllowed_('dayEnd')) {
    var rollcall = readRollcallRange_(today, today, '');
    var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
    var tomorrow = shiftLineBotDate_(today, 1);
    var tomorrowRow = findContactBookRow_(sheets.contactbook, tomorrow);
    var summary = ['🌇 放學小結'];
    summary.push(rollcall.attendance.length || rollcall.homework.length
      ? '・今天的點名與作業已回報完成。'
      : '・今天還沒收到大屏回報，記得補登。');
    summary.push(tomorrowRow !== -1
      ? '・明天的聯絡本已經寫好了 ✅'
      : '・明天的聯絡本還沒寫；可直接傳「聯絡本：……」補上。');
    sections.push(summary.join('\n'));
  }

  if (pushAllowed_('missingAlert')) {
    var threshold = Math.max(2, Number(lineBotProperty_('MISSING_ALERT_DAYS') || 3));
    var alerts = findConsecutiveMissing_(threshold);
    if (alerts.length) {
      var alertLines = ['⚠️ 早期缺交預警（同一科連續 ' + threshold + ' 次缺交）'];
      alerts.slice(0, 10).forEach(function (item) {
        alertLines.push('・' + item.seat + '號｜' + item.subject);
      });
      alertLines.push('建議先個別關心，不必等到週五統計。');
      sections.push(alertLines.join('\n'));
    }
  }

  if (pushAllowed_('dueTomorrow')) {
    var snapshot = readWorkspaceSnapshot_();
    var tomorrowTasks = snapshot && Array.isArray(snapshot.tomorrowTasks) ? snapshot.tomorrowTasks : [];
    if (tomorrowTasks.length) {
      var taskLines = ['⏳ 明天到期（' + tomorrowTasks.length + ' 件）'];
      tomorrowTasks.slice(0, 8).forEach(function (task) {
        taskLines.push('・' + task.name + (task.dueTime ? '｜' + task.dueTime : ''));
      });
      sections.push(taskLines.join('\n'));
    }
  }

  if (!sections.length) return;
  users.forEach(function (userId) { pushLineMessage_(userId, sections.join('\n\n')); });
}

function lineBotHelpText_() {
  return [
    '我是教師工作台的 LINE 小幫手，可以這樣用：',
    '・直接描述一件事（例：明天要收回條）→ 整理成任務',
    '・「記：……」→ 存成記事（會自動加上家長聯繫、學生概況等分類）',
    '・傳語音 → 自動聽寫再整理（需 Gemini 金鑰）',
    '・拍通知單、黑板 → 自動辨識重點（需 Gemini 金鑰）',
    '・「今天上到哪」「今日任務」→ 回報工作台快照',
    '・「聯絡本：數習P.20、帶直笛」→ 直接寫入今天的聯絡本（大屏黑板自動顯示）',
    '・「今日點名」→ 回報大屏的出缺與作業登記',
    '・「缺交統計」→ 近 30 天各科缺交天數排行',
    '・「9號」→ 查該座號近 30 天的出缺與缺交（親師溝通前快速掌握）',
    '・「請假」「明天請假」→ 產生代課交接包，可直接轉發給代課老師',
    '・「聯絡簿：項目1、項目2」→ 產生家長群公告',
    '・「照片轉聯絡本」→ 把剛剛辨識的通知單重點寫進今天的聯絡本',
    '・傳照片或檔案 → 自動備份到雲端硬碟，AI 會依內容命名並分類歸檔',
    '・「找檔案 通知單」→ 從備份索引找出檔案並附連結（不加關鍵字就看最近幾筆）',
    '・「推播設定」→ 查看本月用量與各項推播開關；「開啟 放學小結」「關閉 作業推播」可切換',
    '・「撤回」→ 作廢剛剛那一筆；「刪除 關鍵字」→ 作廢含關鍵字的最新一筆',
    '・「我的ID」→ 查詢自己的 LINE userId（安裝設定用）',
    '訊息會先進工作台的 LINE 收件匣，由你確認後才正式建立。',
    '（以上你問我答的功能都不用 LINE 額度；只有主動推播才會計算。）'
  ].join('\n');
}

function appendLineInboxRow_(classified, text, userId, medium) {
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var id = 'L-' + new Date().getTime() + '-' + Math.floor(Math.random() * 1000);
  var extra = {};
  if (classified.tag) extra.tag = classified.tag;
  if (medium) extra.medium = medium;
  sheets.inbox.appendRow([
    id,
    new Date(),
    classified.type === 'task' ? 'task' : 'note',
    text,
    String(classified.title || '').slice(0, 120),
    String(classified.dueDate || ''),
    LINE_BOT_CONFIG.WORK_AXES.indexOf(classified.axis) === -1 ? '' : classified.axis,
    'new',
    userId,
    Object.keys(extra).length ? JSON.stringify(extra) : ''
  ]);
  trimLineInbox_(sheets.inbox);
  return { id: id };
}

/** 收件匣過大時，從最舊的已處理列開始清除，避免試算表無限成長。 */
function trimLineInbox_(inbox) {
  var lastRow = inbox.getLastRow();
  var excess = lastRow - 1 - LINE_BOT_CONFIG.MAX_INBOX_ROWS;
  if (excess <= 0) return;
  var statuses = inbox.getRange(2, 8, lastRow - 1, 1).getValues();
  for (var index = 0; index < statuses.length && excess > 0; index += 1) {
    if (String(statuses[index][0]) !== 'new') {
      inbox.deleteRow(index + 2 - (lastRow - 1 - statuses.length));
      excess -= 1;
      lastRow -= 1;
    }
  }
}

// ---------------------------------------------------------------------------
// 訊息分類：規則優先，Gemini 選用
// ---------------------------------------------------------------------------

function classifyLineMessage_(text) {
  var ruled = classifyByRules_(text);
  if (ruled) return ruled;
  var geminiKey = lineBotProperty_('GEMINI_API_KEY');
  if (geminiKey) {
    var byGemini = classifyByGemini_(text, geminiKey);
    if (byGemini) return byGemini;
  }
  // 沒有 AI 時的保守預設：整理成任務草稿，反正還要經教師確認。
  return { type: 'task', title: text.slice(0, 60), dueDate: '', axis: '' };
}

function classifyByRules_(text) {
  if (/^(記|記事|筆記|備忘)[:：]/.test(text)) {
    return { type: 'note', title: text.replace(/^(記|記事|筆記|備忘)[:：]\s*/, '').slice(0, 60), dueDate: '', axis: '' };
  }
  if (/^(任務|待辦|代辦)[:：]/.test(text)) {
    return { type: 'task', title: text.replace(/^(任務|待辦|代辦)[:：]\s*/, '').slice(0, 60), dueDate: extractRoughDate_(text), axis: '' };
  }
  if (/^聯絡本[:：]?/.test(text)) {
    return { type: 'contactbook', content: text.replace(/^聯絡本[:：]?\s*/, '') };
  }
  if (/^聯絡簿[:：]?/.test(text)) {
    return { type: 'contact', content: text.replace(/^聯絡簿[:：]?\s*/, '') };
  }
  if (/(上到哪|今日任務|今天任務|今日進度|今天進度|今日簡報)/.test(text) || (/[?？]$/.test(text) && /(進度|任務)/.test(text))) {
    return { type: 'query' };
  }
  return null;
}

/** 簡單的中文相對日期解析，僅供規則模式；Gemini 模式會給更準的日期。 */
function extractRoughDate_(text) {
  var today = new Date();
  function formatDate(dateValue) {
    return Utilities.formatDate(dateValue, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }
  if (/今天/.test(text)) return formatDate(today);
  if (/明天/.test(text)) return formatDate(new Date(today.getTime() + 24 * 3600 * 1000));
  if (/後天/.test(text)) return formatDate(new Date(today.getTime() + 48 * 3600 * 1000));
  var match = text.match(/(\d{1,2})[\/月](\d{1,2})/);
  if (match) {
    var candidate = new Date(today.getFullYear(), Number(match[1]) - 1, Number(match[2]));
    if (candidate.getTime() < today.getTime() - 24 * 3600 * 1000) candidate.setFullYear(candidate.getFullYear() + 1);
    return formatDate(candidate);
  }
  return '';
}

function classifyByGemini_(text, apiKey) {
  var model = lineBotProperty_('GEMINI_MODEL') || LINE_BOT_CONFIG.DEFAULT_GEMINI_MODEL;
  var prompt = [
    '你是臺灣國小教師工作台的訊息分類器。把老師傳來的 LINE 訊息分類，只回傳 JSON，不要其他文字。',
    'JSON 格式：{"type":"task|note|query|contact|contactbook","title":"20字內標題","dueDate":"yyyy-MM-dd或空字串","axis":"教學|行政|學年主任|導師|空字串","tag":"家長聯繫|學生概況|作業缺交|備課靈感|生活雜事|空字串","content":"若type=contact或contactbook，放項目內容"}',
    '分類原則：要辦的事＝task；純紀錄（學生狀況、家長聯繫、心得）＝note；詢問進度或今日任務＝query；要產生給家長群的公告＝contact；提到「聯絡本」要記錄當天聯絡本內容＝contactbook。tag 只在 note 類型且明確符合時才給。',
    '今天是 ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd') + '（供相對日期換算）。',
    '老師的訊息：' + text
  ].join('\n');
  try {
    var response = UrlFetchApp.fetch(LINE_BOT_CONFIG.GEMINI_ENDPOINT + model + ':generateContent?key=' + encodeURIComponent(apiKey), {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      payload: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0.1 } })
    });
    if (response.getResponseCode() !== 200) return null;
    var data = JSON.parse(response.getContentText());
    var answer = String(((data.candidates || [])[0] || {}).content && data.candidates[0].content.parts[0].text || '');
    var jsonMatch = answer.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return null;
    var parsed = JSON.parse(jsonMatch[0]);
    if (['task', 'note', 'query', 'contact', 'contactbook'].indexOf(parsed.type) === -1) return null;
    return {
      type: parsed.type,
      title: String(parsed.title || '').slice(0, 60),
      dueDate: /^\d{4}-\d{2}-\d{2}$/.test(String(parsed.dueDate || '')) ? String(parsed.dueDate) : '',
      axis: LINE_BOT_CONFIG.WORK_AXES.indexOf(String(parsed.axis || '')) === -1 ? '' : String(parsed.axis),
      tag: LINE_BOT_CONFIG.NOTE_TAGS.indexOf(String(parsed.tag || '')) === -1 ? '' : String(parsed.tag),
      content: String(parsed.content || '')
    };
  } catch (error) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 查詢與聯絡簿
// ---------------------------------------------------------------------------

function buildSnapshotReply_() {
  var snapshot = readWorkspaceSnapshot_();
  if (!snapshot) {
    return '工作台還沒有推送快照。請先開啟教師工作台，在「系統設定 → LINE 小幫手」按「立即同步」。';
  }
  var lines = ['📋 工作台快照（' + formatSnapshotTime_(snapshot.updatedAt) + ' 同步）'];
  var courses = Array.isArray(snapshot.todayCourses) ? snapshot.todayCourses : [];
  if (courses.length) {
    lines.push('📚 今日課程進度：');
    courses.slice(0, 8).forEach(function (course) {
      lines.push('・' + course.subject + '：' + course.content);
    });
  } else {
    lines.push('📚 今日沒有排定的課程進度。');
  }
  var tasks = Array.isArray(snapshot.todayTasks) ? snapshot.todayTasks : [];
  if (tasks.length) {
    lines.push('✅ 今日任務（' + tasks.length + ' 件）：');
    tasks.slice(0, 8).forEach(function (task) {
      lines.push('・' + task.name + (task.dueTime ? '｜' + task.dueTime : ''));
    });
  } else {
    lines.push('✅ 今天沒有到期任務。');
  }
  var notes = Array.isArray(snapshot.todayNotes) ? snapshot.todayNotes : [];
  if (notes.length) {
    lines.push('📌 今日記事提醒（' + notes.length + ' 則）：');
    var snapshotToday = lineBotToday_();
    notes.slice(0, 10).forEach(function (note) {
      var overdueMark = note.remindDate && note.remindDate < snapshotToday
        ? '⏰' + String(note.remindDate).slice(5).replace('-', '/') + '｜'
        : '';
      lines.push('・' + overdueMark + note.text);
    });
  }
  if (snapshot.overdueCount) {
    lines.push('⚠️ 逾期任務（' + snapshot.overdueCount + ' 件）：');
    var overdueTasks = Array.isArray(snapshot.overdueTasks) ? snapshot.overdueTasks : [];
    if (overdueTasks.length) {
      overdueTasks.slice(0, 10).forEach(function (task) {
        lines.push('・' + task.name + (task.dueDate ? '｜原期限 ' + String(task.dueDate).slice(5).replace('-', '/') : ''));
      });
      if (snapshot.overdueCount > overdueTasks.length) lines.push('…其餘 ' + (snapshot.overdueCount - overdueTasks.length) + ' 件請回工作台查看。');
    } else {
      lines.push('請回工作台查看明細。');
    }
  }
  return lines.join('\n');
}

function formatSnapshotTime_(value) {
  try {
    return Utilities.formatDate(new Date(value), Session.getScriptTimeZone(), 'M/d HH:mm');
  } catch (error) {
    return '稍早';
  }
}

function buildContactBookReply_(content) {
  var items = String(content || '').split(/[\n、;；]+/).map(function (value) { return value.trim(); }).filter(String);
  if (!items.length) return '請在「聯絡簿：」後面接上今天的事項，例如：聯絡簿：數習p20、帶直笛。';
  var weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  var today = new Date();
  var lines = ['📣 今日聯絡簿｜' + (today.getMonth() + 1) + '月' + today.getDate() + '日（週' + weekdays[today.getDay()] + '）', ''];
  items.forEach(function (item, index) { lines.push((index + 1) + '. ' + item); });
  lines.push('');
  lines.push('請家長協助孩子完成與準備，謝謝您們的配合 🙏');
  return lines.join('\n');
}

function buildRollcallTodayReply_() {
  var today = lineBotToday_();
  var data = readRollcallRange_(today, today, '');
  if (!data.attendance.length && !data.homework.length) {
    return '今天還沒有大屏回報。請在教室大屏完成點名與作業登記後按「送出回報」。';
  }
  var classNames = {};
  data.attendance.forEach(function (row) { classNames[row.className] = true; });
  data.homework.forEach(function (row) { classNames[row.className] = true; });
  var replies = [];
  Object.keys(classNames).forEach(function (className) {
    var attendance = data.attendance.filter(function (row) { return row.className === className; });
    var boards = {};
    data.homework.forEach(function (row) {
      if (row.className !== className) return;
      var key = row.subject + '｜' + (row.assignment || '');
      if (!boards[key]) boards[key] = { subject: row.subject, assignment: row.assignment || '', missing: [], resubmitted: [] };
      (row.status === '補交' ? boards[key].resubmitted : boards[key].missing).push(row.seat);
    });
    replies.push(buildRollcallSummaryText_(today, className, attendance, Object.keys(boards).map(function (key) { return boards[key]; })));
  });
  return replies.join('\n\n');
}

function buildHomeworkStatsReply_() {
  var today = new Date();
  var from = Utilities.formatDate(new Date(today.getTime() - 29 * 24 * 3600 * 1000), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var data = readRollcallRange_(from, lineBotToday_(), '');
  if (!data.homework.length) return '最近 30 天沒有作業缺交紀錄 🎉';
  var bySubject = {};
  data.homework.forEach(function (row) {
    if (row.status !== '缺交') return;
    if (!bySubject[row.subject]) bySubject[row.subject] = {};
    bySubject[row.subject][row.seat] = (bySubject[row.subject][row.seat] || 0) + 1;
  });
  var lines = ['📊 近 30 天各科缺交天數統計：'];
  Object.keys(bySubject).forEach(function (subject) {
    var seats = Object.keys(bySubject[subject])
      .map(function (seat) { return { seat: Number(seat), days: bySubject[subject][seat] }; })
      .sort(function (a, b) { return b.days - a.days; })
      .slice(0, 10)
      .map(function (entry) { return entry.seat + '號' + entry.days + '天'; });
    lines.push('・' + subject + '：' + seats.join('、'));
  });
  lines.push('（詳細名單與區間統計請開大屏頁的「查詢」分頁）');
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// LINE 傳訊
// ---------------------------------------------------------------------------

function replyLineMessage_(replyToken, text) {
  replyLineMessages_(replyToken, [text]);
}

function replyLineMessages_(replyToken, texts) {
  var messages = (texts || []).filter(String).slice(0, 5)
    .map(function (text) { return { type: 'text', text: String(text).slice(0, 4900) }; });
  if (!replyToken || !messages.length) return;
  var accessToken = lineBotProperty_('LINE_CHANNEL_ACCESS_TOKEN');
  if (!accessToken) return;
  UrlFetchApp.fetch(LINE_BOT_CONFIG.REPLY_ENDPOINT, {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + accessToken },
    payload: JSON.stringify({ replyToken: replyToken, messages: messages })
  });
}

function pushLineMessage_(userId, text) {
  var accessToken = lineBotProperty_('LINE_CHANNEL_ACCESS_TOKEN');
  if (!accessToken || !userId || !text) return;
  UrlFetchApp.fetch(LINE_BOT_CONFIG.PUSH_ENDPOINT, {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + accessToken },
    payload: JSON.stringify({ to: userId, messages: [{ type: 'text', text: String(text).slice(0, 4900) }] })
  });
}

// ---------------------------------------------------------------------------
// 聯絡本：每天一筆，大屏與教師工作台共用；最後儲存者生效。
// 教室金鑰只能讀寫「今天」；老師金鑰可讀寫任何日期（工作台管理版面用）。
// ---------------------------------------------------------------------------

function findContactBookRow_(sheet, date) {
  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) return -1;
  var values = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (var index = 0; index < values.length; index += 1) {
    var rowDate = values[index][0] instanceof Date
      ? Utilities.formatDate(values[index][0], Session.getScriptTimeZone(), 'yyyy-MM-dd')
      : String(values[index][0]);
    if (rowDate === date) return index + 2;
  }
  return -1;
}

function getContactBook_(body, isTeacher) {
  var date = String(body.date || lineBotToday_());
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error('日期格式不正確');
  if (!isTeacher && date !== lineBotToday_()) throw new Error('教室端只能讀取今天的聯絡本');
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var rowIndex = findContactBookRow_(sheets.contactbook, date);
  if (rowIndex === -1) return { ok: true, date: date, text: '', updatedAt: '', source: '' };
  var row = sheets.contactbook.getRange(rowIndex, 1, 1, 5).getValues()[0];
  return {
    ok: true,
    date: date,
    className: String(row[1] || ''),
    text: String(row[2] || '').slice(0, 5000),
    updatedAt: row[3] instanceof Date ? row[3].toISOString() : String(row[3] || ''),
    source: String(row[4] || '')
  };
}

function saveContactBook_(body, isTeacher) {
  var date = String(body.date || lineBotToday_());
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error('日期格式不正確');
  if (!isTeacher && date !== lineBotToday_()) throw new Error('教室端只能編輯今天的聯絡本');
  var text = String(body.text || '').slice(0, 5000);
  var className = String(body.className || '').trim().slice(0, 20);
  var source = isTeacher ? 'teacher' : 'classroom';
  saveContactBookRecord_(date, className, text, source);
  return { ok: true, date: date, source: source };
}

function saveContactBookRecord_(date, className, text, source) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
    var rowIndex = findContactBookRow_(sheets.contactbook, date);
    var record = [date, className, String(text).slice(0, 5000), new Date(), source];
    if (rowIndex === -1) sheets.contactbook.appendRow(record);
    else sheets.contactbook.getRange(rowIndex, 1, 1, 5).setValues([record]);
  } finally {
    lock.releaseLock();
  }
}

/** LINE 傳「聯絡本：…」（文字或語音）→ 追加到今天的聯絡本，大屏黑板一分鐘內自動顯示。 */
function writeContactBookFromLine_(content) {
  var items = String(content || '').split(/[\n、;；，,]+/)
    .map(function (value) { return value.trim(); }).filter(String).slice(0, 20);
  if (!items.length) return '請在「聯絡本：」後面接上項目，例如：聯絡本：數習 P.20、帶直笛。';
  var today = lineBotToday_();
  var existing = getContactBook_({ date: today }, true);
  var lines = String(existing.text || '').split('\n')
    .map(function (line) { return line.trim(); }).filter(String);
  items.forEach(function (item) { lines.push(lines.length + 1 + '. ' + item); });
  var text = lines.join('\n').slice(0, 5000);
  saveContactBookRecord_(today, String(existing.className || ''), text, 'line');
  return '📖 已寫入今天的聯絡本：\n' + text + '\n\n（大屏黑板一分鐘內自動更新；要修改可到工作台或大屏編輯。）';
}

/** 老師金鑰限定：聯絡本歷史清單（近 limit 筆，新到舊，含內容預覽）。 */
function listContactBook_(body) {
  var limit = Math.min(60, Math.max(1, parseInt(body.limit, 10) || 30));
  var sheets = ensureLineBotSheets_(SpreadsheetApp.getActiveSpreadsheet());
  var lastRow = sheets.contactbook.getLastRow();
  if (lastRow <= 1) return { ok: true, entries: [] };
  var values = sheets.contactbook.getRange(2, 1, lastRow - 1, 5).getValues();
  var entries = values.map(function (row) {
    var date = row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : String(row[0]);
    var text = String(row[2] || '');
    return {
      date: date,
      preview: text.replace(/\s+/g, ' ').slice(0, 50),
      empty: !text.trim(),
      updatedAt: row[3] instanceof Date ? row[3].toISOString() : String(row[3] || ''),
      source: String(row[4] || '')
    };
  }).filter(function (entry) { return /^\d{4}-\d{2}-\d{2}$/.test(entry.date); })
    .sort(function (a, b) { return b.date.localeCompare(a.date); })
    .slice(0, limit);
  return { ok: true, entries: entries };
}

/**
 * 每週作業關懷（選用）：在 Apps Script「觸發條件」新增時間驅動觸發器，
 * 選擇本函式與「週計時器 → 每週五 → 下午 3–4 點」（或你偏好的時段）。
 *
 * 統計最近 7 天各座號缺交次數；達門檻（預設 5 次，可在指令碼屬性設
 * WEEKLY_ALERT_THRESHOLD 調整）時：
 * 1. 為每位學生產生一則「委婉的家長溝通訊息草稿」，放進 LINE收件匣
 *    （同步後出現在教師工作台，標籤：家長聯繫）。
 * 2. LINE 推播提醒老師有哪些座號達門檻。
 * 訊息只含座號與缺交明細，不含姓名；請老師在工作台補上稱謂與孩子的優點後再轉發。
 */
function sendWeeklyHomeworkAlerts() {
  if (!pushAllowed_('weekly')) return;
  var threshold = parseInt(lineBotProperty_('WEEKLY_ALERT_THRESHOLD'), 10);
  if (!(threshold >= 1)) threshold = 5;
  var today = lineBotToday_();
  var from = Utilities.formatDate(new Date(new Date().getTime() - 6 * 24 * 3600 * 1000), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var data = readRollcallRange_(from, today, '');
  var byStudent = {};
  data.homework.forEach(function (row) {
    if (row.status !== '缺交') return;
    var key = row.className + '|' + row.seat;
    if (!byStudent[key]) byStudent[key] = { className: row.className, seat: row.seat, items: [] };
    byStudent[key].items.push(row);
  });
  var flagged = Object.keys(byStudent).map(function (key) { return byStudent[key]; })
    .filter(function (student) { return student.items.length >= threshold; })
    .sort(function (a, b) { return b.items.length - a.items.length; });
  if (!flagged.length) return;

  flagged.forEach(function (student) {
    var message = buildParentHomeworkMessage_(student.items);
    appendLineInboxRow_({
      type: 'note',
      title: student.className + ' ' + student.seat + '號 家長溝通訊息草稿（本週缺交 ' + student.items.length + ' 次）',
      tag: '家長聯繫'
    }, message, 'weekly-alert');
  });

  var users = lineBotProperty_('LINE_ALLOWED_USER_IDS')
    .split(',').map(function (value) { return value.trim(); }).filter(String);
  var summary = [
    '📮 每週作業關懷（' + from + ' ～ ' + today + '）',
    '缺交達 ' + threshold + ' 次的座號：',
    flagged.map(function (student) { return '・' + student.className + ' ' + student.seat + '號：' + student.items.length + ' 次'; }).join('\n'),
    '',
    '已為每位學生準備一則委婉的家長訊息草稿，放在工作台的 LINE 收件匣。',
    '請開工作台按「立即同步」，補上稱謂與孩子的優點後再轉發給家長。'
  ].join('\n');
  users.forEach(function (userId) { pushLineMessage_(userId, summary); });
}

function buildParentHomeworkMessage_(items) {
  var subjectCounts = {};
  items.forEach(function (row) {
    var label = row.subject + (row.assignment ? '／' + row.assignment : '');
    subjectCounts[label] = (subjectCounts[label] || 0) + 1;
  });
  var detail = Object.keys(subjectCounts).map(function (label) {
    return '・' + label + '：' + subjectCounts[label] + ' 次';
  }).join('\n');
  return [
    '親愛的家長您好：',
    '',
    '想利用週末前的時間，跟您分享孩子這週在學校的學習情況。',
    '',
    '孩子這週有幾項作業還沒有完成繳交：',
    detail,
    '',
    '孩子平時在班上（老師補充：孩子的優點或近期進步），這部分我們都看在眼裡，也很欣賞。作業的部分，我們在學校會持續提醒與陪伴孩子完成；也想邀請您在家方便的時候，幫忙關心一下孩子的作業情形，我們一起幫孩子慢慢建立穩定的學習習慣。',
    '',
    '如果孩子最近在家有什麼特別的狀況，或有需要老師配合協助的地方，都非常歡迎隨時跟我聯繫。謝謝您的支持與配合！',
    '',
    '導師敬上'
  ].join('\n');
}

/**
 * 每日簡報（雲端備援）：內容包含今日點名與作業回報＋今日課程進度＋今日任務＋
 * 今日記事＋逾期任務清單。有使用晨間大屏時，這些內容已附在大屏的點名推播裡，
 * 本函式會自動略過不重複發送；沒開大屏的日子才由這裡補上。
 * 推播訊息計入 LINE 免費額度（目前每月 200 則）。
 */
function sendLineDailyBriefing() {
  var users = lineBotProperty_('LINE_ALLOWED_USER_IDS')
    .split(',').map(function (value) { return value.trim(); }).filter(String);
  if (!users.length) return;
  if (!pushAllowed_('dailyBrief')) return;   // 預設關閉：點名推播已含相同內容
  var today = lineBotToday_();
  var props = PropertiesService.getScriptProperties();
  // 大屏的點名推播已經帶過今日重點就不再重複；老師早上只會收到一則含任務的訊息。
  if (String(props.getProperty(MORNING_BRIEF_FLAG) || '') === today) return;
  props.setProperty(MORNING_BRIEF_FLAG, today);
  var sections = ['☀️ 早安！今日簡報：'];
  var rollcall = readRollcallRange_(today, today, '');
  if (rollcall.attendance.length || rollcall.homework.length) {
    sections.push(buildRollcallTodayReply_());
  } else {
    sections.push('📋 大屏今天還沒有點名與作業回報。');
  }
  sections.push(buildSnapshotReply_());
  users.forEach(function (userId) { pushLineMessage_(userId, sections.join('\n\n')); });
}
