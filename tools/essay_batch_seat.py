"""作文整班批次：怎麼知道誰是誰（老師 2026-11-02「但怎知，誰是誰?」）
- 「座號怎麼對」：先讓 AI 讀紙上寫的座號，讀不到才照檔名順序（也可以選只照順序）
- 每份旁邊放照片縮圖；座號重複、紙上沒讀到的標 ⚠；老師改座號，已批好的批改單上的座號跟著改
- AI 只回座號數字，不回傳學生姓名
python tools/essay_batch_seat.py（要先套過 tools/essay_batch.py）
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'Studio.html'
s = path.read_text(encoding='utf-8')
assert 'esGradeOne' in s and 'esBatchSeatMode' not in s


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


rep("""    async function esGradeOne(text, esFiles, seat) {
      const hasImages = esFiles.length > 0;""", """    async function esGradeOne(text, esFiles, seat, opts) {
      const hasImages = esFiles.length > 0;
      const readSeat = !!(opts && opts.readSeat && hasImages);""")
rep("""      ].filter(Boolean).join('\\n');
      {
        const imageParts = await filesToParts(esFiles, 0);""", """      ].filter(Boolean).join('\\n') + (readSeat ? '\\n另外：作文紙上如果有寫座號，把座號填在 seatOnPaper（只填數字；看不到就填空字串）。不要抄寫或回傳學生姓名。' : '');
      {
        const imageParts = await filesToParts(esFiles, 0);""")
rep("""        const data = extractJson(resultText);
        $('esStatus').textContent = '';""", """        const data = extractJson(resultText);
        $('esStatus').textContent = '';
        // 整班批次：用紙上寫的座號（讀不到就沿用排序給的座號）
        const paperSeat = readSeat ? String(data.seatOnPaper == null ? '' : data.seatOnPaper).replace(/[^0-9]/g, '').slice(0, 3) : '';
        if (paperSeat && Number(paperSeat) > 0) seat = String(Number(paperSeat));
        delete data.name;""")
rep("""        return { html, data, band, noTypos: esOut('typoSheet') && !typoSheet };""",
    """        return { html, data, band, seat, paperSeat, noTypos: esOut('typoSheet') && !typoSheet };""")

rep("""              <label>空號 <input class="input" id="esBatchSkip" placeholder="例：5、12" style="width:110px"></label></div>""",
    """              <label>空號 <input class="input" id="esBatchSkip" placeholder="例：5、12" style="width:110px"></label></div>
            <div class="field" style="margin-top:8px"><label>座號怎麼對</label>
              <select class="select" id="esBatchSeatMode"><option value="paper" selected>先讀紙上寫的座號，讀不到才照順序</option><option value="order">只照順序</option></select></div>""")
rep("""照片依檔名排序（手機照片就是拍照順序），分好後每份的座號都可以再改。請學生只寫座號、不要寫姓名。""",
    """請學生在作文紙右上角<strong>寫大大的座號</strong>（不要寫姓名），AI 會讀紙上的座號，讀不到才照檔名順序（手機照片就是拍照順序）。每份旁邊有照片縮圖，座號都可以再改；讀不到或重複的會標 ⚠。""")

rep("""        items.push({ seat: String(seat), files: pages.slice(i, i + per), status: 'wait', html: '', data: null, band: '', rec: null, error: '' });""",
    """        const group = pages.slice(i, i + per);
        items.push({ seat: String(seat), files: group, status: 'wait', html: '', data: null, band: '', rec: null, error: '', seatNote: '',
          thumb: group[0] && group[0].type.startsWith('image/') ? URL.createObjectURL(group[0]) : '' });""")
rep("""      const count = k => items.filter(x => x.status === k).length;""", """      const count = k => items.filter(x => x.status === k).length;
      const seen = {};
      items.forEach(x => { seen[x.seat] = (seen[x.seat] || 0) + 1; });""")
rep("""          <td>座號 <input class="input es-bseat" data-i="${i}" value="${escapeHtml(x.seat)}"${x.status === 'run' ? ' disabled' : ''}></td>""",
    """          <td>${x.thumb ? `<img src="${x.thumb}" alt="" style="width:42px;height:56px;object-fit:cover;border:1px solid #ccc;border-radius:4px;vertical-align:middle">` : '📄'}</td>
          <td>座號 <input class="input es-bseat" data-i="${i}" value="${escapeHtml(x.seat)}"${x.status === 'run' ? ' disabled' : ''}>
            ${seen[x.seat] > 1 ? '<div class="st-fail" style="font-size:11.5px">⚠ 座號重複</div>' : x.seatNote ? `<div class="${x.seatNote.startsWith('⚠') ? 'st-fail' : 'st-ok'}" style="font-size:11.5px">${escapeHtml(x.seatNote)}</div>` : ''}</td>""")
rep("""    $('esBatchList').addEventListener('input', e => {
      const box = e.target.closest('.es-bseat');
      if (box) ES_BATCH.items[Number(box.dataset.i)].seat = box.value.trim();
    });""", """    $('esBatchList').addEventListener('change', e => {
      const box = e.target.closest('.es-bseat');
      if (!box) return;
      const item = ES_BATCH.items[Number(box.dataset.i)];
      const old = item.seat;
      item.seat = box.value.trim();
      item.seatNote = '老師改過';
      // 已批好的批改單、錯字訂正單上的座號一起改
      if (item.html) item.html = item.html.split(`座號：${escapeHtml(old)}<`).join(`座號：${escapeHtml(item.seat)}<`);
      if (item.rec) item.rec.seat = item.seat;
      if (ES_BATCH.viewing === Number(box.dataset.i)) { $('esPreview').innerHTML = item.html; $('esSeat').value = item.seat; }
      esBatchRender();
    });""")
rep("""            const r = await esGradeOne('', item.files, item.seat);
            Object.assign(item, { status: 'done', html: r.html, data: r.data, band: r.band, rec: null, error: '' });""",
    """            const readSeat = $('esBatchSeatMode').value === 'paper';
            const r = await esGradeOne('', item.files, item.seat, { readSeat });
            const note = !readSeat ? '' : r.paperSeat ? (r.seat === item.seat ? '📷 紙上座號相符' : `📷 依紙上座號（原本排 ${item.seat}）`) : '⚠ 紙上沒讀到座號，照順序';
            Object.assign(item, { status: 'done', html: r.html, data: r.data, band: r.band, rec: null, error: '', seat: r.seat, seatNote: note });""")

path.write_text(s, encoding='utf-8')
print('ok')
