// DOM Elements
const fileInput = document.getElementById("fileInput");
const uploadArea = document.getElementById("uploadArea");
const processBtn = document.getElementById("processBtn");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const fileStatus = document.getElementById("fileStatus");
const loadingStatus = document.getElementById("loadingStatus");
const loadingSpinner = document.getElementById("loadingSpinner");
const systemStatus = document.getElementById("systemStatus");
const statusText = document.getElementById("statusText");
const questionInput = document.getElementById("questionInput");
const chatMessages = document.getElementById("chatMessages");
const qaContainer = document.getElementById("qaContainer");
const noBookMessage = document.getElementById("noBookMessage");
const sourcesSection = document.getElementById("sourcesSection");
const sourcesList = document.getElementById("sourcesList");

let selectedFile = null;
let isProcessing = false;
let uploadedBooks = [];
let currentPdfFile = null;
let currentPdfPage = 1;
let currentPdfTotalPages = 0;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  checkSystemStatus();
  setupUploadArea();
  // Load existing vector store on startup
  loadExistingStore();
  loadBooksList();
});

// Upload Area Events
function setupUploadArea() {
  uploadArea.addEventListener("click", () => fileInput.click());
}

function handleDragOver(event) {
  event.preventDefault();
  uploadArea.classList.add("dragover");
}

document.addEventListener("dragleave", () => {
  uploadArea.classList.remove("dragover");
});

function handleDrop(event) {
  event.preventDefault();
  uploadArea.classList.remove("dragover");

  const files = event.dataTransfer.files;
  if (files.length > 0) {
    handleFileSelect({ target: { files } });
  }
}

function handleFileSelect(event) {
  const files = event.target.files;
  if (files.length > 0) {
    selectedFile = files[0];

    // Validate file type
    if (!selectedFile.name.endsWith(".pdf")) {
      showStatus("Only PDF files are allowed", "error");
      return;
    }

    // Update UI
    fileName.textContent = selectedFile.name;
    fileInfo.classList.remove("hidden");
    processBtn.style.display = "block";
    fileStatus.textContent = "-";
    fileStatus.style.color = "#64748b";

    clearStatus();
  }
}

// Process File
async function processFile() {
  if (!selectedFile) {
    showStatus("No file selected", "error");
    return;
  }

  isProcessing = true;
  processBtn.disabled = true;

  // Calculate expected time based on file size (MB)
  const fileSizeMB = (selectedFile.size / (1024 * 1024)).toFixed(1);
  const estimatedSeconds = Math.max(45, Math.round(fileSizeMB * 12 + 20)); // ~12 seconds per MB + overhead
  const estimatedMinutes = (estimatedSeconds / 60).toFixed(1);

  // Show processing status immediately
  showStatus("⏳ Processing: Uploading PDF...", "processing");
  fileStatus.textContent = "⏳ Uploading...";
  fileStatus.style.color = "#f59e0b";
  showLoading(true, `Uploading PDF (${fileSizeMB} MB)...\nExpected time: ~${estimatedMinutes} minutes`);

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    fileStatus.textContent = "⏳ Processing with AI...";
    showStatus("⏳ Processing: Creating embeddings with AI...", "processing");
    showLoading(
      true,
      `Processing ${fileSizeMB} MB with Llama3.2...\nExpected time: ~${estimatedMinutes} minutes\n(Creating 1500-char chunks with embeddings)`,
    );

    const data = await response.json();

    if (data.success) {
      showStatus(
        `✓ Successfully processed ${selectedFile.name} (${data.chunks} chunks)`,
        "success",
      );
      fileStatus.textContent = "✓ Complete";
      fileStatus.style.color = "#10b981";

      // Store current PDF file for page viewing (use actual saved filename)
      currentPdfFile = data.filename || selectedFile.name;

      // Add book to list
      addBookToList(data.filename || selectedFile.name);

      // Enable Q&A
      qaContainer.style.display = "flex";
      noBookMessage.style.display = "none";
      questionInput.focus();

      // Clear chat
      chatMessages.innerHTML = "";
      addMessage(
        "bot",
        "👋 Ready! I've indexed the document. You can add more documents or start asking questions!",
      );

      // Reset file selection
      selectedFile = null;
      fileInput.value = "";
      processBtn.style.display = "none";
      fileInfo.classList.add("hidden");

      // Update status
      checkSystemStatus();
    } else {
      showStatus(`Error: ${data.error}`, "error");
      fileStatus.textContent = "✗ Error";
      fileStatus.style.color = "#ef4444";
    }
  } catch (error) {
    showStatus(`Upload failed: ${error.message}`, "error");
    fileStatus.textContent = "✗ Failed";
    fileStatus.style.color = "#ef4444";
  } finally {
    isProcessing = false;
    processBtn.disabled = false;
    showLoading(false);
  }
}

