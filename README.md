# LLMinate

LLMinate is a powerful AI-driven tool designed to optimize and refactor AI-heavy codebases. It detects expensive or redundant LLM calls and replaces them with efficient, deterministic, rule-based logic or synthesized local functions.

## Features

- Deep Scan: Detect AI model interactions (OpenAI, Anthropic, Gemini) across your codebase using advanced static analysis.
- Intent Inference: Automatically determines the purpose of each AI call (e.g., classification, extraction, summarization).
- Strategy Synthesis: Uses AI to generate high-performance, deterministic Python or Javascript code that can replace the found pattern.
- Deterministic Rule Store: Maintains a searchable library of public and private rules to avoid re-synthesizing common logic.
- Shadow Running: Validates synthesized logic against existing AI outputs to ensure behavioral parity before refactoring.
- Real-time Activity Feed: Track the progress of your scans and synthesis operations with a granular live feed.

## Technology Stack

- Backend: FastAPI, SQLAlchemy, Semgrep, Tree-sitter
- Frontend: React, Vite, Tailwind CSS, Lucide Icons
- AI Integration: OpenAI SDK, Anthropic SDK, Google Generative AI SDK

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/llminate.git
   cd llminate
   ```

2. Set up the environment:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and provide your API keys for OpenAI, Anthropic, or Gemini.

3. Install backend dependencies:
   ```bash
   # It is recommended to use a virtual environment
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running without Docker

To run LLMinate locally without using Docker, follow these steps. You will need two separate terminal windows or a split-terminal session.

**Step 1: Start the Backend Server**

From the root project directory:
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000 --app-dir backend
```
The backend API will be available at `http://localhost:8000`.

**Step 2: Start the Frontend App**

From the root project directory in a new terminal:
```bash
cd frontend
npm run dev
```

**Step 3: Access the UI**

Open your browser and navigate to the URL provided by Vite (usually `http://localhost:5173`).

## Usage

### Scanning a Local Directory
1. Navigate to the Local Path tab.
2. Enter the absolute path to your source code.
3. Click Start Scan.

### Analyzing Results
1. Browse detected AI calls in the left sidebar.
2. Select a candidate to view the proposed refactoring patch and explanation.
3. Use the Apply button to commit the refactor to your codebase.

## Configuration

Configuration is handled via the `.env` file in the root directory.

- OPENAI_API_KEY: Your OpenAI API key.
- ANTHROPIC_API_KEY: Your Anthropic API key.
- GOOGLE_API_KEY: Your Google Gemini API key.
- LOCAL_AUTH_TOKEN: Token for local backend authentication.

## Security

LLMinate stores synthesized rules locally in `backend/app/rules/private/`. This directory is excluded from version control to protect your synthesized logic and any embedded patterns.
