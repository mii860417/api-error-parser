import json
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSemB7XiPBrg_BJx3k_m0o_JHXfbhleKEdwu78vVOVidEByCdw/formResponse"

FIELD_TOOL_NAME = "entry.38392295"
FIELD_EVENT_TYPE = "entry.1467972143"
FIELD_INPUT_SOURCE = "entry.2139090681"
FIELD_NOTE = "entry.2065255547"


def is_keep_alive() -> bool:
    try:
        return str(st.query_params.get("keep_alive", "")).lower() in {"1", "true", "yes"}
    except Exception:
        return False


def track(tool_name: str, event_type: str, input_source: str = "none", note: str = "") -> None:
    if is_keep_alive():
        return

    data = {
        FIELD_TOOL_NAME: tool_name,
        FIELD_EVENT_TYPE: event_type,
        FIELD_INPUT_SOURCE: input_source,
        FIELD_NOTE: note,
    }

    try:
        requests.post(FORM_URL, data=data, timeout=5)
    except Exception:
        pass


st.set_page_config(
    page_title="API Error Parser",
    page_icon="🔍",
    layout="wide",
)


COMMON_STATUS_EXPLANATIONS = {
    400: {
        "title": "Bad Request",
        "meaning": "The server could not understand the request because the request format, parameters, or payload is invalid.",
        "common_causes": [
            "Missing required field",
            "Invalid JSON structure",
            "Wrong parameter type",
            "Malformed query string",
        ],
        "suggestions": [
            "Validate request body fields and data types",
            "Check whether all required parameters are included",
            "Compare the payload with the API documentation",
        ],
    },
    401: {
        "title": "Unauthorized",
        "meaning": "Authentication is missing, expired, or invalid.",
        "common_causes": [
            "Missing access token",
            "Expired token",
            "Invalid API key",
            "Wrong Authorization header format",
        ],
        "suggestions": [
            "Check whether the token is present",
            "Verify token expiration",
            "Confirm Authorization header format",
            "Try regenerating the token or API key",
        ],
    },
    403: {
        "title": "Forbidden",
        "meaning": "Authentication may be valid, but the client does not have permission to access the resource.",
        "common_causes": [
            "Insufficient permissions",
            "Role or scope mismatch",
            "IP restriction or policy restriction",
        ],
        "suggestions": [
            "Check user role or permission scope",
            "Verify whether the API key is allowed for this action",
            "Review environment or policy restrictions",
        ],
    },
    404: {
        "title": "Not Found",
        "meaning": "The requested resource or endpoint could not be found.",
        "common_causes": [
            "Wrong endpoint path",
            "Incorrect resource ID",
            "Resource deleted or unavailable",
        ],
        "suggestions": [
            "Verify the endpoint URL",
            "Check the resource ID",
            "Confirm that the resource exists in the current environment",
        ],
    },
    405: {
        "title": "Method Not Allowed",
        "meaning": "The endpoint exists, but the HTTP method is not supported.",
        "common_causes": [
            "Using GET instead of POST",
            "Using POST instead of PUT/PATCH",
        ],
        "suggestions": [
            "Check the allowed HTTP method in the API documentation",
            "Confirm whether the endpoint expects GET, POST, PUT, PATCH, or DELETE",
        ],
    },
    409: {
        "title": "Conflict",
        "meaning": "The request conflicts with the current state of the resource.",
        "common_causes": [
            "Duplicate resource creation",
            "Concurrent update conflict",
            "Business rule conflict",
        ],
        "suggestions": [
            "Check whether the resource already exists",
            "Retry after fetching the latest state",
            "Review conflict-specific business constraints",
        ],
    },
    415: {
        "title": "Unsupported Media Type",
        "meaning": "The server does not support the request payload format.",
        "common_causes": [
            "Wrong Content-Type header",
            "Sending form-data instead of JSON",
            "Sending XML to a JSON-only endpoint",
        ],
        "suggestions": [
            "Check the Content-Type header",
            "Confirm the endpoint accepts the payload format you are sending",
        ],
    },
    422: {
        "title": "Unprocessable Entity",
        "meaning": "The request format is valid, but the content failed validation.",
        "common_causes": [
            "Field validation failure",
            "Invalid enum value",
            "Business rule validation error",
        ],
        "suggestions": [
            "Inspect field-level validation messages",
            "Check allowed value ranges or enum options",
            "Compare the payload with backend validation rules",
        ],
    },
    429: {
        "title": "Too Many Requests",
        "meaning": "The client has sent too many requests in a given amount of time.",
        "common_causes": [
            "Rate limit exceeded",
            "Burst traffic",
            "Retry loop or automation too aggressive",
        ],
        "suggestions": [
            "Check rate-limit headers",
            "Add retry with backoff",
            "Reduce request frequency",
        ],
    },
    500: {
        "title": "Internal Server Error",
        "meaning": "The server encountered an unexpected condition and could not complete the request.",
        "common_causes": [
            "Unhandled backend exception",
            "Database or downstream service issue",
            "Unexpected null value or logic failure",
        ],
        "suggestions": [
            "Check backend logs and stack traces",
            "Look for correlation/request ID",
            "Verify whether a downstream dependency is failing",
        ],
    },
    502: {
        "title": "Bad Gateway",
        "meaning": "A server acting as a gateway or proxy received an invalid response from an upstream server.",
        "common_causes": [
            "Upstream service unavailable",
            "Proxy/gateway issue",
            "Network failure between services",
        ],
        "suggestions": [
            "Check upstream service health",
            "Review proxy or API gateway logs",
            "Retry after confirming dependency stability",
        ],
    },
    503: {
        "title": "Service Unavailable",
        "meaning": "The service is temporarily unavailable or overloaded.",
        "common_causes": [
            "Maintenance window",
            "Service overload",
            "Dependency outage",
        ],
        "suggestions": [
            "Retry later",
            "Check service status or maintenance announcements",
            "Review autoscaling, capacity, or dependency health",
        ],
    },
    504: {
        "title": "Gateway Timeout",
        "meaning": "A gateway or proxy did not receive a timely response from an upstream server.",
        "common_causes": [
            "Upstream response too slow",
            "Database timeout",
            "Long-running backend processing",
        ],
        "suggestions": [
            "Check timeout settings",
            "Review slow queries or dependency latency",
            "Investigate performance bottlenecks",
        ],
    },
}


