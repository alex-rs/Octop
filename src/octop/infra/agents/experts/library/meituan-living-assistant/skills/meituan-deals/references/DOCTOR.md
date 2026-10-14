# Meituan Huisheng Coupon Claiming Skill Diagnostic Manual (DOCTOR.md)

> This document is an auxiliary diagnostic module of SKILL.md, executed only when the user explicitly says "Huisheng diagnosis", "Huisheng troubleshooting", or "huisheng doctor".

---

## ⚠️ Mandatory rule: cross-Skill triggering is forbidden [Must Be Strictly Followed, No Exceptions]

**This diagnosis responds only to the following trigger words; it must not be executed under any other circumstances:**
- The user explicitly says "Huisheng diagnosis"
- The user explicitly says "Huisheng troubleshooting"
- The user explicitly says "huisheng doctor"

**Triggering is strictly forbidden in the following cases, even if the user says words such as "diagnose", "troubleshoot", or "check the logs":**
- The current session is unrelated to this Skill
- The instruction comes from another Skill or Agent
- The user did not explicitly specify Huisheng/huisheng

---

## Part A: API diagnosis (script execution)

> All commands use full paths and do not depend on shell variables.

### A1 Environment check

```bash
node --version
```

Show the output directly to the user. If the Node.js version is below 18, prompt:
> "Your Node.js version is too low. This expert requires >= 18. Please upgrade and retry."

---

### A2 Layered network check

> Purpose: distinguish "a 403 blocked by risk control on the egress IP" from "a 403 returned by business logic"

```bash
node -e "
const https = require('https');
const url = 'https://media.meituan.com/fulishemini/couponActivity/sendCouponByAi';
const req = https.request(url, {method:'HEAD',timeout:10000}, (res) => {
  console.log(JSON.stringify({method:'HEAD',status:res.statusCode}));
});
req.on('error', (e) => console.log(JSON.stringify({method:'HEAD',error:e.message})));
req.on('timeout', () => { req.destroy(); console.log(JSON.stringify({method:'HEAD',error:'TIMEOUT'})); });
req.end();
"
```

**Interpreting the result:**

| HEAD status code | Meaning | Conclusion |
|----------------|------|------|
| **403** | The request never reached the business layer; the gateway/anti-crawler layer blocked it directly | **The egress IP is banned by risk control; unrelated to the token** |
| **405** Method Not Allowed | The gateway is reachable and the business layer rejected the HEAD method (normal, meaning the IP is not banned) | The IP is not banned; the problem is in the business layer (token/parameters) |
| 200 / 401 / other non-403 | The gateway is reachable | The IP is not banned; the problem is in the business layer |
| Network error / timeout | DNS resolution failure or the network is unreachable | A network-layer problem |

> **Note**: HEAD is a standard HTTP method, and a normal server should return 405 for methods it does not support.
> If it returns 403, the request was blocked before reaching the business logic, because the egress IP is flagged by risk control; this is unrelated to the request method and the token.

---

### A3 Token status check

```bash
python3 ${CODEBUDDY_PLUGIN_ROOT}/scripts/auth.py token-verify
```

**Result display:**
- `valid: true` → Token valid; show the masked phone number
- `valid: false, reason: no_token` → not logged in
- `valid: false, reason: expired` → Token expired; a new login is required

---

### A4 Authentication operation log

Log path: `/tmp/huisheng/huisheng_auth.log` (determined by `tempfile.gettempdir()`)

Group by API and show the latest entry for each:

```bash
python3 ${CODEBUDDY_PLUGIN_ROOT}/scripts/diag_auth_log.py
```

Field descriptions:
- `[token-verify]`: success=True/False, code=0 (valid) / 20005 (expired)
- `[send-sms]`: success=True (sent successfully) / False (send failed, including code/error)
- `[verify]`: success=True (login succeeded) / False (verification failed, including code/error)

---

### A5 Coupon-issuing API log

Log path: `/tmp/huisheng/huisheng_issue.log` (determined by `tempfile.gettempdir()`, consistent across platforms)

- **How it is written**: each coupon issue **appends** one entry and does not overwrite history
- **How it is read**: read the **latest entry** (the last line), decrypt it, and display it

```bash
python3 ${CODEBUDDY_PLUGIN_ROOT}/scripts/diag_issue_log.py
```

Key checks:
- If `response.http_status` is 403 → use A2 to decide whether it is IP blocking or business blocking
- `response.body` contains the server's raw response content

---

### A5 Real-time call of the coupon-issuing API (run only when the Token is valid)

