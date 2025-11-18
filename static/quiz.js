// Initialize current model on page load
window.addEventListener('load', async function() {
    if (window.initialModel) {
        currentModel = window.initialModel;
        updateModelDisplay();
    } else {
        try {
            const response = await fetch('/current_model');
            const data = await response.json();
            if (data.model) {
                currentModel = data.model;
                updateModelDisplay();
            }
        } catch (error) {
            console.error('Error fetching current model:', error);
        }
    }
});

async function generateQuestion() {
    const topic = document.getElementById('topic-input').value.trim();
    const generateBtn = document.getElementById('generate-btn');
    const quizContent = document.getElementById('quiz-content');
    
    // Disable button
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    // Clear previous content
    quizContent.innerHTML = '<div class="loading-message">Generating question...</div>';
    
    try {
        const response = await fetch('/generate_question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: currentModel,
                topic: topic
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentQuestion = data.question;
            currentContext = data.context;
            
            // Update model if changed
            if (data.model && data.model !== currentModel) {
                currentModel = data.model;
                updateModelDisplay();
            }
            
            // Display question
            displayQuestion(data.question);
        } else {
            quizContent.innerHTML = `<div class="error-message">Error: ${data.error || 'Failed to generate question'}</div>`;
        }
    } catch (error) {
        quizContent.innerHTML = `<div class="error-message">Error: Could not connect to server</div>`;
        console.error('Error:', error);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Question';
    }
}

function displayQuestion(question) {
    const quizContent = document.getElementById('quiz-content');
    
    // Render markdown if available (in case question contains markdown)
    let questionHtml = question;
    if (typeof marked !== 'undefined') {
        questionHtml = marked.parse(question);
    } else {
        questionHtml = escapeHtml(question);
    }
    
    const questionSectionHtml = `
        <div class="question-section">
            <h2>Question</h2>
            <div class="question-text">${questionHtml}</div>
        </div>
        <div class="answer-section">
            <h3>Your Answer</h3>
            <textarea id="answer-input" 
                      placeholder="Type your answer here..." 
                      rows="6"></textarea>
            <button id="submit-btn" class="btn-primary" onclick="submitAnswer()">
                Submit Answer
            </button>
        </div>
        <div id="feedback-section" class="feedback-section" style="display: none;"></div>
    `;
    
    quizContent.innerHTML = questionSectionHtml;
    
    // Focus on answer input
    document.getElementById('answer-input').focus();
}

async function submitAnswer() {
    const answer = document.getElementById('answer-input').value.trim();
    const submitBtn = document.getElementById('submit-btn');
    const feedbackSection = document.getElementById('feedback-section');
    
    if (!answer) {
        alert('Please enter an answer before submitting.');
        return;
    }
    
    // Disable button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Evaluating...';
    
    // Show feedback section
    feedbackSection.style.display = 'block';
    feedbackSection.innerHTML = '<div class="loading-message">Evaluating your answer...</div>';
    
    try {
        const response = await fetch('/submit_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: currentQuestion,
                answer: answer,
                context: currentContext,
                model: currentModel
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update model if changed
            if (data.model && data.model !== currentModel) {
                currentModel = data.model;
                updateModelDisplay();
            }
            
            // Display feedback
            displayFeedback(data.explanation);
        } else {
            feedbackSection.innerHTML = `<div class="error-message">Error: ${data.error || 'Failed to evaluate answer'}</div>`;
        }
    } catch (error) {
        feedbackSection.innerHTML = `<div class="error-message">Error: Could not connect to server</div>`;
        console.error('Error:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Answer';
    }
}

function displayFeedback(explanation) {
    const feedbackSection = document.getElementById('feedback-section');
    
    // Render markdown explanation
    let explanationHtml = explanation;
    if (typeof marked !== 'undefined') {
        explanationHtml = marked.parse(explanation);
    } else {
        explanationHtml = escapeHtml(explanation).replace(/\n/g, '<br>');
    }
    
    const feedbackHtml = `
        <h3>Feedback</h3>
        <div class="explanation">
            ${explanationHtml}
        </div>
        <div class="quiz-actions">
            <button class="btn-secondary" onclick="generateQuestion()">
                New Question
            </button>
            <button class="btn-secondary" onclick="clearQuiz()">
                Clear
            </button>
        </div>
    `;
    
    feedbackSection.innerHTML = feedbackHtml;
}

function clearQuiz() {
    const quizContent = document.getElementById('quiz-content');
    quizContent.innerHTML = `
        <div class="welcome-message">
            <p>Click "Generate Question" to start a quiz based on your course material.</p>
            <p>You can optionally specify a topic to focus the question on.</p>
        </div>
    `;
    currentQuestion = '';
    currentContext = '';
    document.getElementById('topic-input').value = '';
}

async function switchModel(modelName) {
    if (modelName === currentModel) return;
    
    try {
        const response = await fetch('/switch_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: modelName
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentModel = data.model;
            updateModelDisplay();
        } else {
            alert('Error: ' + (data.error || 'Could not switch model'));
        }
    } catch (error) {
        alert('Error: Could not switch model');
        console.error('Error:', error);
    }
}

function updateModelDisplay() {
    // Update current model name
    const modelNameEl = document.getElementById('current-model-name');
    if (modelNameEl) {
        modelNameEl.textContent = currentModel.charAt(0).toUpperCase() + currentModel.slice(1);
    }
    
    // Update active button
    document.querySelectorAll('.model-btn').forEach(btn => {
        if (btn.dataset.model === currentModel) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Allow Enter key to submit answer (with Shift+Enter for new line)
document.addEventListener('DOMContentLoaded', function() {
    // This will be set up when the answer input is created
    document.addEventListener('keydown', function(e) {
        const answerInput = document.getElementById('answer-input');
        if (answerInput && document.activeElement === answerInput) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitAnswer();
            }
        }
    });
});

