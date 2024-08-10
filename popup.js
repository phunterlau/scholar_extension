document.addEventListener('DOMContentLoaded', function() {
    const message = document.getElementById('message');
    message.textContent = "Click the red panda icon next to the Google Scholar search box to start summarizing. The icon will animate while summarizing is in progress.";

    // Fetch and display the user's unique ID
    chrome.storage.sync.get('extensionUniqueId', function(result) {
        const userIdElement = document.getElementById('userId');
        if (result.extensionUniqueId) {
            userIdElement.textContent = `My token: ${result.extensionUniqueId}`;
        } else {
            userIdElement.textContent = "My token: Not found";
        }
    });
});