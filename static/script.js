// ========================================
// quickcareAI - Voice Intake & Form Logic
// ========================================


// Wait until the HTML page has loaded
document.addEventListener("DOMContentLoaded", function () {


    // ========================================
    // GET HTML ELEMENTS
    // ========================================

    const form = document.getElementById("symptomForm");

    const loadingOverlay =
        document.getElementById("loadingOverlay");

    const submitBtn =
        document.getElementById("submitBtn");

    const micBtn =
        document.getElementById("micBtn");

    const micStatus =
        document.getElementById("micStatus");

    const symptomText =
        document.getElementById("symptom_text");


    // ========================================
    // FORM SUBMISSION
    // ========================================

    form.addEventListener("submit", function () {

        // Show loading screen
        loadingOverlay.style.display = "flex";

        // Prevent multiple submissions
        submitBtn.disabled = true;

    });


    // ========================================
    // SPEECH RECOGNITION SUPPORT CHECK
    // ========================================

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    // Browser does not support speech recognition
    if (!SpeechRecognition) {

        micBtn.style.display = "none";

        micStatus.textContent =
            "Voice input is not supported in this browser. " +
            "Please use Google Chrome or Microsoft Edge.";

        console.log(
            "Speech Recognition is not supported."
        );

        return;
    }


    // ========================================
    // CREATE SPEECH RECOGNITION OBJECT
    // ========================================

    const recognition = new SpeechRecognition();


    // Hindi - India
    recognition.lang = "hi-IN";


    // Only return final speech
    recognition.interimResults = false;


    // Return only the best result
    recognition.maxAlternatives = 1;


    // Only listen for one speech session
    recognition.continuous = false;


    // Track microphone state
    let isListening = false;


    // ========================================
    // MICROPHONE BUTTON
    // ========================================

    micBtn.addEventListener("click", function () {


        // If already listening,
        // stop the microphone
        if (isListening) {

            recognition.stop();

            return;
        }


        try {

            // Start listening
            recognition.start();

            isListening = true;

            // Add CSS class
            micBtn.classList.add("listening");

            // Show status
            micStatus.textContent =
                "🎙️ Listening... speak your symptoms";


        } catch (error) {

            console.error(
                "Could not start microphone:",
                error
            );

            micStatus.textContent =
                "⚠️ Could not start microphone. " +
                "Please try again.";

            isListening = false;
        }

    });


    // ========================================
    // WHEN SPEECH IS RECOGNIZED
    // ========================================

    recognition.addEventListener(
        "result",
        function (event) {


            // Get recognized speech
            const transcript =
                event.results[0][0].transcript;


            console.log(
                "Recognized speech:",
                transcript
            );


            // Add speech to textarea
            if (symptomText.value.trim() !== "") {

                symptomText.value +=
                    " " + transcript;

            } else {

                symptomText.value =
                    transcript;
            }


            // Show success message
            micStatus.textContent =
                "✅ Speech added successfully!";


            // Remove message after 2 seconds
            setTimeout(function () {

                micStatus.textContent = "";

            }, 2000);

        }
    );


    // ========================================
    // SPEECH RECOGNITION ERRORS
    // ========================================

    recognition.addEventListener(
        "error",
        function (event) {


            console.error(
                "Speech recognition error:",
                event.error
            );


            // Microphone permission denied
            if (event.error === "not-allowed") {

                micStatus.textContent =
                    "🚫 Microphone permission denied. " +
                    "Please allow microphone access.";

            }


            // User did not speak
            else if (event.error === "no-speech") {

                micStatus.textContent =
                    "🔇 No speech detected. " +
                    "Please try speaking again.";

            }


            // Browser cannot access microphone
            else if (event.error === "audio-capture") {

                micStatus.textContent =
                    "🎤 Microphone not found. " +
                    "Please check your microphone.";

            }


            // Network problem
            else if (event.error === "network") {

                micStatus.textContent =
                    "🌐 Network error. " +
                    "Please check your internet connection.";

            }


            // Other errors
            else {

                micStatus.textContent =
                    "⚠️ Voice input error: " +
                    event.error;
            }


            // Reset microphone state
            isListening = false;

            micBtn.classList.remove("listening");


            // Clear error after 4 seconds
            setTimeout(function () {

                micStatus.textContent = "";

            }, 4000);

        }
    );


    // ========================================
    // WHEN MICROPHONE STARTS
    // ========================================

    recognition.addEventListener(
        "start",
        function () {

            console.log(
                "Speech recognition started."
            );

            isListening = true;

            micBtn.classList.add("listening");

            micStatus.textContent =
                "🎙️ Listening... speak now";

        }
    );


    // ========================================
    // WHEN MICROPHONE STOPS
    // ========================================

    recognition.addEventListener(
        "end",
        function () {

            console.log(
                "Speech recognition ended."
            );

            isListening = false;

            micBtn.classList.remove("listening");

        }
    );

});