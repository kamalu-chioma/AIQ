
document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 Page Loaded. Checking LocalStorage...");

    // Check if the pre-screen exists (i.e. we are on index.html)
    if (document.getElementById("prescreen")) {
        // Step 1: Check if user has set up profile
        if (!localStorage.getItem("userName") ) {
            console.log("📌 No user data found. Showing pre-screen.");
            showPreScreen();
        } else {
            console.log("✅ User already set up. Redirecting to main app...");
            window.location.href = "/main";
        }
        
    }

    // Check if the main chat app exists (i.e. we are on main.html)
    if (document.getElementById("chat-app")) {
        console.log("🎯 Initializing main app...");
        initializeApp();
    }
});

// 🟢 Ensure Pre-Screen is Visible at First (for index.html)
function showPreScreen() {
    const prescreen = document.getElementById("prescreen");
    const chatApp = document.getElementById("chat-app");
    const avatarSection = document.getElementById("avatar-section");
    
    if (prescreen) prescreen.classList.remove("hidden");
    if (chatApp) chatApp.classList.add("hidden");
    if (avatarSection) avatarSection.classList.add("hidden");
}

// 🟢 Initialize App After Pre-Screen is Completed (for main.html)
function initializeApp() {
    console.log("🎯 Initializing app...");

    const prescreen = document.getElementById("prescreen");
    const chatApp = document.getElementById("chat-app");
    const avatarSection = document.getElementById("avatar-section");

    if (prescreen) prescreen.classList.add("hidden");
    if (chatApp) chatApp.classList.remove("hidden");
    if (avatarSection) avatarSection.classList.remove("hidden");

    loadChats();
    loadChatHistory();
    setAvatar();
    setupWebSocket();
    updateChatTitleFromStorage();
}

// 🟢 Save User Details Before Entering App (called on index.html)
function saveUserDetails() {
    let nameEl = document.getElementById("user-name");
    let avatarEl = document.getElementById("avatar");
    
    if (!nameEl || !avatarEl) {
        console.error("Some required elements are missing on this page.");
        return;
    }
    
    let name = nameEl.value.trim();
    let avatar = avatarEl.value;
    // let coinsInput = coinsEl.value.trim();

    console.log("📝 Saving user details:", { name, avatar });

    // if (!name || !coinsInput) {
    //     alert("⚠️ Please enter your name and the coins you want to track.");
    //     return;
    // }

    // let coins = coinsInput.split(",").map(c => c.trim().toLowerCase());

    // Save user details
    localStorage.setItem("userName", name);
    localStorage.setItem("avatar", avatar);
    // localStorage.setItem("coinsToTrack", JSON.stringify(coins));

    console.log("✅ User data saved! Redirecting to main app...");

    // Redirect to main page after saving user data
    window.location.href = "/main";
}

function setAvatar() {
    let avatar = localStorage.getItem("avatar") || "👤"; // Default to '👤' if no avatar is selected
    document.getElementById("avatar-display").textContent = avatar;
}

// 🟢 Delete Chat Functionality (shared by both pages if needed)
function deleteChat() {
    if (confirm("⚠️ Are you sure you want to delete this chat?")) {
        let chats = JSON.parse(localStorage.getItem("chats")) || {};
        delete chats[activeChatId];
        localStorage.setItem("chats", JSON.stringify(chats));

        // Using FontAwesome icon in console log
        console.log("%c Chat deleted: ", "font-size: 16px; color: red;", "🗑️", activeChatId);
        activeChatId = "chat-1"; // Reset to default chat
        saveChatHistory();
        loadChats();
        loadChatHistory();
    }
}


// Active Chat Session ID (shared variable)
let activeChatId = localStorage.getItem("activeChat") || "chat-1";