KEYWORD_HINTS = {
    "timeout": {
        "category": "Timeout",
        "causes": [
            "Downstream service is slow or unavailable",
            "Network latency is too high",
            "Request timeout is too short",
        ],
        "suggestions": [
            "Check server-side latency",
            "Review timeout settings",
            "Add retries with backoff if appropriate",
        ],
    },
    "token": {
        "category": "Authentication / Token",
        "causes": [
            "Expired token",
            "Invalid token",
            "Wrong token scope",
        ],
        "suggestions": [
            "Regenerate the token",
            "Check token expiration",
            "Verify permission scope",
        ],
    },
    "unauthorized": {
        "category": "Authentication",
        "causes": [
            "Missing or invalid credentials",
        ],
        "suggestions": [
            "Check Authorization header",
            "Verify access token or API key",
        ],
    },
    "forbidden": {
        "category": "Authorization",
        "causes": [
            "Authenticated but not permitted",
        ],
        "suggestions": [
            "Check role, permissions, or access scope",
        ],
    },
    "validation": {
        "category": "Validation",
        "causes": [
            "Payload field validation failure",
            "Required field missing",
            "Data type mismatch",
        ],
        "suggestions": [
            "Check detailed validation message",
            "Compare payload with schema",
        ],
    },
    "invalid": {
        "category": "Validation / Invalid Input",
        "causes": [
            "Unexpected field value",
            "Wrong input format",
        ],
        "suggestions": [
            "Validate the payload carefully",
            "Check field type, enum, and required fields",
        ],
    },
    "not found": {
        "category": "Resource Not Found",
        "causes": [
            "Wrong endpoint path",
            "Missing resource",
            "Environment mismatch",
        ],
        "suggestions": [
            "Verify endpoint and resource ID",
            "Check whether the object exists in the current environment",
        ],
    },
    "rate limit": {
        "category": "Rate Limit",
        "causes": [
            "Too many requests in a short time",
        ],
        "suggestions": [
            "Slow down request frequency",
            "Use retry-after or backoff strategy",
        ],
    },
    "duplicate": {
        "category": "Conflict / Duplicate",
        "causes": [
            "Resource already exists",
            "Duplicate request",
        ],
        "suggestions": [
            "Check whether the resource was already created",
            "Make the operation idempotent if possible",
        ],
    },
    "quota": {
        "category": "Quota / Usage Limit",
        "causes": [
            "Usage limit exceeded",
        ],
        "suggestions": [
            "Check account quota and usage plan",
        ],
    },
    "permission": {
        "category": "Permission",
        "causes": [
            "Missing permission",
            "Scope mismatch",
        ],
        "suggestions": [
            "Check account role or token scope",
        ],
    },
}


