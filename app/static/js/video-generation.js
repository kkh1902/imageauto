// Video Generation Module - Simplified
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the video generation page
    if (!document.querySelector('.video-generation-tabs')) {
        return;
    }
    
    initializeVideoGeneration();
});

function initializeVideoGeneration() {
    // Initialize tabs
    initializeTabs();
    
    // Initialize form interactions
    initializeFormInteractions();
    
    // Initialize file upload
    initializeFileUpload();
    
    // Initialize image source tabs
    initializeImageSourceTabs();
    
    // Initialize template selection
    initializeTemplateSelection();
    
    // Initialize generation buttons
    initializeGenerationButtons();
    
    // Set default tab based on URL
    setDefaultTab();
}

function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active classes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active classes
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

function initializeFormInteractions() {
    // Character counter for text prompt
    const textPrompt = document.getElementById('text-video-prompt');
    const textPromptCount = document.getElementById('text-prompt-count');
    
    if (textPrompt && textPromptCount) {
        textPrompt.addEventListener('input', function() {
            const count = this.value.length;
            textPromptCount.textContent = count;
            
            if (count > 2250) {
                textPromptCount.style.color = '#dc2626';
            } else if (count > 2000) {
                textPromptCount.style.color = '#f59e0b';
            } else {
                textPromptCount.style.color = '#6b7280';
            }
        });
    }
    
    // Character counter for image video prompt
    const imagePrompt = document.getElementById('image-video-prompt');
    const imagePromptCount = document.getElementById('image-prompt-count');
    
    if (imagePrompt && imagePromptCount) {
        imagePrompt.addEventListener('input', function() {
            const count = this.value.length;
            imagePromptCount.textContent = count;
            
            if (count > 2250) {
                imagePromptCount.style.color = '#dc2626';
            } else if (count > 2000) {
                imagePromptCount.style.color = '#f59e0b';
            } else {
                imagePromptCount.style.color = '#6b7280';
            }
        });
    }
    
    // Character counter for image negative prompt
    const imageNegativePrompt = document.getElementById('image-negative-prompt');
    const imageNegativeCount = document.getElementById('image-negative-count');
    
    if (imageNegativePrompt && imageNegativeCount) {
        imageNegativePrompt.addEventListener('input', function() {
            const count = this.value.length;
            imageNegativeCount.textContent = count;
            
            if (count > 2250) {
                imageNegativeCount.style.color = '#dc2626';
            } else if (count > 2000) {
                imageNegativeCount.style.color = '#f59e0b';
            } else {
                imageNegativeCount.style.color = '#6b7280';
            }
        });
    }
    
    // Range input value display
    const cfgScale = document.getElementById('text-cfg-scale');
    const cfgValue = document.getElementById('text-cfg-value');
    
    if (cfgScale && cfgValue) {
        cfgScale.addEventListener('input', function() {
            cfgValue.textContent = this.value;
        });
    }
}

function initializeFileUpload() {
    const fileInput = document.getElementById('video-image');
    const uploadArea = document.getElementById('image-upload-area');
    const uploadPlaceholder = uploadArea.querySelector('.upload-placeholder');
    const uploadPreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    
    if (!fileInput || !uploadArea) return;
    
    // Click to upload
    uploadArea.addEventListener('click', function(e) {
        if (e.target.closest('.remove-file')) return;
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileUpload(this.files[0]);
        }
    });
    
    function handleFileUpload(file) {
        if (!file.type.startsWith('image/')) {
            showMessage('이미지 파일만 업로드 가능합니다.', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            uploadPlaceholder.style.display = 'none';
            uploadPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
        
        // Upload to server
        uploadImageToServer(file);
    }
}

function removeImage() {
    const uploadArea = document.getElementById('image-upload-area');
    const uploadPlaceholder = uploadArea.querySelector('.upload-placeholder');
    const uploadPreview = document.getElementById('image-preview');
    const fileInput = document.getElementById('video-image');
    
    uploadPlaceholder.style.display = 'block';
    uploadPreview.style.display = 'none';
    fileInput.value = '';
    
    // Clear uploaded file reference
    window.uploadedImagePath = null;
}

function uploadImageToServer(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.uploadedImagePath = data.filepath;
            showMessage('이미지가 업로드되었습니다.', 'success');
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        showMessage('이미지 업로드 실패: ' + error.message, 'error');
        removeImage();
    });
}

