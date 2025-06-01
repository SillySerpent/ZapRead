/**
 * ZapRead Admin Dashboard Charts
 * 
 * This file contains the chart initialization for the admin dashboard.
 * It's kept separate from the template to avoid linting issues.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get chart contexts
    const userGrowthCtx = document.getElementById('userGrowthChart');
    const documentTypesCtx = document.getElementById('documentTypesChart');
    
    // Only initialize charts if the elements exist
    if (userGrowthCtx) {
        // Get users count from the data attribute
        const usersCount = userGrowthCtx.getAttribute('data-users-count') || 0;
        
        // User Growth Chart
        new Chart(userGrowthCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'New Users',
                    data: [12, 19, 25, 31, 42, 56, 68, 75, 87, 94, 120, parseInt(usersCount)],
                    backgroundColor: 'rgba(58, 134, 255, 0.2)',
                    borderColor: 'rgba(58, 134, 255, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointBackgroundColor: 'rgba(58, 134, 255, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    if (documentTypesCtx) {
        // Document Types Chart
        new Chart(documentTypesCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['PDF', 'DOCX', 'TXT'],
                datasets: [{
                    data: [65, 25, 10],
                    backgroundColor: [
                        'rgba(58, 134, 255, 0.8)',
                        'rgba(255, 0, 110, 0.8)',
                        'rgba(29, 209, 161, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
});
