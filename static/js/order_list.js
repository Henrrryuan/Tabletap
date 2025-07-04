// Order mark as completed functionality
document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    document.querySelectorAll('.complete-order').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.dataset.orderId;
            const card = this.closest('.order-card');
            
            fetch(`/tabletap/orders/${orderId}/complete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update statistics
                    document.getElementById('totalOrders').textContent = data.total_orders;
                    document.getElementById('total-revenue').textContent = '¥' + data.total_revenue.toFixed(2);
                    
                    // Update order card status
                    const statusBadge = card.querySelector('.badge');
                    statusBadge.className = 'badge bg-success';
                    statusBadge.textContent = 'Completed';
                    
                    // Remove complete button
                    this.remove();
                    
                    // Add completion time
                    const orderInfo = card.querySelector('.order-info');
                    const completedTime = document.createElement('p');
                    completedTime.innerHTML = `<i class="fas fa-check-circle"></i>Completion Time: ${new Date().toLocaleString()}`;
                    orderInfo.appendChild(completedTime);
                } else {
                    alert('Operation failed: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Operation failed, please try again');
            });
        });
    });
}); 