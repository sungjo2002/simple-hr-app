function digitsOnly(value) {
  return String(value || "").replace(/\D/g, "");
}

function formatBusinessNumber(value) {
  const digits = digitsOnly(value).slice(0, 10);
  if (digits.length <= 3) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}`;
}

function formatPhoneNumber(value) {
  const digits = digitsOnly(value).slice(0, 11);
  if (!digits) return "";
  if (digits.startsWith("02")) {
    if (digits.length <= 2) return digits;
    if (digits.length <= 5) return `${digits.slice(0, 2)}-${digits.slice(2)}`;
    if (digits.length <= 9) return `${digits.slice(0, 2)}-${digits.slice(2, 5)}-${digits.slice(5)}`;
    return `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  if (digits.length <= 10) return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`;
}

function bindAutoFormat(selector, formatter) {
  document.querySelectorAll(selector).forEach((input) => {
    const applyFormat = () => {
      const formatted = formatter(input.value);
      if (input.value !== formatted) input.value = formatted;
    };
    input.addEventListener("input", applyFormat);
    input.addEventListener("blur", applyFormat);
    applyFormat();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindAutoFormat('input[data-format="business-number"]', formatBusinessNumber);
  bindAutoFormat('input[data-format="phone"]', formatPhoneNumber);
});
