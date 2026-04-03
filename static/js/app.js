document.addEventListener("DOMContentLoaded", () => {
  const cards = Array.from(document.querySelectorAll(".summary-card"));
  const rows = Array.from(document.querySelectorAll(".worker-row"));
  const titleEl = document.getElementById("worker-panel-title");
  const countEl = document.getElementById("worker-panel-count");
  const rowLimitEl = document.getElementById("row-limit");

  if (!cards.length || !rows.length || !titleEl || !countEl || !rowLimitEl) {
    return;
  }

  const statusMap = {
    all: "전체",
    before_work: "출근전",
    working: "근무중",
    done: "퇴근완료",
    hospital: "병원",
    absent: "결근",
  };

  let activeStatus = "all";

  function applyFilter() {
    const limit = Number(rowLimitEl.value || 10);
    let matched = 0;
    let visible = 0;

    rows.forEach((row) => {
      const rowStatus = row.dataset.status || "";
      const isMatch = activeStatus === "all" || rowStatus === activeStatus;

      if (!isMatch) {
        row.style.display = "none";
        return;
      }

      matched += 1;

      if (visible < limit) {
        row.style.display = "";
        visible += 1;
      } else {
        row.style.display = "none";
      }
    });

    const label = statusMap[activeStatus] || "전체";
    titleEl.textContent = `${label} 인력현황`;
    countEl.textContent = `${label} 상태 · 표시 ${visible}명 / 전체 ${matched}명`;
  }

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      activeStatus = card.dataset.status || "all";

      cards.forEach((item) => {
        item.classList.toggle("is-active", item === card);
      });

      applyFilter();
    });
  });

  rowLimitEl.addEventListener("change", applyFilter);

  applyFilter();
});
