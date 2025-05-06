document.addEventListener("DOMContentLoaded", function () {
    let fileInput = document.getElementById('file-input');
    let fileNameDisplay = document.getElementById('file-name');
    let startVoice = document.getElementById("start-voice");

    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            var fileName = event.target.files[0] ? event.target.files[0].name : "No file chosen";
            if (fileNameDisplay) {
                fileNameDisplay.textContent = fileName;
            }
        });
    }

    if (startVoice) {
        startVoice.addEventListener("click", function(event) {
            let statusText = document.getElementById("status-text");
            let recognizedText = document.getElementById("recognized-text");
            let errorText = document.getElementById("error-text");

            if (!statusText || !recognizedText || !errorText) {
                console.error("One or more required elements are missing.");
                return;
            }

            statusText.textContent = "Listening...";

            fetch("/add_expense_voice", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    recognizedText.textContent = "Recognized: " + data.recognized_text + " Refresh To See Log !";
                } else {
                    errorText.textContent = "Error: " + data.error;
                }
                statusText.textContent = "Click mic to start listening";
            })
            .catch(error => {
                errorText.textContent = "Error: Something went wrong.";
                statusText.textContent = "Click mic to start listening"; 
            });
        });
    }
});

// Confirmation pop-ups
function confirmLogout() {
    return confirm("Are you sure you want to log out?");
}

function confirmdeletion(){
    return confirm("All data will be lost upon account deletion. Are you sure?");
}


function downloadReport() {
    window.location.href = "/download_report";
}

document.getElementById('see-more').addEventListener('click', function() {
    window.location.href = "/transactions"; 
});

function fetchGraph(chart) {
    document.getElementById("expense-chart").src = "/generate_report/" + chart + "?t=" + new Date().getTime();
}