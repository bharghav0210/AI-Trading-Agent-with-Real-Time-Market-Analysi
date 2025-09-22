import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime, timedelta
import random
import requests
import ollama
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class FinancialDataProcessor:
    def __init__(self):
        self.categories_mapping = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC'],
            'Finance': ['JPM', 'BAC', 'GS', 'MS', 'V', 'MA', 'PYPL'],
            'Healthcare': ['JNJ', 'PFE', 'UNH', 'MRK', 'ABT', 'TMO'],
            'Consumer': ['AMZN', 'WMT', 'TGT', 'HD', 'NKE', 'MCD'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
            'Indian': ['RELIANCE.NS', 'TATAMOTORS.NS', 'HDFCBANK.NS', 'INFY.NS', 'TCS.NS', 'ICICIBANK.NS', 'SBIN.NS']
        }
        
    def get_stock_category(self, ticker):
        base_ticker = ticker.replace('.NS', '') if '.NS' in ticker else ticker
        for category, tickers in self.categories_mapping.items():
            if base_ticker in tickers:
                return category
        return "Other"
    
    def process_market_data(self, ticker, price, sentiment):
        category = self.get_stock_category(ticker)
        volatility = random.uniform(0.1, 0.3)
        
        return {
            'ticker': ticker,
            'price': price,
            'category': category,
            'volatility': volatility,
            'sentiment': sentiment,
            'timestamp': datetime.now()
        }

class SentimentAnalyzer:
    def __init__(self):
        self.model_name = "gemma2:2b"
        self.ollama_available = self._check_ollama()
        self.labels = ['Negative', 'Neutral', 'Positive']
        
    def _check_ollama(self):
        try:
            response = ollama.list()
            models = [model['name'] for model in response['models']]
            
            if self.model_name in models:
                print(f"✓ Ollama model '{self.model_name}' is available")
                return True
            else:
                print(f"✗ Model '{self.model_name}' not found. Available models: {models}")
                return False
                
        except Exception as e:
            print(f"✗ Ollama not available: {e}")
            return False
    
    def analyze_sentiment(self, text):
        if not text or not isinstance(text, str):
            return {'sentiment': 'Neutral', 'confidence': 0.5}
        
        if not self.ollama_available:
            return self._mock_sentiment_analysis(text)
        
        try:
            prompt = f"""
            Analyze the sentiment of this financial news text and respond ONLY with JSON format:
            {{
                "sentiment": "Positive", "Neutral", or "Negative",
                "confidence": 0.0 to 1.0,
                "reason": "brief explanation"
            }}
            
            Text: "{text}"
            """
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1}
            )
            
            result_text = response['message']['content'].strip()
            
            try:
                result = json.loads(result_text)
                sentiment = result.get('sentiment', 'Neutral')
                confidence = float(result.get('confidence', 0.5))
                
                if sentiment not in self.labels:
                    sentiment = 'Neutral'
                
                return {
                    'sentiment': sentiment,
                    'confidence': max(0.1, min(confidence, 1.0)),
                    'reason': result.get('reason', '')
                }
                
            except json.JSONDecodeError:
                return self._analyze_sentiment_from_text(result_text)
                
        except Exception as e:
            print(f"Ollama sentiment analysis error: {e}")
            return self._mock_sentiment_analysis(text)
    
    def _analyze_sentiment_from_text(self, text):
        text_lower = text.lower()
        
        positive_words = ['positive', 'bullish', 'buy', 'recommend', 'strong', 'growth', 'profit', 'gain', 'up']
        negative_words = ['negative', 'bearish', 'sell', 'avoid', 'weak', 'decline', 'loss', 'down', 'drop']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in negative_words)
        
        if positive_count > negative_count:
            return {'sentiment': 'Positive', 'confidence': 0.7, 'reason': 'Positive keywords detected'}
        elif negative_count > positive_count:
            return {'sentiment': 'Negative', 'confidence': 0.7, 'reason': 'Negative keywords detected'}
        else:
            return {'sentiment': 'Neutral', 'confidence': 0.5, 'reason': 'Neutral or mixed signals'}
    
    def _mock_sentiment_analysis(self, text):
        words = text.lower().split()
        positive_words = ['rise', 'up', 'strong', 'good', 'great', 'positive', 'buy', 'upgrade', 'profit', 'growth']
        negative_words = ['fall', 'down', 'weak', 'bad', 'poor', 'negative', 'sell', 'downgrade', 'loss', 'decline']
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            return {'sentiment': 'Positive', 'confidence': min(0.7 + positive_count * 0.05, 0.95), 'reason': 'Positive keywords'}
        elif negative_count > positive_count:
            return {'sentiment': 'Negative', 'confidence': min(0.7 + negative_count * 0.05, 0.95), 'reason': 'Negative keywords'}
        else:
            return {'sentiment': 'Neutral', 'confidence': 0.5, 'reason': 'Neutral content'}

