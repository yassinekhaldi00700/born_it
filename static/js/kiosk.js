/* Borne de services UEMF - kiosk behaviour shared by every page.
 *
 * <body> options (data attributes):
 *   data-auto-return="100000"   go back to "/" after this many ms (0 = never)
 *   data-short-card-alert       alert when Enter is pressed with fewer than 8 characters
 * Any element with [data-countdown] shows the seconds left before the auto return.
 */

function goToIndexPage() {
    window.location.href = "/";
}

// Card reader on a French AZERTY layout sends symbols instead of digits
function fixCardInput(input) {
    var symbolToDigit = {
        '&': '1', 'é': '2', '"': '3', "'": '4', '(': '5',
        '-': '6', 'è': '7', '_': '8', 'ç': '9', 'à': '0'
    };
    input.value = input.value.split('').map(function (c) { return symbolToDigit[c] || c; }).join('');
}

function handleKeyPress(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        var userInput = document.getElementById("hidden_input").value;
        if (userInput.length >= 8) {
            document.getElementById("input_form").submit();
            document.getElementById("hidden_input").value = "";
        } else if (document.body.hasAttribute("data-short-card-alert")) {
            alert("Veuillez entrer au moins 8 caractères.");
        }
    }
}

(function () {
    // Keep the card reader input focused
    setInterval(function () {
        document.getElementById("hidden_input").focus();
    }, 1000);

    // Automatic return to the home screen
    var delay = parseInt(document.body.getAttribute("data-auto-return") || "0", 10);
    if (delay > 0) {
        setInterval(goToIndexPage, delay);

        var secondsLeft = Math.round(delay / 1000);
        var counters = document.querySelectorAll("[data-countdown]");
        counters.forEach(function (c) { c.textContent = secondsLeft; });
        setInterval(function () {
            secondsLeft = Math.max(0, secondsLeft - 1);
            counters.forEach(function (c) { c.textContent = secondsLeft; });
        }, 1000);
    }
})();
