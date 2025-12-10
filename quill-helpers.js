// Replace TinyMCE functions with Quill equivalents
function initTinyMCE() {
    // Initialize Quill editor
    editor = new Quill('#post-content', {
        theme: 'snow',
        modules: {
            toolbar: [
                [{ 'header': [1, 2, 3, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                [{ 'align': [] }],
                ['link', 'image'],
                ['clean']
            ]
        }
    });
}

// Get content from Quill
function getEditorContent() {
    return editor ? editor.root.innerHTML : '';
}

// Set content in Quill
function setEditorContent(html) {
    if (editor) {
        editor.root.innerHTML = html;
    }
}
