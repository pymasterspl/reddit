// Function updating character limit in text fields
function updateCharCount(textField, charCountElement) {
    const maxChars = textField.maxLength;
    const remainingChars = maxChars - textField.value.length;
    charCountElement.innerText = `${remainingChars} characters left`;
}

document.addEventListener("DOMContentLoaded", function() {
    const textFields = document.querySelectorAll("input[type='text'], textarea");

    textFields.forEach(function(textField) {
        const charCountElement = document.createElement("p");
        charCountElement.className = "form-text text-light-emphasis";
        textField.parentNode.appendChild(charCountElement);

        // Initialize the character count display
        updateCharCount(textField, charCountElement);

        // Add event listener to update count on input
        textField.addEventListener("input", function() {
            updateCharCount(textField, charCountElement);
        });
    });
});