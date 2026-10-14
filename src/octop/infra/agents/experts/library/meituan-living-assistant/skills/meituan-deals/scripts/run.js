#!/usr/bin/env node
/**
 * huisheng-coupon-tool unified entry script
 *
 * Unified dispatch across platforms (macOS / Windows); the AI only needs to run:
 *   node run.js <command> [options]
 *
 * Subcommands:
 *   init                          Environment setup (Python check + npm check + pt-passport install)
 *   get-device-token              Get the device identifier
 *   get-token [--env test|prod]   Get the cached user token
 *   auth-get-code [--env test|prod]  Get the authorization link
 *   auth-poll-token               Get the user authorization result
 *   qrcode <url>                  Get the QR code (server-side first, local PNG/ASCII fallback)
 *   issue                         Claim coupons
 *   hotword --city-id <id>        Hot search word query
 *   search --keyword <kw> --lat <lat> --lng <lng> --city-id <id> [--page N] [--page-size N] [--query-id Q] [--request-id R] [--max-distance-km D]
 *   location                      Get the user's recent location
 *   location-by-address --address <addr>  Get latitude/longitude from an address
 *   order --product-id <pid> --poi-id <pid> --city-id <id> --uuid <u> [--lat <lat>] [--lng <lng>] [--quantity N]
 *   logout                        Log out
 *   clear-device-token            Clear the device identifier
 *
 * All commands output JSON to stdout and error messages to stderr.
 */


const { execSync, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const https = require('https');

// ── Global constants ─────────────────────────────────────────────────
const SCRIPTS_DIR = __dirname;
const SKILL_DIR = path.dirname(SCRIPTS_DIR);
const CLIENT_ID = 'c6f50b5a1e2f4e2bb00a3e2f58df3ced';
const PT_PASSPORT_BIN = path.join(SCRIPTS_DIR, 'node_modules', '.bin', 'pt-passport');
// Auth directory: injected via the OCTOP_AUTH_DIR environment variable when Octop isolates multiple users/Agents
// (e.g. ~/.octop/agents/<id>/credentials/meituan/); falls back to the local default directory when not injected.
const AUTH_DIR = process.env.OCTOP_AUTH_DIR
    || path.join(require('os').homedir(), '.workbuddy', 'credentials', 'meituan-living-deals-assistant');

// Self-heal: after the expert template is seeded into the Agent workspace via a byte-stream copy, the npm bin executable bit is lost.
// Best-effort restore here during constant initialization (including the nested cliguard); failure does not block startup.
(function ensureBinExecBit() {
  const binPaths = [
    PT_PASSPORT_BIN,
    path.join(SCRIPTS_DIR, 'node_modules', '@mtuser', 'pt-passport', 'node_modules', '.bin', 'cliguard'),
  ];
  for (const p of binPaths) {
    try { fs.chmodSync(p, 0o755); } catch (_) { /* ignore */ }
  }
})();
const PYTHON = findPython();

// Dynamically resolve the certifi certificate path to fix macOS Python SSL certificate issues
// Empty string when certifi is not installed; Python scripts then use the system default certificate
const CERT_FILE = (() => {
  try {
    return execSync(`${PYTHON} -m certifi`, { encoding: 'utf-8', timeout: 5000, stdio: 'pipe' }).trim();
  } catch (_) { return ''; }
})();

// ── Utility functions ─────────────────────────────────────────────────

/** Check that the given Python executable exists and is Python 3 */
function isPython3(pythonPath) {
  try {
    const ver = execSync(`"${pythonPath}" --version`, { encoding: 'utf-8', timeout: 10000, stdio: 'pipe' }).trim();
    return !!ver && !ver.startsWith('Python 2.');
  } catch (_) { return false; }
}

/**
 * Python interpreter resolution priority:
 * 1. OCTOP_PYTHON environment variable (explicitly specified)
 * 2. Octop self-hosted venv (bare-metal install: $OCTOP_HOME/venv/bin/python, default ~/.octop/venv)
 * 3. Octop Docker image venv (/app/.venv/bin/python)
 * 4. Fallback: python3 / python on PATH (compatibility path for non-Octop host environments)
 */
function findPython() {
  if (process.env.OCTOP_PYTHON && isPython3(process.env.OCTOP_PYTHON)) {
    return process.env.OCTOP_PYTHON;
  }
  const octopHome = process.env.OCTOP_HOME || path.join(require('os').homedir(), '.octop');
  const venvCandidates = [
    path.join(octopHome, 'venv', 'bin', 'python'),            // macOS / Linux
    path.join(octopHome, 'venv', 'Scripts', 'python.exe'),    // Windows
    '/app/.venv/bin/python',                                   // Octop Docker image
  ];
  for (const p of venvCandidates) {
    try {
      if (fs.existsSync(p) && isPython3(p)) return p;
    } catch (_) { /* ignore */ }
  }
  for (const cmd of ['python3', 'python']) {
    try {
      const ver = execSync(`${cmd} --version`, { encoding: 'utf-8', timeout: 10000, stdio: 'pipe' }).trim();
      if (ver && !ver.startsWith('Python 2.')) return cmd;
    } catch (_) { /* ignore */ }
  }
  return 'python3';
}

function out(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function fail(error, extra) {
  out(Object.assign({ ok: false, error }, extra || {}));
  process.exit(1);
}

/** Run a Python script and return the parsed JSON */
function runPython(scriptName, args) {
  const scriptPath = path.join(SCRIPTS_DIR, scriptName);
  const cmdArgs = [scriptPath, ...args];
  try {
    try { fs.mkdirSync(AUTH_DIR, { recursive: true }); } catch (_) {}
    const sslEnv = CERT_FILE
        ? { SSL_CERT_FILE: CERT_FILE, REQUESTS_CA_BUNDLE: CERT_FILE }
        : {};
    const result = spawnSync(PYTHON, cmdArgs, {
      encoding: 'utf-8',
      timeout: 30000,
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: SCRIPTS_DIR,
      env: Object.assign({}, process.env, sslEnv, {
        WORKBUDDY_AUTH_FILE: path.join(AUTH_DIR, 'token.json'),
        NODE_OPTIONS: ''
      })
    });
    const stdout = (result.stdout || '').trim();
    if (result.status !== 0) {
      try { return JSON.parse(stdout); } catch (_) {}
      return { ok: false, error: 'SCRIPT_ERROR', message: (result.stderr || stdout || 'Unknown error').trim() };
    }
    try { return JSON.parse(stdout); } catch (_) {
      return { ok: false, error: 'PARSE_ERROR', message: 'Invalid JSON from script', raw: stdout };
    }
  } catch (e) {
    return { ok: false, error: 'EXEC_ERROR', message: e.message };
  }
}

/** Run a pt-passport CLI command and return raw stdout */
function runPassport(args) {
  try {
    const result = spawnSync(PT_PASSPORT_BIN, args, {
      encoding: 'utf-8',
      timeout: 620000,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: Object.assign({}, process.env, {
        HOME: require('os').homedir(),
        PT_PASSPORT_AUTH_FILE: path.join(AUTH_DIR, 'pt_passport_auth.json'),
        NODE_OPTIONS: ''
      }),
      shell: true
    });
    return {
      exitCode: result.status,
      stdout: (result.stdout || '').trim(),
      stderr: (result.stderr || '').trim()
    };
  } catch (e) {
    return { exitCode: 1, stdout: '', stderr: e.message };
  }
}

/**
 * Read the current user token from the pt-passport cache
 * Internal use only; not exposed as a command-line argument, to prevent token leaks
 */
function getCachedToken() {
  const res = runPassport(['get-token', '--client_id', CLIENT_ID]);
  if (res.exitCode === 0 && res.stdout) {
    return res.stdout;
  }
  return null;
}

/** Parse command-line arguments in the --key value form */
function parseArgs(argv) {
  const args = {};
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      if (i + 1 < argv.length && !argv[i + 1].startsWith('--')) {
        args[key] = argv[++i];
      } else {
        args[key] = 'true';
      }
    } else {
      positional.push(argv[i]);
    }
  }
  return { args, positional };
}



