// Video Generation Module
document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generate-video-btn');
    const imageInput = document.getElementById('video-image');
    const imagePreview = document.getElementById('image-preview');
    const promptTextarea = document.getElementById('video-prompt');
    const negativePromptTextarea = document.getElementById('negative-prompt');
    const modeSelect = document.getElementById('video-mode');
    const durationSelect = document.getElementById('video-duration');
    const cfgScaleSlider = document.getElementById('cfg-scale');
    const cfgValue = document.getElementById('cfg-value');
    const resultContainer = document.getElementById('video-result');
    const resultContent = resultContainer.querySelector('.result-content');
    
    let selectedImagePath = null;
    
    // cfg scale 슬라이더 값 표시
    cfgScaleSlider.addEventListener('input', function() {
        cfgValue.textContent = this.value;
    });
    
    // Handle image selection
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.innerHTML = `<img src="${e.target.result}" alt="Selected image">`;
            };
            reader.readAsDataURL(file);
            
            // Upload image first
            uploadImage(file);
        }
    });
    
    // Listen for image from image generation page
    document.addEventListener('loadImageForVideo', function(e) {
        selectedImagePath = e.detail.imagePath;
        // Display the image
        fetch(`/api/media/download/${selectedImagePath.replace(/\\/g, '/')}`)
            .then(response => response.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                imagePreview.innerHTML = `<img src="${url}" alt="Selected image">`;
            });
    });
    
    // Upload image
    async function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                selectedImagePath = data.filepath;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            alert('이미지 업로드 실패: ' + error.message);
        }
    }
    
    // Generate video
    generateBtn.addEventListener('click', async function() {
        const prompt = promptTextarea.value.trim();
        
        if (!selectedImagePath) {
            alert('이미지를 선택해주세요.');
            return;
        }
        
        if (!prompt) {
            alert('동영상 프롬프트를 입력해주세요.');
            return;
        }
        
        const negativePrompt = negativePromptTextarea.value.trim();
        const mode = modeSelect.value;
        const duration = parseInt(durationSelect.value);
        const cfgScale = parseFloat(cfgScaleSlider.value);
        
        showLoading('동영상을 생성하고 있습니다. 시간이 걸릴 수 있습니다...');
        
        try {
            const response = await fetch('/api/generate/video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_path: selectedImagePath,
                    prompt: prompt,
                    negative_prompt: negativePrompt,
                    mode: mode,
                    cfg_scale: cfgScale,
                    duration: duration
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayVideoResult(data);
            } else {
                throw new Error(data.error || '동영상 생성에 실패했습니다.');
            }
        } catch (error) {
            alert('오류: ' + error.message);
        } finally {
            hideLoading();
        }
    });
    
    function displayVideoResult(data) {
        resultContent.innerHTML = `
            <div class="result-item">
                <div>
                    <video controls style="max-width: 600px; max-height: 400px; border-radius: 0.5rem;">
                        <source src="/api/media/download/videos/${data.filename}" type="video/mp4">
                        브라우저가 비디오 재생을 지원하지 않습니다.
                    </video>
                </div>
                <div style="margin-top: 1rem;">
                    <p><strong>파일명:</strong> ${data.filename}</p>
                    <p><strong>프롬프트:</strong> ${data.prompt}</p>
                    <p><strong>길이:</strong> ${data.duration}초</p>
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-primary" onclick="downloadFile('videos/${data.filename}')">
                            <i class="fas fa-download"></i> 다운로드
                        </button>
                        <button class="btn btn-secondary" onclick="useVideoForEdit('${data.filepath}')">
                            <i class="fas fa-edit"></i> 편집하기
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        resultContainer.style.display = 'block';
    }
    
    // Check if there's a selected image from previous page
    const storedImagePath = sessionStorage.getItem('selectedImagePath');
    if (storedImagePath) {
        selectedImagePath = storedImagePath;
        sessionStorage.removeItem('selectedImagePath');
        
        // Trigger load event
        const event = new CustomEvent('loadImageForVideo', { detail: { imagePath: selectedImagePath } });
        document.dispatchEvent(event);
    }
});

// Helper function to use video for editing
window.useVideoForEdit = function(videoPath) {
    sessionStorage.setItem('selectedVideoPath', videoPath);
    window.navigateToPage('video-editor');
    
    setTimeout(() => {
        const event = new CustomEvent('loadVideoForEdit', { detail: { videoPath } });
        document.dispatchEvent(event);
    }, 100);
};