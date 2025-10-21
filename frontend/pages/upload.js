import { useState, useEffect } from "react";

export default function UploadPage() {
  const [imageUrl, setImageUrl] = useState("");
  const [file, setFile] = useState(null);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [darkMode, setDarkMode] = useState(false);
  const [animateTags, setAnimateTags] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setTags([]);
    setAnimateTags(false);
    setUploadedImage(null);
    setProgress(0);
    setLoading(true);

    try {
      let res;
      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        setUploadedImage(URL.createObjectURL(file));

        // Simulate progress bar
        let prog = 0;
        const interval = setInterval(() => {
          prog += 5;
          if (prog >= 95) clearInterval(interval);
          setProgress(prog);
        }, 100);

        res = await fetch("http://localhost:8000/generate-tags", {
          method: "POST",
          body: formData,
        });
      } else if (imageUrl) {
        setUploadedImage(imageUrl);
        res = await fetch("http://localhost:8000/generate-tags", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_url: imageUrl }),
        });
      } else {
        throw new Error("لطفاً URL یا فایل تصویر انتخاب کنید.");
      }

      if (!res.ok) throw new Error(`خطا از سرور: ${res.status}`);

      const data = await res.json();
      const extractedTags = data.entities?.flatMap((e) => e.مقادیر || []) || [];
      setTags(extractedTags);
      setAnimateTags(true);
      setProgress(100);
    } catch (err) {
      setError(err.message || "خطا در ارتباط با سرور.");
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const tagStyle = {
    padding: "8px 16px",
    borderRadius: "20px",
    color: "#fff",
    fontWeight: "500",
    cursor: "pointer",
    background: "linear-gradient(45deg, #6a11cb, #2575fc)",
    backgroundSize: "200% 200%",
    transition: "all 0.4s ease",
    boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
  };

  const skeletonStyle = {
    width: "80px",
    height: "28px",
    borderRadius: "20px",
    background: "linear-gradient(90deg, #e0e0e0 25%, #f7f7f7 50%, #e0e0e0 75%)",
    backgroundSize: "200% 100%",
    animation: "loading 1.5s infinite",
    margin: "5px",
  };

  const progressBarStyle = {
    width: `${progress}%`,
    height: "6px",
    borderRadius: "3px",
    background: "linear-gradient(90deg, #6a11cb, #2575fc)",
    transition: "width 0.2s ease",
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
        background: darkMode
          ? "linear-gradient(to bottom right, #2c3e50, #34495e)"
          : "linear-gradient(to bottom right, #a1c4fd, #c2e9fb)",
        position: "relative",
        transition: "background 0.5s ease",
      }}
    >
      <button
        onClick={() => setDarkMode(!darkMode)}
        style={{
          position: "absolute",
          top: "20px",
          left: "20px",
          padding: "8px 16px",
          borderRadius: "20px",
          border: "none",
          cursor: "pointer",
          background: darkMode ? "#fff" : "#333",
          color: darkMode ? "#333" : "#fff",
          transition: "all 0.3s ease",
        }}
      >
        {darkMode ? "Light Mode" : "Dark Mode"}
      </button>

      <img
        src="https://tmooty.com/wp-content/uploads/2023/09/download-1-1.png"
        alt="Logo"
        style={{
          position: "absolute",
          top: "20px",
          right: "20px",
          width: "400px",
          height: "auto",
          opacity: 0.9,
        }}
      />

      <h1 style={{ marginBottom: "20px", color: darkMode ? "#f7f7f7" : "#333" }}>
        Welcome to Image Tagging
      </h1>

      <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: "400px" }}>
        <p style={{ color: darkMode ? "#f7f7f7" : "#333" }}>آدرس تصویر (URL):</p>
        <input
          type="text"
          placeholder="Enter image URL..."
          value={imageUrl}
          onChange={(e) => { setImageUrl(e.target.value); setFile(null); }}
          style={{ width: "100%", padding: "10px", fontSize: "16px", marginBottom: "10px" }}
        />

        <p style={{ color: darkMode ? "#f7f7f7" : "#333" }}>یا فایل تصویر از سیستم خود انتخاب کنید:</p>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => { setFile(e.target.files[0]); setImageUrl(""); }}
          style={{ width: "100%", marginBottom: "10px" }}
        />

        <button
          type="submit"
          style={{ width: "100%", padding: "10px", fontSize: "16px" }}
          disabled={loading}
        >
          {loading ? "Processing..." : "Generate Tags"}
        </button>
      </form>

      {progress > 0 && loading && (
        <div style={{ width: "100%", maxWidth: "400px", marginTop: "10px", background: "#ddd", borderRadius: "3px" }}>
          <div style={progressBarStyle}></div>
        </div>
      )}

      {error && <p style={{ color: "crimson", marginTop: "10px" }}>{error}</p>}

      {uploadedImage && (
        <img
          src={uploadedImage}
          alt="Uploaded"
          style={{ marginTop: "20px", maxWidth: "400px", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.15)" }}
        />
      )}

      {loading && !file && (
        <div style={{ marginTop: "20px", display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={skeletonStyle}></div>
          ))}
        </div>
      )}

      {tags.length > 0 && (
        <div
          style={{
            marginTop: "20px",
            display: "flex",
            flexWrap: "wrap",
            gap: "12px",
            justifyContent: "center",
          }}
        >
          {tags.map((tag, i) => (
            <span
              key={i}
              style={{
                ...tagStyle,
                opacity: animateTags ? 1 : 0,
                transform: animateTags ? "translateY(0)" : "translateY(20px)",
                transition: `all 0.5s ease ${i * 0.05}s`,
              }}
              onMouseEnter={e => {
                e.target.style.backgroundPosition = "100% 0";
                e.target.style.transform = "scale(1.15) translateY(0)";
                e.target.style.boxShadow = "0 6px 16px rgba(0,0,0,0.25)";
              }}
              onMouseLeave={e => {
                e.target.style.backgroundPosition = "0 0";
                e.target.style.transform = "scale(1) translateY(0)";
                e.target.style.boxShadow = "0 2px 6px rgba(0,0,0,0.15)";
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <style jsx>{`
        @keyframes loading {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}