function initializeImageSourceTabs() {
    const sourceTabBtns = document.querySelectorAll('.source-tab-btn');
    const sourceContents = document.querySelectorAll('.image-source-content');
    
    sourceTabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetSource = this.getAttribute('data-source');
            
            // Remove active classes
            sourceTabBtns.forEach(b => b.classList.remove('active'));
            sourceContents.forEach(c => c.style.display = 'none');
            
            // Add active class and show content
            this.classList.add('active');
            const targetContent = document.getElementById(targetSource + '-source');
            if (targetContent) {
                targetContent.style.display = 'block';
            }
            
            // Load gallery if gallery tab is selected
            if (targetSource === 'gallery') {
                loadImageGallery();
            }
        });
    });
}

function loadImageGallery() {
    const gallery = document.getElementById('image-gallery');
    if (!gallery) return;
    
    // Show loading
    gallery.innerHTML = `
        <div class="gallery-loading">
            <i class="fas fa-spinner fa-spin"></i> 로딩 중...
        </div>
    `;
    
    // Fetch images from server
    fetch('/api/media/list?type=images')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.media.images.length > 0) {
                displayImageGallery(data.media.images);
            } else {
                displayEmptyGallery();
            }
        })
        .catch(error => {
            console.error('Gallery loading error:', error);
            gallery.innerHTML = `
                <div class="gallery-empty">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>이미지를 불러오는 중 오류가 발생했습니다.</p>
                </div>
            `;
        });
}

