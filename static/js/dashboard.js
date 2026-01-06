let priceChart = null;
let allProducts = [];
let currentView = 'grid';

// Load dashboard stats
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        
        if (!response.ok) {
            console.error(`Failed to load dashboard stats: ${response.status}`);
            return;
        }
        
        const stats = await response.json();
        
        document.getElementById('total-products').textContent = stats.total_products || 0;
        document.getElementById('total-price-points').textContent = stats.total_price_points || 0;
        document.getElementById('products-drops').textContent = stats.products_with_drops || 0;
        
        // Update last updated time
        const now = new Date();
        document.getElementById('last-updated').textContent = now.toLocaleTimeString();
        
        // Update product count badge
        document.getElementById('product-count').textContent = stats.total_products || 0;
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Load products
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        allProducts = await response.json();
        displayProducts(allProducts);
        updateBestDeals(allProducts);
        updateRecentActivity(allProducts);
    } catch (error) {
        console.error('Error loading products:', error);
        const productsList = document.getElementById('products-list');
        if (productsList) {
            productsList.innerHTML = `
                <div class="col-12 text-center text-danger py-5">
                    <i class="bi bi-exclamation-triangle" style="font-size: 3rem;"></i>
                    <p class="mt-3">Error loading products: ${error.message}</p>
                </div>
            `;
        }
    }
}

