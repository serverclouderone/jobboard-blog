exports.handler = async function (event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  const auth = event.headers.authorization || event.headers.Authorization || '';
  if (!auth.startsWith('Bearer ')) {
    return { statusCode: 401, body: 'Unauthorized' };
  }

  const user = event.clientContext && event.clientContext.user;
  if (!user) {
    return { statusCode: 401, body: 'Unauthorized' };
  }

  const allowedRoles = (process.env.ADMIN_ALLOWED_ROLES || 'admin').split(',').map(s => s.trim()).filter(Boolean);
  const roles = (user.app_metadata && user.app_metadata.roles) || [];
  const hasRole = roles.some(r => allowedRoles.includes(r));
  if (!hasRole) {
    return { statusCode: 403, body: 'Forbidden' };
  }

  let payload;
  try {
    payload = JSON.parse(event.body || '{}');
  } catch (e) {
    return { statusCode: 400, body: 'Invalid JSON' };
  }

  const workflow = (payload.workflow || '').trim();
  const ref = (payload.ref || 'main').trim();
  const inputs = payload.inputs || undefined;

  const allowedWorkflows = (process.env.ALLOWED_WORKFLOWS || 'pipeline_offres.yml,pipeline_public.yml,pipeline_etranger.yml,pipeline_editorial.yml').split(',').map(s => s.trim()).filter(Boolean);
  if (!workflow || !allowedWorkflows.includes(workflow)) {
    return { statusCode: 400, body: 'Workflow not allowed' };
  }

  const owner = process.env.GITHUB_OWNER;
  const repo = process.env.GITHUB_REPO;
  const token = process.env.GITHUB_TOKEN;

  if (!owner || !repo || !token) {
    return { statusCode: 500, body: 'Missing server configuration (GITHUB_OWNER/GITHUB_REPO/GITHUB_TOKEN)' };
  }

  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'bejob-netlify-function'
    },
    body: JSON.stringify(inputs ? { ref, inputs } : { ref })
  });

  if (!res.ok) {
    const t = await res.text();
    return { statusCode: res.status, body: t || 'GitHub API error' };
  }

  return { statusCode: 200, body: 'Workflow déclenché' };
};
