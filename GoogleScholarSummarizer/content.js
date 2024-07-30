let isSummarizationInProgress = false;
let totalArticles = 0;
let completedArticles = 0;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'startSummarization') {
    if (!isSummarizationInProgress) {
      processSearchResults();
    }
  }
});

async function processSearchResults() {
  if (isSummarizationInProgress) return;
  
  isSummarizationInProgress = true;
  const articles = document.querySelectorAll('.gs_r');
  totalArticles = articles.length;
  completedArticles = 0;
  
  chrome.runtime.sendMessage({
    action: 'showStartMessage', 
    total: totalArticles
  });

  const contents = [];
  for (let article of articles) {
    const link = article.querySelector('.gs_rt a')?.href;
    if (link) {
      contents.push({ link: link });
    }
  }

  const searchQuery = document.querySelector('#gs_hdr_tsi').value;

  try {
    const response = await fetch('http://127.0.0.1:5000/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ contents, searchQuery })
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
            chrome.runtime.sendMessage({
              action: 'updateProgress',
              completed: completedArticles
            });
            displayIndividualSummary(data.index - 1, data.summary);
          } else if (data.overall_summary) {
            displayOverallSummary(data.overall_summary);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }

  isSummarizationInProgress = false;
}

function displayIndividualSummary(index, summary) {
  const articles = document.querySelectorAll('.gs_r');
  if (articles[index]) {
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'gs-summarizer-individual';
    summaryDiv.style.cssText = `
      border: 1px dashed #4285F4;
      border-radius: 4px;
      padding: 10px;
      margin: 10px 0;
      background-color: #E8F0FE;
      font-family: Arial, sans-serif;
    `;
    
    summaryDiv.textContent = summary;
    articles[index].appendChild(summaryDiv);
  }
}

function displayOverallSummary(summary) {
  const overallSummaryStyle = `
    border: 2px solid #4285F4;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
    background-color: #F8F9FA;
    font-family: Arial, sans-serif;
  `;

  const summaryDiv = document.createElement('div');
  summaryDiv.id = 'gs-summarizer-overall';
  summaryDiv.style.cssText = overallSummaryStyle;
  
  summaryDiv.innerHTML = `<h2 style="color: #4285F4; margin-top: 0;">Overall Summary</h2>${summary}`;
  
  const searchBar = document.querySelector('#gs_hdr');
  searchBar.parentNode.insertBefore(summaryDiv, searchBar.nextSibling);
}