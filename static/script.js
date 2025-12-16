// Get DOM elements
const arabicTextInput = document.getElementById('arabicText');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const successMessage = document.getElementById('successMessage');

// Statistics elements
const sentenceCount = document.getElementById('sentenceCount');
const wordCount = document.getElementById('wordCount');
const errorCount = document.getElementById('errorCount');
const suggestionCount = document.getElementById('suggestionCount');

// Feedback sections
const errorsSection = document.getElementById('errorsSection');
const suggestionsSection = document.getElementById('suggestionsSection');
const grammarSection = document.getElementById('grammarSection');
const errorsList = document.getElementById('errorsList');
const suggestionsList = document.getElementById('suggestionsList');
const grammarTableBody = document.getElementById('grammarTableBody');

// Event listeners
analyzeBtn.addEventListener('click', analyzeText);
clearBtn.addEventListener('click', clearAll);

// Allow Enter key with Ctrl to trigger analysis
arabicTextInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        analyzeText();
    }
});

async function analyzeText() {
    // Check if user is logged in
    if (!checkLogin()) {
        return;
    }
    
    const text = arabicTextInput.value.trim();
    
    if (!text) {
        alert('الرجاء إدخال نص للتحليل\nPlease enter text to analyze');
        return;
    }
    
    // Show loading, hide results
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    successMessage.classList.add('hidden');
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error_ar || error.error || 'حدث خطأ في التحليل');
        }
        
        const data = await response.json();
        displayResults(data);
        
        // Show success message briefly
        successMessage.classList.remove('hidden');
        setTimeout(() => {
            successMessage.classList.add('hidden');
        }, 3000);
        
    } catch (error) {
        alert('حدث خطأ: ' + error.message + '\nError: ' + error.message);
        console.error('Analysis error:', error);
    } finally {
        loading.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
}

