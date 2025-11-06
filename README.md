# AI Trading Agent with Market Analysis

A trading agent that uses local AI models (Ollama) to analyze real-time market data and financial news for both US and Indian stocks.

This tool is built for privacy and reliability, running all AI analysis locally. It features a robust fallback system, using mock data when live APIs (Polygon.io, NewsAPI) are unavailable, ensuring the application always runs.

---

## Features

* **Local Sentiment Analysis:** Uses Ollama (Gemma2, Llama3) to analyze financial news and provide BUY/SELL/HOLD recommendations.
* **Multi-Market Support:** Capable of analyzing both US (NASDAQ/NYSE) and Indian (NSE) stocks.
* **Real-Time Data:** Integrates with Polygon.io for live stock prices.
* **News Integration:** Fetches current financial news via NewsAPI.
* **Virtual Portfolio:** Includes a simple portfolio manager with a $10,000 starting balance for paper trading.
* **Privacy-Focused:** All AI analysis runs 100% locally. No data is sent to external services.
* **Mock Data Fallback:** Automatically uses high-quality mock data if API keys are not provided or are unavailable.

---

## Getting Started

### Prerequisites

* Python 3.8+
* Ollama ([install from ollama.ai](https://ollama.ai))
* API keys (Optional) for Polygon.io and NewsAPI

### Installation

1.  Clone the repository:
    ```sh
    git clone <your-repo-url>
    cd trading-agent
    ```

2.  Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3.  Pull a local AI model:
    ```sh
    ollama pull gemma2:2b
    ```
    or
    ```sh
    ollama pull llama3.2
    ```

### Configuration (Optional)

Create a `.env` file in the root directory to use live data:

POLYGON_API_KEY=your_polygon_key_here NEWS_API_KEY=your_newsapi_key_here

If this file is not present, the agent will automatically use mock data.

### Running the Agent

```sh
python trading_agent.py
