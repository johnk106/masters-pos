/**
 * POS Orders Filters Enhancement
 * Provides enhanced functionality for the POS orders page filters
 */

document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    const customerFilter = document.getElementById('customer-filter');
    const statusFilter = document.getElementById('status-filter');
    const paymentStatusFilter = document.getElementById('payment-status-filter');
    const sortFilter = document.getElementById('sort-filter');

    // Auto-submit form when filters change (for better UX)
    const autoSubmitFilters = [customerFilter, statusFilter, paymentStatusFilter, sortFilter];
    
    autoSubmitFilters.forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function() {
                // Add a small delay to allow for quick changes
                setTimeout(() => {
                    filterForm.submit();
                }, 300);
            });
        }
    });

    // Enhanced keyboard navigation
    autoSubmitFilters.forEach(filter => {
        if (filter) {
            filter.addEventListener('keydown', function(e) {
                // Submit on Enter key
                if (e.key === 'Enter') {
                    e.preventDefault();
                    filterForm.submit();
                }
                
                // Clear selection on Escape key
                if (e.key === 'Escape') {
                    e.preventDefault();
                    this.selectedIndex = 0; // Reset to first option (placeholder)
                    filterForm.submit();
                }
            });
        }
    });

    // Add loading state when filters are being applied
    filterForm.addEventListener('submit', function() {
        const submitBtn = filterForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<i class="ti ti-loader-2 animate-spin me-1"></i>Applying...';
        submitBtn.disabled = true;
        
        // Reset button state if form submission fails
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 5000);
    });

    // Customer filter enhancement - add search capability if there are many customers
    if (customerFilter && customerFilter.options.length > 20) {
        // Convert to searchable dropdown if too many options
        enhanceCustomerFilter();
    }

    // Add visual feedback for active filters
    highlightActiveFilters();

    // Reset disabled placeholder options to prevent submission
    function resetPlaceholders() {
        autoSubmitFilters.forEach(filter => {
            if (filter && filter.selectedIndex === 0) {
                filter.value = '';
            }
        });
    }

    // Highlight active filters with visual indicators
    function highlightActiveFilters() {
        autoSubmitFilters.forEach(filter => {
            if (filter && filter.value && filter.selectedIndex > 0) {
                filter.classList.add('filter-active');
                filter.style.borderColor = '#007bff';
                filter.style.backgroundColor = '#f8f9fa';
            } else if (filter) {
                filter.classList.remove('filter-active');
                filter.style.borderColor = '';
                filter.style.backgroundColor = '';
            }
        });
    }

    // Enhanced customer filter for large datasets
    function enhanceCustomerFilter() {
        // Add data-live-search attribute for Bootstrap Select enhancement
        customerFilter.setAttribute('data-live-search', 'true');
        customerFilter.setAttribute('data-size', '8');
        customerFilter.setAttribute('title', 'Search for a customer...');
        
        // If Bootstrap Select is available, initialize it
        if (typeof $.fn.selectpicker !== 'undefined') {
            $(customerFilter).selectpicker({
                liveSearch: true,
                size: 8,
                title: 'Search for a customer...',
                noneResultsText: 'No customers found'
            });
        }
    }

    // Add filter summary for accessibility
    function updateFilterSummary() {
        const activeFilters = [];
        
        autoSubmitFilters.forEach(filter => {
            if (filter && filter.value && filter.selectedIndex > 0) {
                const label = filter.getAttribute('aria-label') || 'Filter';
                const value = filter.options[filter.selectedIndex].text;
                activeFilters.push(`${label}: ${value}`);
            }
        });

        // Update screen reader announcement
        let summary = '';
        if (activeFilters.length > 0) {
            summary = `Applied filters: ${activeFilters.join(', ')}`;
        } else {
            summary = 'No filters applied';
        }

        // Create or update filter summary for screen readers
        let summaryElement = document.getElementById('filter-summary-sr');
        if (!summaryElement) {
            summaryElement = document.createElement('div');
            summaryElement.id = 'filter-summary-sr';
            summaryElement.className = 'visually-hidden';
            summaryElement.setAttribute('aria-live', 'polite');
            filterForm.appendChild(summaryElement);
        }
        summaryElement.textContent = summary;
    }

    // Update filter highlights and summary when page loads
    highlightActiveFilters();
    updateFilterSummary();

    // Monitor for filter changes to update highlights and summary
    autoSubmitFilters.forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function() {
                setTimeout(() => {
                    highlightActiveFilters();
                    updateFilterSummary();
                }, 100);
            });
        }
    });

    // Add tooltip functionality for filter explanations
    function addFilterTooltips() {
        const tooltips = {
            'customer-filter': 'Filter orders by customer name',
            'status-filter': 'Filter by order status (Draft, Completed, Canceled)',
            'payment-status-filter': 'Filter by payment status (Paid, Partial, Unpaid)',
            'sort-filter': 'Sort orders by different criteria'
        };

        Object.keys(tooltips).forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                filter.setAttribute('title', tooltips[filterId]);
                filter.setAttribute('data-bs-toggle', 'tooltip');
                filter.setAttribute('data-bs-placement', 'top');
            }
        });

        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    // Initialize tooltips
    addFilterTooltips();

    // Prevent form submission with empty values
    filterForm.addEventListener('submit', function(e) {
        resetPlaceholders();
    });

    // Add filter count indicator
    function showFilterCount() {
        const activeFilterCount = autoSubmitFilters.filter(filter => 
            filter && filter.value && filter.selectedIndex > 0
        ).length;

        const submitBtn = filterForm.querySelector('button[type="submit"]');
        if (activeFilterCount > 0) {
            const badge = `<span class="badge bg-primary ms-1">${activeFilterCount}</span>`;
            if (!submitBtn.innerHTML.includes('badge')) {
                submitBtn.innerHTML = submitBtn.innerHTML.replace('Apply Filters', `Apply Filters ${badge}`);
            }
        } else {
            submitBtn.innerHTML = submitBtn.innerHTML.replace(/<span class="badge[^>]*>.*?<\/span>/, '');
        }
    }

    // Update filter count on changes
    autoSubmitFilters.forEach(filter => {
        if (filter) {
            filter.addEventListener('change', showFilterCount);
        }
    });

    // Initial filter count
    showFilterCount();
});