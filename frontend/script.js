const portfolioTable = document.getElementById("portfolio-table").getElementsByTagName("tbody")[0];
const ordersTable = document.getElementById("orders-table").getElementsByTagName("tbody")[0];
const historyTable = document.getElementById("history-table").getElementsByTagName("tbody")[0];
const orderForm = document.getElementById("order-form");
const sellModal = document.getElementById("sell-modal");
const sellForm = document.getElementById("sell-form");
const closeModal = document.getElementsByClassName("close")[0];
const usernameSpan = document.getElementById("username");
const accountIdSpan = document.getElementById("account-id");
const balanceSpan = document.getElementById("balance");
const themeToggle = document.getElementById("theme-toggle");
const socket = io();

socket.on('price_update', function(data) {
    updatePortfolioWithRealtimeData(data);
});

function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

// Function to fetch and display the portfolio
async function fetchPortfolio() {
    const response = await fetch("/api/portfolio");
    const portfolio = await response.json();

    // Clear the table
    portfolioTable.innerHTML = "";

    // Populate the table with portfolio data
    for (const item of portfolio) {
        const row = portfolioTable.insertRow();
        row.insertCell(0).innerText = item.symbol;
        row.insertCell(1).innerText = item.quantity;
        row.insertCell(2).innerText = item.avg_price;
        row.insertCell(3).innerText = item.position_size.toFixed(2);

        row.insertCell(4).innerText = "Loading..."; // Current Price
        row.insertCell(5).innerText = "Loading..."; // P&L
        row.insertCell(6).innerText = "Loading..."; // P&L %

        // Notes
        const notesCell = row.insertCell(7);
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

function updatePortfolioWithRealtimeData(data) {
    for (let i = 0; i < portfolioTable.rows.length; i++) {
        const row = portfolioTable.rows[i];
        const symbol = row.cells[0].innerText;
        if (data.symbol === symbol) {
            const quantity = parseFloat(row.cells[1].innerText);
            const avg_price = parseFloat(row.cells[2].innerText);
            const currentPrice = data.ltp;
            const pnl = (currentPrice - avg_price) * quantity;
            const pnlPercent = ((pnl / (avg_price * quantity)) * 100).toFixed(2);
            row.cells[4].innerText = currentPrice;
            row.cells[5].innerText = pnl.toFixed(2);
            row.cells[6].innerText = `${pnlPercent}%`;
        }
    }
}

// Function to fetch and display pending orders
async function fetchPendingOrders() {
    const response = await fetch("/api/pending_orders");
    const orders = await response.json();
    ordersTable.innerHTML = "";
    for (const order of orders) {
        const row = ordersTable.insertRow();
        row.insertCell(0).innerText = order.order_id;
        row.insertCell(1).innerText = order.symbol;
        row.insertCell(2).innerText = order.quantity;
        row.insertCell(3).innerText = order.price;
        row.insertCell(4).innerText = order.order_type;
    }
}

// Function to fetch and display trade history
async function fetchTradeHistory() {
    const response = await fetch("/api/trade_history");
    const history = await response.json();
    historyTable.innerHTML = "";
    for (const trade of history) {
        const row = historyTable.insertRow();
        row.insertCell(0).innerText = trade.symbol;
        row.insertCell(1).innerText = trade.quantity;
        row.insertCell(2).innerText = trade.buy_price;
        row.insertCell(3).innerText = trade.sell_price;
        row.insertCell(4).innerText = trade.pnl.toFixed(2);
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
    if (response.ok) {
        alert(result.message);
        sellModal.style.display = "none";
        fetchPortfolio();
        fetchAccountBalance();
    } else {
        alert(`Error: ${result.error}`);
    }
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
    if (response.ok) {
        alert(result.message);
        fetchPortfolio();
        fetchAccountBalance();
    } else {
        alert(`Error: ${result.error}`);
    }
}

// Function to fetch and display user profile
async function fetchProfile() {
    const response = await fetch("/api/profile");
    const profile = await response.json();
    usernameSpan.innerText = profile.username;
    accountIdSpan.innerText = profile.account_id;
}

// Function to fetch and display account balance
async function fetchAccountBalance() {
    const response = await fetch("/api/account");
    const account = await response.json();
    balanceSpan.innerText = account.balance.toFixed(2);
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
document.getElementsByClassName("tablink")[0].click();
fetchProfile();
fetchAccountBalance();
fetchPortfolio();
fetchPendingOrders();
fetchTradeHistory();
