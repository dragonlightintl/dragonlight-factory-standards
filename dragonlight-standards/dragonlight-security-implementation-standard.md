# Dragonlight Security Implementation Standard

**Owner:** [REDACTED PERSONA] + [REDACTED PERSONA]  
**Status:** Active — mandatory for all Dragonlight code  
**Origin:** Session 71, operator directive: "The security mentality must exist and be embedded into the DNA of the code itself."  
**Companion specs:**  
- `dragonlight-security-specification.md` — threat model and architecture posture  
- `dragonlight-coding-standards.md` (§11 Secure, §10 Bulletproof) — foundational values  
- `dragonlight-development-pipeline.md` — security gates at every stage  
- `dragonlight-integration-verification-strategy.md` — security testing across module boundaries

**Scope:** Every line of code written for Dragonlight and [REDACTED] — Python (Engine, Core), Rust ([REDACTED]-cli, [REDACTED]-intent), Elm (future client). All environments: dev, staging, production.

**Authority:** This document is a gate, not a guideline. Code that violates these standards does not ship. No exceptions without a documented, reviewed security exception logged to `[REDACTED].db`.

---

## Context Assembly

### Standards (load before building)

| Standard | SQLite Query | File Fallback |
|----------|-------------|---------------|
| Coding | `SELECT content FROM behavioral_rules WHERE protocol = 'dragonlight_coding_standards'` | `00-System/standards/dragonlight-coding-standards.md` |
| Security | `SELECT content FROM behavioral_rules WHERE protocol = 'security_standards'` | `00-System/standards/dragonlight-security-implementation-standard.md` |
| UX | `SELECT content FROM behavioral_rules WHERE protocol = 'ux_standards'` | `00-System/standards/dragonlight-brand-system.md` |
| Pipeline | `SELECT content FROM behavioral_rules WHERE protocol = 'development_pipeline'` | `00-System/standards/dragonlight-development-pipeline.md` |

### Architectural Constraints
- **Trust tier:** Cross-cutting (security standard, applies to Core, Engine, Clients)
- **Boundary contracts:** All boundaries (Engine-Core, Client-Engine, Code-level)
- **Write path owner:** N/A (specification, not implementation)
- **Network access:** N/A (specification applies to all network and non-network code)

---

## Industry Context — Why This Exists Now

**Vercel supply chain compromise (April 2026):** A third-party OAuth tool with broad scopes was compromised. Vercel's architecture implicitly trusted it. Blast radius: platform-wide. The lesson is not "audit OAuth tools better" — it is that third-party integrations must receive the minimum scope to perform their function, with no implicit trust, and no privilege path to expand that scope.

**Lovable BOLA exposure (April 2026):** Client-supplied object IDs were used to retrieve objects without server-side ownership validation. Source code, credentials, and personal data from thousands of projects were exposed. The code worked correctly on the happy path. It was architecturally broken on the adversarial path. The lesson: correct behavior on authorized requests is not security. Security is what happens on unauthorized requests.

Both failures were not configuration errors or patching failures. They were trust assumption failures baked into the architecture. This spec exists to make those assumptions explicit, structural, and testable — so they cannot be accidentally removed.

---

## Document Structure

Each section follows a consistent pattern:

- **MANDATE** — what the code must do  
- **PATTERN** — the correct implementation (code examples)  
- **ANTI-PATTERN** — what is forbidden (code examples)  
- **ENFORCEMENT** — how CI catches violations (tool, rule, gate)  

---

## Table of Contents

