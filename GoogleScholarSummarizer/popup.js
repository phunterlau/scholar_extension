let totalSummaries = 0;
let completedSummaries = 0;

document.getElementById('startButton').addEventListener('click', function() {
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    chrome.tabs.sendMessage(tabs[0].id, {action: 'startSummarization'});
    document.getElementById('startButton').style.display = 'none';
    document.getElementById('message').textContent = 'Summarization started. Please wait...';
  });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showStartMessage') {
    document.getElementById('message').textContent = 
      "Your scholarly red panda has started producing the summary. Please be patient!";
    totalSummaries = request.total;
    document.getElementById('progressContainer').style.display = 'block';
    updateProgress(0);
  } else if (request.action === 'updateProgress') {
    completedSummaries = request.completed;
    updateProgress(completedSummaries);
  }
});

function updateProgress(completed) {
  const progressBar = document.getElementById('progressBar');
  const percentage = Math.round((completed / totalSummaries) * 100);
  progressBar.style.width = percentage + '%';
  progressBar.textContent = percentage + '%';
  
  document.getElementById('message').textContent = 
    `Summarizing: ${completed} of ${totalSummaries} articles complete`;
}