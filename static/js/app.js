// Handle Image Upload and Display Preview
function handleImageUpload(event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = function (e) {
        const image = document.getElementById('imagePreview');
        image.style.display = 'block';
        image.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Extract Text using Flask and Tesseract
function extractText() {
    const fileInput = document.getElementById('imageUpload');
    const file = fileInput.files[0];
    
    if (file) {
        const formData = new FormData();
        formData.append('image', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.extracted_text) {
                document.getElementById('resultText').innerText = data.extracted_text;
                const modal = new bootstrap.Modal(document.getElementById('resultModal'));
                modal.show();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    } else {
        alert('Please upload an image first!');
    }
}