// ── Subcommand implementations ───────────────────────────────────────────────

const commands = {};

/**
 * init — environment setup
 */
commands.init = function () {
  // 1. Path validation
  if (!fs.existsSync(SCRIPTS_DIR) || !fs.statSync(SCRIPTS_DIR).isDirectory()) {
    fail('PATH_NOT_FOUND');
  }

  // 2. Python check (prefer the Octop self-hosted venv; see the findPython resolution order)
  let pyVer = '';
  try {
    pyVer = execSync(`"${PYTHON}" --version`, { encoding: 'utf-8', timeout: 10000, stdio: 'pipe' }).trim();
  } catch (_) { /* ignore */ }

  if (!pyVer) fail('PYTHON_NOT_FOUND');
  if (pyVer.startsWith('Python 2.')) fail('PYTHON_VERSION_2');

  // 3. Node.js version check
  const nodeMajor = parseInt(process.versions.node.split('.')[0], 10);
  if (nodeMajor < 18) {
    fail('NODE_VERSION_LOW', { current: String(nodeMajor), required: '>=18' });
  }

  // 4. npm check
  try {
    execSync('npm --version', { encoding: 'utf-8', timeout: 10000, stdio: 'pipe', env: Object.assign({}, process.env, { NODE_OPTIONS: '' }) });
  } catch (_) {
    fail('NPM_NOT_FOUND');
  }

  // 5. Local install/update of the pt-passport CLI
  const tgzFiles = fs.readdirSync(SCRIPTS_DIR)
      .filter(f => f.startsWith('mtuser-pt-passport-') && f.endsWith('.tgz'))
      .sort()
      .map(f => path.join(SCRIPTS_DIR, f));

  if (tgzFiles.length === 0) fail('TGZ_NOT_FOUND');

  const tgzFile = tgzFiles[tgzFiles.length - 1];
  const bundleVersion = path.basename(tgzFile).replace('mtuser-pt-passport-', '').replace('.tgz', '');

  let localVersion = '';
  try {
    const res = spawnSync(PT_PASSPORT_BIN, ['--version'], { encoding: 'utf-8', timeout: 10000, stdio: 'pipe', shell: true, env: Object.assign({}, process.env, { NODE_OPTIONS: '' }) });
    localVersion = (res.stdout || '').trim().split('\n').pop();
  } catch (_) { /* not installed */ }

  if (localVersion !== bundleVersion) {
    try {
      execSync(`npm install "${tgzFile}" --prefix "${SCRIPTS_DIR}" --save-exact --force`, { encoding: 'utf-8', timeout: 60000, stdio: 'pipe', env: Object.assign({}, process.env, { NODE_OPTIONS: '' }) });
    } catch (_) {
      fail('INSTALL_FAILED');
    }
  }

  // 6. Ensure the .auth directory exists
  try { fs.mkdirSync(AUTH_DIR, { recursive: true }); } catch (_) {}

  // 7. Detect the client type
  var clientType = (function () {
    var envType = (process.env.WORKBUDDY_CLIENT_TYPE || '').toLowerCase();
    if (envType === 'mac' || envType === 'windows' || envType === 'miniprogram') return envType;
    if (envType === 'pc') return process.platform === 'darwin' ? 'mac' : 'windows';
    if (process.platform === 'darwin') return 'mac';
    if (process.platform === 'win32') return 'windows';
    if (process.platform === 'linux') return 'miniprogram';
    return 'pc';
  })();

  out({ ok: true, scripts_dir: SCRIPTS_DIR, skill_dir: SKILL_DIR, clientType: clientType });
};

/**
 * get-client-type — detect the current runtime environment
 * Returns: mac / windows / miniprogram
 */
commands['get-client-type'] = function () {
  var envType = (process.env.WORKBUDDY_CLIENT_TYPE || '').toLowerCase();
  if (envType === 'mac' || envType === 'windows' || envType === 'miniprogram') {
    out({ ok: true, clientType: envType });
    return;
  }
  if (envType === 'pc') {
    out({ ok: true, clientType: process.platform === 'darwin' ? 'mac' : 'windows' });
    return;
  }
  // OS inference
  if (process.platform === 'darwin') {
    out({ ok: true, clientType: 'mac' });
  } else if (process.platform === 'win32') {
    out({ ok: true, clientType: 'windows' });
  } else if (process.platform === 'linux') {
    out({ ok: true, clientType: 'miniprogram' });
  } else {
    out({ ok: true, clientType: 'pc' });
  }
};

