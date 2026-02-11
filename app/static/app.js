const form = document.getElementById("upload-form");
const fileInput = document.getElementById("pdf-file");
const resultEl = document.getElementById("result");

function showResult(type, content) {
  resultEl.classList.remove("hidden", "success", "error");
  resultEl.classList.add(type);
  resultEl.textContent = content;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const files = Array.from(fileInput.files || []);
  if (files.length === 0) {
    showResult("error", "Please choose at least one PDF file.");
    return;
  }

  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const submitButton = form.querySelector("button");
  submitButton.disabled = true;
  showResult("success", `Uploading and analyzing ${files.length} file(s)...`);

  try {
    const response = await fetch("/api/upload-invoices", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      showResult("error", `Error: ${data.detail || "unknown error"}`);
      return;
    }

    showResult(
      "success",
      `Success: ${data.message}\n\nSummary: ${JSON.stringify(
        data.summary,
        null,
        2,
      )}\n\nAnalyzed invoices: ${JSON.stringify(data.analyzed_invoices, null, 2)}\n\nInvalid files: ${JSON.stringify(
        data.invalid_files,
        null,
        2,
      )}`,
    );
  } catch (error) {
    showResult("error", `Network error: ${error.message}`);
  } finally {
    submitButton.disabled = false;
  }
});