function displayResults(data) {
    // Show results section
    results.classList.remove('hidden');
    
    // Update statistics
    sentenceCount.textContent = data.sentence_count;
    wordCount.textContent = data.word_count;
    errorCount.textContent = data.errors.length;
    suggestionCount.textContent = data.suggestions.length;
    
    // Display errors
    if (data.errors && data.errors.length > 0) {
        errorsSection.classList.remove('hidden');
        
        // Display errors in table format
        const errorsTableBody = document.getElementById('errorsTableBody');
        errorsTableBody.innerHTML = '';
        
        data.errors.forEach(error => {
            const row = document.createElement('tr');
            
            // Extract sentence context if available
            let sentence = error.sentence || 'الجملة الكاملة';
            
            // Highlight the error word in the sentence if both are provided
            if (error.word && error.sentence) {
                sentence = error.sentence.replace(
                    new RegExp(error.word, 'g'),
                    `<mark style="background: #fca5a5; padding: 2px 4px; border-radius: 3px;">${error.word}</mark>`
                );
            }
            
            row.innerHTML = `
                <td style="max-width: 300px;">${sentence}</td>
                <td><strong style="color: #dc2626;">${error.word || '-'}</strong></td>
                <td><strong style="color: #16a34a;">${error.correction || '-'}</strong></td>
                <td><span style="background: #fee2e2; padding: 4px 8px; border-radius: 5px; font-size: 0.9rem;">${error.type || 'خطأ'}</span></td>
                <td style="max-width: 400px;">${error.explanation || error.message || '-'}</td>
            `;
            
            errorsTableBody.appendChild(row);
        });
        
        // Also display in card format for detailed view
        errorsList.innerHTML = '';
        data.errors.forEach(error => {
            const errorItem = createFeedbackItem(error, 'error');
            errorsList.appendChild(errorItem);
        });
    } else {
        errorsSection.classList.add('hidden');
    }
    
    // Display suggestions
    if (data.suggestions && data.suggestions.length > 0) {
        suggestionsSection.classList.remove('hidden');
        suggestionsList.innerHTML = '';
        data.suggestions.forEach(suggestion => {
            const suggestionItem = createFeedbackItem(suggestion, 'suggestion');
            suggestionsList.appendChild(suggestionItem);
        });
    } else {
        suggestionsSection.classList.add('hidden');
    }
    
    // Display grammar analysis
    if (data.grammar_analysis && data.grammar_analysis.length > 0) {
        grammarSection.classList.remove('hidden');
        grammarTableBody.innerHTML = '';
        
        // Show only first 20 words to avoid overwhelming the display
        const wordsToShow = data.grammar_analysis.slice(0, 20);
        
        wordsToShow.forEach(analysis => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${analysis.word}</td>
                <td>${analysis.lemma}</td>
                <td>${analysis.pos || translatePOS(analysis.pos)}</td>
            `;
            grammarTableBody.appendChild(row);
        });
        
        if (data.grammar_analysis.length > 20) {
            const moreRow = document.createElement('tr');
            moreRow.innerHTML = `
                <td colspan="3" style="text-align: center; color: var(--text-secondary); font-style: italic;">
                    ... و ${data.grammar_analysis.length - 20} كلمة أخرى
                </td>
            `;
            grammarTableBody.appendChild(moreRow);
        }
    } else {
        grammarSection.classList.add('hidden');
    }
    
    // Display overall feedback if available
    const overallFeedbackSection = document.getElementById('overallFeedback');
    if (data.overall_feedback) {
        overallFeedbackSection.classList.remove('hidden');
        document.getElementById('overallFeedbackText').textContent = data.overall_feedback;
    } else {
        overallFeedbackSection.classList.add('hidden');
    }
    
    // Scroll to results
    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function createFeedbackItem(item, type) {
    const div = document.createElement('div');
    div.className = `feedback-item ${type}`;
    
    const message = item.message || 'رسالة غير متوفرة';
    const messageEn = item.message_en || '';
    
    let content = `<div class="feedback-message">${message}</div>`;
    
    if (messageEn) {
        content += `<div class="feedback-type">${messageEn}</div>`;
    }
    
    // Add word and correction for errors
    if (item.word) {
        content += `<div class="feedback-detail"><strong>الكلمة:</strong> ${item.word}</div>`;
    }
    
    if (item.correction) {
        content += `<div class="feedback-detail"><strong>✅ التصحيح:</strong> ${item.correction}</div>`;
    }
    
    // Add explanation
    if (item.explanation) {
        content += `<div class="feedback-explanation"><strong>📖 الشرح:</strong> ${item.explanation}</div>`;
    }
    
    // Add example
    if (item.example) {
        content += `<div class="feedback-example"><strong>💡 مثال:</strong> ${item.example}</div>`;
    }
    
    // Add improvement suggestion
    if (item.improvement) {
        content += `<div class="feedback-improvement"><strong>🔧 كيفية التحسين:</strong> ${item.improvement}</div>`;
    }
    
    // Add examples list
    if (item.examples) {
        content += `<div class="feedback-type">أمثلة: ${item.examples.join('، ')}</div>`;
    }
    
    div.innerHTML = content;
    return div;
}

function clearAll() {
    arabicTextInput.value = '';
    results.classList.add('hidden');
    successMessage.classList.add('hidden');
    arabicTextInput.focus();
}

// Translation helpers for Arabic grammar terms
function translatePOS(pos) {
    const translations = {
        'noun': 'اسم',
        'verb': 'فعل',
        'adj': 'صفة',
        'adv': 'ظرف',
        'prep': 'حرف جر',
        'conj': 'حرف عطف',
        'pron': 'ضمير',
        'part': 'أداة',
        'interj': 'حرف نداء'
    };
    return translations[pos] || pos;
}

function translateGender(gender) {
    const translations = {
        'm': 'مذكر',
        'f': 'مؤنث',
        '-': '-'
    };
    return translations[gender] || gender;
}

function translateNumber(number) {
    const translations = {
        's': 'مفرد',
        'd': 'مثنى',
        'p': 'جمع',
        '-': '-'
    };
    return translations[number] || number;
}

// Auto-resize textarea
arabicTextInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Login Management
function checkLogin() {
    // Check if already logged in this session
    const isLoggedIn = sessionStorage.getItem('isLoggedIn');
    
    if (isLoggedIn === 'true') {
        return true;
    }
    
    // Show login dialog
    return showLoginDialog();
}

function showLoginDialog() {
    const username = prompt('اسم المستخدم / Username:');
    
    if (username === null) {
        // User cancelled
        return false;
    }
    
    const password = prompt('كلمة المرور / Password:');
    
    if (password === null) {
        // User cancelled
        return false;
    }
    
    // Check credentials
    if (username === 'admin' && password === '1234') {
        // Successful login
        sessionStorage.setItem('isLoggedIn', 'true');
        alert('✅ تم تسجيل الدخول بنجاح!\n✅ Login successful!');
        return true;
    } else {
        // Failed login
        alert('❌ اسم المستخدم أو كلمة المرور غير صحيحة!\n❌ Incorrect username or password!');
        return false;
    }
}

function logout() {
    sessionStorage.removeItem('isLoggedIn');
    alert('تم تسجيل الخروج بنجاح\nLogged out successfully');
    clearAll();
}