/**
 * get-device-token — get the device identifier
 */
commands['get-device-token'] = function () {
  const result = runPython('auth.py', ['get-device-token']);
  if (result.success && result.device_token) {
    out({ ok: true, device_token: result.device_token });
  } else if (result.device_token) {
    out({ ok: true, device_token: result.device_token });
  } else {
    fail('DEVICE_TOKEN_FAILED', { detail: result });
  }
};

/**
 * get-token — get the cached user token
 */
commands['get-token'] = function (argv) {
  const { args } = parseArgs(argv || []);
  const passportArgs = ['get-token', '--client_id', CLIENT_ID];
  if (args['env'] === 'test') {
    passportArgs.push('--env', 'test');
  }
  const res = runPassport(passportArgs);
  if (res.exitCode === 0 && res.stdout) {
    out({ ok: true, token: res.stdout });
  } else {
    out({ ok: false, error: 'NO_TOKEN', message: 'Token not found or expired' });
  }
};

/**
 * auth-get-code — get the authorization link
 */
commands['auth-get-code'] = function (argv) {
  const { args } = parseArgs(argv || []);
  const passportArgs = ['auth', 'get-code', '--client_id', CLIENT_ID];
  if (args['env'] === 'test') {
    passportArgs.push('--env', 'test');
  }
  const res = runPassport(passportArgs);
  const stdout = res.stdout;

  // Token: <token> — cache hit
  const tokenMatch = stdout.match(/Token:\s*(.+)/);
  if (tokenMatch) {
    out({ ok: true, type: 'token', token: tokenMatch[1].trim() });
    return;
  }

  // AUTH_LINK: <url>
  const linkMatch = stdout.match(/AUTH_LINK:\s*(.+)/);
  if (linkMatch) {
    out({ ok: true, type: 'auth_link', url: linkMatch[1].trim() });
    return;
  }

  // ❌ error
  const errorMatch = stdout.match(/❌\s*code=(\d+)\s*message=(.*)/);
  if (errorMatch) {
    out({ ok: false, error: 'AUTH_ERROR', code: errorMatch[1], message: errorMatch[2].trim() });
    return;
  }

  out({ ok: false, error: 'UNKNOWN', raw: stdout, stderr: res.stderr });
};

/**
 * auth-poll-token — get the user authorization result
 * Note: poll-token reads the environment info from the session file generated by get-code, so --env is not needed.
 *
 * Fallback logic: if poll-token fails, automatically call auth get-code to double-check,
 * because a backend race condition exists (the user already scanned successfully but the poll session was already closed).
 */
commands['auth-poll-token'] = function () {
  const res = runPassport(['auth', 'poll-token', '--client_id', CLIENT_ID]);
  const stdout = res.stdout;

  // Normal success
  const tokenMatch = stdout.match(/Token:\s*(.+)/);
  if (res.exitCode === 0 && tokenMatch) {
    out({ ok: true, token: tokenMatch[1].trim() });
    return;
  }

  // poll failed; run the fallback: call auth get-code to check whether a token already exists
  const fallbackRes = runPassport(['auth', 'get-code', '--client_id', CLIENT_ID]);
  const fallbackStdout = fallbackRes.stdout;

  // Fallback cache hit: the user already scanned successfully
  const fallbackTokenMatch = fallbackStdout.match(/Token:\s*(.+)/);
  if (fallbackTokenMatch) {
    out({ ok: true, token: fallbackTokenMatch[1].trim() });
    return;
  }

  // Fallback cache miss: confirm that login really failed
  out({ ok: false, error: 'POLL_FAILED', message: 'Login failed; please log in again' });
};

// ── CLIGuard signature integration ─────────────────────────────────────────

function loadCliguard() {
  const vendorPath = path.join(SCRIPTS_DIR, 'vendor', 'cliguard', 'js', 'cliguard.js');
  const updatePath = path.join(
      require('os').homedir(), '.cliguard', 'cliguard-updates', 'core', 'cliguard.js'
  );
  if (fs.existsSync(vendorPath)) return require(vendorPath);
  if (fs.existsSync(updatePath)) return require(updatePath);
  return null;
}

function addCommonParams(urlStr) {
  try {
    const cliguard = loadCliguard();
    if (!cliguard || typeof cliguard.addCommonParams !== 'function') return urlStr;
    const result = cliguard.addCommonParams(urlStr);
    return (result && result.url) ? result.url : urlStr;
  } catch (e) {
    process.stderr.write('[run.js:addCommonParams] warning: ' + e.message + '\n');
    return urlStr;
  }
}

function makeSignHeaders(method, urlStr, bodyHash) {
  try {
    const cliguard = loadCliguard();
    if (!cliguard || typeof cliguard.signRequest !== 'function') return {};
    return cliguard.signRequest(method.toUpperCase(), urlStr, bodyHash || '') || {};
  } catch (e) {
    process.stderr.write('[run.js:makeSignHeaders] warning: ' + e.message + '\n');
    return {};
  }
}

function httpsPost(urlStr, bodyObj, extraHeaders) {
  return new Promise(function (resolve, reject) {
    const bodyStr = JSON.stringify(bodyObj);
    const bodyBuf = Buffer.from(bodyStr, 'utf-8');
    const hashSlice = bodyBuf.slice(0, 16200);
    const bodyHash = crypto.createHash('md5').update(hashSlice).digest('hex');
    const signedUrl = addCommonParams(urlStr);
    const sigHeaders = makeSignHeaders('POST', signedUrl, bodyHash);
    const parsed = new URL(signedUrl);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || 443,
      path: parsed.pathname + parsed.search,
      method: 'POST',
      headers: Object.assign({
        'Content-Type': 'application/json',
        'Content-Length': bodyBuf.length,
        'X-Requested-With': 'XMLHttpRequest'
      }, sigHeaders, extraHeaders || {})
    };
    const req = https.request(options, function (res) {
      const chunks = [];
      res.on('data', function (chunk) { chunks.push(chunk); });
      res.on('end', function () {
        const body = Buffer.concat(chunks).toString('utf-8');
        try { resolve({ status: res.statusCode, data: JSON.parse(body) }); }
        catch (_) { resolve({ status: res.statusCode, data: null, raw: body }); }
      });
    });
    req.on('error', function (e) { reject(e); });
    req.setTimeout(15000, function () { req.destroy(); reject(new Error('TIMEOUT')); });
    req.write(bodyBuf);
    req.end();
  });
}

