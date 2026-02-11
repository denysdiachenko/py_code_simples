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

  const file = fileInput.files[0];
  if (!file) {
    showResult("error", "Please choose a PDF file.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const submitButton = form.querySelector("button");
  submitButton.disabled = true;
  showResult("success", "Uploading and analyzing...");

  try {
    const response = await fetch("/api/upload-invoice", {
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
      `Success: ${data.message}\n\nFile: ${data.filename}\nValidation: ${JSON.stringify(
        data.validation,
        null,
        2,
      )}\n\nAI (mock): ${JSON.stringify(data.ai_analysis, null, 2)}`,
    );
  } catch (error) {
    showResult("error", `Network error: ${error.message}`);
  } finally {
    submitButton.disabled = false;
  }
});