class StockDataFetcher:
    def __init__(self):
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        self.last_call_time = 0
        self.min_call_interval = 1
        self.use_mock_data = not self.polygon_key
        
        if self.use_mock_data:
            print("Using mock stock data (no Polygon API key found)")
        else:
            print("Polygon API key found - attempting real data")
    
    def get_stock_price(self, ticker):
        if self.use_mock_data:
            return self._get_mock_price(ticker)
        
        current_time = time.time()
        if current_time - self.last_call_time < self.min_call_interval:
            time.sleep(self.min_call_interval)
        
        self.last_call_time = current_time
        
        try:
            if '.NS' in ticker:
                url = f"https://api.polygon.io/v2/snapshot/locale/global/markets/stocks/tickers/{ticker}?apiKey={self.polygon_key}"
            else:
                url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={self.polygon_key}"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                if '.NS' in ticker and 'ticker' in data:
                    price = data['ticker']['day']['c']
                elif 'results' in data and len(data['results']) > 0:
                    price = data['results'][0]['c']
                else:
                    raise ValueError("Invalid response format")
                
                print(f"✓ Live price for {ticker}: ${price:.2f}")
                return price
            else:
                print(f"Polygon API error for {ticker}: {data.get('error', 'Unknown error')}")
                return self._get_mock_price(ticker)
                
        except Exception as e:
            print(f"Error fetching {ticker} price: {e}")
            return self._get_mock_price(ticker)
    
    def _get_mock_price(self, ticker):
        mock_prices = {
            'AAPL': random.uniform(170, 190),
            'MSFT': random.uniform(320, 350),
            'GOOGL': random.uniform(130, 150),
            'TSLA': random.uniform(180, 220),
            'AMZN': random.uniform(140, 160),
            'NVDA': random.uniform(420, 480),
            'JPM': random.uniform(170, 190),
            'V': random.uniform(250, 270),
            'RELIANCE.NS': random.uniform(2500, 2800),
            'TATAMOTORS.NS': random.uniform(800, 950),
            'HDFCBANK.NS': random.uniform(1600, 1800),
            'INFY.NS': random.uniform(1500, 1700),
            'TCS.NS': random.uniform(3500, 3800),
            'ICICIBANK.NS': random.uniform(900, 1100),
            'SBIN.NS': random.uniform(550, 650),
        }
        price = mock_prices.get(ticker, random.uniform(100, 200))
        print(f"Mock price for {ticker}: ${price:.2f}")
        return price

