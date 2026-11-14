const form = document.querySelector("#expense-form");
const controls = document.querySelector("#entry-controls");
const { date, description, amount } = form.elements;
const entries = document.querySelector("#entries");
const entriesPlaceholder = document.querySelector("#entries-placeholder");
const analyzeButton = document.querySelector("#analyze");
const error = document.querySelector("#analysis-error");
const report = document.querySelector("#report");
const reportPlaceholder = document.querySelector("#report-placeholder");

const transactions = [];
const currency = new Intl.NumberFormat("ru-RU", { style: "currency", currency: "EUR" });
const dates = new Intl.DateTimeFormat("ru-RU", { timeZone: "UTC" });
const categories = {
  Groceries: "Продукты",
  Transport: "Транспорт",
  Subscriptions: "Подписки",
  Dining: "Кафе и доставка",
  Shopping: "Покупки",
  Health: "Здоровье",
  Entertainment: "Развлечения",
  Other: "Прочее",
};

const now = new Date();
date.value = [
  now.getFullYear(),
  String(now.getMonth() + 1).padStart(2, "0"),
  String(now.getDate()).padStart(2, "0"),
].join("-");

function detailRow(label, value, detail) {
  const row = document.createElement("li");
  const heading = document.createElement("span");
  heading.textContent = label;

  if (detail) {
    const subtitle = document.createElement("small");
    subtitle.textContent = detail;
    heading.append(subtitle);
  }

  const number = document.createElement("strong");
  number.textContent = currency.format(value);
  row.append(heading, number);
  return row;
}

function renderEntries() {
  entries.replaceChildren(...transactions.map((transaction, index) => {
    const row = detailRow(transaction.description, transaction.amount, dates.format(new Date(transaction.date)));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove";
    remove.textContent = "Удалить";
    remove.setAttribute("aria-label", `Удалить трату «${transaction.description}»`);
    remove.addEventListener("click", () => {
      transactions.splice(index, 1);
      renderEntries();
      (entries.children[index]?.querySelector("button")
        ?? entries.lastElementChild?.querySelector("button")
        ?? description).focus();
    });
    row.append(remove);
    return row;
  }));

  entriesPlaceholder.hidden = transactions.length > 0;
  analyzeButton.disabled = transactions.length === 0;
  report.hidden = true;
  reportPlaceholder.hidden = false;
  reportPlaceholder.textContent = "После анализа здесь появятся категории и суммы.";
  error.hidden = true;
}

for (const input of [description, amount]) {
  input.addEventListener("input", () => input.setCustomValidity(""));
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const label = description.value.trim();
  const enteredAmount = amount.value.trim();
  const value = Number(enteredAmount.replace(",", "."));

  if (!label) {
    description.setCustomValidity("Введите описание траты.");
    description.reportValidity();
    return;
  }

  if (!/^(?:\d+(?:[.,]\d{1,2})?|[.,]\d{1,2})$/.test(enteredAmount)
      || value <= 0 || !Number.isSafeInteger(Math.round(value * 100))) {
    amount.setCustomValidity("Введите положительную сумму с точностью до цента.");
    amount.reportValidity();
    return;
  }

  transactions.push({ date: date.value, description: label, amount: value });
  description.value = "";
  amount.value = "";
  renderEntries();
  description.focus();
});

function renderReport(result) {
  document.querySelector("#total").textContent = currency.format(result.total);
  document.querySelector("#by-category").replaceChildren(
    ...result.by_category.map(({ category, amount }) => detailRow(categories[category] ?? category, amount)),
  );
  document.querySelector("#by-week").replaceChildren(
    ...result.by_week.map(({ week, amount }) => detailRow(`Неделя ${week}`, amount)),
  );
  document.querySelector("#top-transactions").replaceChildren(
    ...result.top_transactions.map(({ date, description, amount, category }) =>
      detailRow(description, amount, `${dates.format(new Date(date))} · ${categories[category] ?? category}`),
    ),
  );
  reportPlaceholder.hidden = true;
  report.hidden = false;
}

analyzeButton.addEventListener("click", async () => {
  controls.disabled = true;
  analyzeButton.textContent = "Анализируем…";
  error.hidden = true;

  try {
    const response = await fetch("/api/analyze-transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions }),
    });
    const result = await response.json();
    if (!response.ok) {
      error.textContent = result.error || "Не удалось проанализировать траты.";
      error.hidden = false;
      return;
    }
    renderReport(result);
  } catch {
    error.textContent = "Не удалось получить отчёт. Проверьте, что локальный сервер запущен.";
    error.hidden = false;
  } finally {
    controls.disabled = false;
    analyzeButton.textContent = "Проанализировать";
  }
});
