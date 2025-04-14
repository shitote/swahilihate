document.addEventListener("DOMContentLoaded", function () {
  setTimeout(function () {
    var messages = document.querySelectorAll(".alert");
    messages.forEach(function (message) {
      message.style.display = "none";
    });
  }, 3000); // Auto-hide after 3 seconds
});
