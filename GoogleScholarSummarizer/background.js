// Function to generate a unique ID for the extension
function generateUniqueId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// When the extension is installed or updated
chrome.runtime.onInstalled.addListener(() => {
  const uniqueId = generateUniqueId();
  chrome.storage.sync.set({ 'extensionUniqueId': uniqueId }, function() {
    console.log('Unique ID is set to ' + uniqueId);
  });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getToken") {
    chrome.storage.sync.get(['userToken', 'extensionUniqueId'], function(result) {
      sendResponse({token: result.userToken, uniqueId: result.extensionUniqueId});
    });
    return true;  // Will respond asynchronously
  }
});