let isSummarizationInProgress = false;
let totalArticles = 0;
let completedArticles = 0;
let downloadToken = '';

async function getValidToken() {
  let token = await new Promise((resolve) => {
    chrome.storage.sync.get(['userToken', 'extensionUniqueId'], function(result) {
      resolve({ token: result.userToken, uniqueId: result.extensionUniqueId });
    });
  });

  if (!token.token) {
    // No token, request a new one
    const response = await fetch('http://127.0.0.1:5000/get_token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ uniqueId: token.uniqueId }),
    });

    if (response.ok) {
      const data = await response.json();
      token.token = data.token;
      // Store the new token
      chrome.storage.sync.set({ 'userToken': token.token });
    } else {
      console.error('Failed to get token');
      return null;
    }
  }

  return token.token;
}

function addRedPandaIcon() {
  const searchForm = document.querySelector('#gs_hdr_frm');
  if (!searchForm) return;

  let redPandaContainer = document.getElementById('redPandaContainer');
  if (!redPandaContainer) {
    redPandaContainer = document.createElement('div');
    redPandaContainer.id = 'redPandaContainer';
    redPandaContainer.style.cssText = `
      width: 50px;
      height: 50px;
      position: absolute;
      right: -60px;
      top: 50%;
      transform: translateY(-50%);
      cursor: pointer;
    `;
    
    const staticIcon = document.createElement('img');
    staticIcon.id = 'redPandaStatic';
    staticIcon.src = chrome.runtime.getURL('images/red_panda_static.png');
    staticIcon.style.cssText = `
      width: 100%;
      height: 100%;
      display: block;
    `;

    const animatedIcon = document.createElement('img');
    animatedIcon.id = 'redPandaAnimated';
    animatedIcon.src = chrome.runtime.getURL('images/red_panda_animated.gif');
    animatedIcon.style.cssText = `
      width: 100%;
      height: 100%;
      display: none;
    `;

    redPandaContainer.appendChild(staticIcon);
    redPandaContainer.appendChild(animatedIcon);
    searchForm.style.position = 'relative';
    searchForm.appendChild(redPandaContainer);

    redPandaContainer.addEventListener('click', startSummarization);
  }
  return redPandaContainer;
}

async function startSummarization() {
  if (!isSummarizationInProgress) {
    const staticIcon = document.getElementById('redPandaStatic');
    const animatedIcon = document.getElementById('redPandaAnimated');
    if (staticIcon && animatedIcon) {
      staticIcon.style.display = 'none';
      animatedIcon.style.display = 'block';
    }
    
    // Show loading message
    displayLoadingMessage();
    
    await processSearchResults();
  }
}

