chrome.action.onClicked.addListener((tab) => {
  if (tab.url.includes('scholar.google.com')) {
    chrome.tabs.sendMessage(tab.id, {action: 'startSummarization'});
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'updateProgress') {
    chrome.runtime.sendMessage(request);
  }
});