function httpsGet(urlStr, extraHeaders) {
  return new Promise(function (resolve, reject) {
    const signedUrl = addCommonParams(urlStr);
    const sigHeaders = makeSignHeaders('GET', signedUrl, '');
    const parsed = new URL(signedUrl);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || 443,
      path: parsed.pathname + parsed.search,
      method: 'GET',
      headers: Object.assign({
        'X-Requested-With': 'XMLHttpRequest'
      }, sigHeaders, extraHeaders || {})
    };
    const req = https.request(options, function (res) {
      const chunks = [];
      res.on('data', function (chunk) { chunks.push(chunk); });
      res.on('end', function () {
        const body = Buffer.concat(chunks).toString('utf-8');
        try { resolve({ status: res.statusCode, data: JSON.parse(body) }); }
        catch (_) { resolve({ status: res.statusCode, data: null, raw: body }); }
      });
    });
    req.on('error', function (e) { reject(e); });
    req.setTimeout(15000, function () { req.destroy(); reject(new Error('TIMEOUT')); });
    req.end();
  });
}

/**
 * qrcode — get the login QR code, three-tier strategy:
 *   1. The Meituan server-side API generates an image URL (preferred; click statistics count)
 *   2. The local qrcode library generates a PNG data URI (fallback when the server fails)
 *   3. Locally generated ASCII art (final fallback when the qrcode library is missing)
 * Usage: node run.js qrcode <url>
 */
function qrcodeLocalFallback(url) {
  // Try the PNG data URI first; degrade to ASCII art when the library is missing
  const pngRes = runPython('qr_local.py', [url]);
  if (pngRes.ok) return pngRes;
  if (pngRes.error === 'QRCODE_LIB_MISSING') {
    const asciiRes = runPython('qr_local.py', [url, '--ascii']);
    if (asciiRes.ok) return asciiRes;
    // The qrcode library is missing so even ASCII failed → install it on the spot and retry once
    try {
      execSync(`"${PYTHON}" -m pip install --quiet qrcode pillow`, { encoding: 'utf-8', timeout: 60000, stdio: 'pipe' });
      return runPython('qr_local.py', [url]);
    } catch (_) {
      return pngRes;
    }
  }
  return pngRes;
}

commands.qrcode = function (argv) {
  const url = (argv || [])[0] || '';

  if (!url) {
    out({ ok: false, type: 'skip' });
    return;
  }

  // Payment links are not allowed to generate a QR code; skip directly
  if (url.indexOf('npay.meituan.com') !== -1) {
    out({ ok: false, type: 'skip', message: 'Payment URL is not allowed to generate QR code' });
    return;
  }

  const apiUrl = 'https://click.meituan.com/cps/ai/product/getQrCodeImage';
  const body = { originalUrl: url, clientSource: 'coupon-fusion-workbuddy' };

  httpsPost(apiUrl, body)
      .then(function (resp) {
        const data = resp.data;
        if (data && data.data) {
          out({ ok: true, type: 'image', imageUrl: data.data });
        } else {
          // Server returned no image → local fallback
          const local = qrcodeLocalFallback(url);
          if (local.ok) {
            out(Object.assign({ source: 'local' }, local));
          } else {
            out({ ok: false, type: 'skip', message: 'No image returned', raw: data });
          }
        }
      })
      .catch(function (e) {
        // Server request failed (network/timeout) → local fallback
        const local = qrcodeLocalFallback(url);
        if (local.ok) {
          out(Object.assign({ source: 'local' }, local));
        } else {
          out({ ok: false, type: 'skip', message: e.message });
        }
      });
};

/**
 * issue — claim coupons (pure Node.js implementation)
 * Usage: node run.js issue
 *
 * The token is read automatically from the pt-passport cache; it is never passed on the command line.
 *
 * Return format (success):
 *   { ok: true, success: true, coupon_count: N, coupons: [...], count_str: "...", display_coupons: [...] }
 * Return format (failure):
 *   { ok: false, success: false, error: "<ERROR_TYPE>", message: "..." }
 */
