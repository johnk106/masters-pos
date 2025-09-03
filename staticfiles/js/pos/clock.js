/**
 * POS Clock Manager
 * Handles real-time clock display for East Africa Time (UTC+3)
 * Supports auto-refresh, page visibility handling, and prevents multiple intervals
 */
class POSClock {
    constructor() {
        this.intervalId = null;
        this.clockElement = null;
        this.isRunning = false;
        this.lastVisibilityState = true;
        this.timeFormat = '24'; // Default to 24-hour format to match existing UI, can be changed to '12'
        
        // East Africa Time offset (UTC+3)
        this.timezoneOffset = 3 * 60 * 60 * 1000; // 3 hours in milliseconds
        
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Find the clock element
        this.findClockElement();
        
        if (!this.clockElement) {
            console.warn('POS Clock: Clock element not found');
            return;
        }

        // Set up page visibility handling
        this.setupVisibilityHandler();
        
        // Start the clock
        this.start();
        
        // Set up cleanup on page unload
        window.addEventListener('beforeunload', () => this.stop());
    }

    findClockElement() {
        // Try different selectors to find the clock element
        const selectors = [
            '.time-nav span',
            '.nav-item.time-nav span',
            '[class*="time-nav"] span',
            '.clock-display',
            '#clock-display'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                this.clockElement = element;
                console.log('POS Clock: Found clock element with selector:', selector);
                break;
            }
        }

