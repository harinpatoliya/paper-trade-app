# Paper Trading Platform

This is a web-based paper trading platform designed to help users test their stock market strategies in a simulated, real-time environment. The platform uses the Fyers v3 API to fetch live price data, providing a realistic trading experience without any financial risk.

## Features

- **Real-Time Data**: Integrated with the Fyers v3 API for live stock quotes.
- **Portfolio Monitoring**: A comprehensive dashboard to track your positions, including:
    - Average buy price and quantity.
    - Real-time Profit & Loss (P&L) in both absolute and percentage terms.
    - A section to add and edit personal notes for each stock.
- **Order Placement**:
    - **Buy Orders**: Place both Market and Limit buy orders.
    - **Sell Orders**: A dedicated modal to place Market and Limit sell orders for existing positions.
- **User-Friendly Interface**:
    - Displays user profile information (Username and Account ID).
    - Features a theme switcher for both **Light and Dark modes**.
    - Branded for "VR securities limited".
- **Persistent Storage**: Uses a local SQLite database to save your portfolio and order history.

## Technology Stack

- **Backend**: Python with Flask
- **Frontend**: HTML, CSS, and vanilla JavaScript
- **Database**: SQLite
- **API**: Fyers v3 API

## Setup and Installation

Follow these steps to set up and run the project locally.

### 1. Prerequisites

- Python 3.6+
- An active Fyers trading account and API credentials.

### 2. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 3. Install Backend Dependencies

Install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

The application uses a `.env` file to manage sensitive API credentials.

Create a file named `.env` inside the `backend/` directory:

```bash
touch backend/.env
```

Open the `backend/.env` file and add your Fyers API credentials as follows:

```
FYERS_APP_ID=YOUR_APP_ID
FYERS_SECRET_KEY=YOUR_SECRET_KEY
FYERS_REDIRECT_URI=YOUR_REDIRECT_URI
```

Replace `YOUR_APP_ID`, `YOUR_SECRET_KEY`, and `YOUR_REDIRECT_URI` with the actual credentials you obtained from the Fyers API dashboard.

### 5. Generate Fyers API Access Token

The application requires a one-time authentication process to generate an access token.

**Step 1: Generate the Authentication URL**

Run the following command in your terminal:

```bash
python backend/generate_auth_url.py
```

This will print an authentication URL.

**Step 2: Authorize and Get the `auth_code`**

- Copy the URL and paste it into your web browser.
- Log in with your Fyers credentials and grant the necessary permissions to the application.
- After authorization, you will be redirected to your `REDIRECT_URI`. The URL in the address bar will now contain an `auth_code`. It will look something like this: `https://your-redirect-uri/?s=ok&code=200&auth_code=YOUR_AUTH_CODE`.
- Copy the value of the `auth_code` parameter.

**Step 3: Generate the Access Token**

Run the following command in your terminal, replacing `<auth_code>` with the code you copied in the previous step:

```bash
python backend/generate_access_token.py <auth_code>
```

This will create a `fyers_token.txt` file in the `backend/` directory, which will allow the application to make authenticated API calls.

## Running the Application

Once the setup is complete, you can start the backend server.

```bash
python backend/main.py
```

The server will start, and you can access the paper trading platform by opening your web browser and navigating to:

[http://127.0.0.1:5000](http://127.0.0.1:5000)
