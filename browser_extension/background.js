// Background service worker for Price Tracker extension

chrome.runtime.onInstalled.addListener(() => {
    console.log('Price Tracker extension installed');
});

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getCurrentTab') {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            sendResponse({ url: tabs[0].url, title: tabs[0].title });
        });
        return true; // Keep message channel open for async response
    }
});




