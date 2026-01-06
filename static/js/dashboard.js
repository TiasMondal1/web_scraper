let priceChart = null;

// Load dashboard stats
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        const stats = await response.json();
        
        document.getElementById('total-products').textContent = stats.total_products;
        document.getElementById('total-price-points').textContent = stats.total_price_points;
        document.getElementById('products-drops').textContent = stats.products_with_drops;
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Load products
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        const products = await response.json();
        
        const productsList = document.getElementById('products-list');
        productsList.innerHTML = '';
        
        if (products.length === 0) {
            productsList.innerHTML = '<div class="col-12 text-center"><p>No products tracked yet. Add one to get started!</p></div>';
            return;
        }
        
        products.forEach(product => {
            const card = createProductCard(product);
            productsList.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('products-list').innerHTML = '<div class="col-12 text-center text-danger"><p>Error loading products</p></div>';
    }
}

// Create product card
function createProductCard(product) {
    const col = document.createElement('div');
    col.className = 'col-md-4 mb-3';
    
    const latestPrice = product.latest_price || 0;
    const stats = product.stats || {};
    const priceChange = stats.price_change_percent || 0;
    const priceChangeClass = priceChange < 0 ? 'price-drop' : priceChange > 0 ? 'price-rise' : '';
    
    col.innerHTML = `
        <div class="card product-card" onclick="showProductDetails(${product.id}, '${product.name.replace(/'/g, "\\'")}')">
            <div class="card-body">
                <h5 class="card-title">${escapeHtml(product.name)}</h5>
                <p class="price-tag">₹${latestPrice.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                ${priceChange !== 0 ? `<p class="price-change ${priceChangeClass}">${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}%</p>` : ''}
                <p class="text-muted small">Updated: ${new Date(product.updated_at).toLocaleString()}</p>
                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteProduct(${product.id}, '${product.name.replace(/'/g, "\\'")}')">Delete</button>
            </div>
        </div>
    `;
    
    return col;
}

// Show product details
async function showProductDetails(productId, productName) {
    document.getElementById('productDetailsTitle').textContent = productName;
    
    try {
        // Load price history
        const historyResponse = await fetch(`/api/products/${productId}/history`);
        const historyData = await historyResponse.json();
        
        // Load stats
        const statsResponse = await fetch(`/api/products/${productId}/stats`);
        const stats = await statsResponse.json();
        
        // Create chart
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        if (priceChart) {
            priceChart.destroy();
        }
        
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: historyData.labels || [],
                datasets: [{
                    label: 'Price (₹)',
                    data: historyData.data || [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    },
                    title: {
                        display: true,
                        text: 'Price History'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
        
        // Display stats
        const statsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Average Price:</strong> ₹${(stats.avg_price || 0).toFixed(2)}</p>
                    <p><strong>Minimum Price:</strong> ₹${(stats.min_price || 0).toFixed(2)}</p>
                    <p><strong>Maximum Price:</strong> ₹${(stats.max_price || 0).toFixed(2)}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Price Records:</strong> ${stats.count || 0}</p>
                    <p><strong>Standard Deviation:</strong> ₹${(stats.std_price || 0).toFixed(2)}</p>
                    <p><strong>Price Change:</strong> ${((stats.price_change_percent || 0) > 0 ? '+' : '')}${(stats.price_change_percent || 0).toFixed(2)}%</p>
                </div>
            </div>
        `;
        document.getElementById('productStats').innerHTML = statsHtml;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('productDetailsModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading product details:', error);
        alert('Error loading product details');
    }
}

// Add product
async function addProduct() {
    const name = document.getElementById('productName').value;
    const url = document.getElementById('productUrl').value;
    
    if (!name || !url) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch('/api/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, url })
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
            modal.hide();
            document.getElementById('addProductForm').reset();
            loadProducts();
            loadDashboardStats();
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error adding product:', error);
        alert('Error adding product');
    }
}

// Delete product
async function deleteProduct(productId, productName) {
    if (!confirm(`Are you sure you want to delete "${productName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadProducts();
            loadDashboardStats();
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        alert('Error deleting product');
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
    loadDashboardStats();
    
    // Refresh every 30 seconds
    setInterval(() => {
        loadProducts();
        loadDashboardStats();
    }, 30000);
});




