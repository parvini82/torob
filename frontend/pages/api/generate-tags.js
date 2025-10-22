// Server-side API route that proxies to the backend
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Backend URL is only available on the server
    const backendUrl = process.env.API_URL || 'http://localhost:8000';

    const response = await fetch(`${backendUrl}/generate-tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return res.status(500).json({
      error: 'Failed to connect to backend',
      detail: error.message,
    });
  }
}
