module.exports = async function handler(req, res) {
  const code = (req.query && req.query.code) || '';
  const state = (req.query && req.query.state) || '';

  const clientId = process.env.GITHUB_OAUTH_CLIENT_ID;
  const clientSecret = process.env.GITHUB_OAUTH_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    res.statusCode = 500;
    return res.end('Missing server configuration (GITHUB_OAUTH_CLIENT_ID/GITHUB_OAUTH_CLIENT_SECRET)');
  }

  if (!code) {
    res.statusCode = 400;
    return res.end('Missing code');
  }

  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': 'bejob-vercel-oauth'
    },
    body: JSON.stringify({
      client_id: clientId,
      client_secret: clientSecret,
      code
    })
  });

  const tokenJson = await tokenRes.json().catch(() => null);
  const accessToken = tokenJson && tokenJson.access_token;

  if (!tokenRes.ok || !accessToken) {
    res.statusCode = 400;
    return res.end((tokenJson && (tokenJson.error_description || tokenJson.error)) || 'OAuth token exchange failed');
  }

  // Decap CMS OAuth provider pattern: postMessage back to opener.
  // We keep `state` as-is and return it to the client. Decap uses it to validate the origin.
  const payload = { token: accessToken, provider: 'github', state };

  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  return res.end(`<!doctype html>
<html>
  <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Authorization</title></head>
  <body>
    <script>
      (function(){
        var msg = 'authorization:github:success:' + ${JSON.stringify(JSON.stringify(payload))};
        if (window.opener && window.opener.postMessage) {
          window.opener.postMessage(msg, '*');
        }
        window.close();
      })();
    </script>
  </body>
</html>`);
};
