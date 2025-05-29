// Video Editor Module
document.addEventListener('DOMContentLoaded', function() {
    const editBtn = document.getElementById('edit-video-btn');
    const videoInput = document.getElementById('edit-video');
    const videoPreview = document.getElementById('video-preview');
    const editActionSelect = document.getElementById('edit-action');
    const resultContainer = document.getElementById('edit-result');
    const resultContent = resultContainer.querySelector('.result-content');
    
    let selectedVideoPath = null;
    let subtitles = [];
    
    // Option containers
    const subtitleOptions = document.getElementById('subtitle-options');
    const trimOptions = document.getElementById('trim-options');
    const mergeOptions = document.getElementById('merge-options');
    const watermarkOptions = document.getElementById('watermark-options');
    
    // Handle video selection
    videoInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            videoPreview.innerHTML = `<video controls src="${url}"></video>`;
            
            // Upload video
            uploadVideo(file);
        }
    });
    
    // Listen for video from video generation page
    document.addEventListener('loadVideoForEdit', function(e) {
        selectedVideoPath = e.detail.videoPath;
        // Display the video
        fetch(`/api/media/download/${selectedVideoPath.replace(/\\/g, '/')}`)
            .then(response => response.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                videoPreview.innerHTML = `<video controls src="${url}"></video>`;
            });
    });
    
    // Handle edit action change
    editActionSelect.addEventListener('change', function() {
        // Hide all options
        document.querySelectorAll('.edit-options').forEach(opt => opt.style.display = 'none');
        
        // Show selected option
        switch(this.value) {
            case 'add_subtitles':
                subtitleOptions.style.display = 'block';
                break;
            case 'trim':
                trimOptions.style.display = 'block';
                break;
            case 'merge':
                mergeOptions.style.display = 'block';
                break;
            case 'add_watermark':
                watermarkOptions.style.display = 'block';
                break;
        }
    });
    
    // Subtitle management
    const addSubtitleBtn = document.getElementById('add-subtitle-btn');
    const subtitlesContainer = document.getElementById('subtitles-container');
    
    addSubtitleBtn.addEventListener('click', function() {
        const subtitleId = Date.now();
        const subtitleItem = document.createElement('div');
        subtitleItem.className = 'subtitle-item';
        subtitleItem.innerHTML = `
            <input type="number" placeholder="시작(초)" step="0.1" data-id="${subtitleId}" data-type="start">
            <input type="number" placeholder="종료(초)" step="0.1" data-id="${subtitleId}" data-type="end">
            <input type="text" placeholder="자막 텍스트" data-id="${subtitleId}" data-type="text">
            <button onclick="removeSubtitle(${subtitleId})"><i class="fas fa-trash"></i></button>
        `;
        subtitlesContainer.appendChild(subtitleItem);
    });
    
    window.removeSubtitle = function(id) {
        const item = document.querySelector(`.subtitle-item input[data-id="${id}"]`).parentElement;
        item.remove();
    };
    
    // Handle watermark opacity
    const opacitySlider = document.getElementById('watermark-opacity');
    const opacityValue = document.getElementById('opacity-value');
    
    opacitySlider.addEventListener('input', function() {
        opacityValue.textContent = this.value;
    });
    
    // Upload video
    async function uploadVideo(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                selectedVideoPath = data.filepath;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            alert('동영상 업로드 실패: ' + error.message);
        }
    }
    
    // Edit video
    editBtn.addEventListener('click', async function() {
        if (!selectedVideoPath) {
            alert('동영상을 선택해주세요.');
            return;
        }
        
        const action = editActionSelect.value;
        const editOptions = {
            action: action,
            params: {}
        };
        
        // Collect parameters based on action
        switch(action) {
            case 'add_subtitles':
                const subtitleInputs = subtitlesContainer.querySelectorAll('.subtitle-item');
                const subtitleList = [];
                
                subtitleInputs.forEach(item => {
                    const start = item.querySelector('input[data-type="start"]').value;
                    const end = item.querySelector('input[data-type="end"]').value;
                    const text = item.querySelector('input[data-type="text"]').value;
                    
                    if (start && end && text) {
                        subtitleList.push({
                            start: parseFloat(start),
                            end: parseFloat(end),
                            text: text
                        });
                    }
                });
                
                if (subtitleList.length === 0) {
                    alert('자막을 추가해주세요.');
                    return;
                }
                
                editOptions.params = {
                    subtitles: subtitleList,
                    font_size: parseInt(document.getElementById('font-size').value),
                    font_color: document.getElementById('font-color').value,
                    position: 'bottom'
                };
                break;
                
            case 'trim':
                editOptions.params = {
                    start_time: parseFloat(document.getElementById('trim-start').value),
                    end_time: parseFloat(document.getElementById('trim-end').value)
                };
                break;
                
            case 'merge':
                const additionalVideos = document.getElementById('additional-videos').files;
                if (additionalVideos.length === 0) {
                    alert('합칠 동영상을 선택해주세요.');
                    return;
                }
                // Upload additional videos first
                // This would need implementation
                break;
                
            case 'add_watermark':
                const watermarkFile = document.getElementById('watermark-image').files[0];
                if (!watermarkFile) {
                    alert('워터마크 이미지를 선택해주세요.');
                    return;
                }
                // Upload watermark first
                // This would need implementation
                editOptions.params = {
                    watermark_path: 'path/to/watermark',
                    position: document.getElementById('watermark-position').value,
                    opacity: parseFloat(document.getElementById('watermark-opacity').value)
                };
                break;
        }
        
        showLoading('동영상을 편집하고 있습니다...');
        
        try {
            const response = await fetch('/api/edit/video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_path: selectedVideoPath,
                    edit_options: editOptions
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayEditResult(data);
            } else {
                throw new Error(data.error || '동영상 편집에 실패했습니다.');
            }
        } catch (error) {
            alert('오류: ' + error.message);
        } finally {
            hideLoading();
        }
    });
    
    function displayEditResult(data) {
        resultContent.innerHTML = `
            <div class="result-item">
                <div>
                    <video controls style="max-width: 600px; max-height: 400px; border-radius: 0.5rem;">
                        <source src="/api/media/download/edited/${data.filename}" type="video/mp4">
                        브라우저가 비디오 재생을 지원하지 않습니다.
                    </video>
                </div>
                <div style="margin-top: 1rem;">
                    <p><strong>파일명:</strong> ${data.filename}</p>
                    <p><strong>편집 작업:</strong> ${editActionSelect.options[editActionSelect.selectedIndex].text}</p>
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-primary" onclick="downloadFile('edited/${data.filename}')">
                            <i class="fas fa-download"></i> 다운로드
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        resultContainer.style.display = 'block';
    }
    
    // Check if there's a selected video from previous page
    const storedVideoPath = sessionStorage.getItem('selectedVideoPath');
    if (storedVideoPath) {
        selectedVideoPath = storedVideoPath;
        sessionStorage.removeItem('selectedVideoPath');
        
        // Trigger load event
        const event = new CustomEvent('loadVideoForEdit', { detail: { videoPath: selectedVideoPath } });
        document.dispatchEvent(event);
    }
});