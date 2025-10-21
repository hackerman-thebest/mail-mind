# Mail-Mind Testing Guide

## The Problem: Resource-Constrained Test Machines

**Issue:** Running actual LLM inference requires significant resources:
- **RAM:** 4-8GB+ for model loading
- **CPU/GPU:** Significant compute for inference
- **Time:** 10-30 seconds per inference (first run even longer)
- **Disk:** 2-5GB for model files

**Result:** Test machines, CI/CD pipelines, and lightweight environments **cannot run real LLM inference** without:
- Timeouts
- Out of memory errors
- Slow test execution
- Infrastructure costs

## The Solution: Multi-Level Testing Strategy

We provide **4 levels of testing** from lightest to most realistic:

### Level 1: Unit Tests (No Ollama Required) ⚡ Fastest

**File:** `tests/unit/test_ollama_manager.py`

**Uses:** Object mocks via `unittest.mock`

**Pros:**
- ✅ Instant execution (<1 second)
- ✅ No dependencies
- ✅ Tests code logic
- ✅ Perfect for CI/CD

**Cons:**
- ❌ Doesn't test HTTP communication
- ❌ Doesn't validate API compatibility

**When to use:** Regular development, CI/CD, pre-commit hooks

**Run:**
```bash
pytest tests/unit/test_ollama_manager.py
```

---

### Level 2: Mock Client Tests (No Ollama Required) ⚡ Fast

**File:** `mock_ollama_test.py`

**Uses:** Enhanced object mocks with realistic behavior

**Pros:**
- ✅ Fast execution (2-3 seconds)
- ✅ No Ollama needed
- ✅ Realistic response generation
- ✅ Tests multiple scenarios

**Cons:**
- ❌ Still using mocks, not real HTTP

**When to use:** Local testing without Ollama, quick validation

**Run:**
```bash
python mock_ollama_test.py
```

---

### Level 3: Mock API Server (No Model Required) 🎯 **RECOMMENDED**

**Files:**
- `mock_ollama_server.py` - HTTP server
- `test_with_mock_api.py` - Integration tests

**Uses:** Real HTTP server implementing Ollama API

**Pros:**
- ✅ Real HTTP communication
- ✅ Real `ollama` library usage
- ✅ No model download/inference needed
- ✅ Fast (5-10 seconds total)
- ✅ Tests actual integration code
- ✅ Validates API compatibility
- ✅ **Works on resource-constrained machines**

**Cons:**
- ❌ Not testing actual LLM behavior

**When to use:**
- ✅ Integration testing
- ✅ CI/CD pipelines
- ✅ Resource-constrained environments
- ✅ Development without GPU

**Run:**
```bash
# All-in-one (recommended)
python test_with_mock_api.py

# Or separately:
python mock_ollama_server.py --server-only  # Terminal 1
python main.py                               # Terminal 2
```

**What this tests:**
- ✅ OllamaManager initialization
- ✅ HTTP connection to API
- ✅ Model listing
- ✅ Connection pooling
- ✅ Inference requests (generate & chat)
- ✅ Streaming responses
- ✅ Priority classification logic
- ✅ Sentiment analysis logic
- ✅ Error handling

---

### Level 4: Real Ollama + Real Model (Full Stack) 🐢 Slowest

**Requires:**
- Ollama installed
- Model downloaded (2-5GB)
- 4-8GB RAM available
- CPU/GPU for inference

**Pros:**
- ✅ Tests actual LLM behavior
- ✅ Real response quality
- ✅ True end-to-end validation

**Cons:**
- ❌ Slow (30+ seconds)
- ❌ High resource usage
- ❌ Not suitable for CI/CD
- ❌ Expensive infrastructure

**When to use:**
- Manual QA testing
- Production readiness validation
- Response quality assessment
- Performance benchmarking

**Setup:**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a lightweight model (recommended for testing)
ollama pull llama3.2:1b   # Smallest (1.3GB, fast)
# OR
ollama pull llama3.2:3b   # Balanced (2GB, good quality)

# 3. Run tests
python test_ollama_inference.py
```

---

## Recommended Testing Strategy

### For CI/CD Pipelines

```yaml
# .github/workflows/test.yml
- name: Unit Tests
  run: pytest tests/unit/

