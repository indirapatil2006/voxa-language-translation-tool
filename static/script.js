
/* ==========================================
   VOXA - LANGUAGE TRANSLATION TOOL
   Complete JavaScript Code
========================================== */


/* ==========================================
   1. ELEMENTS
========================================== */

const themeToggle = document.getElementById("themeToggle");
const inputText = document.getElementById("inputText");
const charCount = document.getElementById("charCount");

const sourceLanguage =
    document.getElementById("sourceLanguage");

const targetLanguage =
    document.getElementById("targetLanguage");

const outputText =
    document.getElementById("outputText");

const outputStatus =
    document.getElementById("outputStatus");

const translateButton =
    document.getElementById("translateButton");


/* ==========================================
   2. LIGHT AND DARK MODE
========================================== */

themeToggle.addEventListener("click", () => {

    document.body.classList.toggle("dark");

    const icon = themeToggle.querySelector("i");

    icon.className = document.body.classList.contains("dark")
        ? "fa-solid fa-sun"
        : "fa-solid fa-moon";

});


/* ==========================================
   3. CHARACTER COUNTER
========================================== */

inputText.addEventListener("input", () => {

    charCount.textContent =
        `${inputText.value.length} / 5000`;

});


/* ==========================================
   4. CLEAR TEXT
========================================== */

document.getElementById("clearButton")
.addEventListener("click", () => {

    inputText.value = "";

    charCount.textContent = "0 / 5000";

    outputText.innerHTML = `
        <span class="output-placeholder">
            Your translation will appear here...
        </span>
    `;

    outputStatus.textContent = "Waiting for your words";

    window.speechSynthesis?.cancel();

});


/* ==========================================
   5. SWAP LANGUAGES
========================================== */

document.getElementById("swapButton")
.addEventListener("click", () => {

    const source = sourceLanguage.value;
    const target = targetLanguage.value;

    if (source === target) return;

    const translatedText = outputText.innerText.trim();

    const hasTranslation =
        translatedText &&
        !translatedText.includes("Your translation will appear here");

    sourceLanguage.value = target;
    targetLanguage.value = source;

    if (inputText.value.trim() && hasTranslation) {

        inputText.value = translatedText;

        charCount.textContent =
            `${inputText.value.length} / 5000`;

        outputText.innerHTML = `
            <span class="output-placeholder">
                Your translation will appear here...
            </span>
        `;

        outputStatus.textContent = "Ready for translation";

    }

});


/* ==========================================
   6. COPY TRANSLATION
========================================== */

document.getElementById("copyButton")
.addEventListener("click", async () => {

    const output = outputText.innerText.trim();

    if (
        !output ||
        output.includes("Your translation will appear here")
    ) {

        outputStatus.textContent = "Nothing to copy";

        return;

    }

    try {

        await navigator.clipboard.writeText(output);

        outputStatus.textContent = "Copied successfully!";

    } catch (error) {

        console.error("Copy error:", error);

        outputStatus.textContent = "Unable to copy text";

    }

});


/* ==========================================
   7. TEXT TO SPEECH
========================================== */

const synth = window.speechSynthesis;


function getAvailableVoices() {

    return synth ? synth.getVoices() : [];

}


function findVoice(language) {

    const voices = getAvailableVoices();

    const normalizedLanguage = language.toLowerCase();

    return voices.find(voice =>
        voice.lang.toLowerCase() === normalizedLanguage
    ) || voices.find(voice =>
        voice.lang.toLowerCase().startsWith(
            normalizedLanguage.split("-")[0]
        )
    ) || null;

}


function speakText(text, language) {

    text = text.trim();

    if (!text) {

        alert("There is no text available to speak!");

        return;

    }

    if (!("speechSynthesis" in window)) {

        alert("Your browser does not support text-to-speech.");

        return;

    }

    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.lang = language;
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;

    const selectedVoice = findVoice(language);

    if (selectedVoice) {

        utterance.voice = selectedVoice;

        console.log("Selected voice:", selectedVoice.name);

    } else {

        console.warn("No matching voice found for:", language);

    }

    utterance.onstart = () => {
        console.log("Voxa: Speech started");
    };

    utterance.onend = () => {
        console.log("Voxa: Speech completed");
    };

    utterance.onerror = (event) => {
        console.error("Voxa speech error:", event.error);
    };

    synth.resume();

    synth.speak(utterance);

}


if (synth) {

    synth.addEventListener("voiceschanged", () => {

        console.log("Available speech voices:", getAvailableVoices());

    });

}


/* ==========================================
   7A. SPEAK INPUT TEXT
========================================== */

document.getElementById("speakInput")
.addEventListener("click", () => {

    speakText(
        inputText.value,
        sourceLanguage.value
    );

});


/* ==========================================
   7B. SPEAK OUTPUT TEXT
========================================== */

document.getElementById("speakOutput")
.addEventListener("click", () => {

    const output = outputText.innerText.trim();

    if (
        !output ||
        output.includes("Your translation will appear here")
    ) {

        alert("Please translate some text first!");

        return;

    }

    speakText(
        output,
        targetLanguage.value
    );

});


/* ==========================================
   8. TRANSLATION API
========================================== */

translateButton.addEventListener("click", async () => {

    const text = inputText.value.trim();

    const source = sourceLanguage.value;
    const target = targetLanguage.value;

    if (!text) {

        alert("Please enter some text first!");

        return;

    }

    if (source === target) {

        outputText.textContent = text;

        outputStatus.textContent =
            "Both languages are the same";

        return;

    }

    // MyMemory has a 500-byte per-query limit.

    if (new TextEncoder().encode(text).length > 500) {

        alert(
            "Please shorten your text to 500 bytes or less for now."
        );

        return;

    }

    // Show loading state

    const originalButtonContent = translateButton.innerHTML;

    translateButton.disabled = true;

    translateButton.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin"></i> Translating...';

    outputStatus.textContent = "Translating your text...";

    outputText.textContent = "Please wait...";

    if (synth) {
        synth.cancel();
    }

    try {

        const response = await fetch("/translate", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                text: text,

                source: source,

                target: target

            })

        });

        const result = await response.json();

        if (!response.ok) {

            throw new Error(
                result.error || "Translation failed."
            );

        }

        if (!result.translation) {

            throw new Error("No translation was returned.");

        }

        // Display translated text

        outputText.textContent = result.translation;

        outputStatus.textContent =
            "Translation completed successfully!";

        console.log("Original text:", text);

        console.log("Translated text:", result.translation);

        console.log("From:", source);

        console.log("To:", target);

    } catch (error) {

        console.error("Translation error:", error);

        outputText.innerHTML = `
            <span class="output-placeholder">
                Your translation will appear here...
            </span>
        `;

        outputStatus.textContent = error.message;

    } finally {

        translateButton.disabled = false;

        translateButton.innerHTML = originalButtonContent;

    }

});


/* ==========================================
   9. VOXA INITIALIZATION
========================================== */

console.log("Voxa loaded successfully!");

console.log("Speech support:", "speechSynthesis" in window);

console.log("Available voices:", getAvailableVoices());
