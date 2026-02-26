module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    return res.end();
  }

  if (req.method !== 'POST') {
    res.statusCode = 405;
    return res.end('Method Not Allowed');
  }

  const auth = req.headers.authorization || '';
  if (!auth.startsWith('Bearer ')) {
    res.statusCode = 401;
    return res.end('Unauthorized');
  }

  const providedKey = auth.slice('Bearer '.length).trim();
  const expectedKey = (process.env.ADMIN_API_KEY || '').trim();
  if (!expectedKey || providedKey !== expectedKey) {
    res.statusCode = 403;
    return res.end('Forbidden');
  }

  let payload;
  try {
    payload = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  } catch (e) {
    res.statusCode = 400;
    return res.end('Invalid JSON');
  }

  const workflow = (payload.workflow || '').trim();
  const ref = (payload.ref || 'main').trim();
  const inputs = payload.inputs || undefined;

  const allowedWorkflows = (process.env.ALLOWED_WORKFLOWS || 'pipeline_offres.yml,pipeline_public.yml,pipeline_etranger.yml,pipeline_editorial.yml')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  if (!workflow || !allowedWorkflows.includes(workflow)) {
    res.statusCode = 400;
    return res.end('Workflow not allowed');
  }

  const owner = process.env.GITHUB_OWNER;
  const repo = process.env.GITHUB_REPO;
  const token = process.env.GITHUB_TOKEN;

  if (!owner || !repo || !token) {
    res.statusCode = 500;
    return res.end('Missing server configuration (GITHUB_OWNER/GITHUB_REPO/GITHUB_TOKEN)');
  }

  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`;

  const ghRes = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'bejob-vercel-function'
    },
    body: JSON.stringify(inputs ? { ref, inputs } : { ref })
  });

  if (!ghRes.ok) {
    const t = await ghRes.text();
    res.statusCode = ghRes.status;
    return res.end(t || 'GitHub API error');
  }

  res.statusCode = 200;
  return res.end('Workflow déclenché');
};