// 🟢 Send Message & Save History
function sendMessage() {
    let inputField = document.getElementById("chat-input");
    let message = inputField.value.trim();
    if (!message) return;

    

    let avatar = localStorage.getItem("avatar") || "👤";
    appendMessage(avatar, localStorage.getItem("userName") || "You", message);
    inputField.value = "";

    fetch("/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => appendMessage("", "AIQ", data.response))
    .catch(() => appendMessage("", "AIQ", "Sorry, something went wrong."));

    saveChatHistory();
}

// 🟢 Append Messages to the Chat Box
function appendMessage(avatar, sender, text) {
    let chatBox = document.getElementById("chat-box");
    let msgDiv = document.createElement("div");

    // Apply different classes for user and bot
    msgDiv.classList.add("message", sender === "You" ? "user" : "bot");

    // Set the message content with proper structure
    msgDiv.innerHTML = `
        <div class="message-bubble">
            <strong>${avatar} ${sender}</strong><br>${text}
        </div>
    `;

    // Append the message to the chat box
    chatBox.appendChild(msgDiv);

    // Scroll the chat box to the bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}



// Function to enable the chat title input when pencil is clicked
// function editChatTitle() {
//     let chatTitleInput = document.getElementById("chat-title");
//     chatTitleInput.disabled = false;
//     chatTitleInput.focus();  // Focus on the input to start editing
// }

function editChatTitle() {
    let chatTitleInput = document.getElementById("chat-title");
    chatTitleInput.disabled = false;  // Enable the input field
    chatTitleInput.focus();  // Focus on the input to start editing
}

// 🟢 Make Chat Title Editable & Save to LocalStorage
document.getElementById("chat-title").addEventListener("input", function () {
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    if (chats[activeChatId]) {
        chats[activeChatId].title = this.value;
    }
    localStorage.setItem("chats", JSON.stringify(chats));
});

// 🟢 Update Chat Title from LocalStorage
function updateChatTitleFromStorage() {
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    if (chats[activeChatId] && chats[activeChatId].title) {
        document.getElementById("chat-title").value = chats[activeChatId].title;
    } else {
        document.getElementById("chat-title").value = "New Chat";
    }
}

// 🟢 Save Chat History to LocalStorage (per chat session)
function saveChatHistory() {
    let chatBoxContent = document.getElementById("chat-box").innerHTML;
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    chats[activeChatId] = chats[activeChatId] || {};
    chats[activeChatId].content = chatBoxContent;
    localStorage.setItem("chats", JSON.stringify(chats));
}

// 🟢 Load Active Chat History
function loadChatHistory() {
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    document.getElementById("chat-box").innerHTML = chats[activeChatId]?.content || "";
}

// 🟢 Create a New Chat Session
function newChat() {
    activeChatId = `chat-${Date.now()}`;
    localStorage.setItem("activeChat", activeChatId);
    document.getElementById("chat-box").innerHTML = "";
    saveChatHistory();
    loadChats();
    updateChatTitleFromStorage();
}

// 🟢 Load Chat Sessions & Display in Sidebar with Edit & Delete Options
function loadChats() {
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    let historyDiv = document.getElementById("chat-history");
    historyDiv.innerHTML = "";

    Object.keys(chats).forEach(chatId => {
        let chatWrapper = document.createElement("div");
        chatWrapper.classList.add("chat-item");

        // Editable Chat Title
        let titleInput = document.createElement("input");
        titleInput.type = "text";
        titleInput.classList.add("chat-title-input");
        titleInput.value = chats[chatId]?.title || chatId.replace("chat-", "Chat ");
        titleInput.onchange = function () {
            chats[chatId].title = this.value;
            localStorage.setItem("chats", JSON.stringify(chats));
        };

        // Delete Chat Button
        let deleteBtn = document.createElement("button");
        deleteBtn.innerHTML = "🗑️";
        deleteBtn.classList.add("delete-chat-btn");
        deleteBtn.onclick = function () {
            deleteChat(chatId);
        };

        chatWrapper.appendChild(titleInput);
        chatWrapper.appendChild(deleteBtn);
        historyDiv.appendChild(chatWrapper);

        // Click to load chat
        titleInput.onclick = () => {
            activeChatId = chatId;
            localStorage.setItem("activeChat", activeChatId);
            loadChatHistory();
            updateChatTitleFromStorage();
        };
    });
}

// 🟢 Delete Chat Functionality
function deleteChat(chatId) {
    if (confirm("⚠️ Are you sure you want to delete this chat?")) {
        let chats = JSON.parse(localStorage.getItem("chats")) || {};
        delete chats[chatId];
        localStorage.setItem("chats", JSON.stringify(chats));

        console.log("🗑️ Chat deleted:", chatId);
        activeChatId = "chat-1"; // Reset to default chat
        saveChatHistory();
        loadChats();
        loadChatHistory();
    }
}

// 🟢 Update Chat Title from LocalStorage
function updateChatTitleFromStorage() {
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    if (chats[activeChatId] && chats[activeChatId].title) {
        document.getElementById("chat-title").value = chats[activeChatId].title;
    } else {
        document.getElementById("chat-title").value = "New Chat";
    }
}

// 🟢 Make Chat Title Editable
document.getElementById("chat-title").addEventListener("input", function () {
    let chats = JSON.parse(localStorage.getItem("chats")) || {};
    if (chats[activeChatId]) {
        chats[activeChatId].title = this.value;
    }
    localStorage.setItem("chats", JSON.stringify(chats));
});


// // 🟢 Show Tooltip Only for First-Time Users
// function showTooltip() {
//     if (!localStorage.getItem("tooltipSeen")) {
//         setTimeout(() => {
//             document.getElementById("tooltip").classList.remove("hidden");
//         }, 1000);
//     }
// }

// 🟢 Hide Tooltip & Store Preference
// function hideTooltip() {
//     document.getElementById("tooltip").classList.add("hidden");
//     localStorage.setItem("tooltipSeen", "true");
// }

// 🟢 Setup WebSocket Connection for Live Market Updates
// function setupWebSocket() {
//     const socket = io();
//     socket.on("price_update", data => {
//         let trackedCoins = JSON.parse(localStorage.getItem("coinsToTrack")) || ["bitcoin", "ethereum"];
        
//         if (trackedCoins.includes("bitcoin")) {
//             document.getElementById("btc-price").textContent = `$${data.bitcoin}`;
//         }
//         if (trackedCoins.includes("ethereum")) {
//             document.getElementById("eth-price").textContent = `$${data.ethereum}`;
//         }
//     });
// }

