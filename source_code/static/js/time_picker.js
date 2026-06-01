(function () {
  function pad(value) {
    return String(value).padStart(2, "0");
  }

  function parseTime(value, fallbackHour) {
    if (!value || !value.includes(":")) {
      return { hour: fallbackHour, minute: 0 };
    }
    const parts = value.split(":");
    return {
      hour: parseInt(parts[0], 10) || fallbackHour,
      minute: parseInt(parts[1], 10) || 0,
    };
  }

  function nearestStep(minute, step) {
    return Math.round(minute / step) * step % 60;
  }

  function buildSelect(className, ariaLabel) {
    const select = document.createElement("select");
    select.className = "form-select time-picker-select rounded-xl " + className;
    select.setAttribute("aria-label", ariaLabel);
    return select;
  }

  function setPickerValue(container, value) {
    const startHour = parseInt(container.dataset.startHour, 10);
    const step = parseInt(container.dataset.step, 10) || 30;
    const parsed = parseTime(value, startHour);
    const snappedMinute = step >= 60 ? 0 : nearestStep(parsed.minute, step);
    const hourSelect = container.querySelector(".time-picker-hour");
    const minuteSelect = container.querySelector(".time-picker-minute");
    const hiddenInput = container.querySelector('input[type="hidden"]');

    if (hourSelect) {
      hourSelect.value = pad(parsed.hour);
    }
    if (minuteSelect) {
      minuteSelect.value = pad(snappedMinute);
    }

    hiddenInput.value =
      (hourSelect ? hourSelect.value : pad(parsed.hour)) +
      ":" +
      (minuteSelect ? minuteSelect.value : "00");
    container.dataset.value = hiddenInput.value;
    container.dispatchEvent(new Event("timechange", { bubbles: true }));
  }

  function addOneHour(timeValue, maxHour) {
    const parsed = parseTime(timeValue, 0);
    const nextHour = Math.min(parsed.hour + 1, maxHour);
    return pad(nextHour) + ":" + pad(parsed.minute);
  }

  function initTimePicker(container) {
    const startHour = parseInt(container.dataset.startHour, 10);
    const endHour = parseInt(container.dataset.endHour, 10);
    const step = parseInt(container.dataset.step, 10) || 30;
    const row = container.querySelector(".time-picker-row");
    const hiddenInput = container.querySelector('input[type="hidden"]');
    const current = parseTime(container.dataset.value || hiddenInput.value, startHour);
    const snappedMinute = step >= 60 ? 0 : nearestStep(current.minute, step);

    const hourSelect = buildSelect("time-picker-hour", "시");
    for (let hour = startHour; hour <= endHour; hour += 1) {
      const option = document.createElement("option");
      option.value = pad(hour);
      option.textContent = hour + "시";
      option.selected = hour === current.hour;
      hourSelect.appendChild(option);
    }
    row.appendChild(hourSelect);

    let minuteSelect = null;
    if (step < 60) {
      minuteSelect = buildSelect("time-picker-minute", "분");
      for (let minute = 0; minute < 60; minute += step) {
        const option = document.createElement("option");
        option.value = pad(minute);
        option.textContent = pad(minute) + "분";
        option.selected = minute === snappedMinute;
        minuteSelect.appendChild(option);
      }
      row.appendChild(minuteSelect);
    }

    function syncHidden() {
      const minute = minuteSelect ? minuteSelect.value : "00";
      hiddenInput.value = hourSelect.value + ":" + minute;
      container.dataset.value = hiddenInput.value;
      container.dispatchEvent(new Event("timechange", { bubbles: true }));
    }

    hourSelect.addEventListener("change", syncHidden);
    if (minuteSelect) {
      minuteSelect.addEventListener("change", syncHidden);
    }

    syncHidden();
  }

  function linkEndTime(startContainer) {
    const endId = startContainer.dataset.linkedEnd;
    if (!endId) {
      return;
    }

    const endContainer = document.getElementById(endId)?.closest("[data-time-picker]");
    if (!endContainer) {
      return;
    }

    startContainer.addEventListener("timechange", function () {
      const startHidden = startContainer.querySelector('input[type="hidden"]');
      const maxHour = parseInt(endContainer.dataset.endHour, 10);
      setPickerValue(endContainer, addOneHour(startHidden.value, maxHour));
      endContainer.dispatchEvent(new Event("timechange", { bubbles: true }));
    });
  }

  document.querySelectorAll("[data-time-picker]").forEach(function (container) {
    initTimePicker(container);
    linkEndTime(container);
  });

  window.setTimePickerValue = function (inputId, value) {
    const container = document.getElementById(inputId)?.closest("[data-time-picker]");
    if (container) {
      setPickerValue(container, value);
    }
  };
})();
