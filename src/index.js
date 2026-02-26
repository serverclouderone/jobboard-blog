function json(res, obj, status = 200, extraHeaders = {}) {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    ...extraHeaders,
  };
  return new Response(JSON.stringify(obj), { status, headers });
}

function text(resText, status = 200, extraHeaders = {}) {
  const headers = {
    'Content-Type': 'text/plain; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    ...extraHeaders,
  };
  return new Response(resText, { status, headers });
}

function html(resHtml, status = 200, extraHeaders = {}) {
  const headers = {
    'Content-Type': 'text/html; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    ...extraHeaders,
  };
  return new Response(resHtml, { status, headers });
}

function corsPreflight() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    },
  });
}

function mustBePost(req) {
  if (req.method !== 'POST') return { ok: false, res: text('Method Not Allowed', 405) };
  return { ok: true };
}

function prefersHtml(req) {
  const accept = (req.headers.get('Accept') || '').toLowerCase();
  if (accept.includes('text/html')) return true;
  const secFetchDest = (req.headers.get('Sec-Fetch-Dest') || '').toLowerCase();
  if (secFetchDest === 'document') return true;
  return false;
}

function redirectBack(req, fallbackPath = '/') {
  const ref = req.headers.get('Referer') || '';
  let location = fallbackPath;
  try {
    if (ref) {
      const u = new URL(ref);
      u.searchParams.set('submitted', '1');
      location = u.toString();
    }
  } catch {
    // ignore
  }

  return new Response(null, {
    status: 303,
    headers: {
      Location: location,
      'Access-Control-Allow-Origin': '*',
    }
  });
}

function getBearer(req) {
  const auth = req.headers.get('Authorization') || '';
  if (!auth.startsWith('Bearer ')) return '';
  return auth.slice('Bearer '.length).trim();
}

function requireEnv(env, keys) {
  const missing = keys.filter(k => !env[k]);
  if (missing.length) {
    return { ok: false, res: text(`Missing server configuration (${missing.join('/')})`, 500) };
  }
  return { ok: true };
}

function parseForm(bodyText) {
  const params = new URLSearchParams(bodyText);
  const obj = {};
  for (const [k, v] of params.entries()) obj[k] = v;
  return obj;
}

async function githubAuthorizeUrl(env, requestUrl) {
  const clientId = env.GITHUB_OAUTH_CLIENT_ID;
  const redirectUri = env.GITHUB_OAUTH_REDIRECT_URI;
  const url = new URL('https://github.com/login/oauth/authorize');
  url.searchParams.set('client_id', clientId);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('scope', 'repo');

  // Decap may pass a 'state' param; if present we forward it
  const incomingState = new URL(requestUrl).searchParams.get('state');
  if (incomingState) url.searchParams.set('state', incomingState);

  return url.toString();
}

async function exchangeGithubCodeForToken(env, code) {
  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': 'bejob-cf-worker-oauth'
    },
    body: JSON.stringify({
      client_id: env.GITHUB_OAUTH_CLIENT_ID,
      client_secret: env.GITHUB_OAUTH_CLIENT_SECRET,
      code
    })
  });

  const tokenJson = await tokenRes.json().catch(() => null);
  const accessToken = tokenJson && tokenJson.access_token;

  if (!tokenRes.ok || !accessToken) {
    return { ok: false, error: (tokenJson && (tokenJson.error_description || tokenJson.error)) || 'OAuth token exchange failed' };
  }

  return { ok: true, token: accessToken };
}

async function handleAuth(req, env) {
  const check = requireEnv(env, ['GITHUB_OAUTH_CLIENT_ID', 'GITHUB_OAUTH_REDIRECT_URI']);
  if (!check.ok) return check.res;

  const location = await githubAuthorizeUrl(env, req.url);
  return new Response(null, { status: 302, headers: { Location: location, 'Access-Control-Allow-Origin': '*' } });
}

