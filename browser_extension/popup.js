// Popup script for Price Tracker extension

document.addEventListener('DOMContentLoaded', async () => {
    const trackButton = document.getElementById('trackButton');
    const productNameInput = document.getElementById('productName');
    const apiUrlInput = document.getElementById('apiUrl');
    const statusDiv = document.getElementById('status');
    
    // Load saved API URL
    const savedApiUrl = await chrome.storage.local.get('apiUrl');
    if (savedApiUrl.apiUrl) {
        apiUrlInput.value = savedApiUrl.apiUrl;
    }
    
    // Get current tab URL
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentUrl = tab.url;
    
    // Auto-fill product name from page title
    if (tab.title) {
        productNameInput.value = tab.title.substring(0, 100);
    }
    
    // Show status message
    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = type;
        statusDiv.style.display = 'block';
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
    
    // Track product
    trackButton.addEventListener('click', async () => {
        const apiUrl = apiUrlInput.value.trim();
        const productName = productNameInput.value.trim();
        
        if (!apiUrl) {
            showStatus('Please enter API URL', 'error');
            return;
        }
        
        if (!productName) {
            showStatus('Please enter product name', 'error');
            return;
        }
        
        if (!currentUrl) {
            showStatus('Could not get current page URL', 'error');
            return;
        }
        
        // Save API URL
        await chrome.storage.local.set({ apiUrl: apiUrl });
        
        trackButton.disabled = true;
        trackButton.textContent = 'Adding...';
        
        try {
            const response = await fetch(`${apiUrl}/api/products`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: productName,
                    url: currentUrl
                })
            });
            
            if (response.ok) {
                showStatus('Product added successfully!', 'success');
                productNameInput.value = '';
                
                // Close popup after 1 second
                setTimeout(() => {
                    window.close();
                }, 1000);
            } else {
                const error = await response.json();
                showStatus(`Error: ${error.error || 'Failed to add product'}`, 'error');
            }
        } catch (error) {
            showStatus(`Error: ${error.message}. Make sure the API is running.`, 'error');
        } finally {
            trackButton.disabled = false;
            trackButton.textContent = 'Track This Product';
        }
    });
});




