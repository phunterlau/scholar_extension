chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'summarize') {
      summarizeContents(request.data)
        .then(result => sendResponse({ success: true, ...result }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true; // Indicates that the response is sent asynchronously
    }
  });

async function summarizeContents({ contents, searchQuery }) {
  const backendUrl = 'http://127.0.0.1:5000/summarize';

  const response = await fetch(backendUrl, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Origin': chrome.runtime.id
    },
    body: JSON.stringify({ contents, searchQuery })
  });

  if (!response.ok) {
    throw new Error('Failed to summarize contents');
  }

  return await response.json();
}