(function () {
  const path = window.location.pathname;
  if (path.includes("/ops/")) requireAuth(["organiser", "staff", "safety_officer", "ops_lead"]);
  else if (path.includes("/organiser/") || path.includes("/vendor/")) requireAuth(["organiser", "ops_lead"]);
  else if (path.includes("/portal/")) requireAuth(["participant", "speaker"]);

  if (path.includes("/organiser/") || path.includes("/vendor/") || path.includes("/ops/")) addWorkspaceSignOut();
})();

function addWorkspaceSignOut() {
  function signOut() {
    if (typeof clearSession === "function") clearSession();
    window.location.href = "/index.html";
  }

  const existing = document.querySelectorAll("[data-sign-out]");
  if (existing.length) {
    existing.forEach(function (button) {
      button.addEventListener("click", signOut);
    });
    return;
  }

  const style = document.createElement("style");
  style.textContent = ".sign-out-btn{border:1px solid #d9d3c4;background:#fff;color:#123a26;border-radius:8px;padding:8px 12px;font-size:12px;font-weight:700;cursor:pointer;margin-left:10px}.sign-out-btn:hover{background:#f3e7c8}";
  document.head.appendChild(style);
  const button = document.createElement("button");
  button.type = "button";
  button.className = "sign-out-btn";
  button.dataset.signOut = "1";
  button.textContent = "Sign out";
  button.addEventListener("click", signOut);
  const host =
    document.querySelector(".profile-area") ||
    document.querySelector(".user") ||
    document.querySelector(".topbar-actions") ||
    document.querySelector(".topbar") ||
    document.querySelector(".sidebar-foot") ||
    document.querySelector(".sidebar-footer");
  if (host) host.appendChild(button);
}
