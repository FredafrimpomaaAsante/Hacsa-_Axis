(function () {
  function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('ops-theme', theme);

    var buttons = document.querySelectorAll('[data-theme-toggle]');
    buttons.forEach(function (button) {
      var nextTheme = theme === 'dark' ? 'light' : 'dark';
      button.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
      button.setAttribute('aria-label', 'Switch to ' + nextTheme + ' mode');
    });
  }

  var savedTheme = localStorage.getItem('ops-theme');
  var initialTheme = savedTheme || 'dark';
  applyTheme(initialTheme);

  document.addEventListener('click', function (event) {
    var target = event.target;
    if (!target.matches('[data-theme-toggle]')) {
      return;
    }

    var currentTheme = document.body.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    var nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(nextTheme);
  });
})();
