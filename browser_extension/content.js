// Content script for Price Tracker extension
// This script runs on all web pages

(function() {
    'use strict';
    
    // Detect if we're on a supported e-commerce site
    const hostname = window.location.hostname.toLowerCase();
    const supportedSites = ['amazon', 'flipkart', 'snapdeal', 'myntra', 'nykaa', 'ebay'];
    const isSupportedSite = supportedSites.some(site => hostname.includes(site));
    
    if (isSupportedSite) {
        // Add visual indicator that extension is active
        const indicator = document.createElement('div');
        indicator.id = 'price-tracker-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: #4CAF50;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 10000;
            font-family: Arial, sans-serif;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;
        indicator.textContent = 'Price Tracker Active';
        document.body.appendChild(indicator);
        
        // Remove indicator after 3 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        }, 3000);
    }
})();





