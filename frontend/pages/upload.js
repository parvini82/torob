import { useState } from "react";

export default function UploadPage() {
  const [imageUrl, setImageUrl] = useState("");
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!imageUrl) return setError("لطفاً آدرس تصویر را وارد کنید.");

    setLoading(true);
    setError("");
    setTags([]);

    try {
      const res = await fetch("http://127.0.0.1:8000/generate-tags", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl }),
      });

      if (!res.ok) throw new Error(`خطا از سرور: ${res.status}`);

      const data = await res.json();
      const extractedTags = data.entities.flatMap(e => e.مقادیر);
      setTags(extractedTags);
    } catch (err) {
      setError(err.message || "خطا در ارتباط با سرور.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "sans-serif",
        padding: "20px",
      }}
    >
      <h1 style={{ marginBottom: "20px" }}>Welcome to Image Tagging</h1>

      <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: "400px" }}>
        <input
          type="text"
          placeholder="Enter image URL..."
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          style={{ width: "100%", padding: "10px", fontSize: "16px", marginBottom: "10px" }}
        />
        <button
          type="submit"
          style={{ width: "100%", padding: "10px", fontSize: "16px" }}
          disabled={loading}
        >
          {loading ? "Processing..." : "Generate Tags"}
        </button>
      </form>

      {error && <p style={{ color: "crimson", marginTop: "10px" }}>{error}</p>}

      {tags.length > 0 && (
        <div
          style={{
            marginTop: "20px",
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
            justifyContent: "center",
          }}
        >
          {tags.map((tag, i) => (
            <span
              key={i}
              style={{
                padding: "6px 12px",
                border: "1px solid #ddd",
                borderRadius: "16px",
                background: "#f7f7f7",
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
