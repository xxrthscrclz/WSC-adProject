(function () {
  const previewRoot = document.getElementById("schedule-preview");
  if (!previewRoot) {
    return;
  }

  function parseTime(value) {
    if (!value || !value.includes(":")) {
      return null;
    }
    const parts = value.split(":");
    return {
      hour: parseInt(parts[0], 10),
      minute: parseInt(parts[1], 10) || 0,
    };
  }

  function timeToMinutes(value) {
    const parsed = parseTime(value);
    if (!parsed) {
      return null;
    }
    return parsed.hour * 60 + parsed.minute;
  }

  function updatePreview() {
    const daySelect = document.getElementById("day-of-week");
    const startInput = document.querySelector('[name="start_time"]');
    const endInput = document.querySelector('[name="end_time"]');
    const subjectInput = document.getElementById("subject-name");

    if (!daySelect || !startInput || !endInput) {
      return;
    }

    const gridStart = parseInt(previewRoot.dataset.startHour, 10) * 60;
    const gridEnd = parseInt(previewRoot.dataset.endHour, 10) * 60;
    const totalMinutes = gridEnd - gridStart;
    const startMinutes = timeToMinutes(startInput.value);
    const endMinutes = timeToMinutes(endInput.value);

    previewRoot.querySelectorAll(".weekly-preview-block").forEach(function (block) {
      block.hidden = true;
    });

    if (startMinutes === null || endMinutes === null || endMinutes <= startMinutes) {
      return;
    }

    const column = previewRoot.querySelector(
      '.weekly-day-column[data-day="' + daySelect.value + '"]'
    );
    if (!column) {
      return;
    }

    const block = column.querySelector(".weekly-preview-block");
    if (!block) {
      return;
    }

    const offsetStart = startMinutes - gridStart;
    const offsetEnd = endMinutes - gridStart;
    const topPct = (offsetStart / totalMinutes) * 100;
    const heightPct = ((offsetEnd - offsetStart) / totalMinutes) * 100;

    block.style.top = topPct + "%";
    block.style.height = heightPct + "%";
    block.hidden = false;

    const label = block.querySelector(".weekly-preview-label");
    if (label) {
      label.textContent = subjectInput && subjectInput.value.trim()
        ? subjectInput.value.trim()
        : "새 수업";
    }
  }

  document.getElementById("day-of-week")?.addEventListener("change", updatePreview);
  document.getElementById("subject-name")?.addEventListener("input", updatePreview);
  document.querySelectorAll("#schedule-add-form [data-time-picker]").forEach(function (picker) {
    picker.addEventListener("timechange", updatePreview);
  });

  updatePreview();
})();