class NewsFetcher:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.use_mock_data = not self.api_key
        
        if self.use_mock_data:
            print("Using mock news data (no News API key found)")
        else:
            print("News API key found - attempting real news")
    
    def fetch_news(self, ticker, days=1):
        if self.use_mock_data:
            return self._get_mock_news(ticker)
        
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            from_str = from_date.strftime('%Y-%m-%d')
            to_str = to_date.strftime('%Y-%m-%d')
            
            search_ticker = ticker.replace('.NS', '') if '.NS' in ticker else ticker
            
            url = f"https://newsapi.org/v2/everything?q={search_ticker}&from={from_str}&to={to_str}&sortBy=publishedAt&apiKey={self.api_key}"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                articles = data['articles'][:3]
                news_items = []
                for article in articles:
                    title = article.get('title', 'No title')
                    description = article.get('description', 'No description')
                    news_items.append(f"{title}: {description}")
                print(f"✓ Live news fetched for {ticker}")
                return news_items
            else:
                print(f"News API error for {ticker}")
                return self._get_mock_news(ticker)
                
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return self._get_mock_news(ticker)
    
    def _get_mock_news(self, ticker):
        base_ticker = ticker.replace('.NS', '') if '.NS' in ticker else ticker
        
        mock_news_db = {
            'AAPL': [
                "Apple announces new iPhone with revolutionary AI features",
                "Apple Q3 earnings beat expectations by 15%, stock surges",
                "Apple partners with OpenAI for iOS 18 integration"
            ],
            'MSFT': [
                "Microsoft Azure cloud revenue grows 25% year-over-year",
                "Microsoft announces major Windows 12 update with AI copilot",
                "Satya Nadella: AI will transform every industry"
            ],
            'GOOGL': [
                "Google Gemini AI outperforms competitors in latest benchmarks",
                "Google Cloud expands AI services to new markets",
                "Sundar Pichai discusses AI future at Google IO"
            ],
            'TSLA': [
                "Tesla unveils new Robotaxi prototype with full autonomy",
                "Elon Musk: Tesla will achieve Level 5 autonomy this year",
                "Tesla energy storage business grows 40% quarterly"
            ],
            'RELIANCE': [
                "Reliance Jio announces 5G rollout across India completed",
                "Mukesh Ambani: Reliance to invest $10B in green energy",
                "Reliance Retail expands to 1000 new locations"
            ],
            'TATAMOTORS': [
                "Tata Motors electric vehicle sales double year-over-year",
                "Tata Steel announces new sustainable manufacturing initiative",
                "Tata Group to acquire major e-commerce platform"
            ],
            'HDFCBANK': [
                "HDFC Bank reports strong quarterly results with 18% growth",
                "HDFC launches new digital banking platform with AI features",
                "HDFC expands rural banking services across India"
            ]
        }
        
        news = mock_news_db.get(base_ticker, [
            f"{base_ticker} shows strong performance in recent market trading",
            f"Analysts upgrade {base_ticker} rating based on strong fundamentals",
            f"Market sentiment for {base_ticker} remains positive amid volatility"
        ])
        print(f"Mock news for {ticker}: {len(news)} articles")
        return news

