// Workflow Module
document.addEventListener('DOMContentLoaded', function() {
    const startWorkflowBtn = document.getElementById('start-workflow-btn');
    const imagePromptTextarea = document.getElementById('workflow-image-prompt');
    const videoPromptTextarea = document.getElementById('workflow-video-prompt');
    const durationSelect = document.getElementById('workflow-duration');
    const addSubtitlesCheckbox = document.getElementById('workflow-add-subtitles');
    const subtitleOptions = document.getElementById('workflow-subtitle-options');
    const subtitleTextarea = document.getElementById('workflow-subtitle-text');
    const progressContainer = document.getElementById('workflow-progress');
    const progressSteps = progressContainer.querySelectorAll('.progress-step');
    const progressMessage = progressContainer.querySelector('.progress-message');
    const resultContainer = document.getElementById('workflow-result');
    const resultContent = resultContainer.querySelector('.result-content');
    
    // Toggle subtitle options
    addSubtitlesCheckbox.addEventListener('change', function() {
        subtitleOptions.style.display = this.checked ? 'block' : 'none';
    });
    
    // Start workflow
    startWorkflowBtn.addEventListener('click', async function() {
        const imagePrompt = imagePromptTextarea.value.trim();
        const videoPrompt = videoPromptTextarea.value.trim();
        
        if (!imagePrompt || !videoPrompt) {
            alert('이미지와 동영상 프롬프트를 모두 입력해주세요.');
            return;
        }
        
        const duration = parseInt(durationSelect.value);
        
        // Prepare workflow data
        const workflowData = {
            image_prompt: imagePrompt,
            video_prompt: videoPrompt,
            video_options: {
                negative_prompt: '',
                model: 'default',
                duration: duration
            }
        };
        
        // Add edit options if subtitles are requested
        if (addSubtitlesCheckbox.checked && subtitleTextarea.value.trim()) {
            const subtitleText = subtitleTextarea.value.trim();
            workflowData.edit_options = {
                action: 'add_subtitles',
                params: {
                    subtitles: [{
                        start: 0,
                        end: duration,
                        text: subtitleText
                    }],
                    font_size: 24,
                    font_color: 'white',
                    position: 'bottom'
                }
            };
        }
        
        // Show progress
        progressContainer.style.display = 'block';
        resultContainer.style.display = 'none';
        updateProgress('image', 'active', '이미지를 생성하고 있습니다...');
        
        showLoading('워크플로우를 실행하고 있습니다...');
        
        try {
            const response = await fetch('/api/workflow/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(workflowData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayWorkflowResult(data.result);
            } else {
                throw new Error(data.error || '워크플로우 실행에 실패했습니다.');
            }
        } catch (error) {
            alert('오류: ' + error.message);
            progressContainer.style.display = 'none';
        } finally {
            hideLoading();
        }
    });
    
    function updateProgress(step, status, message) {
        progressSteps.forEach(s => {
            if (s.getAttribute('data-step') === step) {
                s.className = `progress-step ${status}`;
            }
        });
        progressMessage.textContent = message;
    }
    
    function displayWorkflowResult(result) {
        let html = '<div class="workflow-results">';
        
        // Image result
        if (result.image && result.image.status === 'success') {
            updateProgress('image', 'completed', '이미지 생성 완료');
            html += `
                <div class="result-section">
                    <h4>생성된 이미지</h4>
                    <img src="/api/media/download/images/${result.image.filename}" 
                         alt="Generated image" 
                         style="max-width: 400px; max-height: 300px; border-radius: 0.5rem;">
                    <p>프롬프트: ${result.image.prompt}</p>
                </div>
            `;
        }
        
        // Video result
        if (result.video && result.video.status === 'success') {
            updateProgress('video', 'completed', '동영상 생성 완료');
            html += `
                <div class="result-section">
                    <h4>생성된 동영상</h4>
                    <video controls style="max-width: 600px; max-height: 400px; border-radius: 0.5rem;">
                        <source src="/api/media/download/videos/${result.video.filename}" type="video/mp4">
                    </video>
                    <p>프롬프트: ${result.video.prompt}</p>
                    <p>길이: ${result.video.duration}초</p>
                </div>
            `;
        }
        
        // Edited video result
        if (result.edited_video && result.edited_video.status === 'success') {
            updateProgress('edit', 'completed', '편집 완료');
            html += `
                <div class="result-section">
                    <h4>편집된 동영상</h4>
                    <video controls style="max-width: 600px; max-height: 400px; border-radius: 0.5rem;">
                        <source src="/api/media/download/edited/${result.edited_video.filename}" type="video/mp4">
                    </video>
                    <p>자막 추가됨</p>
                </div>
            `;
        }
        
        html += `
            <div style="margin-top: 2rem; text-align: center;">
                <button class="btn btn-primary" onclick="resetWorkflow()">
                    <i class="fas fa-redo"></i> 새 워크플로우 시작
                </button>
            </div>
        </div>`;
        
        resultContent.innerHTML = html;
        resultContainer.style.display = 'block';
        progressMessage.textContent = '워크플로우가 완료되었습니다!';
    }
});

// Reset workflow
window.resetWorkflow = function() {
    document.getElementById('workflow-image-prompt').value = '';
    document.getElementById('workflow-video-prompt').value = '';
    document.getElementById('workflow-subtitle-text').value = '';
    document.getElementById('workflow-add-subtitles').checked = false;
    document.getElementById('workflow-subtitle-options').style.display = 'none';
    document.getElementById('workflow-progress').style.display = 'none';
    document.getElementById('workflow-result').style.display = 'none';
    
    // Reset progress steps
    document.querySelectorAll('.progress-step').forEach(step => {
        step.className = 'progress-step';
    });
};