commands.issue = function (argv) {
  const { args } = parseArgs(argv || []);
  const token = getCachedToken();
  if (!token) fail('NO_TOKEN', { message: 'Not logged in or token expired; please log in first' });

  const COUPON_BASE_URL = 'https://media.meituan.com';
  const COUPON_ISSUE_PATH = '/fulishemini/couponActivity/sendCouponWork';
  const CONFIG_FILE = path.join(SCRIPTS_DIR, 'config.json');
  const os = require('os');
  const LOG_DIR = path.join(os.tmpdir(), 'huisheng');
  const LOG_FILE = path.join(LOG_DIR, 'huisheng_issue.log');

  // Check today's coupon cache; on a hit return 1014 + cached=true + coupon data to avoid calling the issuance API again
  var todayCache = loadTodayCouponCache();
  if (todayCache) {
    out({
      ok: false, success: false, code: 1014, cached: true,
      message: 'You have already claimed Meituan coupons today',
      coupon_count: todayCache.coupon_count || 0,
      coupons: todayCache.coupons || [],
      count_str: todayCache.count_str || '',
      display_coupons: todayCache.display_coupons || [],
      activity_name: todayCache.activity_name || '',
      activity_link: todayCache.activity_link || ''
    });
    return;
  }

  // ── Utility functions ──────────────────────────────────────────────
  function loadConfig() {
    try { return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8')); } catch (_) { return {}; }
  }

  // ── Today's coupon cache (only today's result is kept; invalidated automatically across days) ─────────
  function getLocalDateStr() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
  }

  function loadTodayCouponCache() {
    try {
      const cacheFile = path.join(AUTH_DIR, 'today_coupons_cache.json');
      if (!fs.existsSync(cacheFile)) return null;
      const content = fs.readFileSync(cacheFile, 'utf-8');
      const cache = JSON.parse(content);
      const today = getLocalDateStr();
      if (cache && cache.date === today) return cache.data;
      return null;
    } catch (_) { return null; }
  }

  function saveTodayCouponCache(data) {
    try {
      const cacheFile = path.join(AUTH_DIR, 'today_coupons_cache.json');
      try { fs.mkdirSync(AUTH_DIR, { recursive: true }); } catch (_) {}
      const today = getLocalDateStr();
      const cache = { date: today, data: data };
      fs.writeFileSync(cacheFile, JSON.stringify(cache), 'utf-8');
    } catch (_) {}
  }

  function getDeviceToken() {
    try {
      const tokenFile = path.join(AUTH_DIR, 'token.json');
      return JSON.parse(fs.readFileSync(tokenFile, 'utf-8')).device_token || '';
    } catch (_) { return ''; }
  }

  function xorEncrypt(data, aiScene) {
    const deviceToken = getDeviceToken();
    var seed, flag;
    if (deviceToken) { seed = deviceToken + aiScene; flag = '1'; }
    else { seed = aiScene; flag = '0'; }
    const keyBytes = crypto.createHash('sha256').update(seed).digest();
    const dataBytes = Buffer.from(data, 'utf-8');
    const result = Buffer.alloc(dataBytes.length);
    for (var i = 0; i < dataBytes.length; i++) {
      result[i] = dataBytes[i] ^ keyBytes[i % 32];
    }
    return flag + ':' + result.toString('hex');
  }

  function writeLog(entry, aiScene) {
    try {
      try { fs.mkdirSync(LOG_DIR, { recursive: true }); } catch (_) {}
      var raw = JSON.stringify(entry);
      var line = aiScene ? xorEncrypt(raw, aiScene) : raw;
      fs.appendFileSync(LOG_FILE, line + '\n', 'utf-8');
    } catch (_) {}
  }

  function fenToYuan(fen) {
    if (!fen) return '0';
    var yuan = parseInt(fen, 10) / 100;
    return yuan === Math.floor(yuan) ? String(Math.floor(yuan)) : yuan.toFixed(1);
  }

  function formatTimestampMs(tsMs) {
    if (!tsMs) return '-';
    try {
      var d = new Date(parseInt(tsMs, 10));
      var year = d.getFullYear();
      var month = String(d.getMonth() + 1).padStart(2, '0');
      var day = String(d.getDate()).padStart(2, '0');
      return year + '-' + month + '-' + day;
    } catch (_) { return String(tsMs); }
  }

  function formatCoupon(c) {
    var priceLimit = c.priceLimit;
    var couponValue = c.couponValue || 0;
    var discountInfo = '';
    if (priceLimit && priceLimit > 0) {
      discountInfo = 'Spend ¥' + fenToYuan(priceLimit) + ', get ¥' + fenToYuan(couponValue) + ' off';
    }
    var start = c.couponStartTime;
    var end = c.couponEndTime;
    var validPeriod = '';
    if (start && end) {
      validPeriod = formatTimestampMs(start) + ' to ' + formatTimestampMs(end);
    }
    return {
      name: c.couponName || '',
      discount_info: discountInfo,
      valid_period: validPeriod,
      priceLimit: priceLimit,
      couponValue: couponValue,
      tabName: c.tabName || ''
    };
  }

  // ── Display result construction ──────────────────────────────────────────
  var _TAB_ORDER = ['外卖', '美食团购', '美团闪购', '休闲娱乐', '生活服务', '丽人医疗', '更多福利'];
  var _TAB_DISPLAY = { '更多福利': 'Other' };
  var _SLOT_PLAN_BASE = [['外卖', 2], ['美食团购', 1], ['美团闪购', 1],
                         ['休闲娱乐', 1], ['生活服务', 1], ['丽人医疗', 1]];

  function buildCountStr(coupons) {
    var tabCount = {};
    for (var i = 0; i < coupons.length; i++) {
      var tab = coupons[i].tabName || '';
      tabCount[tab] = (tabCount[tab] || 0) + 1;
    }
    var unknownTabs = Object.keys(tabCount).filter(function (t) { return _TAB_ORDER.indexOf(t) < 0; });
    var finalOrder = _TAB_ORDER.slice(0, 6).concat(unknownTabs, _TAB_ORDER.slice(6));
    var parts = [];
    for (var j = 0; j < finalOrder.length; j++) {
      var t = finalOrder[j];
      if (!tabCount[t]) continue;
      var displayName = _TAB_DISPLAY[t] || t;
      parts.push(displayName + ' coupons: ' + tabCount[t]);
    }
    return parts.join(', ');
  }

  function buildDisplayCoupons(coupons) {
    function sortKey(c) {
      var pl = c.priceLimit;
      if (!pl) return [0, 0];
      return [1, -(c.couponValue / pl)];
    }
    function compareFn(a, b) {
      var ka = sortKey(a), kb = sortKey(b);
      return ka[0] - kb[0] || ka[1] - kb[1];
    }
    var groups = {};
    for (var i = 0; i < coupons.length; i++) {
      var tab = coupons[i].tabName || '';
      if (!groups[tab]) groups[tab] = [];
      groups[tab].push(coupons[i]);
    }
    for (var t in groups) { groups[t].sort(compareFn); }

    var unknownTabs = Object.keys(groups).filter(function (t) { return _TAB_ORDER.indexOf(t) < 0; });
    var slotPlan = _SLOT_PLAN_BASE.concat(unknownTabs.map(function (t) { return [t, 1]; }), [['更多福利', 1]]);

    var used = {};
    var slots = [];

    for (var s = 0; s < slotPlan.length; s++) {
      if (slots.length >= 8) break;
      var slotTab = slotPlan[s][0], quota = slotPlan[s][1];
      var taken = 0;
      var grp = groups[slotTab] || [];
      for (var g = 0; g < grp.length; g++) {
        if (taken >= quota || slots.length >= 8) break;
        slots.push(grp[g]);
        used[slotTab] = (used[slotTab] || 0) + 1;
        taken++;
      }
    }

    var fallbackOrder = ['外卖', '美食团购', '美团闪购', '休闲娱乐', '生活服务', '丽人医疗']
        .concat(unknownTabs, ['更多福利']);
    while (slots.length < 8) {
      var filled = false;
      for (var f = 0; f < fallbackOrder.length; f++) {
        var remaining = (groups[fallbackOrder[f]] || []).slice(used[fallbackOrder[f]] || 0);
        if (remaining.length > 0) {
          slots.push(remaining[0]);
          used[fallbackOrder[f]] = (used[fallbackOrder[f]] || 0) + 1;
          filled = true;
          break;
        }
      }
      if (!filled) break;
    }
    return slots;
  }

  function buildDisplayResult(coupons) {
    return { count_str: buildCountStr(coupons), display_coupons: buildDisplayCoupons(coupons) };
  }

  // ── Send the request ──────────────────────────────────────────────
  var config = loadConfig();
  var aiScene = config.aiScene || '';

  var bodyObj = {
    token: token,
    aiScene: aiScene,
    version: 2
  };

  var logEntry = {
    time: new Date().toISOString().replace('T', ' ').slice(0, 19),
    request: {
      url: COUPON_BASE_URL + COUPON_ISSUE_PATH,
      aiScene: aiScene,
      token_masked: token.length > 8 ? token.slice(0, 8) + '****' : token
    }
  };

  httpsPost(COUPON_BASE_URL + COUPON_ISSUE_PATH, bodyObj)
    .then(function (resp) {
      logEntry.response = { http_status: resp.status, body: JSON.stringify(resp.data).slice(0, 500) };

      var respData = resp.data;
      if (!respData) {
        logEntry.result = { success: false, error: 'PARSE_ERROR' };
        writeLog(logEntry, aiScene);
        out({ ok: false, success: false, error: 'PARSE_ERROR', message: 'Invalid response from server' });
        return;
      }

      var code = respData.code;
      var msg = respData.msg || '';
      var data = respData.data || {};

      if (code === 200) {
        var couponList = data.couponList || [];
        var formattedCoupons = couponList.map(formatCoupon);
        var display = buildDisplayResult(formattedCoupons);
        var result = {
          ok: true, success: true, code: 200,
          coupon_count: formattedCoupons.length,
          coupons: formattedCoupons,
          count_str: display.count_str,
          display_coupons: display.display_coupons,
          activity_name: data.activityName || '',
          activity_link: data.activityLink || ''
        };
        saveTodayCouponCache(result);
        logEntry.result = { success: true, code: 200, coupon_count: formattedCoupons.length };
        writeLog(logEntry, aiScene);
        out(result);
      } else if (code === 1014) {
        logEntry.result = { success: false, code: 1014, error: 'ALREADY_RECEIVED' };
        writeLog(logEntry, aiScene);
        out({
          ok: false, success: false, code: 1014,
          error: 'ALREADY_RECEIVED',
          message: 'You have already claimed today; you can only claim once per day, so come back tomorrow~',
          activity_name: data.activityName || '',
          activity_link: data.activityLink || ''
        });
      } else if (code === 401) {
        // Proactively clear the local pt-passport cache so auth-get-code cannot hit a stale token and loop forever
        try { runPassport(['logout', '--client_id', CLIENT_ID]); } catch (_) {}

        logEntry.result = { success: false, code: 401, error: 'RE_LOGIN' };
        writeLog(logEntry, aiScene);
        out({ ok: false, success: false, code: 401, error: 'RE_LOGIN', message: 'Login expired; please log in again' });
      } else if (code === 509 || code === 50200) {
        logEntry.result = { success: false, code: code, error: 'RATE_LIMIT' };
        writeLog(logEntry, aiScene);
        out({ ok: false, success: false, code: code, error: 'RATE_LIMIT', message: 'Too many requests; please try again later' });
      } else if (code === 9999) {
        logEntry.result = { success: false, code: 9999, error: 'SYSTEM_ERROR' };
        writeLog(logEntry, aiScene);
        out({ ok: false, success: false, code: 9999, error: 'SYSTEM_ERROR', message: 'System error; please try again later' });
      } else {
        logEntry.result = { success: false, code: code, error: 'UNKNOWN_ERROR' };
        writeLog(logEntry, aiScene);
        out({ ok: false, success: false, code: code, error: 'UNKNOWN_ERROR', message: 'Unknown error (code=' + code + ', msg=' + msg + ')' });
      }
    })
    .catch(function (e) {
      logEntry.response = { error: e.message === 'TIMEOUT' ? 'TIMEOUT' : 'NETWORK_ERROR', detail: e.message };
      writeLog(logEntry, aiScene);
      if (e.message === 'TIMEOUT') {
        out({ ok: false, success: false, error: 'TIMEOUT', message: 'Request timed out; please try again later' });
      } else {
        out({ ok: false, success: false, error: 'NETWORK_ERROR', message: 'Network error: ' + e.message });
      }
    });
};

