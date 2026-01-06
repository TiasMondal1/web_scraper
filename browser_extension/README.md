# Price Tracker Browser Extension

A Chrome/Firefox browser extension for one-click price tracking.

## Installation

### Chrome/Edge

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `browser_extension` folder
5. The extension should now appear in your extensions list

### Firefox

1. Open Firefox and navigate to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select the `manifest.json` file from the `browser_extension` folder

## Usage

1. Navigate to a product page on a supported e-commerce site (Amazon, Flipkart, etc.)
2. Click the extension icon in your browser toolbar
3. Enter a product name (auto-filled from page title)
4. Set the API URL (default: http://localhost:5001)
5. Click "Track This Product"
6. The product will be added to your price tracker

## Configuration

- **API URL**: Set the URL where your price tracker API is running (default: http://localhost:5001)
- The API URL is saved and will be remembered for future uses

## Supported Sites

- Amazon
- Flipkart
- Snapdeal
- Myntra
- Nykaa
- eBay

## Notes

- Make sure the price tracker API is running before using the extension
- The extension communicates with the REST API to add products
- Product name and URL are extracted from the current page





