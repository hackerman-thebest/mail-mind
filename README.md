# MailMind - Sovereign AI Email Assistant

**Your AI, Your Data, Your Rules**

MailMind is a privacy-first desktop application that provides AI-powered email intelligence without sending data to the cloud. All AI processing happens locally on your machine using Ollama.

## Current Status

**Phase:** Implementation (Phase 4)
**Current Story:** 1.2 - Email Preprocessing Pipeline ✅ IMPLEMENTED

## Features (Current)

### ✅ Story 1.1: Ollama Integration & Model Setup (COMPLETE)

- Ollama Python client integration
- Automatic model verification and fallback
- Support for Llama 3.1 8B and Mistral 7B models
- Configuration management via YAML
- Comprehensive error handling
- Full unit test coverage

### ✅ Story 1.2: Email Preprocessing Pipeline (COMPLETE)

- Email metadata extraction (sender, subject, date, threading)
- HTML to plain text conversion with structure preserved
- Intelligent signature and quote stripping
- Attachment metadata handling
- Smart content truncation for long emails (>10k chars)
- Structured JSON output for LLM consumption
- Thread context preservation
- Input sanitization to prevent prompt injection
- Performance: <200ms preprocessing target

## Prerequisites

### System Requirements

- **OS:** Windows 10/11 (Mac support planned for v2.0)
- **RAM:** 16GB minimum, 32GB recommended
- **Disk Space:** 10GB (including models)
- **GPU:** Optional but recommended for optimal performance

### Required Software

1. **Python 3.10+**
   - Download from https://www.python.org/downloads/

2. **Ollama**
   - Download from https://ollama.com/download
   - Install and ensure service is running

3. **AI Model (one of):**
   - Llama 3.1 8B (recommended): `ollama pull llama3.1:8b-instruct-q4_K_M`
   - Mistral 7B (fallback): `ollama pull mistral:7b-instruct-q4_K_M`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mail-mind.git
cd mail-mind
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama

Download and install Ollama from https://ollama.com/download

Verify installation:
```bash
ollama --version
```

### 4. Download AI Model

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
```

This will download approximately 5GB of data.

## Usage

### Run the Application

```bash
python main.py
```

Expected output:
```
2025-10-13 - mailmind - INFO - Starting MailMind...
2025-10-13 - mailmind - INFO - Loading configuration...
2025-10-13 - ollama_manager - INFO - Attempting to connect to Ollama service...
2025-10-13 - ollama_manager - INFO - Connected to Ollama service in 0.123s
2025-10-13 - ollama_manager - INFO - Primary model verified: llama3.1:8b-instruct-q4_K_M
2025-10-13 - ollama_manager - INFO - Test inference successful in 2.456s
✓ Ollama initialization successful!
✓ Story 1.1 (Ollama Integration) complete!
```

### Email Preprocessing Demo

```bash
python examples/email_preprocessing_demo.py
```

This demonstrates:
- Simple plain text email preprocessing
- HTML email parsing
- Signature stripping
- Thread context extraction
- Attachment handling
- Long email truncation
- Suspicious content detection
- Complete structured JSON output

### Using the EmailPreprocessor

```python
from src.mailmind.core.email_preprocessor import EmailPreprocessor

# Create preprocessor instance
preprocessor = EmailPreprocessor()

# Preprocess an email
email = {
    'from': 'alice@example.com',
    'subject': 'Test Email',
    'body': 'Email content here...',
    'date': '2025-10-13T14:30:00Z'
}

result = preprocessor.preprocess_email(email)

# Access structured output
print(f"From: {result['metadata']['from']}")
print(f"Body: {result['content']['body']}")
print(f"Processing time: {result['preprocessing_metadata']['processing_time_ms']}ms")
```

## Development

### Project Structure

```
mail-mind/
├── src/
│   └── mailmind/
│       ├── core/              # Core business logic
│       │   ├── ollama_manager.py      # Story 1.1
│       │   └── email_preprocessor.py  # Story 1.2
│       ├── ui/                # User interface (coming in Story 2.3)
│       ├── utils/             # Utilities
│       │   └── config.py
│       └── models/            # Data models
├── tests/
│   ├── unit/                  # Unit tests
│   │   ├── test_ollama_manager.py        # Story 1.1 tests
│   │   └── test_email_preprocessor.py    # Story 1.2 tests
│   └── integration/           # Integration tests
├── examples/
│   └── email_preprocessing_demo.py       # Story 1.2 demo
├── config/
│   └── default.yaml           # Default configuration
├── docs/
│   ├── stories/               # Story files
│   │   ├── story-1.1.md       # Ollama Integration
│   │   └── story-1.2.md       # Email Preprocessing
│   ├── epic-stories.md        # Epic breakdown
│   └── project-workflow-status-2025-10-13.md
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── pytest.ini                 # Test configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mailmind --cov-report=html

# Run specific test file
pytest tests/unit/test_ollama_manager.py

# Run specific test class
pytest tests/unit/test_ollama_manager.py::TestOllamaConnection
```

### Configuration

Configuration is managed via YAML files in the `config/` directory.

**config/default.yaml:**
```yaml
ollama:
  primary_model: "llama3.1:8b-instruct-q4_K_M"
  fallback_model: "mistral:7b-instruct-q4_K_M"
  temperature: 0.3
  context_window: 8192
  gpu_acceleration: true
```

## Roadmap

### ✅ Completed (2/12 stories - 14% progress)

- **Story 1.1:** Ollama Integration & Model Setup (5 points)
- **Story 1.2:** Email Preprocessing Pipeline (5 points)

### 🔄 Next Up

- **Story 1.3:** Real-Time Analysis Engine (<2s)
- **Story 1.4:** Priority Classification System
- **Story 1.5:** Response Generation Assistant
- **Story 1.6:** Performance Optimization & Caching

### Epic 2: Desktop Application

- **Story 2.1:** Outlook Integration (pywin32)
- **Story 2.2:** SQLite Database & Caching Layer
- **Story 2.3:** CustomTkinter UI Framework
- **Story 2.4:** Settings & Configuration System
- **Story 2.5:** Hardware Profiling & Onboarding Wizard
- **Story 2.6:** Error Handling, Logging & Installer

## Troubleshooting

### Ollama Not Found

**Error:** `Failed to connect to Ollama service`

**Solution:**
1. Ensure Ollama is installed: https://ollama.com/download
2. Start Ollama service: `ollama serve`
3. Verify it's running: `ollama list`

### Model Not Available

**Error:** `Neither primary model nor fallback model are available`

**Solution:**
Download the model:
```bash
ollama pull llama3.1:8b-instruct-q4_K_M
```

### Slow Performance

If AI inference is slow:
1. Check if GPU acceleration is working: Look for GPU detection in logs
2. Consider using a smaller model: `mistral:7b-instruct-q4_K_M`
3. Verify system meets minimum requirements (16GB RAM)

## License

Copyright © 2025 MailMind Team. All rights reserved.

## Contributing

This project is currently in active development. Contributions will be welcome after v1.0 release.

## Support

For issues and questions:
- Check documentation in `docs/`
- Review story files in `docs/stories/`
- See workflow status in `docs/project-workflow-status-2025-10-13.md`

---

**Project Status:** 14% Complete (Phase 4 - Implementation)
**Stories Completed:** 2/12 (10 story points)
**Current Story:** 1.2 ✅ COMPLETE
**Next Story:** 1.3 - Real-Time Analysis Engine
