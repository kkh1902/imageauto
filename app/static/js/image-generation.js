// Image Generation Module
document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generate-image-btn');
    const promptTextarea = document.getElementById('image-prompt');
    const aspectRatioSelect = document.getElementById('aspect-ratio');
    const resultContainer = document.getElementById('image-result');
    const resultContent = resultContainer.querySelector('.result-content');
    
    generateBtn.addEventListener('click', async function() {
        const prompt = promptTextarea.value.trim();
        
        if (!prompt) {
            alert('프롬프트를 입력해주세요.');
            return;
        }
        
        const aspectRatio = aspectRatioSelect.value;
        
        // Show loading
        showLoading('이미지를 생성하고 있습니다...');
        
        try {
            const response = await fetch('/api/generate/image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    aspect_ratio: aspectRatio
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayImageResult(data);
            } else {
                throw new Error(data.error || '이미지 생성에 실패했습니다.');
            }
        } catch (error) {
            alert('오류: ' + error.message);
        } finally {
            hideLoading();
        }
    });
    
    function displayImageResult(data) {
        resultContent.innerHTML = `
            <div class="result-item">
                <div>
                    <img src="/api/media/download/images/${data.filename}" 
                         alt="Generated image" 
                         style="max-width: 400px; max-height: 400px; border-radius: 0.5rem;">
                </div>
                <div style="margin-top: 1rem;">
                    <p><strong>파일명:</strong> ${data.filename}</p>
                    <p><strong>프롬프트:</strong> ${data.prompt}</p>
                    <p><strong>비율:</strong> ${data.aspect_ratio}</p>
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-primary" onclick="downloadFile('images/${data.filename}')">
                            <i class="fas fa-download"></i> 다운로드
                        </button>
                        <button class="btn btn-secondary" onclick="useImageForVideo('${data.filepath}')">
                            <i class="fas fa-video"></i> 동영상 만들기
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        resultContainer.style.display = 'block';
    }
});

// Helper function to use image for video generation
window.useImageForVideo = function(imagePath) {
    // Store image path in session storage
    sessionStorage.setItem('selectedImagePath', imagePath);
    // Navigate to video generation page
    window.navigateToPage('video-generation');
    
    // Trigger custom event to load image
    setTimeout(() => {
        const event = new CustomEvent('loadImageForVideo', { detail: { imagePath } });
        document.dispatchEvent(event);
    }, 100);
};

// Download file helper
window.downloadFile = function(filepath) {
    window.open(`/api/media/download/${filepath}`, '_blank');
};