/**
 * hotword — hot search word query
 * Usage: node run.js hotword --city-id <id>
 */
commands.hotword = function (argv) {
  const { args } = parseArgs(argv || []);
  if (!args['city-id']) fail('MISSING_PARAM', { param: 'city-id' });

  const apiUrl = 'https://peppermall.meituan.com/api/product/search/consumer/hotword?selectCityId=' + encodeURIComponent(args['city-id']);
  httpsGet(apiUrl)
    .then(function (resp) {
      const data = resp.data;
      if (data && data.code === 200) {
        const hotWords = (data.data && data.data.hotWord || []).map(function (item) { return item.word; });
        out({ ok: true, success: true, hotWords: hotWords });
      } else {
        out({ ok: false, success: false, error: 'API_ERROR', code: data && data.code, message: (data && data.message) || 'Failed to fetch hot search words' });
      }
    })
    .catch(function (e) {
      out({ ok: false, success: false, error: e.message });
    });
};

/**
 * search — product search
 * Usage: node run.js search --keyword <kw> --lat <lat> --lng <lng> --city-id <id>
 *        [--page N] [--page-size N] [--query-id Q] [--request-id R] [--max-distance-km D]
 *
 * The token is read automatically from the pt-passport cache; it is never passed on the command line.
 * Requests are sent directly with Node.js https to avoid Windows Python SSL compatibility issues.
 */
