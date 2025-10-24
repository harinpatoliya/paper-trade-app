const portfolioTable = document.getElementById("portfolio-table").getElementsByTagName("tbody")[0];
const orderForm = document.getElementById("order-form");
const sellModal = document.getElementById("sell-modal");
const sellForm = document.getElementById("sell-form");
const closeModal = document.getElementsByClassName("close")[0];
const usernameSpan = document.getElementById("username");
const accountIdSpan = document.getElementById("account-id");
const themeToggle = document.getElementById("theme-toggle");

// Function to fetch and display the portfolio
async function fetchPortfolio() {
    const response = await fetch("/api/portfolio");
    const portfolio = await response.json();

    // Clear the table
    portfolioTable.innerHTML = "";

    // Get all symbols to fetch quotes in a single request
    const symbols = portfolio.map(item => item.symbol).join(",");
    if (!symbols) {
        return;
    }

    const quoteResponse = await fetch(`/api/quotes?symbols=${symbols}`);
    const quotes = await quoteResponse.json();

    // Create a map of symbols to their current prices
    const priceMap = {};
    if (quotes.d) {
        quotes.d.forEach(quote => {
            priceMap[quote.n] = quote.v.lp;
        });
    }

    // Populate the table with portfolio data
    for (const item of portfolio) {
        const row = portfolioTable.insertRow();
        row.insertCell(0).innerText = item.symbol;
        row.insertCell(1).innerText = item.quantity;
        row.insertCell(2).innerText = item.avg_price;

        const currentPrice = priceMap[item.symbol] || 0;
        const pnl = (currentPrice - item.avg_price) * item.quantity;
        const pnlPercent = ((pnl / (item.avg_price * item.quantity)) * 100).toFixed(2);

        row.insertCell(3).innerText = currentPrice;
        row.insertCell(4).innerText = pnl.toFixed(2);
        row.insertCell(5).innerText = `${pnlPercent}%`;

        // Notes
        const notesCell = row.insertCell(6);
        notesCell.innerText = item.notes;
        const editButton = document.createElement("button");
        editButton.innerText = "Edit";
        editButton.addEventListener("click", () => editNotes(item.symbol, item.notes));
        notesCell.appendChild(editButton);

        // Add a sell button
        const sellButton = document.createElement("button");
        sellButton.innerText = "Sell";
        sellButton.addEventListener("click", () => openSellModal(item.symbol, item.quantity));
        row.insertCell(7).appendChild(sellButton);
    }
}

// Function to edit notes
async function editNotes(symbol, currentNotes) {
    const newNotes = prompt("Enter new notes:", currentNotes);
    if (newNotes !== null) {
        const response = await fetch("/api/portfolio/notes", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ symbol, notes: newNotes })
        });
        const result = await response.json();
        alert(result.message);
        fetchPortfolio();
    }
}

// Function to open the sell modal
function openSellModal(symbol, maxQuantity) {
    document.getElementById("sell-symbol").value = symbol;
    document.getElementById("sell-quantity").max = maxQuantity;
    sellModal.style.display = "block";
}

// Function to close the sell modal
closeModal.onclick = function() {
    sellModal.style.display = "none";
}

window.onclick = function(event) {
    if (event.target == sellModal) {
        sellModal.style.display = "none";
    }
}

// Function to place a sell order
async function placeSellOrder(event) {
    event.preventDefault();

    const symbol = document.getElementById("sell-symbol").value;
    const quantity = document.getElementById("sell-quantity").value;
    const orderType = document.getElementById("sell-order-type").value;
    const price = document.getElementById("sell-price").value;

    const order = {
        symbol,
        quantity: -parseInt(quantity),
        order_type: orderType,
        price: parseFloat(price)
    };

    const response = await fetch("/api/orders", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(order)
    });

    const result = await response.json();
    alert(result.message);
    sellModal.style.display = "none";
    fetchPortfolio();
}

// Function to place a buy order
async function placeBuyOrder(event) {
    event.preventDefault();

    const symbol = document.getElementById("symbol").value;
    const quantity = document.getElementById("quantity").value;
    const orderType = document.getElementById("order-type").value;
    const price = document.getElementById("price").value;

    const order = {
        symbol,
        quantity: parseInt(quantity),
        order_type: orderType,
        price: parseFloat(price)
    };

    const response = await fetch("/api/orders", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(order)
    });

    const result = await response.json();
    alert(result.message);
    fetchPortfolio();
}

// Function to fetch and display user profile
async function fetchProfile() {
    const response = await fetch("/api/profile");
    const profile = await response.json();
    usernameSpan.innerText = profile.username;
    accountIdSpan.innerText = profile.account_id;
}

// Function to toggle theme
function toggleTheme() {
    document.body.classList.toggle("dark-mode");
}

// Add event listeners
orderForm.addEventListener("submit", placeBuyOrder);
sellForm.addEventListener("submit", placeSellOrder);
themeToggle.addEventListener("change", toggleTheme);


// Initial data fetch
fetchProfile();
fetchPortfolio();
setInterval(fetchPortfolio, 30000);
