let isSummarizationInProgress = false;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkSummarizationStatus') {
    if (isSummarizationInProgress) {
      chrome.runtime.sendMessage({action: 'showStartMessage'});
    }
  }
  // ... existing message handlers ...
});

async function processSearchResults() {
  isSummarizationInProgress = true;
  chrome.runtime.sendMessage({action: 'showStartMessage'});
  
  // ... existing code to fetch and process results ...

  isSummarizationInProgress = false;
}

async function getPageContent(url) {
    try {
      const response = await fetch(url);
      return await response.text();
    } catch (error) {
      console.error(`Error fetching ${url}:`, error);
      return '';
    }
  }
  
  async function processSearchResults() {
    const articles = document.querySelectorAll('.gs_r');
    const contents = [];
  
    for (let article of articles) {
      const link = article.querySelector('.gs_rt a')?.href;
      if (link) {
        const content = await getPageContent(link);
        contents.push({ link, content });
      }
    }
  
    const searchQuery = document.querySelector('#gs_hdr_tsi').value;
    
    chrome.runtime.sendMessage({
      action: 'summarize',
      data: { contents, searchQuery }
    }, response => {
      if (response.success) {
        displaySummaries(response.summaries, response.overallSummary);
      } else {
        console.error('Error summarizing:', response.error);
      }
    });
  }
  
  function displaySummaries(summaries, overallSummary) {
    // Style for the overall summary
    const overallSummaryStyle = `
      border: 2px solid #4285F4;
      border-radius: 8px;
      padding: 15px;
      margin: 15px 0;
      background-color: #F8F9FA;
      font-family: Arial, sans-serif;
    `;
  
    // Style for individual summaries
    const individualSummaryStyle = `
      border: 1px dashed #4285F4;
      border-radius: 4px;
      padding: 10px;
      margin: 10px 0;
      background-color: #E8F0FE;
      font-family: Arial, sans-serif;
    `;
  
    // Create and insert overall summary
    const summaryDiv = document.createElement('div');
    summaryDiv.id = 'gs-summarizer-overall';
    summaryDiv.style.cssText = overallSummaryStyle;
    
    // Apply bold styling to markdown bold text
    const formattedOverallSummary = overallSummary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    summaryDiv.innerHTML = `<h2 style="color: #4285F4; margin-top: 0;">Overall Summary</h2>${formattedOverallSummary}`;
    
    // Insert after the search bar
    const searchBar = document.querySelector('#gs_hdr');
    searchBar.parentNode.insertBefore(summaryDiv, searchBar.nextSibling);
  
    // Add individual summaries to each article
    const articles = document.querySelectorAll('.gs_r');
    articles.forEach((article, index) => {
      if (summaries[index]) {
        const summaryP = document.createElement('div');
        summaryP.className = 'gs-summarizer-individual';
        summaryP.style.cssText = individualSummaryStyle;
        
        // Apply bold styling to markdown bold text
        const formattedSummary = summaries[index].replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        summaryP.innerHTML = formattedSummary;
        article.appendChild(summaryP);
      }
    });
  }
  
  processSearchResults();