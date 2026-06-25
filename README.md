# Nexus-CLI

Nexus-CLI is an open-source, dual-engine command-line interface chat utility. It provides a clean, aesthetic terminal interface that seamlessly falls back between high-performance AI engines to ensure zero downtime.

## ✨ Features
- **Lightning Fast Primary Engine**: Powered by Groq (`Llama-3.3-70b-versatile`).
- **Automated Failover System**: Gracefully pivots to Google AI Studio (`Gemini-1.5-flash`) on `HTTP 401` (Invalid/Missing Key) or `HTTP 429` (Rate Limits) without breaking the user's terminal loop.
- **High-End UI Aesthetics**: Rendered with the `rich` library for elegant markdown displays, boxed panels, and live character streaming.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Femology/Global-AI-Platform-Engineering.git
   cd Global-AI-Platform-Engineering
   ```

2. **Initialize a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment:**
   Drop your custom API tokens into a `.env` file to chat instantly.
   ```bash
   cp .env.example .env
   ```
   *(Edit `.env` and add your `GROQ_API_KEY` and `GOOGLE_AI_STUDIO_KEY`)*

## 💻 Usage

To start chatting with Nexus-CLI, simply run:
```bash
python nexus.py
```
*To exit the session, type `exit` or `quit`.*

## 🤝 Contributing

We love open-source contributions! To help maintain code quality and safety, please review our [Contributing Guidelines](CONTRIBUTING.md) before opening a pull request. 

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
