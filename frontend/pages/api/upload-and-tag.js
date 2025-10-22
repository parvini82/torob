// Server-side API route that proxies file uploads to the backend
export const config = {
  api: {
    bodyParser: false, // Disable body parsing, we'll handle it manually
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.API_URL || 'http://localhost:8000';

    // Forward the multipart/form-data request to backend
    const formData = new FormData();

    // Parse the incoming request
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const buffer = Buffer.concat(chunks);

    // Extract boundary from content-type
    const contentType = req.headers['content-type'];

    // Forward the raw request to backend
    const response = await fetch(`${backendUrl}/upload-and-tag`, {
      method: 'POST',
      headers: {
        'Content-Type': contentType,
      },
      body: buffer,
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Error proxying upload to backend:', error);
    return res.status(500).json({
      error: 'Failed to upload to backend',
      detail: error.message,
    });
  }
}
