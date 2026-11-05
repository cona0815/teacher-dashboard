"""2026-11-05 老師：存本機的紀錄都留 180 天。
點名、作業和聯絡本共用一個天數；存滿時先清最舊的一天，今天的才存得進去。
補交回溯天數在第 1 級可調到 180；GAS 上限仍是 60，所以接雲端時送出的天數不超過 60。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rep(text, old, new, count=1):
    assert text.count(old) == count, (old[:70], text.count(old))
    return text.replace(old, new)


p = ROOT / 'Morning.html'
t = p.read_text(encoding='utf-8')
t = rep(t, """    const LOCAL_KEEP_DAYS = 30;   // 點名與作業在這台電腦留 30 天，第 1 級的補交靠它
    const CONTACT_LOCAL_PREFIX = 'morningContactLocal:';   // 第 1 級的聯絡本，一天一筆
    const CONTACT_KEEP_DAYS = 180;
""", """    const LOCAL_KEEP_DAYS = 180;   // 點名、作業、聯絡本在這台電腦留 180 天，第 1 級的補交靠它
    const CONTACT_LOCAL_PREFIX = 'morningContactLocal:';   // 第 1 級的聯絡本，一天一筆
    const CLOUD_MAX_DAYS = 60;   // GAS 的 classroom_missing 最多回溯 60 天
""")
t = rep(t, """-CONTACT_KEEP_DAYS)) localStorage.removeItem(key);""", """-LOCAL_KEEP_DAYS)) localStorage.removeItem(key);""")
t = rep(t, """    function saveTodayState() {
      state.dirty = true;""", """    /** 找出最舊的一天（今天不算），把那天的點名、作業、聯絡本都清掉。 */
    function clearOldestLocalDay() {
      const today = todayKey();
      const dated = [];
      for (let index = 0; index < localStorage.length; index += 1) {
        const key = localStorage.key(index);
        const prefix = [STATE_PREFIX, CONTACT_LOCAL_PREFIX].find(item => key && key.startsWith(item));
        if (prefix) dated.push({ key, date: key.slice(prefix.length, prefix.length + 10) });
      }
      const oldest = dated.map(item => item.date).filter(date => date < today).sort()[0];
      if (!oldest) return false;
      dated.filter(item => item.date === oldest).forEach(item => localStorage.removeItem(item.key));
      return true;
    }
    /** 寫進這台電腦；存滿時從最舊的一天開始清，清到存得下為止。回傳有沒有存到。 */
    function setLocalRecord(key, value) {
      for (;;) {
        try {
          localStorage.setItem(key, value);
          return true;
        } catch (error) {
          if (!/quota/i.test(error.name) || !clearOldestLocalDay()) {
            showToast('這台電腦存不下了，這次沒有存到。', true);
            return false;
          }
          if (!state.storageFullWarned) {
            state.storageFullWarned = true;
            showToast('這台電腦的空間滿了，已先清掉最舊的紀錄。', true);
          }
        }
      }
    }
    function saveTodayState() {
      state.dirty = true;""")
t = rep(t, """        localStorage.setItem(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: state.boards, flags: state.flags }));
""", """        setLocalRecord(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: state.boards, flags: state.flags }));
""")
t = rep(t, """      localStorage.setItem(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: firstBoards, flags: state.flags }));
      localStorage.setItem(STATE_PREFIX + todayKey() + suffix, JSON.stringify({ boards: state.boards }));
""", """      setLocalRecord(STATE_PREFIX + todayKey(), JSON.stringify({ attendance: state.attendance, boards: firstBoards, flags: state.flags }));
      setLocalRecord(STATE_PREFIX + todayKey() + suffix, JSON.stringify({ boards: state.boards }));
""")
t = rep(t, """        try {
          localStorage.setItem(CONTACT_LOCAL_PREFIX + todayKey() + classKeySuffix(), JSON.stringify({ text, updatedAt }));
        } catch (error) {
          showToast('這台電腦存不下了，聯絡本沒有存到。', true);
          return;
        }
""", """        if (!setLocalRecord(CONTACT_LOCAL_PREFIX + todayKey() + classKeySuffix(), JSON.stringify({ text, updatedAt }))) return;
""")
t = rep(t, """      localStorage.setItem(key, JSON.stringify(saved));
      return 1;
