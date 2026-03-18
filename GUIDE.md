# 📖 6372-Hybrid-AI-Sentinel: User Guide

Welcome to the official manual for 6372-Hybrid-AI-Sentinel. This tool is designed to be highly customizable to fit your specific trading needs.

## 🛠️ Configuration Methods

There are two ways to customize your Sentinel:

### 1. The Interactive Wizard (Recommended)
We have provided a built-in wizard to help you configure assets and strategies without touching any code.
Run the following command in your terminal:
```bash
crypto-config
```
Follow the on-screen prompts to add coins, change notification thresholds, or update your DCA strategy.

### 2. Manual JSON Configuration
For advanced users, you can directly edit the `config/settings.json` file.

#### Adding a New Coin
Find the `"assets"` section and add a new entry:
```json
"ETH": {
  "symbol": "ETHUSDT",
  "emoji": "🔹",
  "keywords": ["eth", "ethereum", "vitalik"],
  "thresholds": {
    "hourly": 1.0,
    "dips": [{"level": -10.0, "msg": "🚨 ETH CRASH!", "action": "BUY DIP"}],
    "spikes": [{"level": 15.0, "msg": "🚀 ETH MOON!", "action": "SELL 20%"}]
  }
}
```

## 🌍 Language Customization
6372-Hybrid-AI-Sentinel supports multiple languages. To change the language:
1. Open your `.env` file.
2. Change `APP_LANGUAGE` to your desired code (e.g., `id` for Indonesian, `en` for English).
3. Ensure the corresponding `.json` file exists in `config/locales/`.

## 🤖 AI Customization
You can change the AI models and prompts in `.env` and `config/settings.json`.
- **Ollama:** Change `OLLAMA_MODEL` in `.env` (e.g., `mistral`, `gemma`).
- **Prompts:** Edit the `"ai_prompts"` section in `settings.json` to change how the AI analyzes news.

## 🔒 Safety First
- **Never share your `.env` file.**
- Keep your **Gemini API Key** secure.
- This tool is for informational purposes only. Always do your own research (DYOR).

---
Developed with ❤️ by **myikgetzweb3**
