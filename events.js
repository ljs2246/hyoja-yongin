(function () {
  function refreshEvents() {
    var parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(new Date());
    var date = {};
    parts.forEach(function (part) { date[part.type] = part.value; });
    var today = date.year + '-' + date.month + '-' + date.day;
    document.querySelectorAll('[data-event-list]').forEach(function (list) {
      var remaining = 0;
      list.querySelectorAll('[data-event-end]').forEach(function (row) {
        row.hidden = row.getAttribute('data-event-end') < today;
        if (!row.hidden) remaining++;
      });
      list.querySelector('[data-event-empty]').hidden = remaining > 0;
    });
  }
  refreshEvents();
  // Refresh after midnight or when returning to an already open page.
  setInterval(refreshEvents, 60000);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) refreshEvents();
  });
})();