async function handleCallback(req, env) {
  const check = requireEnv(env, ['GITHUB_OAUTH_CLIENT_ID', 'GITHUB_OAUTH_CLIENT_SECRET']);
  if (!check.ok) return check.res;

  const u = new URL(req.url);
  const code = u.searchParams.get('code') || '';
  const state = u.searchParams.get('state') || '';

  if (!code) return text('Missing code', 400);

  const ex = await exchangeGithubCodeForToken(env, code);
  if (!ex.ok) return text(ex.error, 400);

  const payload = { token: ex.token, provider: 'github', state };
  const msg = 'authorization:github:success:' + JSON.stringify(payload);

  return html(`<!doctype html>
<html>
  <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Authorization</title></head>
  <body>
    <script>
      (function(){
        var msg = ${JSON.stringify(msg)};
        if (window.opener && window.opener.postMessage) {
          window.opener.postMessage(msg, '*');
        }
        window.close();
      })();
    </script>
  </body>
</html>`);
}

async function handleDispatchWorkflow(req, env) {
  const post = mustBePost(req);
  if (!post.ok) return post.res;

  const expectedKey = (env.ADMIN_API_KEY || '').trim();
  const providedKey = getBearer(req);
  if (!expectedKey) return text('Missing server configuration (ADMIN_API_KEY)', 500);
  if (!providedKey || providedKey !== expectedKey) return text('Forbidden', 403);

  const cfgCheck = requireEnv(env, ['GITHUB_OWNER', 'GITHUB_REPO', 'GITHUB_TOKEN']);
  if (!cfgCheck.ok) return cfgCheck.res;

  let payload;
  try {
    payload = await req.json();
  } catch {
    return text('Invalid JSON', 400);
  }

  const workflow = (payload.workflow || '').trim();
  const ref = (payload.ref || 'main').trim();
  const inputs = payload.inputs || undefined;

  const allowed = (env.ALLOWED_WORKFLOWS || 'pipeline_offres.yml,pipeline_public.yml,pipeline_etranger.yml,pipeline_editorial.yml')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  if (!workflow || !allowed.includes(workflow)) return text('Workflow not allowed', 400);

  const url = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`;

  const ghRes = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'bejob-cf-worker'
    },
    body: JSON.stringify(inputs ? { ref, inputs } : { ref })
  });

  if (!ghRes.ok) {
    const t = await ghRes.text();
    return text(t || 'GitHub API error', ghRes.status);
  }

  return text('Workflow déclenché', 200);
}

async function resendSend(env, subject, textBody) {
  const check = requireEnv(env, ['RESEND_API_KEY', 'RESEND_FROM', 'RESEND_TO']);
  if (!check.ok) return { ok: false, res: check.res };

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: env.RESEND_FROM,
      to: [env.RESEND_TO],
      subject,
      text: textBody
    })
  });

  if (!res.ok) {
    const t = await res.text();
    return { ok: false, res: text(t || 'Resend API error', res.status) };
  }

  return { ok: true };
}

async function handleForm(req, env, formName) {
  const post = mustBePost(req);
  if (!post.ok) return post.res;

  const contentType = (req.headers.get('Content-Type') || '').toLowerCase();
  let data = {};

  if (contentType.includes('application/json')) {
    try {
      data = await req.json();
    } catch {
      return text('Invalid JSON', 400);
    }
  } else {
    const bodyText = await req.text();
    data = parseForm(bodyText);
  }

  // basic bot field handling
  if (data['bot-field'] || data['bot']) {
    return prefersHtml(req) ? redirectBack(req) : json(null, { ok: true }, 200);
  }

  const subject = `[BeJob] Nouveau formulaire: ${formName}`;
  const lines = [
    `Form: ${formName}`,
    `Date: ${new Date().toISOString()}`,
    '',
    ...Object.keys(data).sort().map(k => `${k}: ${String(data[k]).trim()}`)
  ];

  const send = await resendSend(env, subject, lines.join('\n'));
  if (!send.ok) return send.res;

  // UX: browsers submitting a form should be redirected back to the page.
  if (prefersHtml(req) && !contentType.includes('application/json')) {
    return redirectBack(req);
  }

  return json(null, { ok: true }, 200);
}

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return corsPreflight();

    const url = new URL(req.url);
    const path = url.pathname;

    if (path === '/auth') return handleAuth(req, env);
    if (path === '/callback') return handleCallback(req, env);

    if (path === '/dispatch-workflow') return handleDispatchWorkflow(req, env);

    if (path === '/forms/contact') return handleForm(req, env, 'contact');
    if (path === '/forms/newsletter') return handleForm(req, env, 'newsletter');
    if (path === '/forms/publier-offre') return handleForm(req, env, 'publier-offre');

    return text('Not Found', 404);
  }
};