def try_parse_json(raw_text: str) -> Tuple[Optional[Any], Optional[str]]:
    raw_text = raw_text.strip()
    if not raw_text:
        return None, "Empty body"

    try:
        return json.loads(raw_text), None
    except json.JSONDecodeError:
        return None, "Body is not valid JSON"


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def collect_error_fields(obj: Any, path: str = "") -> List[Tuple[str, str]]:
    results: List[Tuple[str, str]] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            lowered = key.lower()
            if lowered in {
                "error",
                "errors",
                "message",
                "detail",
                "details",
                "description",
                "error_description",
                "reason",
                "code",
                "status",
                "title",
                "type",
            }:
                results.append((current_path, flatten_text(value)))
            results.extend(collect_error_fields(value, current_path))
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            current_path = f"{path}[{index}]"
            results.extend(collect_error_fields(item, current_path))

    return results


def infer_category(status_code: Optional[int], text_blob: str) -> str:
    lowered = text_blob.lower()

    if status_code in COMMON_STATUS_EXPLANATIONS:
        base = COMMON_STATUS_EXPLANATIONS[status_code]["title"]
    else:
        base = "Unknown Error"

    matched_categories = []
    for keyword, meta in KEYWORD_HINTS.items():
        if keyword in lowered:
            matched_categories.append(meta["category"])

    if matched_categories:
        unique = list(dict.fromkeys(matched_categories))
        return f"{base} / {', '.join(unique)}"

    return base


def get_status_analysis(status_code: Optional[int]) -> Dict[str, Any]:
    if status_code in COMMON_STATUS_EXPLANATIONS:
        return COMMON_STATUS_EXPLANATIONS[status_code]

    if status_code is None:
        return {
            "title": "Unknown Status",
            "meaning": "No HTTP status code was provided.",
            "common_causes": ["Status code missing from the input"],
            "suggestions": ["Provide the HTTP status code if available"],
        }

    if 400 <= status_code < 500:
        return {
            "title": "Client Error",
            "meaning": "The request appears to contain invalid data, invalid authentication, or a resource issue.",
            "common_causes": [
                "Invalid request payload",
                "Authentication or authorization issue",
                "Wrong endpoint or resource ID",
            ],
            "suggestions": [
                "Inspect request body, headers, and endpoint path",
                "Check auth token, API key, and permissions",
            ],
        }

    if 500 <= status_code < 600:
        return {
            "title": "Server Error",
            "meaning": "The server failed while processing the request.",
            "common_causes": [
                "Unhandled backend exception",
                "Dependency failure",
                "Infrastructure or timeout issue",
            ],
            "suggestions": [
                "Check backend logs",
                "Look for correlation ID or request ID",
                "Review downstream dependency health",
            ],
        }

    return {
        "title": "Informational Result",
        "meaning": "The status code is outside the typical error range.",
        "common_causes": ["Input may not represent an error response"],
        "suggestions": ["Double-check whether this is the correct response to analyze"],
    }


