function showToast(msg) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2500);
}

function toggleSave(btn, url, name, platform, members, type, description) {
  const isSaved = btn.classList.contains("saved");
  const endpoint = isSaved ? "/unsave" : "/save";
  const label = isSaved ? "Save" : "Saved";

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, name, platform, members, active_users: 0, type, description, title: name })
  })
  .then(r => r.json())
  .then(() => {
    btn.classList.toggle("saved");
    btn.textContent = isSaved ? "Save" : "Saved";
    showToast(isSaved ? "Removed from saved" : "Saved!");
  });
}

function saveNotes(url, textarea) {
  fetch("/notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, notes: textarea.value })
  })
  .then(() => showToast("Notes saved!"));
}

function removeSaved(btn, url) {
  fetch("/unsave", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  })
  .then(() => {
    const card = btn.closest(".card");
    card.style.transition = "opacity 0.3s";
    card.style.opacity = "0";
    setTimeout(() => { card.remove(); showToast("Removed!"); }, 300);
  });
}