// Ask Question
async function askQuestion() {
  const question = questionInput.value.trim();

  if (!question) {
    return;
  }

  // Add user message
  addMessage("user", question);
  questionInput.value = "";

  // Disable input while processing
  questionInput.disabled = true;
  const sendBtn = document.querySelector(".btn-send");
  sendBtn.disabled = true;

  // Calculate expected time based on question length
  const wordCount = question.split(/\s+/).length;
  const baseTime = 12; // Base time for retrieval + setup
  const perWordTime = 0.8; // Additional time per word
  const estimatedSeconds = Math.round(baseTime + (wordCount * perWordTime));

  // Show thinking indicator with calculated time
  const thinkingMsg = addMessage("bot", `🤔 Thinking... (Expected: ~${estimatedSeconds} seconds)`);

  try {
    showLoading(true, "Reading The Document");

    const response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();

    // Remove thinking message
    if (thinkingMsg) {
      thinkingMsg.remove();
    }

    if (data.success) {
      // Add bot response
      addMessage("bot", data.answer);

      // Display sources
      if (data.sources && data.sources.length > 0) {
        displaySources(data.sources);
      }
    } else {
      addMessage("bot", `❌ Error: ${data.error}`);
    }
  } catch (error) {
    addMessage("bot", `❌ Failed to get response: ${error.message}`);
  } finally {
    questionInput.disabled = false;
    sendBtn.disabled = false;
    showLoading(false);
    questionInput.focus();
  }
}

