chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showStartMessage') {
      document.getElementById('message').textContent = 
        "Your scholarly red panda has started producing the summary. Please be patient!";
      document.getElementById('message').style.display = 'block';
    }
  });
  
  // Send a message to check if summarization is in progress
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    chrome.tabs.sendMessage(tabs[0].id, {action: 'checkSummarizationStatus'});
  });