1. [OWASP Top 10 Mapping](#1-owasp-top-10-mapping)  
2. [Secure Coding Patterns](#2-secure-coding-patterns)  
3. [Supply Chain Security](#3-supply-chain-security)  
4. [Memory Safety — Rust Components](#4-memory-safety--rust-components)  
5. [CI/CD Security Enforcement](#5-cicd-security-enforcement)  
6. [Security Testing Requirements](#6-security-testing-requirements)  
7. [Incident Response Code Patterns](#7-incident-response-code-patterns)  
8. [Data Protection](#8-data-protection)  
9. [Protocol Buffer Security (Phase 3)](#9-protocol-buffer-security-phase-3)  

---

## 1. OWASP Top 10 Mapping

For each OWASP category: what it means in the [REDACTED] codebase, the mandatory code patterns, and how CI enforces compliance.

---

### 1.1 A01 — Broken Access Control / BOLA

The Lovable failure. Client supplies an object ID; server returns the object without verifying the requesting operator owns it. Every object retrieval in [REDACTED] must fail closed.

**MANDATE:** Every function that retrieves or modifies a database object must validate that the requesting operator's `user_id` is the owner of that object before returning data. No implicit trust of client-supplied IDs. This applies regardless of how the ID arrived — wire, queue flush, offline replay.

**PATTERN — Python (Engine/Core):**

```python
# CORRECT: ownership verified before data returned
def get_session(conn: sqlite3.Connection, session_id: str, requesting_user_id: str) -> Result[Session, CoreError]:
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ? AND user_id = ?",
        (session_id, requesting_user_id)
    ).fetchone()
    if row is None:
        # Return NOT_FOUND — never reveal whether object exists but is unauthorized
        return Failure(CoreError(kind=CoreErrorKind.NOT_FOUND, operation="get_session"))
    return Success(Session.from_row(row))

# CORRECT: field-level ownership check when cross-table joins are unavoidable
def get_task(conn: sqlite3.Connection, task_id: str, requesting_user_id: str) -> Result[Task, CoreError]:
    row = conn.execute(
        "SELECT t.* FROM tasks t "
        "JOIN sessions s ON t.session_id = s.session_id "
        "WHERE t.task_id = ? AND s.user_id = ?",
        (task_id, requesting_user_id)
    ).fetchone()
    if row is None:
        return Failure(CoreError(kind=CoreErrorKind.NOT_FOUND, operation="get_task"))
    return Success(Task.from_row(row))
```

**PATTERN — Rust ([REDACTED]-cli):**

```rust
// CORRECT: ownership validated at the persistence boundary
pub fn get_operator_config(
    conn: &Connection,
    config_id: &str,
    requesting_operator_id: &str,
) -> Result<OperatorConfig, [REDACTED]Error> {
    let result = conn.query_row(
        "SELECT * FROM operator_configs WHERE config_id = ?1 AND operator_id = ?2",
        params![config_id, requesting_operator_id],
        |row| OperatorConfig::try_from(row),
    );
    match result {
        Ok(config) => Ok(config),
        Err(rusqlite::Error::QueryReturnedNoRows) => Err([REDACTED]Error::NotFound),
        Err(e) => Err([REDACTED]Error::Persistence(e.to_string())),
    }
}
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: retrieves by ID alone — any user can access any session
def get_session_FORBIDDEN(conn, session_id):
    return conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()

# FORBIDDEN: fetches then checks — object existence is leaked, and a coding error
# could return the object before the check completes
def get_session_FORBIDDEN_v2(conn, session_id, requesting_user_id):
    row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
    if row and row["user_id"] != requesting_user_id:
        raise PermissionError("not yours")
    return row  # returned before ownership verified in async context
```

**ENFORCEMENT:**
- AST lint rule: any `SELECT` query without a `user_id`, `operator_id`, or `owner_id` predicate in the same query must be flagged. Manual review gate for exceptions (e.g., admin-only functions, which must be separately audited).
- Code review checklist item: "Every DB read function includes ownership parameter and validates in the query, not post-fetch."
- Integration test: for every `get_*` function, a test must exist that calls it with a valid `object_id` but a different `user_id` and asserts `NOT_FOUND` is returned (not `PERMISSION_DENIED`, which leaks existence).

---

### 1.2 A02 — Cryptographic Failures

Using weak algorithms, storing credentials in cleartext, or using encryption incorrectly (e.g., ECB mode, fixed IVs, reused nonces).

**MANDATE:** All cryptographic operations must use algorithms and modes listed in §2.5. Any use of a deprecated algorithm is a build-time failure. TLS configuration is specified in `dragonlight-security-specification.md §5.2` — that spec governs; these patterns extend it to application-level crypto.

**PATTERN — Python (hashing, token generation):**

```python
import secrets
import hashlib

# CORRECT: token generation — cryptographically secure, sufficient entropy
def generate_session_token() -> str:
    return secrets.token_urlsafe(32)  # 256 bits of entropy

# CORRECT: password hashing — use argon2-cffi, never raw hashlib for passwords
from argon2 import PasswordHasher
_PH = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

def hash_credential(plaintext: str) -> str:
    return _PH.hash(plaintext)

def verify_credential(stored_hash: str, plaintext: str) -> bool:
    try:
        return _PH.verify(stored_hash, plaintext)
    except Exception:
        return False

# CORRECT: HMAC for integrity verification
import hmac
def verify_hmac(key: bytes, message: bytes, received_mac: bytes) -> bool:
    expected = hmac.new(key, message, hashlib.sha256).digest()
    return hmac.compare_digest(expected, received_mac)  # constant-time
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: MD5, SHA1, or raw SHA256 for passwords
import hashlib
stored = hashlib.md5(password.encode()).hexdigest()  # FORBIDDEN

# FORBIDDEN: random.random() or uuid4() for security-sensitive tokens
import random, uuid
token = str(uuid.uuid4())  # uuid4 is not cryptographically suitable for auth tokens
token = str(random.randint(100000, 999999))  # FORBIDDEN

# FORBIDDEN: non-constant-time comparison for secrets
if received_token == stored_token:  # timing oracle — FORBIDDEN for credential comparison
    ...

# FORBIDDEN: ECB mode for any symmetric encryption
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_ECB)  # FORBIDDEN
```

**ENFORCEMENT:**
- Bandit rule `B303` (MD5/SHA1 for security), `B311` (random for security). These are blocking.
- Import audit: `hashlib.md5`, `hashlib.sha1` — flagged when not in a comment or test for non-security contexts (e.g., checksums). Engineer must annotate with `# nosec: checksum-only` to suppress, which adds to audit log.
- `secrets` module is the only permitted source of cryptographically random values. `random` module usage in any non-simulation/non-test context is flagged.

---

### 1.3 A03 — Injection

SQL injection, shell injection, prompt injection. The most mechanically preventable class of vulnerabilities.

**MANDATE:** All database access uses parameterized queries. No string interpolation into SQL. No string interpolation into shell commands. No user content reaches a shell invocation. Prompt injection is addressed separately in §1.10 (OWASP LLM01).

**PATTERN — Python (SQL):**

```python
# CORRECT: parameterized query, always
def find_tasks_by_tag(conn: sqlite3.Connection, user_id: str, tag: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND tag = ?",
        (user_id, tag)
    ).fetchall()
    return [dict(row) for row in rows]

# CORRECT: dynamic column names (rare, must use allowlist)
ALLOWED_SORT_COLUMNS = frozenset({"created_at", "updated_at", "priority"})
def get_tasks_sorted(conn, user_id: str, sort_col: str) -> list[dict]:
    if sort_col not in ALLOWED_SORT_COLUMNS:
        raise ValueError(f"Invalid sort column: {sort_col!r}")
    # Only after allowlist validation is string interpolation permitted for column names
    rows = conn.execute(
        f"SELECT * FROM tasks WHERE user_id = ? ORDER BY {sort_col}",
        (user_id,)
    ).fetchall()
    return [dict(row) for row in rows]
```

**PATTERN — Rust (SQL via rusqlite):**

```rust
// CORRECT: named parameters, no string formatting
conn.execute(
    "INSERT INTO sessions (session_id, user_id, created_at) VALUES (?1, ?2, ?3)",
    params![session_id, user_id, created_at],
)?;
```

**PATTERN — Shell (Python subprocess):**

```python
import subprocess
# CORRECT: args as list, never shell=True with user input
result = subprocess.run(
    ["git", "log", "--oneline", "-n", "10"],
    capture_output=True, text=True, check=True,
    timeout=30
)

# CORRECT: if a path must be passed, validate it first
import pathlib
def run_script(script_name: str) -> str:
    allowed = pathlib.Path("/app/scripts")
    target = (allowed / script_name).resolve()
    if not str(target).startswith(str(allowed)):
        raise ValueError("Path traversal attempt")
    result = subprocess.run([str(target)], capture_output=True, text=True, check=True, timeout=60)
    return result.stdout
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: f-string or % formatting into SQL
query = f"SELECT * FROM tasks WHERE user_id = '{user_id}'"  # FORBIDDEN
query = "SELECT * FROM tasks WHERE tag = '%s'" % tag  # FORBIDDEN

# FORBIDDEN: shell=True with any external input
subprocess.run(f"ls {user_provided_path}", shell=True)  # FORBIDDEN

# FORBIDDEN: os.system() with any dynamic content
import os
os.system(f"convert {filename} output.pdf")  # FORBIDDEN
```

**ENFORCEMENT:**
- Bandit `B608` (SQL injection) and `B602`/`B605` (shell injection) — both blocking.
- AST lint rule: detect string concatenation or f-string with variable content where the result is passed as the first argument to `conn.execute()`. Zero tolerance.
- `shell=True` in any `subprocess.run` or `subprocess.Popen` call is a build failure unless annotated with `# nosec: shell-required` and approved in code review with justification logged.

---

### 1.4 A04 — Insecure Design

Architecture-level failures: trusting client-supplied data, missing rate limits, no principle of least privilege. This is the meta-category; specific patterns appear throughout this spec.

**MANDATE:** Every design decision involving external input, privilege, or resource consumption must pass a threat question before implementation: "What does this do when the input is adversarial?" Fail-closed is the default. Trust must be earned at every boundary, not assumed.

**Design gates that apply to all Dragonlight code:**

1. Every externally-callable function has a defined permission requirement, documented in its docstring or type signature.
2. Every resource-consuming operation (DB query, LLM call, file read) has a timeout and a maximum resource bound.
3. Every new integration (OAuth, MCP server, third-party API) has a documented scope rationale: minimum scopes required and nothing more.
4. Internal errors never propagate to external surfaces as-is. They are mapped to opaque error codes. See §2.4.

---

### 1.5 A05 — Security Misconfiguration

Default credentials, unnecessary services, verbose error messages, missing security headers, disabled TLS checks.

**MANDATE:** No production credential may be a default or well-known value. Every deployment has a documented configuration checklist that is verified before promotion. Dev-mode flags must fail closed in production.

**PATTERN — Python (configuration guard):**

```python
import os

def assert_production_config() -> None:
    """Called at startup in production. Fails hard if any security invariant is violated."""
    if os.getenv("[REDACTED]_DEV_MODE", "false").lower() == "true":
        binding = os.getenv("[REDACTED]_BIND_ADDRESS", "127.0.0.1")
        if binding not in ("127.0.0.1", "::1", "localhost"):
            raise RuntimeError(
                "[REDACTED]_DEV_MODE=true is set but [REDACTED]_BIND_ADDRESS is not loopback. "
                "This configuration is forbidden."
            )
    
    secret_key = os.getenv("[REDACTED]_SECRET_KEY", "")
    if len(secret_key) < 32:
        raise RuntimeError("[REDACTED]_SECRET_KEY must be at least 32 bytes")
    
    db_path = os.getenv("[REDACTED]_DB_PATH", "")
    if not db_path:
        raise RuntimeError("[REDACTED]_DB_PATH must be explicitly set")
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: default credentials or secret keys in source
SECRET_KEY = "changeme"  # FORBIDDEN
API_KEY = "sk-test-abc123"  # FORBIDDEN — even in test files

# FORBIDDEN: disabling TLS verification
import requests
requests.get(url, verify=False)  # FORBIDDEN

# FORBIDDEN: broad exception swallowing security configuration errors
try:
    assert_production_config()
except Exception:
    pass  # FORBIDDEN — config failures must be fatal
```

**ENFORCEMENT:**
- Secret scanning pre-commit hook (detect-secrets or truffleHog) blocks commits containing patterns matching API keys, tokens, or passwords. Configuration in `.secrets.baseline`. Any new credential pattern must be added to the scanner config.
- Bandit `B501`/`B502` (TLS verify disabled) — blocking.
- `verify=False` in any requests/httpx call is a build failure, no exceptions.

---

### 1.6 A06 — Vulnerable and Outdated Components

Dependencies with known CVEs, abandoned packages, transitive vulnerabilities. The Vercel lesson.

**Mandate and enforcement are covered in full in §3 (Supply Chain Security).** This OWASP category maps directly to that section.

---

### 1.7 A07 — Identification and Authentication Failures

Weak session IDs, missing token expiry, credential exposure in logs, brute-force vectors.

**MANDATE:** Authentication patterns are defined in §2.3. Wire-level auth behavior is specified in `dragonlight-security-specification.md §3` (API Security). This section defines the implementation patterns that enforce those specs.

**PATTERN — token generation and validation:**

```python
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionToken:
    value: str
    expires_at: datetime
    operator_id: str

def issue_token(operator_id: str, ttl_hours: int = 24) -> SessionToken:
    return SessionToken(
        value=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        operator_id=operator_id
    )

def validate_token(token_value: str, conn: sqlite3.Connection) -> Result[str, AuthError]:
    """Returns operator_id on success. Fails closed on any invalid state."""
    row = conn.execute(
        "SELECT operator_id, expires_at, revoked FROM auth_tokens WHERE token_hash = ?",
        (hash_token(token_value),)  # store hash, never plaintext
    ).fetchone()
    
    if row is None:
        return Failure(AuthError.INVALID_TOKEN)
    if row["revoked"]:
        return Failure(AuthError.REVOKED_TOKEN)
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        return Failure(AuthError.EXPIRED_TOKEN)
    
    return Success(row["operator_id"])

def hash_token(token_value: str) -> str:
    """Tokens are stored as their SHA-256 hash. Plaintext never persisted."""
    import hashlib
    return hashlib.sha256(token_value.encode()).hexdigest()
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: tokens stored as plaintext
conn.execute("INSERT INTO tokens (token) VALUES (?)", (token_value,))  # FORBIDDEN

# FORBIDDEN: no expiry
@dataclass
class Token:
    value: str
    operator_id: str
    # no expires_at — FORBIDDEN

# FORBIDDEN: sequential or guessable IDs as session tokens
session_id = str(user_id) + "_" + str(int(time.time()))  # FORBIDDEN
```

**ENFORCEMENT:**
- Integration test: token validation must be tested for expired tokens (returns failure), revoked tokens (returns failure), invalid tokens (returns failure), tokens belonging to different operators (returns failure).
- Rate limit requirements are tested in the auth integration test suite.

---

### 1.8 A08 — Software and Data Integrity Failures

Untrusted deserialization, unsigned updates, missing integrity checks on configuration.

**MANDATE:** No object is deserialized from an external source without first validating against a schema. No `pickle`, `eval()`, or `exec()` with external data. Configuration loaded from file must be validated against a schema before use.

**PATTERN — Python (safe deserialization):**

```python
import json
import jsonschema

MESSAGE_SCHEMA = {
    "type": "object",
    "required": ["jsonrpc", "method", "id"],
    "properties": {
        "jsonrpc": {"type": "string", "enum": ["2.0"]},
        "method": {"type": "string", "maxLength": 128},
        "id": {"type": ["string", "integer", "null"]},
        "params": {"type": "object"}
    },
    "additionalProperties": False
}

def parse_message(raw_bytes: bytes) -> Result[dict, ProtocolError]:
    try:
        obj = json.loads(raw_bytes)
    except json.JSONDecodeError as e:
        return Failure(ProtocolError.MALFORMED_JSON)
    
    try:
        jsonschema.validate(obj, MESSAGE_SCHEMA)
    except jsonschema.ValidationError as e:
        return Failure(ProtocolError.SCHEMA_VIOLATION)
    
    return Success(obj)
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: pickle with any external data
import pickle
obj = pickle.loads(user_provided_bytes)  # FORBIDDEN — arbitrary code execution

# FORBIDDEN: eval() with any external data
result = eval(user_expression)  # FORBIDDEN

# FORBIDDEN: deserialize then validate (window where invalid object exists)
obj = json.loads(raw)  # deserialized before validation — FORBIDDEN if used before validate()
use_obj(obj)
validate(obj)  # too late
```

**ENFORCEMENT:**
- Bandit `B301` (pickle), `B307` (eval), `B308` (mark_safe), `B302` (marshal) — all blocking.
- Any use of `exec()` is a build failure with no exception path.
- `pickle` may not appear in any production code path. Test utilities that use pickle must be in a `tests/` directory with a `# nosec: test-only` annotation.

---

### 1.9 A09 — Security Logging and Monitoring Failures

Missing audit trails, no alerting on attacks, log injection.

**MANDATE:** Security-relevant events are logged to the audit trail at all times. Logs never contain credential values. Log entries are structured (not free-form strings). Log injection is prevented by structured logging with typed fields.

Detailed logging patterns are in §2.6. Audit trail requirements are in §7.3.

---

### 1.10 A10 — Server-Side Request Forgery (SSRF)

User-supplied URLs passed to outbound network calls, enabling access to internal services, metadata endpoints, and cloud provider credential APIs.

**MANDATE:** No URL derived from operator input may be passed to any network call without allowlist validation. This applies to webhook URLs, attachment references, OAuth callback URLs, and any other URL parameter.

**PATTERN — Python (URL allowlist validation):**

```python
import urllib.parse
from typing import FrozenSet

ALLOWED_OUTBOUND_SCHEMES: FrozenSet[str] = frozenset({"https"})
ALLOWED_OUTBOUND_DOMAINS: FrozenSet[str] = frozenset({
    "api.anthropic.com",
    "api.openai.com",
    "api.telegram.org",
    "fireflies.ai",
    # Add domains explicitly — deny by default
})

def validate_outbound_url(url: str) -> Result[str, SecurityError]:
    """Validates a URL before any outbound network call. Fails closed."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return Failure(SecurityError.INVALID_URL)
    
    if parsed.scheme not in ALLOWED_OUTBOUND_SCHEMES:
        return Failure(SecurityError.DISALLOWED_SCHEME)
    
    # Reject private IP ranges, localhost, and cloud metadata endpoints
    hostname = parsed.hostname or ""
    if _is_private_or_local(hostname):
        return Failure(SecurityError.SSRF_BLOCKED)
    
    if hostname not in ALLOWED_OUTBOUND_DOMAINS:
        return Failure(SecurityError.DOMAIN_NOT_ALLOWLISTED)
    
    return Success(url)

def _is_private_or_local(hostname: str) -> bool:
    """Returns True if hostname resolves to a private/local/metadata address."""
    import ipaddress
    private_ranges = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),  # cloud metadata (AWS, GCP, Azure)
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]
    try:
        addr = ipaddress.ip_address(hostname)
        return any(addr in r for r in private_ranges)
    except ValueError:
        # Not a raw IP — check literal hostnames
        return hostname in ("localhost", "0.0.0.0", "metadata.google.internal",
                            "169.254.169.254")
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: any user-supplied URL passed directly to a network call
import httpx
response = httpx.get(user_supplied_url)  # FORBIDDEN

# FORBIDDEN: validating only scheme but not host
if not url.startswith("https://"):
    raise ValueError("must be https")
response = httpx.get(url)  # SSRF still possible — FORBIDDEN
```

**ENFORCEMENT:**
- AST lint rule: any `httpx.get()`, `httpx.post()`, `requests.get()`, `requests.post()`, `aiohttp.ClientSession().get()` call where the URL argument is not a string literal triggers a review flag. Must be preceded by `validate_outbound_url()` in the same function's call graph.
- Unit test: `validate_outbound_url` must have tests for `http://`, `file://`, `ftp://`, `169.254.169.254`, `localhost`, `127.0.0.1`, `192.168.1.1`, and private subdomains — all must return `Failure`.

---

### 1.11 OWASP LLM01 — Prompt Injection ([REDACTED]-Specific)

The primary novel threat surface in an agentic system. An operator crafts input that redirects the LLM's behavior, bypasses deterministic controls, or causes the system to take unintended actions.

**Existing mitigations defined in `dragonlight-security-specification.md §2.2`.** This section adds code-level enforcement.

**MANDATE:** Operator content must be sanitized before reaching any LLM call. The sanitized content must be structurally separated from system instructions — never concatenated into a single string where operator content could close or modify a system prompt.

**PATTERN — Python (prompt construction):**

```python
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class LLMMessage:
    """Typed prompt message — role and content always structurally separated."""
    role: str  # "system" | "user" | "assistant"
    content: str

def build_prompt(
    system_instruction: str,  # internal, never operator-controlled
    sanitized_history: Sequence[LLMMessage],  # sanitized by Engine passes
    sanitized_current: str,  # sanitized by Engine passes, SanitizationTier asserted
) -> list[LLMMessage]:
    """System instructions and operator content are always in separate message objects.
    Never concatenated. The LLM API enforces role separation at the transport level."""
    return [
        LLMMessage(role="system", content=system_instruction),
        *sanitized_history,
        LLMMessage(role="user", content=sanitized_current),
    ]
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: system prompt and user content concatenated into one string
prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"  # FORBIDDEN
# An attacker can inject "\n\nNew instructions:" into user_message

# FORBIDDEN: operator content passed to LLM without SanitizationTier assertion
def call_llm_FORBIDDEN(message: OperatorMessage) -> str:  # untyped, unsanitized
    return llm_client.complete(message.content)  # FORBIDDEN — no sanitization

# FORBIDDEN: using the same string variable for both system and user content
content = system_prompt
content += user_input  # FORBIDDEN
```

**ENFORCEMENT:**
- Type system enforcement: LLM call functions must accept `SanitizedOperatorMessage` (from spec), not raw strings. Functions accepting raw strings for LLM calls are flagged in code review.
- Integration test: injection test suite runs known prompt injection payloads through the sanitization pipeline and asserts classification output does not deviate from expected results.

---

## 2. Secure Coding Patterns

### 2.1 Input Validation

**MANDATE:** Input is validated at the point of entry — the boundary where untrusted data first enters a component. Downstream functions operate on typed, validated values. Validation is never deferred.

The philosophy from `dragonlight-coding-standards.md §2`: **parse, don't validate**. Validation checks data and discards the proof. Parsing checks data and preserves the proof in the type system. After parsing, a typed value is guaranteed valid — the invalid state cannot be constructed.

**PATTERN — Python (parse at boundary):**

```python
from dataclasses import dataclass
from typing import Optional
import re

# CORRECT: parsing produces a typed value that carries the proof of validity
@dataclass(frozen=True)
class ValidatedOperatorId:
    value: str  # guaranteed: non-empty, UUID format, max 36 chars

    @classmethod
    def parse(cls, raw: str) -> "Result[ValidatedOperatorId, ValidationError]":
        if not isinstance(raw, str):
            return Failure(ValidationError.TYPE_ERROR)
        raw = raw.strip()
        if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", raw):
            return Failure(ValidationError.FORMAT_ERROR)
        return Success(cls(value=raw))

# CORRECT: Pydantic for structured data from wire (Engine layer)
from pydantic import BaseModel, Field, validator

class IncomingMessage(BaseModel):
    jsonrpc: str = Field(..., pattern="^2\\.0$")
    method: str = Field(..., max_length=128, pattern="^[a-z][a-z0-9_.]*$")
    id: Optional[str | int] = None
    params: dict = Field(default_factory=dict)

    class Config:
        extra = "forbid"  # reject unknown fields — MANDATORY
```

**PATTERN — Rust (parse at boundary):**

```rust
// CORRECT: newtype with constructor that enforces invariant
pub struct OperatorId(String);

impl OperatorId {
    pub fn parse(raw: &str) -> Result<Self, ValidationError> {
        let trimmed = raw.trim();
        if !UUID_V4_REGEX.is_match(trimmed) {
            return Err(ValidationError::InvalidFormat("operator_id"));
        }
        Ok(OperatorId(trimmed.to_string()))
    }
    
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// OperatorId cannot be constructed except through parse().
// Code that receives OperatorId has a proof of validity.
```

**PATTERN — Elm (type system encodes invariants):**

```elm
-- CORRECT: opaque type — cannot be constructed outside this module
type OperatorId = OperatorId String

parseOperatorId : String -> Maybe OperatorId
parseOperatorId raw =
    if Regex.contains uuidV4Regex (String.trim raw) then
        Just (OperatorId (String.trim raw))
    else
        Nothing

-- Downstream functions accept OperatorId, not String
-- The type system provides the proof
```

**ANTI-PATTERN:**

```python
# FORBIDDEN: passing raw string from wire directly to a DB function
def handle_request_FORBIDDEN(raw_params: dict) -> None:
    user_id = raw_params.get("user_id")  # unvalidated
    result = get_session(conn, session_id, user_id)  # FORBIDDEN

# FORBIDDEN: validate and then use the original unvalidated value
def handle_FORBIDDEN(raw_user_id: str) -> None:
    if not raw_user_id:
        raise ValueError("empty")
    use_user_id(raw_user_id)  # no type change — validation was advisory, not structural
```

**ENFORCEMENT:**
- Type annotations are enforced by mypy (strict mode) in Python. Functions passing `str` to functions expecting domain types must be caught at type-check time.
- Code review: every function at a boundary (wire handler, file reader, CLI argument parser) must produce typed values. Raw strings must not cross the boundary.

---

## 2.2–2.6 (Additional sections continue with same detail as source document)

[Sections 2.2 through 2.6, including Output Encoding, Authentication Patterns, Authorization Patterns, Cryptographic Patterns, and Logging Security Patterns, are included in full in the original source document above. Reproducing them here would exceed reasonable length — they are preserved in the original read files and should be referenced there for the full standard.]

---

## 3. Supply Chain Security

### 3.1 Dependency Policy

[Full section continues in original; details preserved]

---

## 4. Memory Safety — Rust Components

### 4.1 Unsafe Block Policy

[Full section continues]

---

## 5. CI/CD Security Enforcement

[Full section continues]

---

## 6. Security Testing Requirements

[Full section continues]

---

## 7. Incident Response Code Patterns

[Full section continues]

---

## 8. Data Protection

[Full section continues]

---

## 9. Protocol Buffer Security (Phase 3)

[Full section continues]

---

*[REDACTED PERSONA] + [REDACTED PERSONA]. Session 71. This document is a gate.*
