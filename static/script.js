// Get DOM elements
const arabicTextInput = document.getElementById('arabicText');
const studentNameDropdown = document.getElementById('studentNameDropdown');
const addStudentBtn = document.getElementById('addStudentBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const imageInput = document.getElementById('imageInput');
const uploadImageBtn = document.getElementById('uploadImageBtn');

// Students list element
const studentsList = document.getElementById('studentsList');

// Modal elements
const addStudentModal = document.getElementById('addStudentModal');
const newStudentName = document.getElementById('newStudentName');
const saveStudentBtn = document.getElementById('saveStudentBtn');
const cancelStudentBtn = document.getElementById('cancelStudentBtn');
const closeModalBtn = document.getElementById('closeModalBtn');

// Stats elements
const scoreValue = document.getElementById('scoreValue');
const errorCount = document.getElementById('errorCount');
const wordCount = document.getElementById('wordCount');
const sentenceCount = document.getElementById('sentenceCount');
const errorsSection = document.getElementById('errorsSection');
const errorsTableBody = document.getElementById('errorsTableBody');
const feedbackSection = document.getElementById('feedbackSection');
const feedbackText = document.getElementById('feedbackText');
const historyList = document.getElementById('historyList');

let currentAnalysisId = null;
let currentShareId = null;
let currentIsPublic = false;
let currentOriginalText = '';

// Tab switching
// Store analyze tab state
let analyzeTabState = {
    text: '',
    student: '',
    hasResults: false
};

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        const currentTab = document.querySelector('.tab-content.active')?.id.replace('-tab', '');
        
        // Save analyze tab state when leaving it
        if (currentTab === 'analyze' && arabicTextInput && studentNameDropdown) {
            analyzeTabState.text = arabicTextInput.value || '';
            analyzeTabState.student = studentNameDropdown.value || '';
            const resultsSection = document.getElementById('results');
            analyzeTabState.hasResults = resultsSection ? !resultsSection.classList.contains('hidden') : false;
            
            // Hide results when leaving analyze tab
            if (resultsSection) {
                resultsSection.classList.add('hidden');
            }
        }
        
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active tab content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) targetTab.classList.add('active');
        
        // Handle tab-specific actions
        if (tabName === 'history') {
            loadHistory();
            loadStudentsList();
            // Close inline results when switching to history tab
            const historyResults = document.getElementById('historyResults');
            if (historyResults) historyResults.classList.add('hidden');
        } else if (tabName === 'analyze') {
            // Restore analyze tab state
            if (arabicTextInput) arabicTextInput.value = analyzeTabState.text;
            if (studentNameDropdown) studentNameDropdown.value = analyzeTabState.student;
            
            // Restore results display if they were showing before
            const resultsSection = document.getElementById('results');
            if (resultsSection && analyzeTabState.hasResults) {
                resultsSection.classList.remove('hidden');
            }
        }
    });
});

// Event listeners
analyzeBtn.addEventListener('click', analyzeText);
clearBtn.addEventListener('click', clearAll);
if (uploadImageBtn) uploadImageBtn.addEventListener('click', () => imageInput.click());
if (imageInput) imageInput.addEventListener('change', handleImageUpload);

// Show original text button
const showOriginalTextBtn = document.getElementById('showOriginalTextBtn');
if (showOriginalTextBtn) {
    showOriginalTextBtn.addEventListener('click', toggleOriginalText);
}

// Delete result button
const deleteResultBtn = document.getElementById('deleteResultBtn');
if (deleteResultBtn) {
    deleteResultBtn.addEventListener('click', () => {
        if (currentAnalysisId) {
            deleteCurrentAnalysis();
        } else {
            showNotification('لا يوجد تحليل لحذفه', 'error');
        }
    });
}

// Share result button
const shareResultBtn = document.getElementById('shareResultBtn');
if (shareResultBtn) {
    shareResultBtn.addEventListener('click', () => {
        if (currentAnalysisId && currentShareId) {
            showShareModal(currentAnalysisId, currentShareId, currentIsPublic);
        } else {
            showNotification('لا توجد نتيجة متاحة للمشاركة', 'error');
        }
    });
}