commands.search = function (argv) {
  const { args } = parseArgs(argv || []);
  const required = ['keyword', 'lat', 'lng', 'city-id'];
  for (const r of required) {
    if (!args[r]) fail('MISSING_PARAM', { param: r });
  }
  const token = getCachedToken();
  if (!token) fail('NO_TOKEN', { message: 'Not logged in or token expired; please log in first' });

  const page = parseInt(args['page'] || '1', 10);
  const pageSize = parseInt(args['page-size'] || '10', 10);
  const maxDistanceKm = parseFloat(args['max-distance-km'] || '8');

  const body = {
    keyword: args['keyword'],
    page: page,
    pageSize: String(pageSize),
    clientSource: 'coupon-fusion-workbuddy',
    userParamDTO: {
      lat: args['lat'],
      lng: args['lng'],
      token: token,
      cityId: args['city-id'],
      app: 216,
      platform: 1,
      partner: 1018
    }
  };
  if (args['query-id']) body.queryId = args['query-id'];
  if (args['request-id']) body.requestId = args['request-id'];

  const apiUrl = 'https://click.meituan.com/cps/ai/product/searchProductByAgent';
  httpsPost(apiUrl, body, { token: token })
    .then(function (resp) {
      const data = resp.data;
      if (data && data.code === 200 && data.success) {
        const dataBlock = data.data || {};
        var productList = (dataBlock.productList || []).map(function (item) {
          if (item.productId) item.productId = String(item.productId);
          if (item.poiId) item.poiId = String(item.poiId);
          return item;
        });
        // Filter by distance
        productList = productList.filter(function (item) {
          var dt = (item.distanceText || '').trim().toLowerCase();
          var km = 999;
          if (dt.endsWith('km')) km = parseFloat(dt.slice(0, -2));
          else if (dt.endsWith('m')) km = parseFloat(dt.slice(0, -1)) / 1000;
          return km <= maxDistanceKm;
        });
        // Renumber
        productList.forEach(function (item, idx) { item.index = idx + 1; });
        out({
          ok: true, success: true,
          productList: productList,
          isLastPage: !!dataBlock.isLastPage,
          queryId: String(dataBlock.queryId || ''),
          requestId: String(dataBlock.requestId || ''),
          page: page,
          pageSize: pageSize
        });
      } else {
        out({ ok: false, success: false, error: 'API_ERROR', code: data && data.code, message: (data && data.message) || 'Search failed' });
      }
    })
    .catch(function (e) {
      out({ ok: false, success: false, error: e.message });
    });
};

/**
 * location — get the user's recent location
 * Usage: node run.js location
 *
 * The token is read automatically from the pt-passport cache; it is never passed on the command line.
 * Requests are sent directly with Node.js https to avoid Windows Python SSL compatibility issues.
 */
commands.location = function (argv) {
  const token = getCachedToken();
  if (!token) fail('NO_TOKEN', { message: 'Not logged in or token expired; please log in first' });

  const apiUrl = 'https://click.meituan.com/cps/ai/product/getUserRecentLocation';
  httpsPost(apiUrl, { token: token }, { token: token })
    .then(function (resp) {
      const data = resp.data;
      if (data && data.code === 200 && data.success) {
        const loc = data.data || {};
        out({
          ok: true,
          success: true,
          cityId: loc.cityId,
          cityName: loc.cityName,
          lng: loc.lng,
          lat: loc.lat,
          formattedAddress: loc.formattedAddress
        });
      } else {
        out({
          ok: false,
          success: false,
          error: (data && data.message) || 'Unknown error',
          code: data && data.code
        });
      }
    })
    .catch(function (e) {
      out({ ok: false, success: false, error: e.message });
    });
};

/**
 * location-by-address — get latitude/longitude from an address
 * Usage: node run.js location-by-address --address <addr>
 * Requests are sent directly with Node.js https to avoid Windows Python SSL compatibility issues.
 */
commands['location-by-address'] = function (argv) {
  const { args } = parseArgs(argv || []);
  if (!args['address']) fail('MISSING_PARAM', { param: 'address' });

  const apiUrl = 'https://click.meituan.com/cps/ai/product/getLocationByAddress';
  httpsPost(apiUrl, { address: args['address'] })
    .then(function (resp) {
      const data = resp.data;
      if (data && data.code === 200 && data.success) {
        const loc = data.data || {};
        out({ ok: true, success: true, cityId: loc.cityId, lng: loc.lng, lat: loc.lat });
      } else {
        out({ ok: false, success: false, error: (data && data.message) || 'Unknown error', code: data && data.code });
      }
    })
    .catch(function (e) {
      out({ ok: false, success: false, error: e.message });
    });
};

/**
 * order — place an order
 * Usage: node run.js order --product-id <pid> --poi-id <pid> --city-id <id> --uuid <u>
 *        [--lat <lat>] [--lng <lng>] [--quantity N]
 *
 * The token is read automatically from the pt-passport cache; it is never passed on the command line.
 * clientType is determined internally.
 * Requests are sent directly with Node.js https to avoid Windows Python SSL compatibility issues.
 */
