let isSummarizationInProgress = false;
let totalArticles = 0;
let completedArticles = 0;
let downloadToken = '';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "startSummarization") {
    processSearchResults();
  }
});

function addProgressBar() {
  const searchForm = document.querySelector('#gs_hdr_frm');
  if (!searchForm) return;

  let progressContainer = document.getElementById('summarizeProgressContainer');
  if (!progressContainer) {
    progressContainer = document.createElement('div');
    progressContainer.id = 'summarizeProgressContainer';
    progressContainer.style.cssText = `
      width: 100%;
      height: 20px;
      background-color: #f3f3f3;
      border-radius: 5px;
      margin-top: 10px;
      display: none;
    `;

    const progressBar = document.createElement('div');
    progressBar.id = 'summarizeProgressBar';
    progressBar.style.cssText = `
      width: 0%;
      height: 100%;
      background-color: #4285F4;
      border-radius: 5px;
      transition: width 0.3s;
    `;

    progressContainer.appendChild(progressBar);
    searchForm.parentNode.insertBefore(progressContainer, searchForm.nextSibling);
  }
}

async function processSearchResults() {
  if (isSummarizationInProgress) return;
  
  isSummarizationInProgress = true;
  const articles = document.querySelectorAll('.gs_r.gs_or.gs_scl');
  totalArticles = articles.length;
  completedArticles = 0;
  
  addProgressBar();
  updateProgress(0);

  const contents = [];
  for (let article of articles) {
    const link = article.querySelector('.gs_rt a')?.href;
    const title = article.querySelector('.gs_rt')?.textContent.trim();
    if (link && title) {
      contents.push({ link: link, title: title });
    }
  }

  const searchQuery = document.querySelector('#gs_hdr_tsi').value;
  const pageNumber = getPageNumber();

  try {
    const response = await fetch('http://127.0.0.1:5000/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'chrome-extension://loojlaeieeklhbpngckhcjhcdcobieln'
      },
      body: JSON.stringify({ contents, searchQuery, pageNumber }),
      credentials: 'include'
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.summary) {
            completedArticles++;
            updateProgress(completedArticles / totalArticles);
            displayIndividualSummary(data.index - 1, data.summary);
          } else if (data.overall_summary) {
            displayOverallSummary(data.overall_summary);
            if (data.token) {
              downloadToken = data.token;
              addDownloadButton();
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }

  isSummarizationInProgress = false;
}

function getPageNumber() {
  const startParam = new URLSearchParams(window.location.search).get('start');
  return startParam ? Math.floor(parseInt(startParam) / 10) + 1 : 1;
}

function updateProgress(progress) {
  const progressContainer = document.getElementById('summarizeProgressContainer');
  const progressBar = document.getElementById('summarizeProgressBar');
  if (progressContainer && progressBar) {
    progressContainer.style.display = 'block';
    progressBar.style.width = `${Math.round(progress * 100)}%`;
  }
}

function renderBoldText(text) {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function displayIndividualSummary(index, summary) {
  const articles = document.querySelectorAll('.gs_r.gs_or.gs_scl');
  if (articles[index]) {
    let summaryDiv = articles[index].querySelector('.gs-summarizer-individual');
    if (!summaryDiv) {
      summaryDiv = document.createElement('div');
      summaryDiv.className = 'gs-summarizer-individual';
      summaryDiv.style.cssText = `
        border: 1px dashed #4285F4;
        border-radius: 4px;
        padding: 10px;
        margin: 10px 0;
        background-color: #E8F0FE;
        font-family: Arial, sans-serif;
      `;
      articles[index].appendChild(summaryDiv);
    }
    summaryDiv.innerHTML = renderBoldText(summary.replace(/\n\n/g, '<br><br>'));
  }
}

function displayOverallSummary(summary) {
  let overallSummaryDiv = document.getElementById('gs-summarizer-overall');
  if (!overallSummaryDiv) {
    overallSummaryDiv = document.createElement('div');
    overallSummaryDiv.id = 'gs-summarizer-overall';
    overallSummaryDiv.style.cssText = `
      border: 2px solid #4285F4;
      border-radius: 8px;
      padding: 15px;
      margin: 15px 0;
      background-color: #F8F9FA;
      font-family: Arial, sans-serif;
      box-sizing: border-box;
      width: 100%;
    `;
    const resultsDiv = document.getElementById('gs_res_ccl');
    if (resultsDiv) {
      resultsDiv.insertBefore(overallSummaryDiv, resultsDiv.firstChild);
    }
  }
  
  overallSummaryDiv.innerHTML = `
    <h2 style="color: #4285F4; margin-top: 0;">Overall Summary</h2>
    ${renderBoldText(summary.replace(/\n\n/g, '<br><br>'))}
  `;
}

function addDownloadButton() {
  let downloadButton = document.getElementById('gs-summarizer-download');
  if (!downloadButton) {
    downloadButton = document.createElement('button');
    downloadButton.id = 'gs-summarizer-download';
    downloadButton.textContent = 'Download Summary';
    downloadButton.style.cssText = `
      background-color: #4285F4;
      color: white;
      border: none;
      padding: 10px 15px;
      border-radius: 4px;
      cursor: pointer;
      font-family: Arial, sans-serif;
      margin-top: 10px;
    `;
    downloadButton.addEventListener('click', downloadMarkdown);
    
    const overallSummaryDiv = document.getElementById('gs-summarizer-overall');
    if (overallSummaryDiv) {
      overallSummaryDiv.appendChild(downloadButton);
    }
  }
}

function downloadMarkdown() {
  if (downloadToken) {
    const downloadUrl = `http://127.0.0.1:5000/download_markdown/${downloadToken}`;
    window.open(downloadUrl, '_blank');
  } else {
    console.error('Download token not available');
  }
}

// Add progress bar when the page loads
document.addEventListener('DOMContentLoaded', addProgressBar);
window.addEventListener('load', addProgressBar);