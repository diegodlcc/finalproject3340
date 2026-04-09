// Check if the file loaded properly
console.log("Vaquero Connect custom JavaScript is loaded and ready!");

// Wait for the HTML to fully load before running scripts
//document.addEventListener('DOMContentLoaded', function() {
    
    // Find the H1 tag and add a click effect to it
    //const mainHeading = document.querySelector('h1');
    
    //if (mainHeading) {
    //    mainHeading.addEventListener('click', function() {
    //        alert('Welcome to Vaquero Connect!');
    //    });
    //}
//});

// Post a "tweet" section:
const tweetInput = document.getElementById("tweetInput");
const tweetButton = document.getElementById("tweetButton");
const charLabel = document.getElementById("charLabel");

const MAX_CHAR = 160;

tweetInput.addEventListener("input", updateCharacterCount);

function updateCharacterCount() {
    const currentLength = tweetInput.value.length;
    const remaining = MAX_CHAR - currentLength;

    // Update the character count label
    if (remaining >= 0) {
        charLabel.textContent = `${remaining} characters remaining`;
        charLabel.style.color = "black"; 
        tweetButton.disabled = false; 
        tweetButton.style.opacity = "1";
        tweetButton.style.cursor = "pointer";
    } else {
        charLabel.textContent = `${-remaining} characters over limit`;
        charLabel.style.color = "red"; 
        tweetButton.disabled = true; 
        tweetButton.style.opacity = "0.5";
        tweetButton.style.cursor = "not-allowed";
    }
}   