chrome.action.onClicked.addListener((tab) => {
  if (tab.url.includes('scholar.google.com')) {
    chrome.tabs.sendMessage(tab.id, {action: "startSummarization"});
  }
});