// Main JavaScript for consistent navigation
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    loadRecentMedia();
});

function initializeNavigation() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
        
        // Close menu when clicking on links
        const navLinks = navMenu.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });
    }
}

async function loadRecentMedia() {
    const mediaGrid = document.getElementById('recent-media-grid');
    if (!mediaGrid) return;
    
    try {
        const response = await fetch('/api/media/list');
        const data = await response.json();
        
        if (data.success) {
            displayRecentMedia(data.media, mediaGrid);
        }
    } catch (error) {
        console.error('최근 미디어 로드 오류:', error);
        mediaGrid.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1 / -1;">미디어를 불러올 수 없습니다.</p>';
    }
}

function displayRecentMedia(media, container) {
    container.innerHTML = '';
    
    // 최근 파일들만 표시 (최대 6개)
    const allFiles = [
        ...media.images.map(f => ({ type: 'image', name: f, path: `images/${f}` })),
        ...media.videos.map(f => ({ type: 'video', name: f, path: `videos/${f}` }))
    ].slice(0, 6);
    
    if (allFiles.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1 / -1;">아직 생성된 미디어가 없습니다. 위의 기능을 사용해 보세요!</p>';
        return;
    }
    
    allFiles.forEach(file => {
        const item = document.createElement('div');
        item.className = 'media-item';
        item.innerHTML = `
            ${file.type === 'image' 
                ? `<img src="/uploads/${file.path}" alt="${file.name}" loading="lazy">`
                : `<video src="/uploads/${file.path}" preload="metadata"></video>`
            }
            <div class="media-info">
                <div style="font-weight: 500; font-size: 0.9rem;">${file.name}</div>
                <div style="font-size: 0.75rem; opacity: 0.7; color: #6b7280;">${file.type === 'image' ? '이미지' : '동영상'}</div>
            </div>
        `;
        container.appendChild(item);
    });
}

// Utility functions
function showLoading(message = '처리 중입니다...') {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        const loadingText = loadingOverlay.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = message;
        }
        loadingOverlay.style.display = 'flex';
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

function downloadFile(path) {
    window.open(`/uploads/${path}`, '_blank');
}

// Make functions globally available
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.downloadFile = downloadFile;
