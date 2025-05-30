// Image Generation Module - Enhanced
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the image generation page
    if (!document.querySelector('#image-prompt')) {
        return;
    }
    
    initializeImageGeneration();
});

function initializeImageGeneration() {
    // Initialize prompt suggestions
    initializePromptSuggestions();
    
    // Initialize form interactions
    initializeFormInteractions();
    
    // Initialize generation button
    initializeGenerationButton();
    
    // Load recent images
    loadRecentImages();
}

function initializePromptSuggestions() {
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');
    const promptTextarea = document.getElementById('image-prompt');
    
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const promptText = this.getAttribute('data-prompt');
            if (promptTextarea && promptText) {
                promptTextarea.value = promptText;
                
                // Add visual feedback
                this.style.background = '#10b981';
                this.style.color = 'white';
                this.style.borderColor = '#10b981';
                
                setTimeout(() => {
                    this.style.background = '';
                    this.style.color = '';
                    this.style.borderColor = '';
                }, 300);
                
                // Focus on textarea
                promptTextarea.focus();
                
                showMessage('프롬프트가 입력되었습니다!', 'success');
            }
        });
    });
}

function initializeFormInteractions() {
    // Character counter for prompt
    const promptTextarea = document.getElementById('image-prompt');
    
    if (promptTextarea) {
        // Auto-resize textarea
        promptTextarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });
        
        // Add character counter
        const formGroup = promptTextarea.closest('.form-group');
        if (formGroup && !formGroup.querySelector('.character-count')) {
            const counter = document.createElement('div');
            counter.className = 'character-count';
            counter.innerHTML = '<span id="prompt-char-count">0</span>/2000';
            formGroup.appendChild(counter);
            
            promptTextarea.addEventListener('input', function() {
                const count = this.value.length;
                const charCount = document.getElementById('prompt-char-count');
                if (charCount) {
                    charCount.textContent = count;
                    
                    if (count > 1800) {
                        charCount.style.color = '#dc2626';
                    } else if (count > 1500) {
                        charCount.style.color = '#f59e0b';
                    } else {
                        charCount.style.color = '#6b7280';
                    }
                }
            });
        }
    }
}

function initializeGenerationButton() {
    const generateBtn = document.getElementById('generate-image-btn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', generateImage);
    }
}

function generateImage() {
    const promptTextarea = document.getElementById('image-prompt');
    const aspectRatio = document.getElementById('aspect-ratio');
    const quality = document.getElementById('image-quality');
    const style = document.getElementById('image-style');
    const seed = document.getElementById('image-seed');
    const negativePrompt = document.getElementById('negative-prompt');
    
    const prompt = promptTextarea ? promptTextarea.value.trim() : '';
    
    if (!prompt) {
        showMessage('프롬프트를 입력해주세요.', 'error');
        if (promptTextarea) promptTextarea.focus();
        return;
    }
    
    const data = {
        prompt: prompt,
        aspect_ratio: aspectRatio ? aspectRatio.value : '9:16',
        quality: quality ? quality.value : 'high',
        style: style ? style.value : 'realistic',
        seed: seed && seed.value ? parseInt(seed.value) : null,
        negative_prompt: negativePrompt ? negativePrompt.value.trim() : ''
    };
    
    startImageGeneration(data);
}

function startImageGeneration(data) {
    const generateBtn = document.getElementById('generate-image-btn');
    const progressContainer = document.getElementById('image-progress');
    const resultContainer = document.getElementById('image-result');
    
    // Show loading state
    if (generateBtn) {
        generateBtn.classList.add('loading');
        generateBtn.disabled = true;
    }
    
    // Show progress
    if (progressContainer) {
        progressContainer.style.display = 'block';
        resultContainer.style.display = 'none';
        progressContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Simulate progress
    simulateImageProgress();
    
    // Make API call
    fetch('/api/generate/image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showImageResult(result);
            showMessage('이미지가 성공적으로 생성되었습니다!', 'success');
            loadRecentImages(); // Refresh recent images
        } else {
            throw new Error(result.error || '이미지 생성에 실패했습니다.');
        }
    })
    .catch(error => {
        showMessage('오류: ' + error.message, 'error');
    })
    .finally(() => {
        // Reset UI
        if (generateBtn) {
            generateBtn.classList.remove('loading');
            generateBtn.disabled = false;
        }
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    });
}

