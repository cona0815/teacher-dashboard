"""閱讀分級改寫合法化（升級規劃第一批第 5 項之一）：
- 新增「原文來源」：自己寫的／已授權、公有領域、CC 授權（填出處）、有著作權的文章（新聞、課文、雜誌…）
- 有著作權的文章不再「改寫原文」，改成先抽事實重點、再用 AI 原創文字重寫（不沿用原句），文末附出處
- 時事搜尋改成只回傳事實條列＋網址，不再請 AI 寫新聞摘要
python tools/reading_copyright_safe.py
"""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'rdSource' not in s, '已套用過'


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep('''          <div class="field"><label>貼上原文（課文、新聞、故事…）</label>''', '''          <div class="field"><label>原文來源（決定 AI 可以怎麼處理）</label>
            <select class="select" id="rdSource">
              <option value="facts" selected>有著作權的文章（新聞、課文、雜誌、書…）→ 只取事實重點，用原創文字重寫</option>
              <option value="own">我自己寫的，或已取得作者授權 → 可以直接分級改寫</option>
              <option value="public">公有領域（作者過世超過 50 年）→ 可以直接分級改寫</option>
              <option value="cc">CC 授權（例如維基百科）→ 可以改寫，要標示出處</option>
            </select>
            <input class="input" id="rdCredit" placeholder="出處（網址或書名・作者），會印在每一版最下面" style="margin-top:6px"></div>
          <div class="field"><label>貼上原文（課文、新聞、故事…）</label>''')
rep('''          <div class="hint">同一篇文章改寫成不同閱讀程度（事實與結論不變，只調整句長、詞彙與背景說明），每版各一頁，方便同班差異化。時事由 Google 搜尋即時取得並經兒童安全過濾，仍請老師過目再發。</div>''', '''          <div class="hint">同一篇文章改寫成不同閱讀程度（事實與結論不變，只調整句長、詞彙與背景說明），每版各一頁，方便同班差異化。時事由 Google 搜尋即時取得並經兒童安全過濾，只取事實重點、用原創文字重寫並附出處，仍請老師過目再發。</div>''')

# 時事：只要事實條列與網址
rep('''        '找 5 則不同的新聞，每則：title（繁體中文標題，20 字內）、date（YYYY-MM-DD）、source（媒體名稱）、summary（用繁體中文、臺灣用語寫 250–350 字的兒童可讀摘要：發生了什麼、在哪裡、為什麼有趣或重要、和小朋友生活的連結；不要用成人新聞腔）、kidSafe（true/false，你再自我檢查一次是否完全符合排除規則）。',
        '只回傳 JSON：{"items":[{"title":"","date":"","source":"","summary":"","kidSafe":true}]}\'''', '''        '找 5 則不同的新聞，每則：title（你自己下的繁體中文標題，20 字內，不要照抄媒體標題）、date（YYYY-MM-DD）、source（媒體名稱）、url（新聞網址，沒有就留空）、facts（6–10 條「事實重點」：誰、在哪裡、做了什麼、數字、結果，每條一句、用你自己的話，不要抄新聞原句）、kidSafe（true/false，你再自我檢查一次是否完全符合排除規則）。',
        '只回傳 JSON：{"items":[{"title":"","date":"","source":"","url":"","facts":[""],"kidSafe":true}]}\'''')
rep('''        const items = ((data && data.items) || []).filter(item => item && item.kidSafe !== false && item.summary && !NEWS_BLOCKLIST.test(item.title + item.summary)).slice(0, 5);''', '''        const items = ((data && data.items) || []).map(item => Object.assign(item, { summary: (item.facts || []).map(f => '・' + f).join('\\n') }))
          .filter(item => item && item.kidSafe !== false && item.summary && !NEWS_BLOCKLIST.test(item.title + item.summary)).slice(0, 5);''')
rep('''      $('rdText').value = `${item.title}\\n\\n${item.summary}${item.source ? `\\n\\n（資料來源：${item.source}，${item.date || ''}）` : ''}`;''', '''      $('rdText').value = `${item.title}\\n\\n${item.summary}`;
      $('rdSource').value = 'facts';
      $('rdCredit').value = [item.source, item.date, item.url].filter(Boolean).join('，');''')

# 分級改寫：依來源決定能不能沿用原文
rep('''        `你是臺灣國小閱讀教學專家。班級為${grade}年級。請把下面的文章改寫成 ${levels.join('、')} 版本，做差異化閱讀。`,''', '''        `你是臺灣國小閱讀教學專家。班級為${grade}年級。請把下面的文章改寫成 ${levels.join('、')} 版本，做差異化閱讀。`,
        $('rdSource').value === 'facts'
          ? '【著作權規定】原文是別人的著作。請先抓出事實與重點，再用你自己的文字「重新寫」成新文章：不得沿用原文的句子、段落安排或特殊說法，不要逐句改寫；可以引用的只有事實、數字、人名地名。'
          : '原文的作者已同意或屬公有領域／CC 授權，可以直接改寫。',''')
rep('''        const versions = (data.levels || []).filter(v => levels.includes(v.level));''', '''        const versions = (data.levels || []).filter(v => levels.includes(v.level));
        const credit = $('rdCredit').value.trim();
        const creditNote = $('rdSource').value === 'facts'
          ? `本文依${credit ? `「${credit}」` : '原文'}的事實重點重新撰寫，非原文。`
          : $('rdSource').value === 'cc' ? `改寫自：${credit || '（請填出處）'}（CC 授權）` : (credit ? `出處：${credit}` : '');''')

path.write_text(s, encoding='utf-8')
print('ok')
