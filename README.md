# LLMinate

LLMinate is a tool designed to optimize codebases by detecting redundant or expensive LLM interactions and replacing them with deterministic, rule-based logic or synthesized local functions.

## Features

- **Static Scanning**: Detects LLM client usage across project files using static analysis.
- **Intent Inference**: Analyzes AI calls to determine their underlying logic and purpose.
- **Logic Synthesis**: Generates deterministic Python or Javascript functions to replace external AI dependencies.
- **Shadow Validation**: Compares synthesized logic against live AI outputs to verify behavior and measure performance gains.
- **Rule Management**: Stores and retrieves synthesized rules for common patterns.

## Architecture

1.  **Scanner**: Identifies AI service calls in local or remote repositories.
2.  **Reasoner**: Evaluates context and prompts to define the required logic.
3.  **Synthesizer**: Produces a local code implementation (Regex, conditional logic, etc.) for the inferred task.
4.  **Validator**: Measures behavioral parity and latency improvements in a shadow execution environment.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- API Keys for supported providers (OpenAI, Anthropic, or Google Gemini)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/rrb115/LLMinate.git
    cd LLMinate
    ```

2.  Configure environment:
    ```bash
    cp .env.example .env
    ```
    Populate the `.env` file with required API credentials.

3.  Setup Backend:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

4.  Setup Frontend:
    ```bash
    cd frontend
    npm install
    ```

### Running Locally

**Backend Server**
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

**Frontend Application**
```bash
cd frontend
npm run dev
```

## Usage

1.  Specify the project path in the Application UI.
2.  Review detected candidates for replacement.
3.  Evaluate proposed patches and validation metrics.
4.  Apply refactored code to the target repository.

## Security

- Analysis is performed locally on the host machine.
- Synthesized logic is stored in `backend/app/rules/private/` and is excluded from version control.
- Code modifications require explicit confirmation.

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Submit a pull request with a description of changes.

## License

This project is licensed under the MIT License.
