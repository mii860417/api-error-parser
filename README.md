# 🔎 API Error Parser

**API Error Parser** is a simple Streamlit tool that helps developers and QA engineers understand API error responses faster.

Paste an HTTP status code and an API error payload, and the tool will:

- Explain the meaning of the error
- Extract common error fields
- Suggest likely causes
- Provide debugging steps

Built with **Python + Streamlit**.

---

# 🚀 Demo

Try the tool online:

https://your-app-name.streamlit.app

---

# ❓ Why This Tool Exists

When an API fails, the response body is often too raw or too technical for quick debugging.

This tool turns common API errors into a more human-readable explanation, which is useful for:

- QA engineers
- Backend developers
- Frontend developers
- Automation engineers
- Anyone debugging REST API responses

## Example use cases

- Understand what a `500 Internal Server Error` may really mean
- Parse a `422 validation_failed` response body
- Diagnose `401 unauthorized` or token expiration issues
- Investigate `429 rate limit exceeded` errors

# ✨ Features

- Parse HTTP status codes such as 400, 401, 403, 404, 422, 429, 500, 502, 503, and 504
- Extract common fields like `error`, `message`, `details`, `code`, and `request_id`
- Detect likely categories such as:
  - Authentication
  - Authorization
  - Validation
  - Timeout
  - Rate limit
  - Resource not found
- Provide practical debugging suggestions


# 🖥 Run Locally

Install dependencies
```
pip install -r requirements.txt
```

Run the Streamlit app
```
streamlit run app.py
```

Then open your browser:
```
http://localhost:8501
```

# 📁 Project Structure
```
logcat-error-filter
│
├── app.py
├── requirements.txt
└── README.md
```


# 🔍 Search Keywords

This project targets common developer searches such as:

- API error parser

- HTTP error parser

- API error response analyzer

- understand API error message

- HTTP 500 error meaning

- HTTP 401 unauthorized parser

- API validation error checker

# 🔗 Related Tools

You may also be interested in:

- Crash Log Analyzer : https://crash-log-analyzer.streamlit.app
- Stack Trace Root Cause Finder : https://stack-trace-root-cause-finder.streamlit.app
- Logcat Error Filter : https://logcat-error-filter.streamlit.app

These tools help developers debug logs more efficiently.