commands.order = function (argv) {
  const { args } = parseArgs(argv || []);
  const required = ['product-id', 'poi-id', 'city-id', 'uuid'];
  for (const r of required) {
    if (!args[r]) fail('MISSING_PARAM', { param: r });
  }
  const token = getCachedToken();
  if (!token) fail('NO_TOKEN', { message: 'Not logged in or token expired; please log in first' });

  // Determine the client type internally
  var clientType = (function () {
    var envType = (process.env.WORKBUDDY_CLIENT_TYPE || '').toLowerCase();
    if (envType === 'mac' || envType === 'windows' || envType === 'miniprogram') return envType;
    if (envType === 'pc') return process.platform === 'darwin' ? 'mac' : 'windows';
    if (process.platform === 'darwin') return 'mac';
    if (process.platform === 'win32') return 'windows';
    if (process.platform === 'linux') return 'miniprogram';
    return 'pc';
  })();

  // Detect whether the weixinpay plugin supports the x402 protocol
  var useWxAIPay = false;
  try {
    var detectResult = spawnSync(PYTHON, [
      path.join(SCRIPTS_DIR, 'plugin_version_lite.py'), '--x402'
    ], {
      encoding: 'utf-8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: SCRIPTS_DIR,
      env: Object.assign({}, process.env, { NODE_OPTIONS: '' })
    });
    if (detectResult.status === 0) {
      useWxAIPay = (detectResult.stdout || '').trim() === 'true';
    }
  } catch (_) { /* on detection failure keep false and use native payment */ }

  const body = {
    productId: String(args['product-id']),
    poiId: String(args['poi-id']),
    quantity: parseInt(args['quantity'] || '1', 10),
    clientSource: 'coupon-fusion-workbuddy',
    clientType: clientType,
    useWxAIPay: useWxAIPay,
    userParamDTO: {
      token: token,
      cityId: args['city-id'],
      uuid: args['uuid'],
      lat: args['lat'] || '',
      lng: args['lng'] || '',
      app: 216,
      platform: 1,
      partner: 1018
    }
  };

  const apiUrl = 'https://click.meituan.com/cps/ai/product/orderByAgent';
  httpsPost(apiUrl, body, { token: token })
    .then(function (resp) {
      const data = resp.data;
      if (data && data.code === 200 && data.success) {
        const dataBlock = data.data || {};
        out({
          ok: true, success: true,
          orderId: String(dataBlock.orderId || ''),
          payShortLink: dataBlock.payShortLink || '',
          payQrCodeImage: dataBlock.payUrlQrCode || '',
          'WeixinPay-Required': dataBlock.wxPaymentCode || '',
          useWxAIPay: useWxAIPay
        });
      } else {
        out({ ok: false, success: false, error: 'API_ERROR', code: data && data.code, message: (data && data.message) || 'Order failed' });
      }
    })
    .catch(function (e) {
      out({ ok: false, success: false, error: e.message });
    });
};

/**
 * check-wx-ai-pay — detect whether the weixinpay plugin supports the x402 protocol
 * Usage: node run.js check-wx-ai-pay
 * Returns: { ok: true, useWxAIPay: true/false, version: "x.y.z" }
 */
commands['check-wx-ai-pay'] = function () {
  try {
    var detectResult = spawnSync(PYTHON, [
      path.join(SCRIPTS_DIR, 'plugin_version_lite.py'), '--json'
    ], {
      encoding: 'utf-8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: SCRIPTS_DIR,
      env: Object.assign({}, process.env, { NODE_OPTIONS: '' })
    });
    if (detectResult.status === 0) {
      var info = JSON.parse((detectResult.stdout || '').trim());
      out({
        ok: true,
        useWxAIPay: !!info.weixinpay_support_x402,
        version: info.version || '0',
        installed: !!info.weixinpay_installed,
        platform: info.platform || ''
      });
    } else {
      out({ ok: true, useWxAIPay: false, version: '0', installed: false, platform: '' });
    }
  } catch (_) {
    out({ ok: true, useWxAIPay: false, version: '0', installed: false, platform: '' });
  }
};

/**
 * check-login — check the Meituan WeChat mini-program login status
 * Usage: node run.js check-login
 *
 * The token is read automatically from the pt-passport cache; it is never passed on the command line.
 * Requests are sent directly with Node.js https to avoid Windows Python SSL compatibility issues.
 */
commands['check-login'] = function () {
  const token = getCachedToken();
  if (!token) fail('NO_TOKEN', { message: 'Not logged in or token expired; please log in first' });

  const apiUrl = 'https://click.meituan.com/cps/ai/product/checkLoginMtMiniProgram';
  const body = {
    clientSource: 'coupon-fusion-workbuddy',
    userParamDTO: { token: token }
  };
  httpsPost(apiUrl, body)
    .then(function (resp) {
      const data = resp.data;
      if (data && data.code === 200 && data.success) {
        out({ ok: true, success: true, logged: !!data.data });
      } else {
        out({ ok: false, success: false, error: 'API_ERROR', code: data && data.code, message: (data && data.message) || 'Verification failed' });
      }
    })
    .catch(function (e) {
      out({ ok: false, success: false, error: e.message });
    });
};

/**
* logout — log out
* Clear the pt-passport CLI cache directly through runPassport (avoids PATH issues where Python cannot find pt-passport)
*/
commands.logout = function () {
var cli_cleared = false;
try {
  var res = runPassport(['logout', '--client_id', CLIENT_ID]);
  cli_cleared = true;
} catch (e) {
  cli_cleared = false;
}
out({ ok: true, success: true, message: 'Logged out; you will need to authorize again next time', device_token_preserved: true, cli_cache_cleared: cli_cleared });
};

/**
* clear-device-token — clear the device identifier
* Clear device_token and the pt-passport CLI cache
*/
commands['clear-device-token'] = function () {
// First clear the pt-passport CLI cache
try { runPassport(['logout', '--client_id', CLIENT_ID]); } catch (e) {}
// Then clear the local device_token (via auth.py)
var result = runPython('auth.py', ['clear-device-token']);
out(Object.assign({ ok: !!result.success }, result));
};

// ── Entry point ─────────────────────────────────────────────────────

const allArgs = process.argv.slice(2);
const command = allArgs[0];
const commandArgs = allArgs.slice(1);

if (!command || command === '--help' || command === '-h') {
  console.log(`Usage: node run.js <command> [options]

Commands:
  init                          Environment setup
  get-device-token              Get device token
  get-token [--env test|prod]   Get cached user token
  auth-get-code [--env test|prod]  Get auth link
  auth-poll-token               Poll auth result
  qrcode <url>                  Get QR code (server-side first, local PNG/ASCII fallback)
  issue                         Issue coupons
  hotword --city-id <id>        Hot search words
  search --keyword <kw> --lat <lat> --lng <lng> --city-id <id>
  location                      Get recent location
  location-by-address --address <addr>  Get location by address
  order --product-id <pid> --poi-id <pid> --city-id <id> --uuid <u>
  check-wx-ai-pay               Check if weixinpay plugin supports x402
  check-login                   Check WeChat mini-program login status
  logout                        Logout
  clear-device-token            Clear device token`);
  process.exit(0);
}

if (!commands[command]) {
  fail('UNKNOWN_COMMAND', { command, available: Object.keys(commands) });
}

commands[command](commandArgs);
