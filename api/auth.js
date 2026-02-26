module.exports = async function handler(req, res) {
  const clientId = process.env.GITHUB_OAUTH_CLIENT_ID;
  const redirectUri = process.env.GITHUB_OAUTH_REDIRECT_URI;

  if (!clientId || !redirectUri) {
    res.statusCode = 500;
    return res.end('Missing server configuration (GITHUB_OAUTH_CLIENT_ID/GITHUB_OAUTH_REDIRECT_URI)');
  }

  const url = new URL('https://github.com/login/oauth/authorize');
  url.searchParams.set('client_id', clientId);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('scope', 'repo');

  res.statusCode = 302;
  res.setHeader('Location', url.toString());
  return res.end();
};