// Display products
function displayProducts(products) {
    const productsList = document.getElementById('products-list');
    productsList.innerHTML = '';
    
    if (!products || products.length === 0) {
        productsList.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-inbox" style="font-size: 4rem; color: #9ca3af;"></i>
                <h5 class="mt-3 text-muted">No products tracked yet</h5>
                <p class="text-muted">Add your first product to start tracking prices!</p>
                <button class="btn btn-primary mt-3" data-bs-toggle="modal" data-bs-target="#addProductModal">
                    <i class="bi bi-plus-circle"></i> Add Product
                </button>
            </div>
        `;
        return;
    }
    
    products.forEach(product => {
        const card = createProductCard(product);
        productsList.appendChild(card);
    });
}

// Create product card
function createProductCard(product) {
    const col = document.createElement('div');
    col.className = currentView === 'grid' ? 'col-md-4 col-sm-6 mb-3' : 'col-12 mb-3';
    
    const latestPrice = product.latest_price || 0;
    const stats = product.stats || {};
    const priceChange = stats.price_change_percent || 0;
    
    let priceChangeClass = 'price-neutral';
    let priceChangeIcon = 'bi-dash-circle';
    let priceChangeText = 'No change';
    
    if (priceChange < 0) {
        priceChangeClass = 'price-drop';
        priceChangeIcon = 'bi-arrow-down-circle';
        priceChangeText = `${Math.abs(priceChange).toFixed(2)}%`;
    } else if (priceChange > 0) {
        priceChangeClass = 'price-rise';
        priceChangeIcon = 'bi-arrow-up-circle';
        priceChangeText = `+${priceChange.toFixed(2)}%`;
    }
    
    const updatedDate = new Date(product.updated_at);
    const timeAgo = getTimeAgo(updatedDate);
    
    const cardClass = currentView === 'grid' ? 'product-card' : 'product-card list-view';
    
    // Different HTML structure for list view
    if (currentView === 'list') {
        col.innerHTML = `
            <div class="${cardClass}" onclick="showProductDetails(${product.id}, '${escapeHtml(product.name).replace(/'/g, "\\'")}')">
                <div class="product-header">
                    <div>
                        <h5 class="product-name mb-1">${escapeHtml(product.name)}</h5>
                        ${stats.min_price && stats.max_price && stats.min_price !== stats.max_price ? `
                            <small class="text-muted">
                                <i class="bi bi-arrow-down"></i> ₹${stats.min_price.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})} 
                                <span class="mx-1">-</span>
                                <i class="bi bi-arrow-up"></i> ₹${stats.max_price.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                            </small>
                        ` : ''}
                    </div>
                    ${priceChange !== 0 ? `
                        <span class="product-badge ${priceChangeClass}">
                            <i class="bi ${priceChangeIcon}"></i> ${priceChangeText}
                        </span>
                    ` : ''}
                </div>
                <div class="price-section">
                    <p class="price-tag mb-0">₹${latestPrice.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</p>
                    ${stats.avg_price ? `
                        <small class="text-muted">
                            <i class="bi bi-graph-up"></i> Avg: ₹${stats.avg_price.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                        </small>
                    ` : ''}
                </div>
                <div class="product-meta">
                    <span class="product-updated">
                        <i class="bi bi-clock"></i> ${timeAgo}
                    </span>
                    <div class="product-actions">
                        <button class="btn btn-action btn-view btn-sm" onclick="event.stopPropagation(); showProductDetails(${product.id}, '${escapeHtml(product.name).replace(/'/g, "\\'")}')">
                            <i class="bi bi-eye"></i> View
                        </button>
                        <button class="btn btn-action btn-delete btn-sm" onclick="event.stopPropagation(); deleteProduct(${product.id}, '${escapeHtml(product.name).replace(/'/g, "\\'")}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Grid view HTML (original)
        col.innerHTML = `
            <div class="${cardClass}" onclick="showProductDetails(${product.id}, '${escapeHtml(product.name).replace(/'/g, "\\'")}')">
                <div class="product-header">
                    <h5 class="product-name">${escapeHtml(product.name)}</h5>
                    ${priceChange !== 0 ? `
                        <span class="product-badge ${priceChangeClass}">
                            <i class="bi ${priceChangeIcon}"></i> ${priceChangeText}
                        </span>
                    ` : ''}
                </div>
                <div class="price-section">
                    <p class="price-tag">₹${latestPrice.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</p>
                    ${stats.avg_price ? `
                        <p class="text-muted small mb-0">
                            <i class="bi bi-graph-up"></i> Avg: ₹${stats.avg_price.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                        </p>
                    ` : ''}
                </div>
                ${stats.min_price && stats.max_price && stats.min_price !== stats.max_price ? `
                    <div class="mb-2">
                        <small class="text-muted">
                            <i class="bi bi-arrow-down"></i> ₹${stats.min_price.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})} 
                            <span class="mx-1">-</span>
                            <i class="bi bi-arrow-up"></i> ₹${stats.max_price.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                        </small>
                    </div>
                ` : ''}
                <div class="product-meta">
                    <span class="product-updated">
                        <i class="bi bi-clock"></i> ${timeAgo}
                    </span>
                    <div class="product-actions">
                        <button class="btn btn-action btn-view btn-sm" onclick="event.stopPropagation(); showProductDetails(${product.id}, '${escapeHtml(product.name).replace(/'/g, "\\'")}')">
                            <i class="bi bi-eye"></i> View
                        </button>
                        <button class="btn btn-action btn-delete btn-sm" onclick="event.stopPropagation(); deleteProduct(${product.id}, '${escapeHtml(product.name).replace(/'/g, "\\'")}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    return col;
}

// Get time ago string
function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

// Filter products
function filterProducts() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = allProducts.filter(product => 
        product.name.toLowerCase().includes(searchTerm)
    );
    displayProducts(filtered);
}

// Sort products
function sortProducts() {
    const sortBy = document.getElementById('sortSelect').value;
    const sorted = [...allProducts];
    
    switch(sortBy) {
        case 'name':
            sorted.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'price':
            sorted.sort((a, b) => (b.latest_price || 0) - (a.latest_price || 0));
            break;
        case 'updated':
            sorted.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
            break;
        case 'change':
            sorted.sort((a, b) => {
                const changeA = (a.stats?.price_change_percent || 0);
                const changeB = (b.stats?.price_change_percent || 0);
                return changeA - changeB; // Negative changes first (drops)
            });
            break;
    }
    
    displayProducts(sorted);
}

// Change view mode
function changeView(mode) {
    currentView = mode;
    displayProducts(allProducts);
}

// Update best deals
function updateBestDeals(products) {
    const dealsList = document.getElementById('best-deals-list');
    
    if (!products || products.length === 0) {
        dealsList.innerHTML = '<p class="text-muted text-center py-3">No products yet</p>';
        return;
    }
    
    // Find products with price drops
    const deals = products
        .filter(p => {
            const change = p.stats?.price_change_percent || 0;
            return change < 0;
        })
        .sort((a, b) => {
            const changeA = Math.abs(a.stats?.price_change_percent || 0);
            const changeB = Math.abs(b.stats?.price_change_percent || 0);
            return changeB - changeA;
        })
        .slice(0, 5);
    
    if (deals.length === 0) {
        dealsList.innerHTML = '<p class="text-muted text-center py-3">No price drops yet</p>';
        return;
    }
    
    dealsList.innerHTML = deals.map(product => {
        const change = Math.abs(product.stats?.price_change_percent || 0);
        return `
            <div class="deal-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${escapeHtml(product.name)}</strong>
                        <p class="mb-0 text-success">₹${(product.latest_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</p>
                    </div>
                    <span class="badge bg-danger">-${change.toFixed(1)}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// Update recent activity
function updateRecentActivity(products) {
    const activityList = document.getElementById('recent-activity-list');
    
    if (!products || products.length === 0) {
        activityList.innerHTML = '<p class="text-muted text-center py-3">No activity yet</p>';
        return;
    }
    
    // Sort by updated_at and take latest 5
    const recent = [...products]
        .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        .slice(0, 5);
    
    activityList.innerHTML = recent.map(product => {
        const timeAgo = getTimeAgo(new Date(product.updated_at));
        return `
            <div class="activity-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${escapeHtml(product.name)}</strong>
                        <p class="mb-0 text-muted small">Price updated</p>
                    </div>
                    <span class="badge bg-info">${timeAgo}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Show product details
async function showProductDetails(productId, productName) {
    document.getElementById('productDetailsTitle').innerHTML = `
        <i class="bi bi-info-circle"></i> ${escapeHtml(productName)}
    `;
    
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
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.05)');
        
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: historyData.labels || [],
                datasets: [{
                    label: 'Price (₹)',
                    data: historyData.data || [],
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: gradient,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: 'rgb(99, 102, 241)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Price History Trend',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `Price: ₹${context.parsed.y.toLocaleString('en-IN')}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString('en-IN');
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        // Display stats
        const priceChange = stats.price_change_percent || 0;
        const priceChangeClass = priceChange < 0 ? 'text-danger' : priceChange > 0 ? 'text-success' : 'text-muted';
        const priceChangeIcon = priceChange < 0 ? 'bi-arrow-down' : priceChange > 0 ? 'bi-arrow-up' : 'bi-dash';
        
        const statsHtml = `
            <div class="stats-card">
                <h6 class="mb-3"><i class="bi bi-bar-chart"></i> Statistics</h6>
                <div class="stat-item mb-3">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Current Price</span>
                        <strong class="text-success">₹${(stats.last_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</strong>
                    </div>
                </div>
                <div class="stat-item mb-3">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Average Price</span>
                        <strong>₹${(stats.avg_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</strong>
                    </div>
                </div>
                <div class="stat-item mb-3">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Minimum Price</span>
                        <strong class="text-success">₹${(stats.min_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</strong>
                    </div>
                </div>
                <div class="stat-item mb-3">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Maximum Price</span>
                        <strong class="text-danger">₹${(stats.max_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</strong>
                    </div>
                </div>
                <div class="stat-item mb-3">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Price Change</span>
                        <strong class="${priceChangeClass}">
                            <i class="bi ${priceChangeIcon}"></i> ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}%
                        </strong>
                    </div>
                </div>
                <div class="stat-item mb-3">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Price Records</span>
                        <strong>${stats.count || 0}</strong>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Standard Deviation</span>
                        <strong>₹${(stats.std_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</strong>
                    </div>
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
            await loadProducts();
            await loadDashboardStats();
            
            // Show success message
            showNotification('Product added successfully!', 'success');
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
            await loadProducts();
            await loadDashboardStats();
            showNotification('Product deleted successfully!', 'success');
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        alert('Error deleting product');
    }
}

// Refresh data
async function refreshData() {
    const btn = event.target.closest('button');
    const icon = btn.querySelector('i');
    icon.classList.add('spin');
    
    await Promise.all([loadProducts(), loadDashboardStats()]);
    
    setTimeout(() => {
        icon.classList.remove('spin');
    }, 500);
    
    showNotification('Data refreshed!', 'info');
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this with a toast library
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
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

// Add spin animation for refresh icon
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spin {
        animation: spin 0.5s linear;
    }
    .stats-card {
        background: #f9fafb;
        padding: 1.5rem;
        border-radius: 12px;
    }
    .stat-item {
        padding: 0.75rem;
        background: white;
        border-radius: 8px;
        border-left: 3px solid var(--primary-color);
    }
`;
document.head.appendChild(style);