        // If no element found, try to find by content (fallback)
        if (!this.clockElement) {
            const spans = document.querySelectorAll('span');
            for (const span of spans) {
                if (span.textContent && span.textContent.match(/\d{1,2}:\d{2}:\d{2}/)) {
                    this.clockElement = span;
                    console.log('POS Clock: Found clock element by content match');
                    break;
                }
            }
        }
    }

    setupVisibilityHandler() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            const isVisible = !document.hidden;
            
            if (isVisible && !this.lastVisibilityState) {
                // Page became visible, ensure clock is accurate
                this.updateTime();
                console.log('POS Clock: Page became visible, time updated');
            }
            
            this.lastVisibilityState = isVisible;
        });

        // Handle window focus/blur events as additional safety
        window.addEventListener('focus', () => {
            if (this.isRunning) {
                this.updateTime();
                console.log('POS Clock: Window focused, time updated');
            }
        });
    }

    getEastAfricaTime() {
        // Method 1: Use Intl.DateTimeFormat for accurate timezone handling
        try {
            const now = new Date();
            
            // Try to use the browser's timezone support for East Africa
            const eatFormatter = new Intl.DateTimeFormat('en-US', {
                timeZone: 'Africa/Nairobi',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
            
            const eatParts = eatFormatter.formatToParts(now);
            const eatString = `${eatParts.find(p => p.type === 'year').value}-${eatParts.find(p => p.type === 'month').value}-${eatParts.find(p => p.type === 'day').value}T${eatParts.find(p => p.type === 'hour').value}:${eatParts.find(p => p.type === 'minute').value}:${eatParts.find(p => p.type === 'second').value}`;
            
            const eatTime = new Date(eatString);
            
            // Verify the result is valid
            if (!isNaN(eatTime.getTime())) {
                return eatTime;
            }
        } catch (error) {
            console.warn('POS Clock: Intl.DateTimeFormat failed, using fallback method');
        }
        
        // Method 2: Fallback - Manual UTC calculation
        const now = new Date();
        
        // Convert to UTC first, then add East Africa offset
        const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
        const eatTime = new Date(utcTime + this.timezoneOffset);
        
        return eatTime;
    }

    formatTime(date) {
        const hours = date.getHours();
        const minutes = date.getMinutes();
        const seconds = date.getSeconds();

        if (this.timeFormat === '24') {
            // 24-hour format
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            // 12-hour format with AM/PM
            const ampm = hours >= 12 ? 'PM' : 'AM';
            const displayHours = hours % 12 || 12;
            return `${displayHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')} ${ampm}`;
        }
    }

    updateTime() {
        if (!this.clockElement) {
            return;
        }

        try {
            const eatTime = this.getEastAfricaTime();
            const formattedTime = this.formatTime(eatTime);
            
            // Handle the specific POS clock structure with image and text
            if (this.clockElement.innerHTML.includes('<img')) {
                // This is the POS clock with image - update only the text part
                this.clockElement.innerHTML = this.clockElement.innerHTML.replace(
                    />\d{1,2}:\d{2}:\d{2}(\s*(AM|PM))?<\/span>$/,
                    `>${formattedTime}</span>`
                );
                
                // Fallback: if the above doesn't work, try replacing just the time pattern
                if (!this.clockElement.textContent.includes(formattedTime)) {
                    this.clockElement.innerHTML = this.clockElement.innerHTML.replace(
                        /\d{1,2}:\d{2}:\d{2}(\s*(AM|PM))?/,
                        formattedTime
                    );
                }
            } else {
                // Standard text-only clock element
                this.clockElement.innerHTML = this.clockElement.innerHTML.replace(
                    /\d{1,2}:\d{2}:\d{2}(\s*(AM|PM))?/,
                    formattedTime
                );
            }
            
            // If no time pattern found in innerHTML, try textContent
            if (!this.clockElement.textContent.match(/\d{1,2}:\d{2}:\d{2}/)) {
                // Find the text node and update it
                const walker = document.createTreeWalker(
                    this.clockElement,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let textNode = walker.nextNode();
                while (textNode) {
                    if (textNode.textContent.trim() && textNode.textContent.match(/\d{1,2}:\d{2}:\d{2}/)) {
                        textNode.textContent = formattedTime;
                        break;
                    }
                    textNode = walker.nextNode();
                }
            }
        } catch (error) {
            console.error('POS Clock: Error updating time:', error);
        }
    }

    start() {
        // Prevent multiple intervals
        if (this.isRunning) {
            console.warn('POS Clock: Clock is already running');
            return;
        }

        // Clear any existing interval
        this.stop();

        // Update immediately
        this.updateTime();

        // Set up interval to update every second
        this.intervalId = setInterval(() => {
            this.updateTime();
        }, 1000);

        this.isRunning = true;
        console.log('POS Clock: Clock started');
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
        console.log('POS Clock: Clock stopped');
    }

    restart() {
        this.stop();
        this.start();
    }

    setTimeFormat(format) {
        if (format === '12' || format === '24') {
            this.timeFormat = format;
            this.updateTime(); // Update immediately with new format
            console.log(`POS Clock: Time format changed to ${format}-hour`);
        } else {
            console.warn('POS Clock: Invalid time format. Use "12" or "24"');
        }
    }

    // Method to manually sync time (useful for debugging)
    syncTime() {
        this.updateTime();
        console.log('POS Clock: Time manually synchronized');
    }

    // Get current status
    getStatus() {
        const now = new Date();
        const eatTime = this.getEastAfricaTime();
        
        return {
            isRunning: this.isRunning,
            timeFormat: this.timeFormat,
            hasClockElement: !!this.clockElement,
            currentTime: eatTime,
            intervalId: this.intervalId,
            // Debug info
            localTime: now.toLocaleString(),
            utcTime: now.toUTCString(),
            eastAfricaTime: eatTime.toLocaleString(),
            timezoneOffset: this.timezoneOffset / (60 * 60 * 1000) + ' hours'
        };
    }

    // Debug method to verify time calculations
    debugTime() {
        const now = new Date();
        const eatTime = this.getEastAfricaTime();
        
        // Test both methods
        let intlMethod = 'Not available';
        let fallbackMethod = 'Not available';
        
        try {
            const eatFormatter = new Intl.DateTimeFormat('en-US', {
                timeZone: 'Africa/Nairobi',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
            intlMethod = eatFormatter.format(now);
        } catch (error) {
            intlMethod = 'Error: ' + error.message;
        }
        
        try {
            const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
            const fallbackTime = new Date(utcTime + this.timezoneOffset);
            fallbackMethod = fallbackTime.toLocaleString();
        } catch (error) {
            fallbackMethod = 'Error: ' + error.message;
        }
        
        console.log('=== POS Clock Debug Info ===');
        console.log('Local time:', now.toLocaleString());
        console.log('UTC time:', now.toUTCString());
        console.log('East Africa Time (calculated):', eatTime.toLocaleString());
        console.log('Formatted EAT:', this.formatTime(eatTime));
        console.log('Timezone offset:', this.timezoneOffset / (60 * 60 * 1000), 'hours');
        console.log('Intl method result:', intlMethod);
        console.log('Fallback method result:', fallbackMethod);
        console.log('============================');
        
        return {
            local: now.toLocaleString(),
            utc: now.toUTCString(),
            eastAfrica: eatTime.toLocaleString(),
            formatted: this.formatTime(eatTime),
            intlMethod: intlMethod,
            fallbackMethod: fallbackMethod
        };
    }
}

// Global instance management
window.POSClock = window.POSClock || null;

// Initialize clock when script loads
(function() {
    // Prevent multiple instances
    if (window.POSClock && window.POSClock.isRunning) {
        console.warn('POS Clock: Instance already exists and is running');
        return;
    }

    // Create new instance
    window.POSClock = new POSClock();

    // Expose useful methods globally for debugging
    window.clockSync = function() {
        if (window.POSClock) {
            window.POSClock.syncTime();
        }
    };

    window.clockStatus = function() {
        if (window.POSClock) {
            console.log('POS Clock Status:', window.POSClock.getStatus());
            return window.POSClock.getStatus();
        }
        return null;
    };

    window.clockRestart = function() {
        if (window.POSClock) {
            window.POSClock.restart();
        }
    };

    window.clockSetFormat = function(format) {
        if (window.POSClock) {
            window.POSClock.setTimeFormat(format);
        }
    };

    window.clockDebug = function() {
        if (window.POSClock) {
            return window.POSClock.debugTime();
        }
        return null;
    };

    console.log('POS Clock: Script loaded and initialized');
})();

// Handle script re-execution
if (document.readyState === 'complete' && window.POSClock) {
    // If document is already loaded and we have a clock instance, restart it
    setTimeout(() => {
        if (window.POSClock && !window.POSClock.isRunning) {
            window.POSClock.restart();
        }
    }, 100);
}