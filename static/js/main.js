function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    
    if (window.innerWidth <= 768 && 
        sidebar.classList.contains('open') && 
        !sidebar.contains(e.target) && 
        !menuBtn.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
});

function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

document.addEventListener('DOMContentLoaded', () => {
    const deleteForms = document.querySelectorAll('form[data-confirm]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!confirmDelete(form.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});

let orderItemIndex = 0;

function addOrderItem() {
    const container = document.getElementById('order-items');
    if (!container) return;
    
    const products = window.productsData || [];
    
    const itemHtml = `
        <div class="order-item" data-index="${orderItemIndex}">
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Product</label>
                    <select name="product_id[]" class="form-control product-select" required onchange="updateItemPrice(this)">
                        <option value="">Select Product</option>
                        ${products.map(p => `<option value="${p.id}" data-price="${p.price}">${p.name} - $${p.price.toFixed(2)} (Stock: ${p.stock_quantity})</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Quantity</label>
                    <input type="number" name="quantity[]" class="form-control quantity-input" min="1" value="1" required onchange="updateOrderTotal()">
                </div>
                <div class="form-group">
                    <label class="form-label">Unit Price</label>
                    <input type="text" class="form-control item-price" readonly value="$0.00">
                </div>
                <div class="form-group" style="display: flex; align-items: flex-end;">
                    <button type="button" class="btn btn-danger btn-sm" onclick="removeOrderItem(${orderItemIndex})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', itemHtml);
    orderItemIndex++;
}

function removeOrderItem(index) {
    const item = document.querySelector(`.order-item[data-index="${index}"]`);
    if (item) {
        item.remove();
        updateOrderTotal();
    }
}

function updateItemPrice(select) {
    const item = select.closest('.order-item');
    const priceInput = item.querySelector('.item-price');
    const selectedOption = select.options[select.selectedIndex];
    const price = selectedOption.dataset.price || 0;
    priceInput.value = `$${parseFloat(price).toFixed(2)}`;
    updateOrderTotal();
}

function updateOrderTotal() {
    const items = document.querySelectorAll('.order-item');
    let total = 0;
    
    items.forEach(item => {
        const select = item.querySelector('.product-select');
        const quantity = item.querySelector('.quantity-input');
        const selectedOption = select.options[select.selectedIndex];
        const price = parseFloat(selectedOption.dataset.price || 0);
        const qty = parseInt(quantity.value || 0);
        total += price * qty;
    });
    
    const totalEl = document.getElementById('order-total');
    if (totalEl) {
        totalEl.textContent = `$${total.toFixed(2)}`;
    }
}

// =============================================================================
// Stock Adjustment Modal
// =============================================================================

function openStockModal(productId, productName, currentStock) {
    const modal = document.getElementById('stock-modal');
    if (!modal) return;
    
    document.getElementById('stock-product-name').textContent = productName;
    document.getElementById('stock-current').textContent = currentStock;
    document.getElementById('stock-adjustment').value = 0;
    document.getElementById('stock-form').action = `/products/adjust-stock/${productId}`;
    
    modal.classList.add('active');
}

function closeStockModal() {
    const modal = document.getElementById('stock-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function updateStockPreview() {
    const current = parseInt(document.getElementById('stock-current').textContent) || 0;
    const adjustment = parseInt(document.getElementById('stock-adjustment').value) || 0;
    const preview = document.getElementById('stock-preview');
    if (preview) {
        const newStock = Math.max(0, current + adjustment);
        preview.textContent = newStock;
        preview.className = adjustment > 0 ? 'text-success' : (adjustment < 0 ? 'text-danger' : '');
    }
}

function initDashboardCharts(salesData, orderStatusData) {
    // Sales Chart
    const salesCtx = document.getElementById('salesChart');
    if (salesCtx && typeof Chart !== 'undefined') {
        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: salesData.map(d => d.date),
                datasets: [{
                    label: 'Sales ($)',
                    data: salesData.map(d => d.sales),
                    borderColor: '#0066FF',
                    backgroundColor: 'rgba(0, 102, 255, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#0066FF',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94A3B8'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94A3B8',
                            callback: value => '$' + value.toLocaleString()
                        }
                    }
                }
            }
        });
    }
    
    const statusCtx = document.getElementById('orderStatusChart');
    if (statusCtx && typeof Chart !== 'undefined') {
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: orderStatusData.map(d => d.status),
                datasets: [{
                    data: orderStatusData.map(d => d.count),
                    backgroundColor: [
                        '#F59E0B', // pending
                        '#0066FF', // confirmed
                        '#6366F1', // shipped
                        '#10B981', // delivered
                        '#EF4444'  // cancelled
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94A3B8',
                            padding: 15,
                            usePointStyle: true
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const required = form.querySelectorAll('[required]');
            let valid = true;
            
            required.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
});

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    const filter = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('ERP-Vision Dashboard initialized');
});
