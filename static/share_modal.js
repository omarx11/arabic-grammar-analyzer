// Clean Share Modal Implementation - Production Version
function showShareModal(analysisId, shareId, isPublic) {
    const modal = document.getElementById('shareModal');
    const statusIcon = document.getElementById('statusIcon');
    const statusTitle = document.getElementById('statusTitle');
    const statusDesc = document.getElementById('statusDesc');
    const shareUrlSection = document.getElementById('shareUrlSection');
    const shareUrlInput = document.getElementById('shareUrlInput');
    const copyUrlBtn = document.getElementById('copyUrlBtn');
    const makePublicBtn = document.getElementById('makePublicBtn');
    const makePrivateBtn = document.getElementById('makePrivateBtn');
    const closeBtn = document.getElementById('closeShareBtn');
    const closeXBtn = document.getElementById('closeShareModalBtn');
    
    // Set share URL
    const shareUrl = `${window.location.origin}/share/${shareId}`;
    shareUrlInput.value = shareUrl;
    
    // Update UI based on current status
    function updateUI(publicStatus) {
        if (publicStatus) {
            statusIcon.textContent = '🔓';
            statusTitle.textContent = 'عامّة';
            statusDesc.textContent = 'النتيجة متاحة للجميع';
            shareUrlSection.style.display = 'block';
            makePublicBtn.style.display = 'none';
            makePrivateBtn.style.display = 'inline-block';
        } else {
            statusIcon.textContent = '🔒';
            statusTitle.textContent = 'خاصّة';
            statusDesc.textContent = 'النتيجة خاصّة حاليًا';
            shareUrlSection.style.display = 'none';
            makePublicBtn.style.display = 'inline-block';
            makePrivateBtn.style.display = 'none';
        }
    }
    
    // Set initial state
    updateUI(isPublic);
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Make Public Handler
    makePublicBtn.onclick = async function() {
        makePublicBtn.disabled = true;
        const origText = makePublicBtn.textContent;
        makePublicBtn.textContent = 'جارٍ...';
        
        try {
            const res = await fetch(`/analysis/${analysisId}/toggle-public`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            
            if (data.success) {
                updateUI(data.is_public);
                updateHistoryItemUI(analysisId, data.is_public);
                if (window.currentAnalysisId === analysisId) window.currentIsPublic = data.is_public;
            } else {
                throw new Error(data.error || 'تعذّر');
            }
        } catch (err) {
            showNotification('خطأ: ' + err.message, 'error');
        } finally {
            makePublicBtn.disabled = false;
            makePublicBtn.textContent = origText;
        }
    };
    
    // Make Private Handler
    makePrivateBtn.onclick = async function() {
        makePrivateBtn.disabled = true;
        const origText = makePrivateBtn.textContent;
        makePrivateBtn.textContent = 'جارٍ...';
        
        try {
            const res = await fetch(`/analysis/${analysisId}/toggle-public`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            
            if (data.success) {
                updateUI(data.is_public);
                updateHistoryItemUI(analysisId, data.is_public);
                if (window.currentAnalysisId === analysisId) window.currentIsPublic = data.is_public;
            } else {
                throw new Error(data.error || 'تعذّر');
            }
        } catch (err) {
            showNotification('خطأ: ' + err.message, 'error');
        } finally {
            makePrivateBtn.disabled = false;
            makePrivateBtn.textContent = origText;
        }
    };
    
    // Copy Handler
    copyUrlBtn.onclick = function() {
        shareUrlInput.select();
        document.execCommand('copy');
        const orig = copyUrlBtn.textContent;
        copyUrlBtn.textContent = '✓ تم';
        setTimeout(() => { copyUrlBtn.textContent = orig; }, 2000);
    };
    
    // Close Handler
    function closeModal() {
        modal.classList.add('hidden');
        makePublicBtn.onclick = null;
        makePrivateBtn.onclick = null;
        copyUrlBtn.onclick = null;
    }
    
    closeBtn.onclick = closeModal;
    closeXBtn.onclick = closeModal;
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };
}
