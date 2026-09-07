// 教師工作台網站版本（每次發布都要更新；各頁左下角會顯示）
window.TD_VERSION = '2026-09-07 22:30';
(function () {
  try {
    var el = document.createElement('div');
    el.id = 'siteVersionBadge';
    el.textContent = '版本 ' + window.TD_VERSION;
    el.title = '網站程式版本（日期 時間）。LINE 小幫手程式版本請看試算表選單「ℹ️ 程式版本」。';
    el.style.cssText = 'position:fixed;left:6px;bottom:4px;z-index:5;font:10px/1.4 "Microsoft JhengHei","Noto Sans TC",sans-serif;color:#657570;opacity:.55;pointer-events:none;';
    document.addEventListener('DOMContentLoaded', function () { document.body.appendChild(el); });
    if (document.readyState !== 'loading') document.body.appendChild(el);
  } catch (error) {}
})();
