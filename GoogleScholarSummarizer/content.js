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
    const summaryDiv = document.createElement('div');
    summaryDiv.id = 'gs-summarizer-overall';
    summaryDiv.innerHTML = `<h2>Overall Summary</h2><p>${overallSummary}</p>`;
    document.body.insertBefore(summaryDiv, document.body.firstChild);
  
    const articles = document.querySelectorAll('.gs_r');
    articles.forEach((article, index) => {
      if (summaries[index]) {
        const summaryP = document.createElement('p');
        summaryP.className = 'gs-summarizer-individual';
        summaryP.textContent = summaries[index];
        article.appendChild(summaryP);
      }
    });
  }
  
  processSearchResults();