// Progress tracking for document generation
function updateProgress(step, text) {
    const stepEl = document.getElementById(`step${step}`);
    const progressText = document.getElementById('progressText');

    console.log(`updateProgress called for step ${step}: ${text}`);

    // Always update progress text first
    if (progressText) {
        progressText.textContent = text;
    }

    if (stepEl) {
        // Check if already completed using data attribute
        const isCompleted = stepEl.getAttribute('data-completed') === 'true';

        if (isCompleted) {
            console.log(`Step ${step} already completed, skipping animation`);
            return;
        }

        // Complete all previous steps immediately if not already completed
        for (let i = 1; i < step; i++) {
            const prevStepEl = document.getElementById(`step${i}`);
            if (prevStepEl && prevStepEl.getAttribute('data-completed') !== 'true') {
                console.log(`Auto-completing previous step ${i}`);
                prevStepEl.setAttribute('data-completed', 'true');
                prevStepEl.classList.remove('bg-gray-200');
                prevStepEl.classList.add('bg-primary-600');

                const prevStepNumber = prevStepEl.querySelector('.step-number');
                const prevStepCheck = prevStepEl.querySelector('.step-check');

                if (prevStepNumber) {
                    prevStepNumber.classList.add('hidden', 'text-white');
                }
                if (prevStepCheck) {
                    prevStepCheck.classList.remove('hidden');
                }

                // Fill the line after previous step
                const prevParentDiv = prevStepEl.parentElement;
                if (prevParentDiv) {
                    const prevLine = prevParentDiv.querySelector('.step-line');
                    if (prevLine) {
                        prevLine.classList.remove('bg-gray-200');
                        prevLine.classList.add('bg-primary-600');
                    }
                }
            }
        }

        // Mark current step as active
        stepEl.classList.remove('bg-gray-200');
        stepEl.classList.add('bg-primary-600');
        const stepNumber = stepEl.querySelector('.step-number');
        if (stepNumber) {
            stepNumber.classList.add('text-white');
        }

        // After a delay, mark as complete
        setTimeout(() => {
            console.log(`Completing step ${step}`);

            // Mark the step element as completed
            stepEl.setAttribute('data-completed', 'true');

            if (stepNumber) {
                stepNumber.classList.add('hidden');
            }
            const stepCheck = stepEl.querySelector('.step-check');
            if (stepCheck) {
                stepCheck.classList.remove('hidden');
                console.log(`Checkmark shown for step ${step}`);
            }

            // Fill the line after this step
            const parentDiv = stepEl.parentElement;
            if (parentDiv) {
                const line = parentDiv.querySelector('.step-line');
                if (line) {
                    line.classList.remove('bg-gray-200');
                    line.classList.add('bg-primary-600');
                }
            }
        }, 800);
    }
}

function showProgressBar() {
    const progressBar = document.getElementById('generationProgress');
    const customizeForm = document.getElementById('customizeForm');

    if (progressBar) progressBar.classList.remove('hidden');
    if (customizeForm) customizeForm.classList.add('hidden');
}

function resetProgressBar() {
    const progressBar = document.getElementById('generationProgress');
    const customizeForm = document.getElementById('customizeForm');

    // Hide progress, show form
    if (progressBar) progressBar.classList.add('hidden');
    if (customizeForm) customizeForm.classList.remove('hidden');

    // Reset all steps
    for (let i = 1; i <= 4; i++) {
        const stepEl = document.getElementById(`step${i}`);
        if (stepEl) {
            stepEl.classList.remove('bg-primary-600');
            stepEl.classList.add('bg-gray-200');
            const stepNumber = stepEl.querySelector('.step-number');
            const stepCheck = stepEl.querySelector('.step-check');
            if (stepNumber) {
                stepNumber.classList.remove('hidden', 'text-white');
            }
            if (stepCheck) {
                stepCheck.classList.add('hidden');
            }
        }
    }

    // Reset lines
    document.querySelectorAll('.step-line').forEach(line => {
        line.classList.remove('bg-primary-600');
        line.classList.add('bg-gray-200');
    });
}

// Make functions globally available
window.updateProgress = updateProgress;
window.showProgressBar = showProgressBar;
window.resetProgressBar = resetProgressBar;

function showProgressError(message) {
    const progressText = document.getElementById('progressText');
    if (progressText) {
        progressText.textContent = message || 'Generation failed';
        progressText.classList.remove('text-gray-600');
        progressText.classList.add('text-red-600', 'font-semibold');
    }

    // Mark current active step as failed (red)
    for (let i = 1; i <= 4; i++) {
        const stepEl = document.getElementById(`step${i}`);
        if (stepEl && stepEl.classList.contains('bg-primary-600')) {
            stepEl.classList.remove('bg-primary-600');
            stepEl.classList.add('bg-red-600');
            break;
        }
    }
}

window.showProgressError = showProgressError;
