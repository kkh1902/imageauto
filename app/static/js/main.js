// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('ImageAuto 애플리케이션이 로드되었습니다.');
    
    // Load recent media on home page
    loadRecentMedia();
});

// Show loading overlay
window.showLoading = function(message = '처리 중입니다...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = overlay.querySelector('.loading-text');
    loadingText.textContent = message;
    overlay.style.display = 'flex';
};

// Hide loading overlay
window.hideLoading = function() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'none';
};

// Load recent media
async function loadRecentMedia() {
    try {
        const response = await fetch('/api/media/list');
        const data = await response.json();
        
        if (data.success) {
            displayRecentMedia(data.media);
        }
    } catch (error) {
        console.error('미디어 로드 실패:', error);
    }
}

// Display recent media
function displayRecentMedia(media) {
    const grid = document.getElementById('recent-media-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    // Combine all media types
    const allMedia = [];
    
    if (media.images) {
        media.images.forEach(filename => {
            allMedia.push({
                type: 'image',
                filename: filename,
                path: `images/${filename}`
            });
        });
    }
    
    if (media.videos) {
        media.videos.forEach(filename => {
            allMedia.push({
                type: 'video',
                filename: filename,
                path: `videos/${filename}`
            });
        });
    }
    
    if (media.edited) {
        media.edited.forEach(filename => {
            if (filename.endsWith('.mp4') || filename.endsWith('.avi') || filename.endsWith('.mov')) {
                allMedia.push({
                    type: 'edited_video',
                    filename: filename,
                    path: `edited/${filename}`
                });
            }
        });
    }
    
    // Sort by modification time (newest first) - this would require server support
    // For now, just show the latest 8 items
    const latestMedia = allMedia.slice(-8).reverse();
    
    latestMedia.forEach(item => {
        const mediaItem = document.createElement('div');
        mediaItem.className = 'media-item';
        
        if (item.type === 'image') {
            mediaItem.innerHTML = `
                <img src="/api/media/download/${item.path}" alt="${item.filename}">
                <div class="media-info">
                    <i class="fas fa-image"></i> ${item.filename}
                </div>
            `;
        } else {
            mediaItem.innerHTML = `
                <video>
                    <source src="/api/media/download/${item.path}" type="video/mp4">
                </video>
                <div class="media-info">
                    <i class="fas fa-video"></i> ${item.filename}
                </div>
            `;
        }
        
        mediaItem.addEventListener('click', () => {
            if (item.type === 'image') {
                window.open(`/api/media/download/${item.path}`, '_blank');
            } else {
                // Create modal for video playback
                showVideoModal(`/api/media/download/${item.path}`);
            }
        });
        
        grid.appendChild(mediaItem);
    });
    
    if (allMedia.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #6b7280;">아직 생성된 미디어가 없습니다.</p>';
    }
}

// Show video modal
function showVideoModal(videoUrl) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div style="position: relative; max-width: 90%; max-height: 90%;">
            <video controls autoplay style="max-width: 100%; max-height: 80vh;">
                <source src="${videoUrl}" type="video/mp4">
            </video>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="position: absolute; top: -40px; right: 0; 
                           background: white; border: none; padding: 10px 20px; 
                           border-radius: 5px; cursor: pointer;">
                <i class="fas fa-times"></i> 닫기
            </button>
        </div>
    `;
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    document.body.appendChild(modal);
}

// Periodic refresh of recent media
setInterval(() => {
    if (document.querySelector('#home.page.active')) {
        loadRecentMedia();
    }
}, 30000); // Refresh every 30 seconds