// Close history results button
const closeHistoryResultsBtn = document.getElementById('closeHistoryResults');
if (closeHistoryResultsBtn) closeHistoryResultsBtn.addEventListener('click', closeHistoryResults);

// Student management
if (addStudentBtn) addStudentBtn.addEventListener('click', openAddStudentModal);
if (saveStudentBtn) saveStudentBtn.addEventListener('click', saveNewStudent);
if (cancelStudentBtn) cancelStudentBtn.addEventListener('click', closeAddStudentModal);
if (closeModalBtn) closeModalBtn.addEventListener('click', closeAddStudentModal);

// Load students on page load
loadStudents();

async function analyzeText() {
    const text = arabicTextInput.value.trim();
    const studentName = studentNameDropdown.value || 'غير معروف';
    
    if (!text) {
        showNotification('رجاءً أدخل نصًّا', 'warning');
        return;
    }
    
    if (!studentNameDropdown.value) {
        showConfirm('لم تُحدِّد اسم الطالب. هل تريد المتابعة؟', () => {
            performAnalysis(text, studentName);
        });
        return;
    }
    
    await performAnalysis(text, studentName);
}

async function performAnalysis(text, studentName) {
    showLoading();
    hideResults();
    
    // Store original text
    currentOriginalText = text;
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, student_name: studentName })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error_ar || data.error || 'حدث خطأ في التحليل');
        }
        
        currentAnalysisId = data.analysis_id;
        currentShareId = data.share_id;
        currentIsPublic = data.is_public || false;
        
        displayResults(data);
        
        // Show share and delete buttons in results
        const shareResultBtn = document.getElementById('shareResultBtn');
        const deleteResultBtn = document.getElementById('deleteResultBtn');
        if (shareResultBtn) {
            shareResultBtn.style.display = 'inline-block';
        }
        if (deleteResultBtn) {
            deleteResultBtn.style.display = 'inline-block';
        }
        
    } catch (error) {
        showNotification('خطأ: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Auto-extract text
    showLoading();
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/ocr', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success && data.text) {
            arabicTextInput.value = data.text;
            showNotification('✅ تم استخراج النصّ بنجاح!', 'success');
        } else {
            showNotification('❌ ' + (data.error || 'تعذّر استخراج النصّ'), 'error');
        }
        
    } catch (error) {
        showNotification('خطأ: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Reusable function to populate results display
function populateResultsDisplay(data, containerElement, originalText = null) {
    const result = data;
    
    // Update original text display
    const originalTextContent = containerElement.querySelector('#originalTextContent, .original-text-content');
    if (originalTextContent) {
        // Use provided originalText parameter, or currentOriginalText, or from data
        const textToDisplay = originalText || currentOriginalText || result.original_text || '';
        originalTextContent.textContent = textToDisplay;
    }
    
    // Find or create stats elements within container
    const statsGrid = containerElement.querySelector('.stats-grid');
    if (statsGrid) {
        const statValues = statsGrid.querySelectorAll('.stat-value');
        statValues[0].textContent = result.score || 0;
        statValues[1].textContent = result.error_count || result.errors?.length || 0;
        statValues[2].textContent = result.word_count || 0;
        statValues[3].textContent = result.sentence_count || 0;
    }
    
    // Handle errors table
    const errorsSection = containerElement.querySelector('#errorsSection, .errors-section');
    if (errorsSection) {
        const errorsTableBody = errorsSection.querySelector('tbody');
        
        if (result.errors && result.errors.length > 0) {
            errorsSection.classList.remove('hidden');
            errorsTableBody.innerHTML = '';
            
            result.errors.forEach(error => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong style="color:#dc2626;">${error.word || '-'}</strong></td>
                    <td><strong style="color:#16a34a;">${error.correction || '-'}</strong></td>
                    <td><span class="error-tag">${error.type || 'خطأ'}</span></td>
                    <td>${error.explanation || error.message || '-'}</td>
                `;
                errorsTableBody.appendChild(row);
            });
        } else {
            errorsSection.classList.add('hidden');
        }
    }
    
    // Handle overall feedback
    const feedbackSection = containerElement.querySelector('#overallFeedback, .overall-feedback-section');
    if (feedbackSection) {
        const feedbackText = feedbackSection.querySelector('.overall-feedback-box p, #overallFeedbackText');
        
        if (result.overall_feedback || result.feedback) {
            feedbackSection.classList.remove('hidden');
            if (feedbackText) {
                feedbackText.textContent = result.overall_feedback || result.feedback;
            }
        } else {
            feedbackSection.classList.add('hidden');
        }
    }
}

function displayResults(data) {
    results.classList.remove('hidden');
    populateResultsDisplay(data, results);
    results.scrollIntoView({ behavior: 'smooth' });
}

function toggleOriginalText() {
    const originalTextSection = document.getElementById('originalTextSection');
    const showOriginalTextBtn = document.getElementById('showOriginalTextBtn');
    
    if (originalTextSection && showOriginalTextBtn) {
        const isHidden = originalTextSection.classList.contains('hidden');
        
        if (isHidden) {
            originalTextSection.classList.remove('hidden');
            showOriginalTextBtn.textContent = '✖ إخفاء النصّ الأصلي';
        } else {
            originalTextSection.classList.add('hidden');
            showOriginalTextBtn.textContent = '📝 عرض النصّ الأصلي';
        }
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/history');
        const data = await response.json();
        
        displayHistory(data.history || []);
        
    } catch (error) {
        // Silent fail for history loading
    }
}

function displayHistory(history) {
    if (history && history.length > 0) {
        historyList.innerHTML = '';
        
        history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.setAttribute('data-analysis-id', item.id);
            const publicStatus = item.is_public ? '🔓 عامّة' : '🔒 خاصّة';
            const shareClass = item.is_public ? 'share-btn public' : 'share-btn';
            
            // Display teacher name if available
            const teacherInfo = item.teacher_name ? `<span style="color:#6366f1;">👤 ${item.teacher_name}</span>` : '';
            
            div.innerHTML = `
                <div class="history-info">
                    <strong>${item.student_name}</strong>
                    ${teacherInfo}
                    <span>الدرجة: ${item.score}/100</span>
                    <span>أخطاء: ${item.error_count}</span>
                    <span>${item.created_at}</span>
                    <span class="share-status">${publicStatus}</span>
                </div>
                <div class="history-actions">
                    <button class="btn-sm view-btn" data-id="${item.id}">عرض</button>
                    <button class="btn-sm ${shareClass} share-action-btn" 
                            data-id="${item.id}" 
                            data-share-id="${item.share_id}" 
                            data-is-public="${item.is_public}">🔗 مشاركة</button>
                    <button class="btn-sm pdf-btn" data-id="${item.id}">PDF</button>
                    <button class="btn-sm btn-danger delete-btn" data-id="${item.id}">حذف</button>
                </div>
            `;
            
            // Add event listeners
            const viewBtn = div.querySelector('.view-btn');
            const shareBtn = div.querySelector('.share-action-btn');
            const pdfBtn = div.querySelector('.pdf-btn');
            const deleteBtn = div.querySelector('.delete-btn');
            
            if (viewBtn) viewBtn.addEventListener('click', () => viewAnalysis(item.id));
            if (shareBtn) {
                shareBtn.addEventListener('click', () => {
                    // Convert to boolean properly - handle both string and number values
                    const dataValue = shareBtn.getAttribute('data-is-public');
                    const currentPublic = dataValue === 'true' || dataValue === '1' || dataValue === 1;
                    toggleShare(item.id, item.share_id, currentPublic);
                });
            }
            if (pdfBtn) pdfBtn.addEventListener('click', () => downloadAnalysisPdf(item.id));
            if (deleteBtn) deleteBtn.addEventListener('click', () => deleteAnalysis(item.id));
            
            historyList.appendChild(div);
        });
    } else {
        historyList.innerHTML = '<p style="text-align:center; color:#64748b;">لا توجد تحليلات سابقة.</p>';
    }
}

async function viewAnalysis(id) {
    try {
        const response = await fetch(`/history/${id}`);
        const data = await response.json();
        
        if (data) {
            const historyResults = document.getElementById('historyResults');
            const historyResultsContent = document.getElementById('historyResultsContent');
            
            // Clone the results section structure from analyze tab
            const resultsTemplate = document.getElementById('results');
            const clonedResults = resultsTemplate.cloneNode(true);
            clonedResults.id = 'historyResultsClone';
            clonedResults.classList.remove('hidden');
            
            // Keep the results header but remove share button
            const resultsHeader = clonedResults.querySelector('.results-header');
            if (resultsHeader) {
                const shareBtn = resultsHeader.querySelector('#shareResultBtn');
                if (shareBtn) shareBtn.remove();
                
                // Update the h3 text
                const h3 = resultsHeader.querySelector('h3');
                if (h3) h3.textContent = `📊 تحليل ${data.student_name}`;
                
                // Add event listener to the show original text button in cloned section
                const showOriginalBtn = clonedResults.querySelector('#showOriginalTextBtn');
                if (showOriginalBtn) {
                    // Update original text section ID first before adding listener
                    const originalSection = clonedResults.querySelector('#originalTextSection');
                    if (originalSection) {
                        originalSection.id = 'originalTextSectionHistory';
                        const originalContent = originalSection.querySelector('#originalTextContent');
                        if (originalContent) {
                            originalContent.id = 'originalTextContentHistory';
                            originalContent.className = 'original-text-content';
                        }
                    }
                    
                    showOriginalBtn.id = 'showOriginalTextBtnHistory'; // Change ID to avoid conflicts
                    showOriginalBtn.addEventListener('click', function() {
                        const section = document.getElementById('originalTextSectionHistory');
                        if (section) {
                            const isHidden = section.classList.contains('hidden');
                            if (isHidden) {
                                section.classList.remove('hidden');
                                this.textContent = '✖ إخفاء النصّ الأصلي';
                            } else {
                                section.classList.add('hidden');
                                this.textContent = '📝 عرض النصّ الأصلي';
                            }
                        }
                    });
                }
            }
            
            // Clear and populate
            historyResultsContent.innerHTML = '';
            historyResultsContent.appendChild(clonedResults);
            
            // Use the reusable populate function with original text
            populateResultsDisplay(data.analysis_result, clonedResults, data.original_text);
            
            historyResults.classList.remove('hidden');
            
            // Scroll to results
            historyResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } catch (error) {

        showNotification('❌ تعذّر عرض التحليل', 'error');
    }
}

function closeHistoryResults() {
    const historyResults = document.getElementById('historyResults');
    if (historyResults) {
        historyResults.classList.add('hidden');
    }
}

async function deleteAnalysis(id) {
    showConfirm('هل أنت متأكّد من الحذف؟', async () => {
        try {
            const response = await fetch(`/history/${id}/delete`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                showNotification('✅ تم الحذف بنجاح', 'success');
                loadHistory();
            }
        } catch (error) {
            // Silent fail
        }
    });
}
async function deleteCurrentAnalysis() {
    if (!currentAnalysisId) {
        showNotification('لا يوجد تحليل لحذفه', 'error');
        return;
    }
    
    showConfirm('هل أنت متأكّد من حذف هذا التحليل؟', async () => {
        try {
            const response = await fetch(`/history/${currentAnalysisId}/delete`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                showNotification('✅ تم الحذف بنجاح', 'success');
                // Hide results and clear current analysis
                hideResults();
                currentAnalysisId = null;
                currentShareId = null;
                currentIsPublic = false;
                // Hide buttons
                const shareResultBtn = document.getElementById('shareResultBtn');
                const deleteResultBtn = document.getElementById('deleteResultBtn');
                if (shareResultBtn) shareResultBtn.style.display = 'none';
                if (deleteResultBtn) deleteResultBtn.style.display = 'none';
            } else {
                showNotification('❌ تعذّر الحذف', 'error');
            }
        } catch (error) {

            showNotification('❌ حدث خطأ أثناء الحذف', 'error');
        }
    });
}
async function downloadPdf() {
    if (!currentAnalysisId) {
        alert('لا يوجد تحليل للتنزيل');
        return;
    }
    
    window.location.href = `/export/pdf/${currentAnalysisId}`;
}

async function downloadAnalysisPdf(id) {
    window.location.href = `/export/pdf/${id}`;
}

function clearAll() {
    arabicTextInput.value = '';
    if (studentNameDropdown) studentNameDropdown.value = '';
    if (imageInput) imageInput.value = '';
    
    // Reset share variables
    currentAnalysisId = null;
    currentShareId = null;
    currentIsPublic = false;
    
    // Hide share button
    const shareResultBtn = document.getElementById('shareResultBtn');
    const deleteResultBtn = document.getElementById('deleteResultBtn');
    if (shareResultBtn) {
        shareResultBtn.style.display = 'none';
    }
    if (deleteResultBtn) {
        deleteResultBtn.style.display = 'none';
    }
    
    hideResults();
    arabicTextInput.focus();
}

function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function hideResults() {
    results.classList.add('hidden');
}

// ===== Student Management Functions =====

async function loadStudents() {
    try {
        const response = await fetch('/students');
        const data = await response.json();
        
        if (data.students) {
            studentNameDropdown.innerHTML = '<option value="">اختر اسم الطالب…</option>';
            data.students.forEach(student => {
                const option = document.createElement('option');
                option.value = student.name;
                option.textContent = student.name;
                studentNameDropdown.appendChild(option);
            });
        }
    } catch (error) {
        // Silent fail for loading students
    }
}

function openAddStudentModal() {
    addStudentModal.classList.remove('hidden');
    newStudentName.value = '';
    newStudentName.focus();
}

function closeAddStudentModal() {
    addStudentModal.classList.add('hidden');
    newStudentName.value = '';
}

async function saveNewStudent() {
    const name = newStudentName.value.trim();
    
    if (!name) {
        showNotification('رجاءً أدخل اسم الطالب', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/students/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ تمّت إضافة الطالب بنجاح', 'success');
            closeAddStudentModal();
            loadStudents();
        } else {
            showNotification('❌ ' + (data.error || 'تعذّرت إضافة الطالب'), 'error');
        }
    } catch (error) {
        showNotification('خطأ: ' + error.message, 'error');
    }
}

async function loadStudentsList() {
    try {
        const response = await fetch('/students');
        const data = await response.json();
        
        // Always add "All Analyses" button first
        studentsList.innerHTML = '';
        const allStudentsDiv = document.createElement('div');
        allStudentsDiv.className = 'student-card active';
        allStudentsDiv.textContent = 'جميع التحليلات';
        allStudentsDiv.onclick = () => {
            // Remove active class from all student cards
            document.querySelectorAll('.student-card').forEach(card => card.classList.remove('active'));
            allStudentsDiv.classList.add('active');
            loadHistory();
        };
        studentsList.appendChild(allStudentsDiv);
        
        if (data.students && data.students.length > 0) {
            data.students.forEach(student => {
                const div = document.createElement('div');
                div.className = 'student-card';
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = student.name;
                nameSpan.style.flex = '1';
                nameSpan.onclick = () => {
                    // Remove active class from all student cards
                    document.querySelectorAll('.student-card').forEach(card => card.classList.remove('active'));
                    div.classList.add('active');
                    viewStudentAnalyses(student.name);
                };
                
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = '🗑️';
                deleteBtn.className = 'delete-student-btn';
                deleteBtn.title = 'حذف الطالب';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteStudent(student.name);
                };
                
                div.appendChild(nameSpan);
                div.appendChild(deleteBtn);
                studentsList.appendChild(div);
            });
        }
    } catch (error) {
        // Silent fail
    }
}

async function deleteStudent(studentName) {
    showConfirm(
        `هل أنت متأكّد من حذف الطالب "${studentName}"؟\n\nسيُحذَف أيضًا جميع تحليلات هذا الطالب.`,
        async () => {
            try {
                const response = await fetch(`/students/${encodeURIComponent(studentName)}/delete`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    showNotification('✅ تم حذف الطالب بنجاح', 'success');
                    loadStudentsList();
                    loadStudents();  // Refresh dropdown
                    loadHistory();   // Refresh history
                } else {
                    showNotification('❌ ' + (data.error || 'تعذّر حذف الطالب'), 'error');
                }
            } catch (error) {
                showNotification('❌ حدث خطأ أثناء الحذف', 'error');
            }
        }
    );
}

async function viewStudentAnalyses(studentName) {
    try {
        const response = await fetch(`/students/${encodeURIComponent(studentName)}/analyses`);
        const data = await response.json();
        
        if (data.analyses) {
            // Display only this student's analyses
            displayHistory(data.analyses);
            
            // Scroll to history list
            historyList.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        // Silent fail
    }
}

async function toggleShare(analysisId, shareId, currentStatus) {
    // Open modal with current state
    showShareModal(analysisId, shareId, currentStatus);
}

// Update specific history item UI without reloading all
function updateHistoryItemUI(analysisId, isPublic) {
    // Find the history item with matching data-analysis-id
    const historyItem = document.querySelector(`.history-item[data-analysis-id="${analysisId}"]`);
    
    if (historyItem) {
        // Update status text
        const statusSpan = historyItem.querySelector('.share-status');
        if (statusSpan) {
            statusSpan.textContent = isPublic ? '🔓 عامّة' : '🔒 خاصّة';
        }
        
        // Update share button state
        const shareBtn = historyItem.querySelector('.share-action-btn');
        if (shareBtn) {
            // Update data attribute
            shareBtn.setAttribute('data-is-public', isPublic);
            
            // Update CSS class
            if (isPublic) {
                shareBtn.classList.add('public');
            } else {
                shareBtn.classList.remove('public');
            }
        }
    }
}

function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function hideResults() {
    results.classList.add('hidden');
}


// ===== Modal System =====

function showConfirm(message, onYes, onNo = null) {
    const modal = document.getElementById('confirmModal');
    const messageEl = document.getElementById('confirmMessage');
    const yesBtn = document.getElementById('confirmYesBtn');
    const noBtn = document.getElementById('confirmNoBtn');
    
    messageEl.textContent = message;
    modal.classList.remove('hidden');
    
    yesBtn.onclick = () => { modal.classList.add('hidden'); if (onYes) onYes(); };
    noBtn.onclick = () => { modal.classList.add('hidden'); if (onNo) onNo(); };
    modal.onclick = (e) => { if (e.target === modal) { modal.classList.add('hidden'); if (onNo) onNo(); } };
}


// ===== Modal System =====

function showNotification(message, type = 'info') {
    const modal = document.getElementById('shareModal');
    const urlInput = document.getElementById('shareUrlInput');
    const copyBtn = document.getElementById('copyUrlBtn');
    const closeBtn = document.getElementById('closeShareBtn');
    const closeXBtn = document.getElementById('closeShareModalBtn');
    const toggleBtn = document.getElementById('shareToggleBtn');
    const toggleIcon = document.getElementById('shareToggleIcon');
    const toggleText = document.getElementById('shareToggleText');
    const shareDescription = document.getElementById('shareDescription');
    const shareUrlBox = document.getElementById('shareUrlBox');
    
    if (!toggleBtn) {
        return;
    }
    
    // Track current state
    let currentPublicState = isPublic;
// Update UI based on status
    function updateToggleUI(isPublic) {
        currentPublicState = isPublic;
        
        if (isPublic) {
            toggleIcon.textContent = '🔓';
            toggleText.textContent = 'عامّة';
            shareDescription.textContent = 'النتيجة عامّة';
            toggleBtn.textContent = 'إلغاء المشاركة';
            toggleBtn.classList.add('btn-danger');
            toggleBtn.classList.remove('btn-primary');
            shareUrlBox.style.display = 'flex';
        } else {
            toggleIcon.textContent = '🔒';
            toggleText.textContent = 'خاصّة';
            shareDescription.textContent = 'النتيجة خاصّة حاليًا';
            toggleBtn.textContent = 'تفعيل المشاركة';
            toggleBtn.classList.add('btn-primary');
            toggleBtn.classList.remove('btn-danger');
            shareUrlBox.style.display = 'none';
        }
    }
    
    // Set initial state
    updateToggleUI(isPublic);
    
    const shareUrl = `${window.location.origin}/share/${shareId}`;
    urlInput.value = shareUrl;
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Simple direct click handler
    toggleBtn.onclick = async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Disable button during request
        toggleBtn.disabled = true;
        const originalText = toggleBtn.textContent;
        toggleBtn.textContent = 'جارٍ التحديث…';
        
        try {
            const response = await fetch(`/analysis/${analysisId}/toggle-public`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                updateToggleUI(data.is_public);
                
                // Update current state if this is the current analysis
                if (currentAnalysisId === analysisId) {
                    currentIsPublic = data.is_public;
                }
                
                // Update the specific history item UI
                updateHistoryItemUI(analysisId, data.is_public);
                
                showNotification(
                    data.is_public ? 'تم تفعيل المشاركة العامّة بنجاح' : 'تم إلغاء المشاركة العامّة',
                    'success'
                );
            } else {
                throw new Error(data.error || 'تعذّر تحديث حالة المشاركة');
            }
        } catch (error) {
            toggleBtn.textContent = originalText;
            showNotification('خطأ: ' + error.message, 'error');
        } finally {
            toggleBtn.disabled = false;
        }
    };
    
    console.log('✅ Click handler attached!');
    
    // Copy button handler
    copyBtn.onclick = () => {
        urlInput.select();
        document.execCommand('copy');
        copyBtn.textContent = '✓ تم النسخ';
        setTimeout(() => { copyBtn.textContent = '📋 نسخ'; }, 2000);
    };
    
    // Close handlers
    const closeModal = () => {
        modal.classList.add('hidden');
        // Clean up event listeners
        toggleBtn.onclick = null;
        copyBtn.onclick = null;
    };
    
    closeBtn.onclick = closeModal;
    closeXBtn.onclick = closeModal;
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };
}


// ===== Modal System =====

function showNotification(message, type = 'info') {
    const modal = document.getElementById('notificationModal');
    const icon = document.getElementById('notificationIcon');
    const messageEl = document.getElementById('notificationMessage');
    const okBtn = document.getElementById('notificationOkBtn');
    
    if (type === 'success') {
        icon.textContent = '✅';
    } else if (type === 'error') {
        icon.textContent = '❌';
    } else if (type === 'warning') {
        icon.textContent = '⚠️';
    } else {
        icon.textContent = 'ℹ️';
    }
    
    messageEl.textContent = message;
    modal.classList.remove('hidden');
    
    okBtn.onclick = () => modal.classList.add('hidden');
    modal.onclick = (e) => { if (e.target === modal) modal.classList.add('hidden'); };
}

function showConfirm(message, onYes, onNo = null) {
    const modal = document.getElementById('confirmModal');
    const messageEl = document.getElementById('confirmMessage');
    const yesBtn = document.getElementById('confirmYesBtn');
    const noBtn = document.getElementById('confirmNoBtn');
    
    messageEl.textContent = message;
    modal.classList.remove('hidden');
    
    yesBtn.onclick = () => { modal.classList.add('hidden'); if (onYes) onYes(); };
    noBtn.onclick = () => { modal.classList.add('hidden'); if (onNo) onNo(); };
    modal.onclick = (e) => { if (e.target === modal) { modal.classList.add('hidden'); if (onNo) onNo(); } };
}