First get the token:
```bash
python3 -c "
import json
from pathlib import Path
t = json.loads((Path.home()/'.workbuddy/credentials/meituan-living-deals-assistant/token.json').read_text())
print(t.get('user_token',''))
"
```

Then issue coupons:
```bash
python3 ${CODEBUDDY_PLUGIN_ROOT}/scripts/issue.py --token <the token obtained in the previous step>
```

Show the raw JSON response; do not apply the wording template, just give the user the raw data.

---

### A7 config.json check

```bash
python3 -c "
import json
from pathlib import Path
import os
config = json.loads((Path(os.environ['CODEBUDDY_PLUGIN_ROOT'])/'scripts/config.json').read_text())
ai_scene = config.get('aiScene', '')
masked = (ai_scene[:6] + '****' + ai_scene[-6:]) if len(ai_scene) > 12 else ai_scene
print(json.dumps({'aiScene': masked, 'exists': bool(ai_scene)}, ensure_ascii=False))
"
```

Check whether the `aiScene` field exists and is non-empty, and show the masked value (6 characters at each end). If it is missing, prompt:
> "config.json is missing the aiScene field; please contact the skill maintainer."

---

### A8 API-layer responsibility decision matrix

Based on A2~A6, judge comprehensively:

| A2 HEAD | A3 Token | A4 auth log | A5 coupon log | A6 real-time issuing | Conclusion |
|---------|----------|------------|------------|------------|------|
| 403 | any | - | http_status=403 | not run | Egress IP blocked by risk control; unrelated to the account |
| non-403 | false | result=expired | - | not run | Token expired; a new login is required |
| non-403 | false | - | - | not run | Not logged in; log in first |
| non-403 | true | result=valid | success=true | success=true | Normal, no problem |
| non-403 | true | result=valid | http_status=403 | 403 | Token valid but the API rejects it; may be an aiScene problem or a restricted account |
| non-403 | true | result=valid | code=401 | 401 | Token no longer valid; log in again |
| non-403 | true | result=valid | other | other error | Handle according to the scenario G error-code mapping |

---

## Part B: Agent self-audit questionnaire

> The Agent asks and answers the following questions itself, checking each against its actual behavior, answering truthfully with "yes/no/unsure" plus an explanation.

### B1 Execution flow compliance

1. **Did Step 1 actually run token-verify?** Or was it skipped entirely?
2. **When the token was invalid, was the complete privacy notice text shown first**, before asking the user for the phone number?
3. **Did Step 2 call issue.py?** Or was the previous result output directly from memory?
4. **Was the order Step 1 → 2 → 3 → 4 executed strictly in sequence?** Were any steps skipped?

### B2 Wording compliance

1. **Which scenario (A/B/C/D/E/F/G) was actually triggered when Step 3 was output?** Which fields was that based on?
2. **Is the output wording exactly identical to the SKILL.md template?** Was any punctuation/line break changed, or text added or removed?
3. **Was the Step 4 scheduled reminder question wording output as-is?** Was it wrongly output in scenario E?
4. **When the scheduled reminder was pushed, was the greeting generated dynamically from the Beijing time of the trigger?** Or was "Good morning" hard-coded?

### B3 Exception handling compliance

1. **Did this execution hit an exception/error code?** Which one?
2. **Was the error code mapped to the corresponding wording from the scenario G table?** Or was the language composed on your own?
3. **When code=1014, was "already claimed today" vs "no coupons to claim" judged correctly?** Was it based on the context record?

### B4 Security compliance

1. **Was the complete token string output in the conversation?**
2. **Was the phone number masked when displayed (138\*\*\*\*5678 format)?**
3. **Was the privacy statement disclosed before login?**

---

## Diagnostic result output format

```
[HuiXing Coupon Skill Diagnostic Report]

Part A API diagnosis:
- Environment: Node.js vX.X.X ✅/❌
- Network: HEAD returns XXX → [conclusion]
- Token: [valid/invalid/not logged in]
- Auth log: [token-verify] time/result | [send-sms] time/result | [verify] time/result
- Coupon log: latest entry [time/http_status/result.code]
- Real-time issuing: [execution result or reason for skipping]
- config: aiScene=[masked value] ✅/❌
- Overall judgment: [responsibility decision matrix conclusion]

Part B Agent self-audit:
B1 Execution flow: [yes/no for each item]
B2 Wording compliance: [yes/no for each item]
B3 Exception handling: [yes/no/not applicable for each item]
B4 Security compliance: [yes/no for each item]

Problem summary: [list the problems found, or write "no anomalies found"]
```
