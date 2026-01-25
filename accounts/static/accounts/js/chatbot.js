const btn = document.getElementById("chatbot-btn");
const box = document.getElementById("chatbot-box");

btn.onclick = () => {
    box.style.display = box.style.display === "block" ? "none" : "block";
};

function sendMessage() {
    let input = document.getElementById("chat-input");
    let msg = input.value.trim();
    if (!msg) return;

    addUserMessage(msg);
    input.value = "";

    fetch("/accounts/chatbot-api/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {
        addBotMessage(data.reply);
    })
    .catch(() => {
        addBotMessage("MediBot sedang tidak bisa menjawab 😢");
    });
}

function addUserMessage(text) {
    document.getElementById("chat-body").innerHTML += `
        <div class="message user">
            <img src="/static/chatbot/user.jpg">
            <div class="bubble">${text}</div>
        </div>`;
}

function addBotMessage(text) {
    document.getElementById("chat-body").innerHTML += `
        <div class="message bot">
            <img src="/static/chatbot/bot.jpg">
            <div class="bubble">${text}</div>
        </div>`;
}

function getCSRFToken() {
    let name = "csrftoken=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i].trim();
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