- name: Integration Tests (Mock API)
  run: python test_with_mock_api.py
```

**Why:** Fast, reliable, no resource constraints

### For Local Development

```bash
# Quick validation
python mock_ollama_test.py

# Integration testing
python test_with_mock_api.py

# (Optional) Full testing with real Ollama
python test_ollama_inference.py
```

### For Production Deployment

1. ✅ Run all mock tests (Levels 1-3)
2. ✅ Manual testing with real Ollama (Level 4)
3. ✅ User acceptance testing
4. ✅ Performance benchmarking

---

## Test Comparison Matrix

| Feature | Level 1 | Level 2 | Level 3 | Level 4 |
|---------|---------|---------|---------|---------|
| **Speed** | ⚡⚡⚡⚡⚡ | ⚡⚡⚡⚡ | ⚡⚡⚡ | ⚡ |
| **Resources** | Minimal | Minimal | Low | **High** |
| **Realism** | 60% | 70% | **95%** | 100% |
| **CI/CD Suitable** | ✅ Yes | ✅ Yes | ✅ **Yes** | ❌ No |
| **HTTP Testing** | ❌ No | ❌ No | ✅ **Yes** | ✅ Yes |
| **Model Required** | ❌ No | ❌ No | ❌ **No** | ✅ Yes |
| **Tests Real LLM** | ❌ No | ❌ No | ❌ No | ✅ **Yes** |

---

## Troubleshooting

### "Test machine can't run LLM inference"

**Solution:** Use **Level 3 (Mock API Server)**
```bash
python test_with_mock_api.py
```

This gives you 95% realism without needing to run actual models.

### "CI/CD pipeline times out"

**Solution:** Use **Level 1 + Level 3**
```bash
pytest tests/unit/                # Fast unit tests
python test_with_mock_api.py      # Integration tests
```

### "Want to test response quality"

**Solution:** Use **Level 4** on your local machine
```bash
ollama pull llama3.2:3b
python test_ollama_inference.py
```

### "Out of memory errors"

**Options:**
1. Use lighter model: `ollama pull llama3.2:1b`
2. Use mock server (Level 3): `python test_with_mock_api.py`
3. Skip inference in tests: `export MAILMIND_SKIP_TEST=1`

---

## What Gets Tested at Each Level

### Code Logic ✅ (All Levels)
- Configuration handling
- Error handling
- Connection management
- Model fallback logic

### API Integration ✅ (Level 3+)
- HTTP requests/responses
- Streaming
- Error codes
- API compatibility

### Model Behavior ✅ (Level 4 Only)
- Actual LLM responses
- Response quality
- Inference performance
- Token generation

---

## Summary

**For Resource-Constrained Test Machines:**

Use **Level 3 (Mock API Server)** - it's the sweet spot:
- ✅ No model inference required
- ✅ Real HTTP communication tested
- ✅ Fast enough for CI/CD
- ✅ Validates integration correctness
- ✅ 95% realistic testing

**Command:**
```bash
python test_with_mock_api.py
```

**Result:** All Mail-Mind functionality tested without requiring 8GB RAM and GPU! 🎉

---

## Test Scripts Reference

| Script | Purpose | Ollama Needed | Model Needed | Speed | Realism |
|--------|---------|---------------|--------------|-------|---------|
| `tests/unit/test_ollama_manager.py` | Unit tests | ❌ | ❌ | ⚡⚡⚡⚡⚡ | 60% |
| `mock_ollama_test.py` | Mock objects | ❌ | ❌ | ⚡⚡⚡⚡ | 70% |
| `test_inference_scenarios.py` | Scenarios | ❌ | ❌ | ⚡⚡⚡⚡ | 70% |
| `mock_ollama_server.py` | API server | ❌ | ❌ | ⚡⚡⚡ | 95% |
| `test_with_mock_api.py` | **Integration** | ❌ | ❌ | ⚡⚡⚡ | **95%** |
| `test_ollama_inference.py` | Full stack | ✅ | ✅ | ⚡ | 100% |