function displayImageGallery(images) {
    const gallery = document.getElementById('image-gallery');
    if (!gallery) return;
    
    gallery.innerHTML = images.map(image => {
        const sizeText = formatFileSize(image.size);
        const dateText = new Date(image.modified * 1000).toLocaleDateString();
        
        return `
            <div class="gallery-item" data-image-path="${image.url}" data-filename="${image.filename}">
                <img src="${image.url}" alt="${image.filename}" loading="lazy">
                <div class="gallery-item-overlay">
                    <div class="gallery-item-name">${image.filename}</div>
                    <div class="gallery-item-info">${sizeText} • ${dateText}</div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add click handlers
    gallery.querySelectorAll('.gallery-item').forEach(item => {
        item.addEventListener('click', function() {
            selectGalleryImage(this);
        });
    });
}

function displayEmptyGallery() {
    const gallery = document.getElementById('image-gallery');
    if (!gallery) return;
    
    gallery.innerHTML = `
        <div class="gallery-empty">
            <i class="fas fa-images"></i>
            <p>아직 업로드된 이미지가 없습니다.</p>
            <p>새 이미지를 업로드하거나 ImageFX로 이미지를 생성해보세요.</p>
        </div>
    `;
}

function selectGalleryImage(galleryItem) {
    // Remove previous selections
    document.querySelectorAll('.gallery-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked item
    galleryItem.classList.add('selected');
    
    // Get image info
    const imagePath = galleryItem.getAttribute('data-image-path');
    const filename = galleryItem.getAttribute('data-filename');
    const imgElement = galleryItem.querySelector('img');
    
    // Store selected image path
    window.uploadedImagePath = imagePath;
    
    // Show selected image preview
    showSelectedImagePreview(imagePath, filename, imgElement.src);
    
    showMessage(`이미지 "선택됨: ${filename}`, 'success');
}

function showSelectedImagePreview(imagePath, filename, imgSrc) {
    // Remove existing preview
    const existingPreview = document.querySelector('.selected-image-preview');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    // Create new preview
    const preview = document.createElement('div');
    preview.className = 'selected-image-preview';
    preview.innerHTML = `
        <img src="${imgSrc}" alt="${filename}">
        <div class="selected-image-info">
            <h5>선택된 이미지</h5>
            <p><strong>파일명:</strong> ${filename}</p>
            <p><strong>경로:</strong> ${imagePath}</p>
        </div>
        <button type="button" class="remove-selected" onclick="removeSelectedImage()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Insert after gallery container
    const galleryContainer = document.querySelector('.gallery-container');
    if (galleryContainer) {
        galleryContainer.parentNode.insertBefore(preview, galleryContainer.nextSibling);
    }
}

function removeSelectedImage() {
    // Remove selection
    document.querySelectorAll('.gallery-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Remove preview
    const preview = document.querySelector('.selected-image-preview');
    if (preview) {
        preview.remove();
    }
    
    // Clear stored path
    window.uploadedImagePath = null;
    
    showMessage('이미지 선택이 취소되었습니다.', 'info');
}

function refreshGallery() {
    loadImageGallery();
    showMessage('갤러리가 새로고침되었습니다.', 'info');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function initializeTemplateSelection() {
    const templateCards = document.querySelectorAll('.template-card');
    const templateContentGroup = document.getElementById('template-content-group');
    const generateBtn = document.getElementById('generate-template-video-btn');
    
    templateCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove selection from all cards
            templateCards.forEach(c => c.classList.remove('selected'));
            
            // Select this card
            this.classList.add('selected');
            
            // Show content input
            templateContentGroup.style.display = 'block';
            generateBtn.disabled = false;
            
            // Store selected template
            window.selectedTemplate = this.getAttribute('data-template');
        });
    });
}

function initializeGenerationButtons() {
    // Text to video
    const textBtn = document.getElementById('generate-text-video-btn');
    if (textBtn) {
        textBtn.addEventListener('click', generateTextVideo);
    }
    
    // Image to video
    const imageBtn = document.getElementById('generate-image-video-btn');
    if (imageBtn) {
        imageBtn.addEventListener('click', generateImageVideo);
    }
    
    // Template video
    const templateBtn = document.getElementById('generate-template-video-btn');
    if (templateBtn) {
        templateBtn.addEventListener('click', generateTemplateVideo);
    }
}

function generateTextVideo() {
    const prompt = document.getElementById('text-video-prompt').value.trim();
    
    if (!prompt) {
        showMessage('동영상 설명을 입력해주세요.', 'error');
        return;
    }
    
    const data = {
        type: 'text-to-video',
        prompt: prompt,
        duration: document.getElementById('text-duration').value,
        aspectRatio: document.getElementById('text-aspect-ratio').value,
        style: document.getElementById('text-style').value,
        cfgScale: document.getElementById('text-cfg-scale').value,
        seed: document.getElementById('text-seed').value || null,
        negativePrompt: document.getElementById('text-negative-prompt').value.trim()
    };
    
    startVideoGeneration(data, 'generate-text-video-btn');
}

function generateImageVideo() {
    if (!window.uploadedImagePath) {
        showMessage('이미지를 먼저 업로드해주세요.', 'error');
        return;
    }
    
    const prompt = document.getElementById('image-video-prompt').value.trim();
    const negativePrompt = document.getElementById('image-negative-prompt').value.trim();
    
    if (!prompt) {
        showMessage('동영상 프롬프트를 입력해주세요.', 'error');
        return;
    }
    
    const data = {
        type: 'image-to-video',
        imagePath: window.uploadedImagePath,
        prompt: prompt,
        negativePrompt: negativePrompt, // negative prompt 추가
        duration: document.getElementById('image-duration').value,
        motionType: document.getElementById('image-motion-type').value
    };
    
    startVideoGeneration(data, 'generate-image-video-btn');
}

function generateTemplateVideo() {
    if (!window.selectedTemplate) {
        showMessage('템플릿을 선택해주세요.', 'error');
        return;
    }
    
    const content = document.getElementById('template-content').value.trim();
    
    if (!content) {
        showMessage('콘텐츠를 입력해주세요.', 'error');
        return;
    }
    
    const data = {
        type: 'template',
        template: window.selectedTemplate,
        content: content
    };
    
    startVideoGeneration(data, 'generate-template-video-btn');
}

function startVideoGeneration(data, buttonId) {
    const button = document.getElementById(buttonId);
    const progressContainer = document.getElementById('video-progress');
    const resultContainer = document.getElementById('video-result');
    
    // Show loading state
    button.classList.add('loading');
    button.disabled = true;
    
    // Show progress
    progressContainer.style.display = 'block';
    resultContainer.style.display = 'none';
    
    // Scroll to progress
    progressContainer.scrollIntoView({ behavior: 'smooth' });
    
    // Simulate progress
    simulateProgress();
    
    // Make API call
    fetch('/api/generate/video', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showVideoResult(result);
            showMessage('동영상이 성공적으로 생성되었습니다!', 'success');
        } else {
            throw new Error(result.error || '동영상 생성에 실패했습니다.');
        }
    })
    .catch(error => {
        showMessage('오류: ' + error.message, 'error');
    })
    .finally(() => {
        // Reset UI
        button.classList.remove('loading');
        button.disabled = false;
        progressContainer.style.display = 'none';
    });
}

function simulateProgress() {
    const progressFill = document.getElementById('video-progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressMessage = document.getElementById('progress-message');
    
    const messages = [
        '프롬프트 분석 중...',
        'AI 모델 처리 중...',
        '동영상 렌더링 중...',
        '최종 처리 중...'
    ];
    
    let progress = 0;
    let messageIndex = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 15 + 5;
        
        if (progress > 100) {
            progress = 100;
            clearInterval(interval);
        }
        
        progressFill.style.width = progress + '%';
        progressPercentage.textContent = Math.round(progress) + '%';
        
        // Update message
        const newMessageIndex = Math.floor(progress / 25);
        if (newMessageIndex !== messageIndex && newMessageIndex < messages.length) {
            messageIndex = newMessageIndex;
            progressMessage.textContent = messages[messageIndex];
        }
        
        if (progress >= 100) {
            progressMessage.textContent = '완료!';
        }
    }, 200);
}

function showVideoResult(data) {
    const resultContainer = document.getElementById('video-result');
    const resultContent = document.getElementById('video-result-content');
    
    resultContent.innerHTML = `
        <div class="video-result-item">
            <video controls>
                <source src="/api/media/download/videos/${data.filename}" type="video/mp4">
                브라우저가 비디오 재생을 지원하지 않습니다.
            </video>
            <div class="video-info">
                <div class="video-details">
                    <h4>${data.title || '생성된 동영상'}</h4>
                    <p>길이: ${data.duration}초 | 생성 시간: ${new Date().toLocaleString()}</p>
                </div>
                <div class="video-actions">
                    <button class="btn btn-secondary" onclick="downloadVideo('${data.filename}')">
                        <i class="fas fa-download"></i> 다운로드
                    </button>
                    <button class="btn btn-secondary" onclick="editVideo('${data.filename}')">
                        <i class="fas fa-edit"></i> 편집하기
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultContainer.style.display = 'block';
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

function setDefaultTab() {
    const urlPath = window.location.pathname;
    let defaultTab = 'text-to-video';
    
    if (urlPath.includes('image-to-video')) {
        defaultTab = 'image-to-video';
    } else if (urlPath.includes('template')) {
        defaultTab = 'template';
    }
    
    // Activate the correct tab if URL specifies one
    const tabBtn = document.querySelector(`[data-tab="${defaultTab}"]`);
    if (tabBtn && !tabBtn.classList.contains('active')) {
        tabBtn.click();
    }
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
    pageHeader.parentNode.insertBefore(messageDiv, pageHeader.nextSibling);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

function downloadVideo(filename) {
    window.open(`/api/media/download/videos/${filename}`, '_blank');
}

function editVideo(filename) {
    sessionStorage.setItem('selectedVideoPath', filename);
    window.location.href = '/video-editor';
}

// Make functions globally available
window.removeImage = removeImage;
window.downloadVideo = downloadVideo;
window.editVideo = editVideo;
window.removeSelectedImage = removeSelectedImage;
window.refreshGallery = refreshGallery;