function displayLoadingMessage() {
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
      position: relative;
    `;
    const resultsDiv = document.getElementById('gs_res_ccl');
    if (resultsDiv) {
      resultsDiv.insertBefore(overallSummaryDiv, resultsDiv.firstChild);
    }
  }

  overallSummaryDiv.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; flex-direction: column;">
      <div class="loading-spinner"></div>
      <p style="margin-top: 10px; font-size: 16px; color: #4285F4;">Collecting article content, please wait...</p>
    </div>
  `;

  // Add CSS for loading spinner
  const style = document.createElement('style');
  style.textContent = `
    .loading-spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #4285F4;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

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

  const userToken = await getValidToken();
  if (!userToken) {
    console.error('No valid token available');
    isSummarizationInProgress = false;
    return;
  }

  const articles = document.querySelectorAll('.gs_r.gs_or.gs_scl');
  totalArticles = articles.length;
  completedArticles = 0;
  
  addProgressBar();
  updateProgress(0);

  const contents = [];
  const links = [];
  for (let article of articles) {
    const link = article.querySelector('.gs_rt a')?.href;
    const title = article.querySelector('.gs_rt')?.textContent.trim();
    if (link && title) {
      contents.push({ link: link, title: title });
      links.push(link);
    }
  }

  const searchQuery = document.querySelector('#gs_hdr_tsi').value;
  const pageNumber = getPageNumber();

  try {
    const response = await fetch('http://127.0.0.1:5000/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userToken}`,
      },
      body: JSON.stringify({ contents, searchQuery, pageNumber }),
      mode: 'cors',
    });

    if (!response.ok) {
      console.error("Response not OK:", response.status, response.statusText);
      const errorText = await response.text();
      console.error("Error response:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

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
          console.log("Received data:", data);
          if (data.summary) {
            completedArticles++;
            updateProgress(completedArticles / totalArticles);
            displayIndividualSummary(data.index - 1, data.summary);
          } else if (data.overall_summary) {
            console.log("Received overall summary");
            displayOverallSummary(
              data.overall_summary, 
              data.followup_questions, 
              data.more_keywords,
              data.mind_map,
              links
            );
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
    // Display error message in the summary div
    displayErrorMessage("An error occurred while summarizing. Please try again.");
  } finally {
    isSummarizationInProgress = false;
    const staticIcon = document.getElementById('redPandaStatic');
    const animatedIcon = document.getElementById('redPandaAnimated');
    if (staticIcon && animatedIcon) {
      staticIcon.style.display = 'block';
      animatedIcon.style.display = 'none';
    }
  }
}

function displayErrorMessage(message) {
  let overallSummaryDiv = document.getElementById('gs-summarizer-overall');
  if (overallSummaryDiv) {
    overallSummaryDiv.innerHTML = `
      <div style="color: #D32F2F; font-size: 16px; text-align: center;">
        <p>${message}</p>
      </div>
    `;
  }
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

function renderHighlightedConcepts(text) {
  return text.replace(/\[\[(.*?)\]\]/g, (match, concept) => {
    const encodedConcept = encodeURIComponent(concept);
    return `<span class="highlighted-concept" onclick="window.open('https://scholar.google.com/scholar?q=${encodedConcept}', '_blank')">${concept}</span>`;
  });
}

function renderCitations(text, links) {
  console.log("Rendering citations. Text:", text);
  console.log("Links:", links);

  if (typeof text !== 'string') {
    console.error("Invalid text input for renderCitations. Expected string, got:", typeof text);
    return text;
  }

  if (!Array.isArray(links)) {
    console.error("Invalid links input for renderCitations. Expected array, got:", typeof links);
    return text;
  }

  const citationRegex = /\[(\d{1,2})\]/g;
  const hasCitations = citationRegex.test(text);

  if (!hasCitations) {
    console.log("No citation markers found in the text.");
    return text;
  }

  const renderedText = text.replace(citationRegex, (match, number) => {
    console.log("Citation match:", match);
    const index = parseInt(number) - 1;
    console.log(`Parsed index: ${index} from number: ${number}`);
    
    if (index >= 0 && index < links.length) {
      const link = links[index];
      console.log(`Creating link for index ${index}: ${link}`);
      return `<a href="${link}" target="_blank">[${number}]</a>`;
    }
    console.warn(`Invalid index ${index} for citation. links.length: ${links.length}`);
    return match;
  });

  console.log("Rendered text:", renderedText);
  return renderedText;
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
    summaryDiv.innerHTML = renderHighlightedConcepts(renderBoldText(summary.replace(/\n\n/g, '<br><br>')));
  }
}

function displayOverallSummary(summary, followupQuestions, moreKeywords, mindMap, links) {
  console.log("Displaying overall summary");
  console.log("Summary:", summary);
  console.log("Links:", links);

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
      position: relative;
    `;
    const resultsDiv = document.getElementById('gs_res_ccl');
    if (resultsDiv) {
      resultsDiv.insertBefore(overallSummaryDiv, resultsDiv.firstChild);
    }
  }
  
  const boldText = renderBoldText(summary);
  console.log("After bold rendering:", boldText);
  
  const highlightedText = renderHighlightedConcepts(boldText);
  console.log("After concept highlighting:", highlightedText);
  
  const processedSummary = renderCitations(highlightedText, links);
  console.log("After citation rendering:", processedSummary);

  let content = `
    <div id="summaryHeader" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      <h2 style="color: #4285F4; margin: 0; font-size: 18px;">Overall Summary</h2>
      <button id="foldButton" style="
        background-color: #4285F4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.3s;
      ">Fold</button>
    </div>
    <div id="summaryMainContent">
      <p style="font-size: 14px; line-height: 1.4;">${processedSummary.replace(/\n\n/g, '<br><br>')}</p>
    </div>
    <div id="summaryAdditionalContent" style="transition: max-height 0.5s ease-out; overflow: hidden;">
  `;

  if (mindMap && mindMap.central_topic) {
    content += `
      <h3 style="color: #4285F4; margin-top: 15px; font-size: 16px;">Mind Map</h3>
      <div class="mind-map" style="margin-top: 10px; font-size: 14px;">
        <ul style="list-style-type: none; padding-left: 0;">
          <li>
            <span style="font-weight: bold;">${mindMap.central_topic}</span>
            <ul style="list-style-type: none; padding-left: 20px;">
              ${mindMap.branches.map(branch => `
                <li>
                  <span style="font-weight: bold;">${branch.topic}</span>
                  <ul style="list-style-type: disc; padding-left: 20px;">
                    ${branch.details.map(detail => `<li>${detail}</li>`).join('')}
                  </ul>
                </li>
              `).join('')}
            </ul>
          </li>
        </ul>
      </div>
    `;
  }

  if (followupQuestions && followupQuestions.length > 0) {
    content += `
      <h3 style="color: #4285F4; margin-top: 15px; font-size: 16px;">Follow-up Questions</h3>
      <ul style="list-style-type: disc; padding-left: 20px; margin-top: 5px;">
        ${followupQuestions.map(q => `
          <li style="font-size: 14px; margin-bottom: 10px;">
            ${q.question}
            <div style="margin-top: 5px; font-size: 12px; color: #666;">
              Suggested keywords: ${q.keywords.join(', ')}
            </div>
          </li>
        `).join('')}
      </ul>
    `;
  }

  if (moreKeywords && moreKeywords.length > 0) {
    content += `
      <h3 style="color: #4285F4; margin-top: 15px; font-size: 16px;">More Keywords</h3>
      <p style="font-size: 14px; margin-top: 5px;">${moreKeywords.join(', ')}</p>
    `;
  }

  content += `</div>`; // Close summaryAdditionalContent div

  overallSummaryDiv.innerHTML = content;
  console.log("Overall summary content set");

  addDownloadButton();

  // Add fold/unfold functionality
  const foldButton = document.getElementById('foldButton');
  const summaryAdditionalContent = document.getElementById('summaryAdditionalContent');
  let isFolded = false;

  function toggleFold() {
    if (isFolded) {
      summaryAdditionalContent.style.maxHeight = summaryAdditionalContent.scrollHeight + "px";
      foldButton.textContent = 'Fold';
      isFolded = false;
    } else {
      summaryAdditionalContent.style.maxHeight = '0';
      foldButton.textContent = 'Unfold';
      isFolded = true;
    }
  }

  foldButton.addEventListener('click', toggleFold);
  
  // Hover effect for the button
  foldButton.addEventListener('mouseover', () => {
    foldButton.style.backgroundColor = '#3367D6';
  });
  foldButton.addEventListener('mouseout', () => {
    foldButton.style.backgroundColor = '#4285F4';
  });

  // Initially show everything (unfolded by default)
  summaryAdditionalContent.style.maxHeight = summaryAdditionalContent.scrollHeight + "px";
  foldButton.textContent = 'Fold';
}

const style = document.createElement('style');
style.textContent = `
  .highlighted-concept {
    border-bottom: 1px dotted #4285F4;
    cursor: pointer;
    transition: background-color 0.3s;
  }
  .highlighted-concept:hover {
    background-color: #E8F0FE;
  }
`;
document.head.appendChild(style);

function addDownloadButton() {
  let downloadButtonContainer = document.getElementById('gs-summarizer-download-container');
  if (!downloadButtonContainer) {
    downloadButtonContainer = document.createElement('div');
    downloadButtonContainer.id = 'gs-summarizer-download-container';
    downloadButtonContainer.style.cssText = `
      margin-top: 15px;
      text-align: left;
    `;

    let downloadButton = document.createElement('button');
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
    `;
    downloadButton.addEventListener('click', downloadMarkdown);
    
    downloadButtonContainer.appendChild(downloadButton);
    
    const overallSummaryDiv = document.getElementById('gs-summarizer-overall');
    if (overallSummaryDiv) {
      overallSummaryDiv.appendChild(downloadButtonContainer);
    }
  }
}

async function downloadMarkdown() {
  if (downloadToken) {
    const userToken = await getValidToken();
    if (!userToken) {
      console.error('No valid token available for download');
      return;
    }

    const downloadUrl = `http://127.0.0.1:5000/download_markdown/${downloadToken}`;
    fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${userToken}`
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      
      // Get the search query and page number
      const searchQuery = document.querySelector('#gs_hdr_tsi').value;
      const pageNumber = getPageNumber();
      
      // Create a filename based on the search query and page number
      const sanitizedQuery = searchQuery.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      const filename = `scholar_summary_${sanitizedQuery}_page${pageNumber}.md`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    })
    .catch(error => console.error('Error:', error));
  } else {
    console.error('Download token not available');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  addRedPandaIcon();
  addProgressBar();
});

window.addEventListener('load', () => {
  addRedPandaIcon();
  addProgressBar();
});