function simulateImageProgress() {
    const progressFill = document.getElementById('image-progress-fill');
    const progressPercentage = document.getElementById('image-progress-percentage');
    const progressMessage = document.getElementById('image-progress-message');
    
    const messages = [
        'AI가 프롬프트를 분석하고 있습니다...',
        '이미지 구성을 계획하고 있습니다...',
        '세부 사항을 렌더링하고 있습니다...',
        '최종 이미지를 생성하고 있습니다...'
    ];
    
    let progress = 0;
    let messageIndex = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 12 + 8;
        
        if (progress > 100) {
            progress = 100;
            clearInterval(interval);
        }
        
        if (progressFill) {
            progressFill.style.width = progress + '%';
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = Math.round(progress) + '%';
        }
        
        // Update message
        const newMessageIndex = Math.floor(progress / 25);
        if (newMessageIndex !== messageIndex && newMessageIndex < messages.length) {
            messageIndex = newMessageIndex;
            if (progressMessage) {
                progressMessage.textContent = messages[messageIndex];
            }
        }
        
        if (progress >= 100) {
            if (progressMessage) {
                progressMessage.textContent = '완료!';
            }
        }
    }, 150);
}

function showImageResult(data) {
    const resultContainer = document.getElementById('image-result');
    const resultContent = document.getElementById('image-result-content');
    
    if (!resultContainer || !resultContent) return;
    
    resultContent.innerHTML = `
        <div class="image-result-item">
            <img src="${data.web_path || '/uploads/' + data.filepath}" alt="Generated Image" loading="lazy">
            <div class="image-info">
                <div class="image-details">
                    <h4>생성된 이미지</h4>
                    <p>크기: ${data.aspect_ratio} | 생성 시간: ${new Date().toLocaleString()}</p>
                    <p class="prompt-text">프롬프트: ${data.prompt.substring(0, 100)}${data.prompt.length > 100 ? '...' : ''}</p>
                </div>
                <div class="image-actions">
                    <button class="btn btn-secondary" onclick="downloadImage('${data.filename}')">
                        <i class="fas fa-download"></i> 다운로드
                    </button>
                    <button class="btn btn-secondary" onclick="useForVideo('${data.filepath}')">
                        <i class="fas fa-video"></i> 동영상 생성
                    </button>
                    <button class="btn btn-secondary" onclick="copyPrompt('${data.prompt.replace(/'/g, "\\'")}')">
                        <i class="fas fa-copy"></i> 프롬프트 복사
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultContainer.style.display = 'block';
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

function loadRecentImages() {
    const imagesGrid = document.getElementById('recent-images-grid');
    if (!imagesGrid) return;
    
    fetch('/api/media/list?type=images')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.media.images.length > 0) {
            displayRecentImages(data.media.images.slice(0, 6), imagesGrid);
        } else {
            imagesGrid.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1 / -1;">아직 생성된 이미지가 없습니다.</p>';
        }
    })
    .catch(error => {
        console.error('Recent images load error:', error);
        imagesGrid.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1 / -1;">이미지를 불러올 수 없습니다.</p>';
    });
}

function displayRecentImages(images, container) {
    container.innerHTML = '';
    
    images.forEach(filename => {
        const item = document.createElement('div');
        item.className = 'media-item';
        item.innerHTML = `
            <img src="/uploads/images/${filename}" alt="${filename}" loading="lazy">
            <div class="media-info">
                <div style="font-weight: 500; font-size: 0.9rem;">${filename}</div>
                <div style="font-size: 0.75rem; opacity: 0.7; color: #6b7280;">이미지</div>
            </div>
        `;
        
        // Add click to view larger
        item.addEventListener('click', () => {
            showImageModal(`/uploads/images/${filename}`, filename);
        });
        
        container.appendChild(item);
    });
}

function showImageModal(imageSrc, filename) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h3>${filename}</h3>
                <button class="modal-close" onclick="this.closest('.image-modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <img src="${imageSrc}" alt="${filename}" style="max-width: 100%; max-height: 70vh; object-fit: contain;">
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="downloadImage('${filename}')">
                    <i class="fas fa-download"></i> 다운로드
                </button>
                <button class="btn btn-primary" onclick="useForVideo('images/${filename}')">
                    <i class="fas fa-video"></i> 동영상 생성
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Helper functions
function showMessage(message, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    // Insert after page header
    const pageHeader = document.querySelector('.page-header');
    if (pageHeader) {
        pageHeader.parentNode.insertBefore(messageDiv, pageHeader.nextSibling);
    }
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 4000);
}

function downloadImage(filename) {
    window.open(`/uploads/images/${filename}`, '_blank');
}

function useForVideo(imagePath) {
    sessionStorage.setItem('selectedImagePath', imagePath);
    window.location.href = '/video-generation/image-to-video';
}

function copyPrompt(prompt) {
    navigator.clipboard.writeText(prompt).then(() => {
        showMessage('프롬프트가 클립보드에 복사되었습니다.', 'success');
    }).catch(() => {
        showMessage('클립보드 복사에 실패했습니다.', 'error');
    });
}

// Make functions globally available
window.downloadImage = downloadImage;
window.useForVideo = useForVideo;
window.copyPrompt = copyPrompt;