class TradingAgent:
    def __init__(self, analyzer, news_fetcher, data_processor):
        self.analyzer = analyzer
        self.news_fetcher = news_fetcher
        self.data_processor = data_processor
        self.stock_fetcher = StockDataFetcher()
        self.portfolio = {}
        self.balance = 10000.0
        self.transaction_history = []
        self.market_data = []
    
    def analyze_news_for_ticker(self, ticker):
        news_articles = self.news_fetcher.fetch_news(ticker)
        sentiments = []
        
        for news in news_articles:
            sentiment = self.analyzer.analyze_sentiment(news)
            sentiments.append(sentiment)
        
        return news_articles, sentiments
    
    def make_trading_decision(self, ticker, sentiments):
        if not sentiments:
            return "HOLD", 0.5
        
        positive_score = sum(s['confidence'] for s in sentiments if s['sentiment'] == 'Positive') / len(sentiments)
        negative_score = sum(s['confidence'] for s in sentiments if s['sentiment'] == 'Negative') / len(sentiments)
        
        if positive_score > 0.65:
            decision = "BUY"
            confidence = positive_score
        elif negative_score > 0.65:
            decision = "SELL"
            confidence = negative_score
        else:
            decision = "HOLD"
            confidence = max(positive_score, negative_score, 0.5)
            
        return decision, confidence
    
    def execute_buy_trade(self, ticker, amount):
        current_price = self.stock_fetcher.get_stock_price(ticker)
        
        if self.balance >= amount:
            shares = amount / current_price
            self.portfolio[ticker] = self.portfolio.get(ticker, 0) + shares
            self.balance -= amount
            
            self.transaction_history.append({
                'date': datetime.now(),
                'ticker': ticker,
                'action': 'BUY',
                'shares': shares,
                'price': current_price,
                'amount': amount
            })
            
            market_data = self.data_processor.process_market_data(ticker, current_price, 'Positive')
            self.market_data.append(market_data)
            
            return f"Bought {shares:.2f} shares of {ticker} at ${current_price:.2f}"
        else:
            return f"Insufficient balance. Available: ${self.balance:.2f}"
    
    def execute_sell_trade(self, ticker, percentage=100):
        if ticker not in self.portfolio or self.portfolio[ticker] <= 0:
            return f"No shares of {ticker} to sell"
        
        current_price = self.stock_fetcher.get_stock_price(ticker)
        shares_owned = self.portfolio[ticker]
        
        if percentage == 100:
            shares_to_sell = shares_owned
        else:
            shares_to_sell = shares_owned * (percentage / 100)
        
        amount = shares_to_sell * current_price
        
        if shares_to_sell > 0:
            self.portfolio[ticker] -= shares_to_sell
            if self.portfolio[ticker] < 0.001:
                self.portfolio.pop(ticker)
            
            self.balance += amount
            
            self.transaction_history.append({
                'date': datetime.now(),
                'ticker': ticker,
                'action': 'SELL',
                'shares': shares_to_sell,
                'price': current_price,
                'amount': amount
            })
            
            market_data = self.data_processor.process_market_data(ticker, current_price, 'Negative')
            self.market_data.append(market_data)
            
            return f"Sold {shares_to_sell:.2f} shares of {ticker} at ${current_price:.2f} for ${amount:.2f}"
        else:
            return "No shares sold"
    
    def execute_ai_trade(self, ticker, decision, confidence):
        current_price = self.stock_fetcher.get_stock_price(ticker)
        
        if decision == "BUY" and self.balance >= 500:
            amount = min(self.balance * 0.1, 1000)
            return self.execute_buy_trade(ticker, amount)
            
        elif decision == "SELL" and ticker in self.portfolio:
            sell_percentage = min(confidence * 100, 50)  # Sell up to 50% based on confidence
            return self.execute_sell_trade(ticker, sell_percentage)
            
        return f"No trade executed for {ticker}"

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Trading Agent with Enhanced Selling Features")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        print("Initializing trading agent components...")
        self.data_processor = FinancialDataProcessor()
        self.analyzer = SentimentAnalyzer()
        self.news_fetcher = NewsFetcher()
        self.agent = TradingAgent(self.analyzer, self.news_fetcher, self.data_processor)
        
        self.setup_styles()
        self.create_gui()
        
        self.update_interval = 30000
        self.schedule_updates()
        print("Trading agent initialized successfully!")
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        self.style.configure('Normal.TLabel', font=('Arial', 10), background='#f0f0f0')
        self.style.configure('Positive.TLabel', font=('Arial', 10), background='#f0f0f0', foreground='green')
        self.style.configure('Negative.TLabel', font=('Arial', 10), background='#f0f0f0', foreground='red')
        self.style.configure('Buy.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0', foreground='green')
        self.style.configure('Sell.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0', foreground='red')
        self.style.configure('Hold.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0', foreground='blue')
        self.style.configure('TFrame', background='#f0f0f0')
    
    def create_gui(self):
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.trading_frame = ttk.Frame(self.notebook)
        self.portfolio_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_frame, text='Dashboard')
        self.notebook.add(self.trading_frame, text='Trading')
        self.notebook.add(self.portfolio_frame, text='Portfolio')
        
        self.create_dashboard_tab()
        self.create_trading_tab()
        self.create_portfolio_tab()
    
    def create_dashboard_tab(self):
        # Dashboard content
        main_frame = ttk.Frame(self.dashboard_frame, padding="10", style='TFrame')
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="AI Trading Agent Dashboard", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status panel
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(status_frame, text="Ollama AI:", style='Header.TLabel').grid(row=0, column=0, sticky='w')
        self.ollama_status_var = tk.StringVar(value="✓ Online" if self.analyzer.ollama_available else "✗ Offline")
        ttk.Label(status_frame, textvariable=self.ollama_status_var, style='Normal.TLabel').grid(row=0, column=1, sticky='w')
        
        ttk.Label(status_frame, text="Stock Data:", style='Header.TLabel').grid(row=1, column=0, sticky='w')
        stock_status = "Live" if not self.agent.stock_fetcher.use_mock_data else "Mock"
        self.stock_status_var = tk.StringVar(value=stock_status)
        ttk.Label(status_frame, textvariable=self.stock_status_var, style='Normal.TLabel').grid(row=1, column=1, sticky='w')
        
        ttk.Label(status_frame, text="News Data:", style='Header.TLabel').grid(row=2, column=0, sticky='w')
        news_status = "Live" if not self.news_fetcher.use_mock_data else "Mock"
        self.news_status_var = tk.StringVar(value=news_status)
        ttk.Label(status_frame, textvariable=self.news_status_var, style='Normal.TLabel').grid(row=2, column=1, sticky='w')
        
        # Quick actions
        action_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="10")
        action_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Button(action_frame, text="Refresh All", command=self.refresh_all).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Debug Info", command=self.show_debug_info).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Reset Portfolio", command=self.reset_portfolio).pack(side='left', padx=5)
    
    def create_trading_tab(self):
        main_frame = ttk.Frame(self.trading_frame, padding="10", style='TFrame')
        main_frame.pack(fill='both', expand=True)
        
        # Left panel - Analysis
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=5)
        
        ttk.Label(left_frame, text="Stock Analysis", style='Header.TLabel').grid(row=0, column=0, pady=5)
        
        ttk.Label(left_frame, text="Ticker:", style='Normal.TLabel').grid(row=1, column=0, sticky='w', pady=2)
        self.ticker_var = tk.StringVar(value="AAPL")
        ticker_entry = ttk.Entry(left_frame, textvariable=self.ticker_var, width=15)
        ticker_entry.grid(row=1, column=1, sticky='w', pady=2)
        
        ttk.Label(left_frame, text="For Indian stocks, use .NS suffix", style='Normal.TLabel', foreground='gray').grid(row=2, column=0, columnspan=2, pady=2)
        
        analyze_btn = ttk.Button(left_frame, text="Analyze Sentiment", command=self.analyze_sentiment)
        analyze_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Results display
        results_frame = ttk.LabelFrame(left_frame, text="Analysis Results")
        results_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)
        
        self.news_text = scrolledtext.ScrolledText(results_frame, width=50, height=15, wrap=tk.WORD)
        self.news_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Decision display
        decision_frame = ttk.Frame(left_frame)
        decision_frame.grid(row=5, column=0, columnspan=2, sticky='ew', pady=5)
        
        ttk.Label(decision_frame, text="AI Decision:", style='Header.TLabel').pack(side='left')
        self.decision_var = tk.StringVar(value="HOLD")
        self.decision_label = ttk.Label(decision_frame, textvariable=self.decision_var, style='Hold.TLabel')
        self.decision_label.pack(side='left', padx=5)
        
        ttk.Label(decision_frame, text="Confidence:", style='Header.TLabel').pack(side='left', padx=(20, 0))
        self.confidence_var = tk.StringVar(value="0.0%")
        ttk.Label(decision_frame, textvariable=self.confidence_var, style='Normal.TLabel').pack(side='left', padx=5)
        
        # Right panel - Trading actions
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        ttk.Label(right_frame, text="Trading Actions", style='Header.TLabel').grid(row=0, column=0, pady=5)
        
        # Manual trading
        manual_frame = ttk.LabelFrame(right_frame, text="Manual Trading", padding="10")
        manual_frame.grid(row=1, column=0, sticky='ew', pady=10)
        
        ttk.Label(manual_frame, text="Buy Amount ($):", style='Normal.TLabel').grid(row=0, column=0, sticky='w')
        self.buy_amount_var = tk.StringVar(value="1000")
        ttk.Entry(manual_frame, textvariable=self.buy_amount_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Button(manual_frame, text="Buy Stock", command=self.manual_buy).grid(row=0, column=2, padx=5)
        
        ttk.Label(manual_frame, text="Sell Percentage:", style='Normal.TLabel').grid(row=1, column=0, sticky='w', pady=5)
        self.sell_percent_var = tk.StringVar(value="100")
        ttk.Entry(manual_frame, textvariable=self.sell_percent_var, width=10).grid(row=1, column=1, sticky='w')
        ttk.Label(manual_frame, text="%", style='Normal.TLabel').grid(row=1, column=2, sticky='w')
        
        ttk.Button(manual_frame, text="Sell Stock", command=self.manual_sell).grid(row=1, column=3, padx=5)
        
        # AI trading
        ai_frame = ttk.LabelFrame(right_frame, text="AI Trading", padding="10")
        ai_frame.grid(row=2, column=0, sticky='ew', pady=10)
        
        ttk.Button(ai_frame, text="Execute AI Trade", command=self.execute_ai_trade, width=20).pack(pady=5)
        
        # Current price
        price_frame = ttk.LabelFrame(right_frame, text="Current Price", padding="10")
        price_frame.grid(row=3, column=0, sticky='ew', pady=10)
        
        self.current_price_var = tk.StringVar(value="$0.00")
        ttk.Label(price_frame, textvariable=self.current_price_var, style='Header.TLabel').pack()
        
        ttk.Button(price_frame, text="Refresh Price", command=self.refresh_price).pack(pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        self.news_text.tag_configure('positive', foreground='green')
        self.news_text.tag_configure('negative', foreground='red')
        self.news_text.tag_configure('neutral', foreground='blue')
    
    def create_portfolio_tab(self):
        main_frame = ttk.Frame(self.portfolio_frame, padding="10", style='TFrame')
        main_frame.pack(fill='both', expand=True)
        
        # Portfolio summary
        summary_frame = ttk.LabelFrame(main_frame, text="Portfolio Summary", padding="10")
        summary_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(summary_frame, text="Total Balance:", style='Header.TLabel').grid(row=0, column=0, sticky='w')
        self.balance_var = tk.StringVar(value=f"${self.agent.balance:.2f}")
        ttk.Label(summary_frame, textvariable=self.balance_var, style='Normal.TLabel').grid(row=0, column=1, sticky='w')
        
        ttk.Label(summary_frame, text="Number of Holdings:", style='Header.TLabel').grid(row=1, column=0, sticky='w')
        self.holdings_count_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.holdings_count_var, style='Normal.TLabel').grid(row=1, column=1, sticky='w')
        
        ttk.Label(summary_frame, text="Total Transactions:", style='Header.TLabel').grid(row=2, column=0, sticky='w')
        self.transactions_count_var = tk.StringVar(value="0")
        ttk.Label(summary_frame, textvariable=self.transactions_count_var, style='Normal.TLabel').grid(row=2, column=1, sticky='w')
        
        # Holdings list
        holdings_frame = ttk.LabelFrame(main_frame, text="Current Holdings", padding="10")
        holdings_frame.grid(row=1, column=0, sticky='nsew', pady=10, padx=5)
        
        columns = ('Ticker', 'Shares', 'Current Price', 'Value')
        self.holdings_tree = ttk.Treeview(holdings_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.holdings_tree.heading(col, text=col)
            self.holdings_tree.column(col, width=100)
        
        self.holdings_tree.grid(row=0, column=0, sticky='nsew')
        
        scrollbar = ttk.Scrollbar(holdings_frame, orient=tk.VERTICAL, command=self.holdings_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.holdings_tree.configure(yscrollcommand=scrollbar.set)
        
        # Transaction history
        history_frame = ttk.LabelFrame(main_frame, text="Transaction History", padding="10")
        history_frame.grid(row=1, column=1, sticky='nsew', pady=10, padx=5)
        
        columns = ('Date', 'Ticker', 'Action', 'Shares', 'Price', 'Amount')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        self.history_tree.grid(row=0, column=0, sticky='nsew')
        
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        holdings_frame.columnconfigure(0, weight=1)
        holdings_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
    
    def refresh_all(self):
        self.refresh_portfolio()
        self.refresh_price()
        messagebox.showinfo("Refresh", "All data refreshed successfully!")
    
    def refresh_portfolio(self):
        self.balance_var.set(f"${self.agent.balance:.2f}")
        self.holdings_count_var.set(str(len(self.agent.portfolio)))
        self.transactions_count_var.set(str(len(self.agent.transaction_history)))
        
        # Update holdings tree
        for item in self.holdings_tree.get_children():
            self.holdings_tree.delete(item)
        
        for ticker, shares in self.agent.portfolio.items():
            price = self.agent.stock_fetcher.get_stock_price(ticker)
            value = shares * price
            self.holdings_tree.insert('', 'end', values=(
                ticker,
                f"{shares:.2f}",
                f"${price:.2f}",
                f"${value:.2f}"
            ))
        
        # Update transaction history
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        for transaction in self.agent.transaction_history[-20:]:
            self.history_tree.insert('', 'end', values=(
                transaction['date'].strftime('%Y-%m-%d %H:%M'),
                transaction['ticker'],
                transaction['action'],
                f"{transaction['shares']:.2f}",
                f"${transaction['price']:.2f}",
                f"${transaction['amount']:.2f}"
            ))
    
    def refresh_price(self):
        ticker = self.ticker_var.get().upper().strip()
        if ticker:
            price = self.agent.stock_fetcher.get_stock_price(ticker)
            self.current_price_var.set(f"${price:.2f}")
    
    def manual_buy(self):
        ticker = self.ticker_var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Please enter a stock ticker")
            return
        
        try:
            amount = float(self.buy_amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Buy amount must be positive")
                return
            
            result = self.agent.execute_buy_trade(ticker, amount)
            self.refresh_portfolio()
            messagebox.showinfo("Buy Executed", result)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def manual_sell(self):
        ticker = self.ticker_var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Please enter a stock ticker")
            return
        
        try:
            percentage = float(self.sell_percent_var.get())
            if percentage <= 0 or percentage > 100:
                messagebox.showerror("Error", "Percentage must be between 0.1 and 100")
                return
            
            result = self.agent.execute_sell_trade(ticker, percentage)
            self.refresh_portfolio()
            messagebox.showinfo("Sell Executed", result)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid percentage")
    
    def execute_ai_trade(self):
        ticker = self.ticker_var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Please enter a stock ticker")
            return
        
        decision = self.decision_var.get()
        if decision == "ANALYZING...":
            messagebox.showerror("Error", "Please analyze sentiment first")
            return
        
        confidence_str = self.confidence_var.get().replace('%', '')
        try:
            confidence = float(confidence_str) / 100
        except:
            confidence = 0.5
        
        result = self.agent.execute_ai_trade(ticker, decision, confidence)
        self.refresh_portfolio()
        messagebox.showinfo("AI Trade Executed", result)
    
    def reset_portfolio(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset your portfolio? All data will be lost."):
            self.agent.portfolio = {}
            self.agent.balance = 10000.0
            self.agent.transaction_history = []
            self.refresh_portfolio()
            messagebox.showinfo("Reset", "Portfolio reset successfully!")
    
    def show_debug_info(self):
        info = [
            f"Ollama Available: {'Yes' if self.analyzer.ollama_available else 'No'}",
            f"Ollama Model: {self.analyzer.model_name}",
            f"Polygon API: {'Live' if not self.agent.stock_fetcher.use_mock_data else 'Mock'}",
            f"News API: {'Live' if not self.news_fetcher.use_mock_data else 'Mock'}",
            f"Balance: ${self.agent.balance:.2f}",
            f"Holdings: {len(self.agent.portfolio)} stocks",
            f"Transactions: {len(self.agent.transaction_history)}"
        ]
        messagebox.showinfo("Debug Information", "\n".join(info))
    
    def analyze_sentiment(self):
        ticker = self.ticker_var.get().upper().strip()
        if not ticker:
            messagebox.showerror("Error", "Please enter a stock ticker")
            return
        
        self.news_text.delete(1.0, tk.END)
        self.news_text.insert(tk.END, f"Analyzing news for {ticker} using Ollama...\n")
        self.decision_var.set("ANALYZING...")
        self.confidence_var.set("0.0%")
        
        thread = threading.Thread(target=self._perform_analysis, args=(ticker,))
        thread.daemon = True
        thread.start()
    
    def _perform_analysis(self, ticker):
        try:
            price = self.agent.stock_fetcher.get_stock_price(ticker)
            news_articles, sentiments = self.agent.analyze_news_for_ticker(ticker)
            decision, confidence = self.agent.make_trading_decision(ticker, sentiments)
            
            self.root.after(0, self._update_analysis_results, ticker, news_articles, sentiments, decision, confidence, price)
        except Exception as e:
            self.root.after(0, self._show_error, f"Analysis error: {str(e)}")
    
    def _update_analysis_results(self, ticker, news_articles, sentiments, decision, confidence, price):
        self.news_text.delete(1.0, tk.END)
        
        data_source = "Live Data" if not self.agent.stock_fetcher.use_mock_data else "Mock Data"
        news_source = "Live News" if not self.news_fetcher.use_mock_data else "Mock News"
        ollama_source = "Ollama AI" if self.analyzer.ollama_available else "Rule-Based"
        
        self.news_text.insert(tk.END, f"Data Source: {data_source} | News: {news_source} | Analysis: {ollama_source}\n")
        self.news_text.insert(tk.END, f"News for {ticker} (Current Price: ${price:.2f}):\n\n")
        
        for i, (news, sentiment) in enumerate(zip(news_articles, sentiments)):
            self.news_text.insert(tk.END, f"{i+1}. {news}\n")
            sentiment_text = f"   Sentiment: {sentiment['sentiment']} (Confidence: {sentiment['confidence']*100:.1f}%)\n"
            if sentiment.get('reason'):
                sentiment_text += f"   Reason: {sentiment['reason']}\n"
            sentiment_text += "\n"
            
            if sentiment['sentiment'] == 'Positive':
                self.news_text.insert(tk.END, sentiment_text, 'positive')
            elif sentiment['sentiment'] == 'Negative':
                self.news_text.insert(tk.END, sentiment_text, 'negative')
            else:
                self.news_text.insert(tk.END, sentiment_text, 'neutral')
        
        self.decision_var.set(decision)
        self.confidence_var.set(f"{confidence*100:.1f}%")
        self.current_price_var.set(f"${price:.2f}")
        
        if decision == "BUY":
            self.decision_label.configure(style='Buy.TLabel')
        elif decision == "SELL":
            self.decision_label.configure(style='Sell.TLabel')
        else:
            self.decision_label.configure(style='Hold.TLabel')
    
    def _show_error(self, message):
        messagebox.showerror("Error", message)
    
    def schedule_updates(self):
        self.periodic_update()
        self.root.after(self.update_interval, self.schedule_updates)
    
    def periodic_update(self):
        self.refresh_portfolio()
        ticker = self.ticker_var.get().upper().strip()
        if ticker:
            self.refresh_price()

def main():
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()