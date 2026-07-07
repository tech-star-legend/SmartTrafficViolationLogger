document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss flash alerts after a few seconds
  document.querySelectorAll(".alert.auto-dismiss").forEach(function (el) {
    setTimeout(function () {
      if (window.bootstrap && bootstrap.Alert) {
        bootstrap.Alert.getOrCreateInstance(el).close();
      } else {
        el.remove();
      }
    }, 5000);
  });

  // Count-up animation for dashboard stat numbers
  document.querySelectorAll("[data-count-to]").forEach(function (el) {
    var target = parseInt(el.getAttribute("data-count-to"), 10) || 0;
    var duration = 900;
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        el.textContent = target;
      }
    }
    window.requestAnimationFrame(step);
  });

  // Copy-to-clipboard for challan numbers
  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var value = btn.getAttribute("data-copy-value");
      if (!value) return;
      navigator.clipboard.writeText(value).then(function () {
        var original = btn.innerHTML;
        btn.innerHTML = "Copied!";
        setTimeout(function () {
          btn.innerHTML = original;
        }, 1400);
      });
    });
  });

  // Mark active nav link based on current path
  var path = window.location.pathname;
  document.querySelectorAll(".app-navbar [data-nav-link]").forEach(function (link) {
    if (link.getAttribute("href") === path) {
      link.classList.add("active");
    }
  });
});
