// This calls the Next.js API route which then calls the backend server-side
export async function generateTags(imageUrl: string) {
  const res = await fetch('/api/generate-tags', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_url: imageUrl }),
  });
  if (!res.ok) {
    throw new Error(`Backend error: ${res.status}`);
  }
  return res.json();
}