def extract_keyword_based_hints(text_blob: str) -> Tuple[List[str], List[str]]:
    lowered = text_blob.lower()
    causes: List[str] = []
    suggestions: List[str] = []

    for keyword, meta in KEYWORD_HINTS.items():
        if keyword in lowered:
            causes.extend(meta["causes"])
            suggestions.extend(meta["suggestions"])

    causes = list(dict.fromkeys(causes))
    suggestions = list(dict.fromkeys(suggestions))
    return causes, suggestions


def extract_request_id(text_blob: str) -> Optional[str]:
    patterns = [
        r"(request[_-]?id[\"':\s]+)([A-Za-z0-9\-_.]+)",
        r"(correlation[_-]?id[\"':\s]+)([A-Za-z0-9\-_.]+)",
        r"(trace[_-]?id[\"':\s]+)([A-Za-z0-9\-_.]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_blob, flags=re.IGNORECASE)
        if match:
            return match.group(2)
    return None


def analyze_api_error(
    status_code: Optional[int],
    raw_body: str,
    endpoint: str,
    method: str,
) -> Dict[str, Any]:
    parsed_json, parse_note = try_parse_json(raw_body)
    status_info = get_status_analysis(status_code)

    error_fields: List[Tuple[str, str]] = []
    text_blob_parts = [raw_body, endpoint, method]

    if parsed_json is not None:
        error_fields = collect_error_fields(parsed_json)
        text_blob_parts.extend([f"{path}: {value}" for path, value in error_fields])

    text_blob = "\n".join(part for part in text_blob_parts if part)
    category = infer_category(status_code, text_blob)
    keyword_causes, keyword_suggestions = extract_keyword_based_hints(text_blob)
    request_id = extract_request_id(text_blob)

    probable_causes = list(dict.fromkeys(status_info["common_causes"] + keyword_causes))
    suggestions = list(dict.fromkeys(status_info["suggestions"] + keyword_suggestions))

    summary_parts = []
    if status_code is not None:
        summary_parts.append(f"HTTP {status_code}")
    summary_parts.append(status_info["title"])
    summary = " — ".join(summary_parts)

    return {
        "summary": summary,
        "category": category,
        "meaning": status_info["meaning"],
        "parse_note": parse_note,
        "parsed_json": parsed_json,
        "error_fields": error_fields,
        "probable_causes": probable_causes,
        "suggestions": suggestions,
        "request_id": request_id,
    }


def render_error_fields(error_fields: List[Tuple[str, str]]) -> None:
    if not error_fields:
        st.info("No common error fields were detected in the response body.")
        return

    st.markdown("### Detected Error Fields")
    for path, value in error_fields:
        st.markdown(f"- **{path}**: `{value}`")


def load_example(example_name: str) -> Tuple[str, str, int, str]:
    examples = {
        "401 Unauthorized": (
            "GET",
            "/v1/user/profile",
            401,
            json.dumps(
                {
                    "error": "unauthorized",
                    "message": "Token expired",
                    "code": "AUTH_401_EXPIRED",
                },
                indent=2,
            ),
        ),
        "422 Validation Error": (
            "POST",
            "/v1/orders",
            422,
            json.dumps(
                {
                    "error": "validation_failed",
                    "message": "Invalid request body",
                    "details": {
                        "email": ["This field is required."],
                        "quantity": ["Must be greater than 0"],
                    },
                },
                indent=2,
            ),
        ),
        "500 Internal Server Error": (
            "POST",
            "/v1/payment/charge",
            500,
            json.dumps(
                {
                    "error": "internal_server_error",
                    "message": "Unexpected null reference",
                    "request_id": "req_abc123xyz",
                },
                indent=2,
            ),
        ),
        "429 Rate Limit": (
            "GET",
            "/v1/report/export",
            429,
            json.dumps(
                {
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please retry later.",
                },
                indent=2,
            ),
        ),
    }
    return examples[example_name]


st.title("🔍 API Error Parser")
st.caption(
    "Paste an HTTP status code and API error response body to get a plain-English explanation, likely causes, and debugging suggestions."
)

if "tracked_visitor" not in st.session_state:
    track("api-error-parser", "visitor")
    st.session_state["tracked_visitor"] = True

with st.sidebar:
    st.header("Examples")
    example_choice = st.selectbox(
        "Load a sample",
        ["None", "401 Unauthorized", "422 Validation Error", "500 Internal Server Error", "429 Rate Limit"],
    )

    st.markdown("---")
    st.markdown("### What this tool does")
    st.markdown(
        """
- Explains common API error responses
- Extracts common error fields
- Suggests likely root causes
- Gives debugging next steps
"""
    )

if example_choice != "None":
    default_method, default_endpoint, default_status, default_body = load_example(example_choice)
else:
    default_method, default_endpoint, default_status, default_body = "POST", "/v1/example", 500, ""

col1, col2 = st.columns([1, 1])

with col1:
    method = st.selectbox(
        "HTTP Method",
        ["GET", "POST", "PUT", "PATCH", "DELETE"],
        index=["GET", "POST", "PUT", "PATCH", "DELETE"].index(default_method),
    )
    endpoint = st.text_input("Endpoint (optional)", value=default_endpoint)
    status_code_raw = st.text_input("HTTP Status Code", value=str(default_status))

with col2:
    st.markdown("### Tips")
    st.markdown(
        """
- Paste the full JSON error body if possible  
- Include endpoint and method for better context  
- This tool works best with API error payloads from REST services  
"""
    )

raw_body = st.text_area(
    "Response Body / Error Payload",
    value=default_body,
    height=280,
    placeholder='e.g. {"error":"validation_failed","message":"Invalid email"}',
)

analyze_clicked = st.button("Analyze API Error", type="primary")

if analyze_clicked:
    input_clean = raw_body.strip()

    is_exact_example = (
        example_choice != "None"
        and method == default_method
        and endpoint == default_endpoint
        and status_code_raw.strip() == str(default_status)
        and raw_body.strip() == default_body.strip()
    )

    input_source = "example" if is_exact_example else "custom"

    track(
        tool_name="api-error-parser",
        event_type="click",
        input_source=input_source,
    )

    status_code: Optional[int] = None
    if status_code_raw.strip():
        try:
            status_code = int(status_code_raw.strip())
        except ValueError:
            st.error("HTTP Status Code must be a number.")
            st.stop()

    if not input_clean:
        st.error("Please paste response body first.")
        st.stop()

    result = analyze_api_error(
        status_code=status_code,
        raw_body=raw_body,
        endpoint=endpoint,
        method=method,
    )

    if len(input_clean) > 20 and input_source == "custom":
        track(
            tool_name="api-error-parser",
            event_type="qualified",
            input_source=input_source,
        )

    st.success("Analysis complete")

    st.markdown("## Summary")
    st.markdown(f"**{result['summary']}**")
    st.markdown(f"**Category:** {result['category']}")
    st.markdown(f"**Meaning:** {result['meaning']}")

    if result["request_id"]:
        st.markdown(f"**Detected Request ID / Trace ID:** `{result['request_id']}`")

    if result["parse_note"]:
        st.warning(result["parse_note"])

    render_error_fields(result["error_fields"])

    st.markdown("### Likely Causes")
    for item in result["probable_causes"]:
        st.markdown(f"- {item}")

    st.markdown("### Suggested Debugging Steps")
    for item in result["suggestions"]:
        st.markdown(f"- {item}")

    if result["parsed_json"] is not None:
        st.markdown("### Parsed JSON")
        st.json(result["parsed_json"])

st.markdown("---")
st.markdown("### Good use cases")
st.markdown(
    """
- Debugging REST API failures  
- Understanding backend error responses  
- Helping QA engineers interpret API errors faster  
- Turning raw API responses into human-readable explanations  
"""
)

st.caption("If this tool helped you, please ⭐ the GitHub repo.")