""", """      return setLocalRecord(key, JSON.stringify(saved)) ? 1 : 0;
""")
# 補交回溯天數：第 1 級最多 180，接雲端時送出的天數不超過 60
t = rep(t, '<label>補交回溯天數</label><input id="setupLookbackDays" type="number" min="1" max="60" value="30">',
        '<label>補交回溯天數（接雲端最多 60）</label><input id="setupLookbackDays" type="number" min="1" max="180" value="30">')
t = rep(t, "s.lookbackDays = Math.min(60, Math.max(1, Number(saved.lookbackDays) || 30));", "s.lookbackDays = Math.min(LOCAL_KEEP_DAYS, Math.max(1, Number(saved.lookbackDays) || 30));")
t = rep(t, "s.lookbackDays = Math.min(60, Math.max(1, Number($('setupLookbackDays').value) || 30));", "s.lookbackDays = Math.min(LOCAL_KEEP_DAYS, Math.max(1, Number($('setupLookbackDays').value) || 30));")
t = rep(t, "    const localDays = () => Math.min(state.settings.lookbackDays, LOCAL_KEEP_DAYS);\n",
        "    const localDays = () => Math.min(state.settings.lookbackDays, LOCAL_KEEP_DAYS);\n"
        "    const cloudDays = () => Math.min(state.settings.lookbackDays, CLOUD_MAX_DAYS);\n")
t = rep(t, "接好後會自動統計近 ' + state.settings.lookbackDays + ' 天", "接好後會自動統計近 ' + cloudDays() + ' 天")
t = rep(t, "className: currentClass(), days: state.settings.lookbackDays });", "className: currentClass(), days: cloudDays() });", count=2)
t = rep(t, "$('correctStatus').textContent = `近 ${state.settings.lookbackDays} 天：", "$('correctStatus').textContent = `近 ${cloudDays()} 天：")
t = rep(t, "$('makeupStatus').textContent = `近 ${state.settings.lookbackDays} 天：", "$('makeupStatus').textContent = `近 ${cloudDays()} 天：")
t = rep(t, "+ '。學生補交或訂正完成後點號碼。';", "+ '。學生補交或訂正完成後點號碼。'\n          + (localDays() < LOCAL_KEEP_DAYS ? `要看更早的，到「設定」把補交回溯天數調大（最多 ${LOCAL_KEEP_DAYS} 天）。` : '');")
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'tests/profile_config.test.js'
t = p.read_text(encoding='utf-8')
t = rep(t, '''assert.match(morningLevelSource, /LOCAL_KEEP_DAYS = 30/, "點名與作業應在本機留 30 天");
assert.match(morningLevelSource, /shiftDate\\(todayKey\\(\\), -LOCAL_KEEP_DAYS\\)/, "清舊資料要照 30 天");
assert.match(morningLevelSource, /CONTACT_KEEP_DAYS = 180/, "第 1 級聯絡本應留 180 天");
assert.match(morningLevelSource, /shiftDate\\(todayKey\\(\\), -CONTACT_KEEP_DAYS\\)/, "清舊聯絡本要照 180 天");
''', '''assert.match(morningLevelSource, /LOCAL_KEEP_DAYS = 180/, "存本機的紀錄應留 180 天");
assert.equal((morningLevelSource.match(/shiftDate\\(todayKey\\(\\), -LOCAL_KEEP_DAYS\\)/g) || []).length, 2, "點名作業與聯絡本都要照 180 天清");
assert.match(morningLevelSource, /max="180"/, "第 1 級補交回溯天數應可調到 180");
assert.match(morningLevelSource, /days: cloudDays\\(\\)/, "接雲端時送出的天數不可超過 GAS 上限");
assert.doesNotMatch(morningLevelSource, /localStorage\\.setItem\\(STATE_PREFIX/, "今天的紀錄要走存滿時會清舊資料的寫入");
''')
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'Install.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '點名與作業的紀錄在這台電腦留 <strong>30 天</strong>，聯絡本留 <strong>180 天</strong>，超過會自動清掉。',
        '點名、作業和聯絡本在這台電腦都留 <strong>180 天</strong>，超過會自動清掉；電腦空間滿了也會先清最舊的。補交清單平常列近 30 天，要看更早的到「設定」調「補交回溯天數」。')
t = rep(t, '第 1 級只看這台電腦近 30 天；', '第 1 級看這台電腦的紀錄（平常列近 30 天，最多可調到 180 天）；')
p.write_text(t, encoding='utf-8', newline='\n')

p = ROOT / 'About.html'
t = p.read_text(encoding='utf-8')
t = rep(t, '不含機敏資料；點名與作業留 30 天，聯絡本留 180 天</td>', '不含機敏資料；紀錄留 180 天</td>')
p.write_text(t, encoding='utf-8', newline='\n')
print('done')
