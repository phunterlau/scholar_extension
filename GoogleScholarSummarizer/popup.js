
document.getElementById('summarize').addEventListener('click', () => {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, {action: 'summarizeResults'});
        document.getElementById('status').innerText = 'Summarizing...';
    });
});