// UI Helpers
function addMessage(type, content) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}-message`;

  const p = document.createElement("p");

  // For bot messages, format the content with markdown support
  if (type === "bot") {
    p.innerHTML = formatMessage(content);
    p.classList.add("formatted-message");
  } else {
    p.textContent = content;
  }

  messageDiv.appendChild(p);
  chatMessages.appendChild(messageDiv);

  // Auto scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return messageDiv;
}

function formatMessage(text) {
  // Escape HTML first to prevent injection
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold text: **text** -> <strong>text</strong>
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Headers: ## text -> <h4>text</h4>
  html = html.replace(/^## (.*?)$/gm, "<h4>$1</h4>");

  // Line breaks -> <br>
  html = html.replace(/\n/g, "<br>");

  // Bullet points: • text or - text
  html = html.replace(/^[•\-]\s+(.*?)(?=<br>|$)/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*?<\/li>)/s, "<ul>$1</ul>");

  // Numbered lists: 1. text, 2. text, etc
  html = html.replace(/^\d+\.\s+(.*?)(?=<br>|$)/gm, "<li>$1</li>");

  // Tables with pipe separators
  html = html.replace(/\|.*?\|/g, (match) => {
    const cells = match.split("|").filter((c) => c.trim());
    if (cells.length > 1) {
      const row = cells.map((c) => `<td>${c.trim()}</td>`).join("");
      return `<tr>${row}</tr>`;
    }
    return match;
  });

  // Wrap consecutive tr in table
  html = html.replace(
    /(<tr>.*?<\/tr>)/s,
    '<table class="message-table">$1</table>',
  );

  return html;
}

function displaySources(sources) {
  sourcesSection.style.display = "block";
  sourcesList.innerHTML = "";

  sources.forEach((source, index) => {
    const card = document.createElement("div");
    card.className = "source-card";

    const pageTag = document.createElement("div");
    pageTag.className = "source-page";
    pageTag.textContent = `Page ${source.page}`;
    pageTag.style.cursor = "pointer";
    pageTag.title = "Click to view this page in the book";

    // Make page clickable
    pageTag.onclick = (e) => {
      e.stopPropagation();
      if (currentPdfFile) {
        openPdfPage(currentPdfFile, parseInt(source.page));
      } else {
        alert("PDF file not found. Please upload a book again.");
      }
    };

    const content = document.createElement("div");
    content.className = "source-content";
    content.textContent = source.content;

    card.appendChild(pageTag);
    card.appendChild(content);
    sourcesList.appendChild(card);
  });
}

function showStatus(message, type) {
  loadingStatus.textContent = message;
  loadingStatus.className = `status-box ${type}`;
}

function clearStatus() {
  loadingStatus.classList.add("hidden");
}

function showLoading(show, message = "Processing...") {
  if (show) {
    document.querySelector("#loadingSpinner p").textContent = message;
    loadingSpinner.classList.remove("hidden");
  } else {
    loadingSpinner.classList.add("hidden");
  }
}

// Check System Status
async function checkSystemStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();

    if (data.qa_chain_ready) {
      statusText.innerHTML =
        '<span style="color: #10b981;">✓ System Ready</span>';
      qaContainer.style.display = "flex";
      noBookMessage.style.display = "none";
    } else {
      statusText.innerHTML =
        '<span style="color: #f59e0b;">⚠ Awaiting book upload</span>';
      qaContainer.style.display = "none";
      noBookMessage.style.display = "flex";
    }
  } catch (error) {
    statusText.innerHTML =
      '<span style="color: #ef4444;">✗ Connection error</span>';
  }
}

// Load Existing Vector Store
async function loadExistingStore() {
  try {
    const response = await fetch("/api/load-existing", { method: "POST" });
    const data = await response.json();
    if (data.success) {
      setTimeout(checkSystemStatus, 500);
    }
  } catch (error) {
    // Silent fail - vector store might not exist
  }
}

// Reset System
async function resetSystem() {
  if (
    !confirm(
      "Are you sure? This will clear the uploaded book and all vector data.",
    )
  ) {
    return;
  }

  showLoading(true, "Resetting system...");

  try {
    const response = await fetch("/api/reset", {
      method: "POST",
    });

    const data = await response.json();

    if (data.success) {
      // Reset UI
      selectedFile = null;
      fileInput.value = "";
      fileInfo.classList.add("hidden");
      processBtn.style.display = "none";
      qaContainer.style.display = "none";
      noBookMessage.style.display = "flex";
      sourcesSection.style.display = "none";
      chatMessages.innerHTML = "";
      questionInput.value = "";

      // Clear books list
      uploadedBooks = [];
      updateBooksList();
      saveBooksList();

      showStatus("✓ System reset - All books cleared", "success");
      checkSystemStatus();
    } else {
      showStatus(`Error: ${data.error}`, "error");
    }
  } catch (error) {
    showStatus(`Reset failed: ${error.message}`, "error");
  } finally {
    showLoading(false);
  }
}

// Keyboard Shortcuts
function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    askQuestion();
  }
}

// Multiple Books Support
function toggleAddBook() {
  if (selectedFile) {
    // If a file is selected, show it's ready to add
    alert('Click "Read The PDF" to add this document to the collection');
  } else {
    // If no file selected, open file picker
    fileInput.click();
  }
}

function addBookToList(bookName) {
  if (!uploadedBooks.includes(bookName)) {
    uploadedBooks.push(bookName);
    updateBooksList();
    saveBooksList();
  }
}

function removeBookFromList(bookName) {
  uploadedBooks = uploadedBooks.filter((b) => b !== bookName);
  updateBooksList();
  saveBooksList();
}

function updateBooksList() {
  const booksList = document.getElementById("booksList");
  const booksContainer = document.getElementById("booksContainer");

  if (uploadedBooks.length > 0) {
    booksList.classList.remove("hidden");
    booksContainer.innerHTML = uploadedBooks
      .map(
        (book) => `
            <div class="book-item">
                <div class="book-item-name">
                    <span>${book}</span>
                </div>
                <button class="book-item-remove" onclick="removeBookFromList('${book}')">Remove</button>
            </div>
        `,
      )
      .join("");
  } else {
    booksList.classList.add("hidden");
  }
}

function saveBooksList() {
  localStorage.setItem("uploadedBooks", JSON.stringify(uploadedBooks));
}

function loadBooksList() {
  try {
    const saved = localStorage.getItem("uploadedBooks");
    if (saved) {
      uploadedBooks = JSON.parse(saved);
      updateBooksList();
    }
  } catch (e) {
    console.log("No saved books list");
  }
}

// PDF Display Functions
function openPdfPage(filename, pageNum) {
  const modal = document.getElementById("pdfModal");
  const overlay = document.getElementById("pdfOverlay");
  const container = document.getElementById("pdfContainer");
  const title = document.getElementById("pdfModalTitle");

  // Store current PDF info for navigation
  currentPdfFile = filename;
  currentPdfPage = pageNum;

  title.textContent = `${filename} - Loading...`;
  modal.classList.remove("hidden");
  overlay.classList.remove("hidden");

  // Load and display PDF
  const pdfUrl = `/api/get-pdf/${encodeURIComponent(filename)}`;
  loadAndDisplayPdfPage(pdfUrl, pageNum, container, title);
}

function closePdfModal() {
  const modal = document.getElementById("pdfModal");
  const overlay = document.getElementById("pdfOverlay");
  const container = document.getElementById("pdfContainer");

  modal.classList.add("hidden");
  overlay.classList.add("hidden");
  container.innerHTML = "";
  currentPdfPage = 1;
  currentPdfTotalPages = 0;
}

function goToPreviousPage() {
  if (currentPdfPage > 1) {
    currentPdfPage--;
    const container = document.getElementById("pdfContainer");
    const title = document.getElementById("pdfModalTitle");
    const pdfUrl = `/api/get-pdf/${encodeURIComponent(currentPdfFile)}`;
    loadAndDisplayPdfPage(pdfUrl, currentPdfPage, container, title);
  }
}

function goToNextPage() {
  if (currentPdfPage < currentPdfTotalPages) {
    currentPdfPage++;
    const container = document.getElementById("pdfContainer");
    const title = document.getElementById("pdfModalTitle");
    const pdfUrl = `/api/get-pdf/${encodeURIComponent(currentPdfFile)}`;
    loadAndDisplayPdfPage(pdfUrl, currentPdfPage, container, title);
  }
}

function updatePdfNavigationButtons() {
  const prevBtn = document.getElementById("pdfPrevBtn");
  const nextBtn = document.getElementById("pdfNextBtn");

  if (prevBtn) {
    prevBtn.disabled = currentPdfPage <= 1;
    prevBtn.style.opacity = currentPdfPage <= 1 ? "0.5" : "1";
    prevBtn.style.cursor = currentPdfPage <= 1 ? "not-allowed" : "pointer";
  }

  if (nextBtn) {
    nextBtn.disabled = currentPdfPage >= currentPdfTotalPages;
    nextBtn.style.opacity =
      currentPdfPage >= currentPdfTotalPages ? "0.5" : "1";
    nextBtn.style.cursor =
      currentPdfPage >= currentPdfTotalPages ? "not-allowed" : "pointer";
  }
}

async function loadAndDisplayPdfPage(pdfUrl, pageNum, container, title) {
  try {
    // Show loading indicator
    container.innerHTML = '<p style="color: #06b6d4; text-align: center; padding: 40px;">Loading Page...</p>';

    const pdf = await pdfjsLib.getDocument(pdfUrl).promise;

    // Store total pages for navigation
    currentPdfTotalPages = pdf.numPages;
    currentPdfPage = pageNum;

    if (pageNum > pdf.numPages || pageNum < 1) {
      container.innerHTML = `<p style="color: #ef4444;">Page ${pageNum} not found. This PDF has ${pdf.numPages} pages.</p>`;
      return;
    }

    const page = await pdf.getPage(pageNum);
    const scale = 1.2;  // Reduced scale for faster rendering
    const viewport = page.getViewport({ scale });

    // Create canvas
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    // Render page to canvas
    const context = canvas.getContext("2d");
    await page.render({
      canvasContext: context,
      viewport: viewport,
    }).promise;

    // Clear and add canvas to container
    container.innerHTML = "";
    container.appendChild(canvas);

    // Update title and page info
    if (title) {
      title.textContent = `${currentPdfFile} - Page ${pageNum} of ${pdf.numPages}`;
    }
    document.getElementById("pdfPageInfo").textContent =
      `Page ${pageNum} of ${pdf.numPages}`;

    // Update navigation buttons
    updatePdfNavigationButtons();
  } catch (error) {
    container.innerHTML = `<p style="color: #ef4444;">Error loading PDF: ${error.message}</p>`;
    console.error("PDF loading error:", error);
  }
}
