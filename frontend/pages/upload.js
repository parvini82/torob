import { useState } from "react";

export default function UploadPage() {
  const [imageUrl, setImageUrl] = useState("");
  const [file, setFile] = useState(null);
  const [tagGroups, setTagGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [darkMode, setDarkMode] = useState(false);
  const [animateTags, setAnimateTags] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [progress, setProgress] = useState(0);
  const [minioImageUrl, setMinioImageUrl] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setTagGroups([]);
    setAnimateTags(false);
    setUploadedImage(null);
    setMinioImageUrl("");
    setProgress(0);
    setLoading(true);

    try {
      let res;

      // Case 1: User uploaded a file
      if (file) {
        const formData = new FormData();
        formData.append("file", file);

        // Show preview of uploaded file
        setUploadedImage(URL.createObjectURL(file));

        // Simulate progress bar
        let prog = 0;
        const interval = setInterval(() => {
          prog += 5;
          if (prog >= 95) clearInterval(interval);
          setProgress(prog);
        }, 100);

        // Use the new upload-and-tag endpoint
        res = await fetch("/api/upload-and-tag", {
          method: "POST",
          body: formData,
        });

        clearInterval(interval);
      }
      // Case 2: User provided an image URL
      else if (imageUrl) {
        setUploadedImage(imageUrl);

        // Use the original generate-tags endpoint
        res = await fetch("/api/generate-tags", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_url: imageUrl }),
        });
      }
      // Case 3: No input provided
      else {
        throw new Error("لطفاً URL یا فایل تصویر انتخاب کنید.");
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `خطا از سرور: ${res.status}`);
      }

      const data = await res.json();

      // If file was uploaded, we get back image_url
      if (file && data.image_url) {
        setMinioImageUrl(data.image_url);
      }

      // Extract tag groups from the response
      let groups = [];

      // Try different response structures
      if (data.tags && data.tags.entities) {
        groups = data.tags.entities;
      } else if (data.entities) {
        groups = data.entities;
      } else if (data.tags && data.tags["ویژگی‌ها"]) {
        groups = data.tags["ویژگی‌ها"];
      } else if (data["ویژگی‌ها"]) {
        groups = data["ویژگی‌ها"];
      }

      // Keep the full structure: [{نام: "...", مقادیر: [...]}]
      setTagGroups(groups);
      setAnimateTags(true);
      setProgress(100);
    } catch (err) {
      console.error("Error:", err);
      setError(err.message || "خطا در ارتباط با سرور.");
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const categoryStyle = {
    marginBottom: "20px",
    padding: "15px",
    borderRadius: "12px",
    background: darkMode ? "rgba(255, 255, 255, 0.1)" : "rgba(255, 255, 255, 0.7)",
    backdropFilter: "blur(10px)",
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  };

  const categoryTitleStyle = {
    fontSize: "16px",
    fontWeight: "600",
    marginBottom: "10px",
    color: darkMode ? "#fff" : "#333",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  };

  const tagStyle = {
    display: "inline-block",
    padding: "6px 12px",
    margin: "4px",
    borderRadius: "16px",
    color: "#fff",
    fontWeight: "500",
    fontSize: "14px",
    background: "linear-gradient(45deg, #6a11cb, #2575fc)",
    backgroundSize: "200% 200%",
    transition: "all 0.3s ease",
    boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
    cursor: "pointer",
  };

  const skeletonStyle = {
    width: "100%",
    height: "60px",
    borderRadius: "12px",
    background: "linear-gradient(90deg, #e0e0e0 25%, #f7f7f7 50%, #e0e0e0 75%)",
    backgroundSize: "200% 100%",
    animation: "loading 1.5s infinite",
    margin: "10px 0",
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
          onChange={(e) => {
            setImageUrl(e.target.value);
            setFile(null);
          }}
          style={{
            width: "100%",
            padding: "10px",
            fontSize: "16px",
            marginBottom: "10px",
            borderRadius: "8px",
            border: "1px solid #ddd",
          }}
        />

        <p style={{ color: darkMode ? "#f7f7f7" : "#333" }}>
          یا فایل تصویر از سیستم خود انتخاب کنید:
        </p>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            setFile(e.target.files[0]);
            setImageUrl("");
          }}
          style={{
            width: "100%",
            marginBottom: "10px",
            padding: "8px",
            color: darkMode ? "#f7f7f7" : "#333",
          }}
        />

        <button
          type="submit"
          style={{
            width: "100%",
            padding: "12px",
            fontSize: "16px",
            borderRadius: "8px",
            border: "none",
            background: loading
              ? "#ccc"
              : "linear-gradient(45deg, #6a11cb, #2575fc)",
            color: "#fff",
            cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.3s ease",
            fontWeight: "600",
          }}
          disabled={loading}
        >
          {loading ? "Processing..." : "Generate Tags"}
        </button>
      </form>

      {progress > 0 && loading && (
        <div
          style={{
            width: "100%",
            maxWidth: "400px",
            marginTop: "10px",
            background: "#ddd",
            borderRadius: "3px",
            overflow: "hidden",
          }}
        >
          <div style={progressBarStyle}></div>
        </div>
      )}

      {error && (
        <p
          style={{
            color: "crimson",
            marginTop: "10px",
            padding: "10px",
            background: darkMode ? "#fff1f0" : "#ffe6e6",
            borderRadius: "8px",
            maxWidth: "400px",
          }}
        >
          {error}
        </p>
      )}

      {uploadedImage && (
        <div style={{ marginTop: "20px", textAlign: "center" }}>
          <img
            src={uploadedImage}
            alt="Uploaded"
            style={{
              maxWidth: "500px",
              maxHeight: "400px",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              objectFit: "contain",
            }}
          />
          {minioImageUrl && (
            <p
              style={{
                marginTop: "10px",
                fontSize: "12px",
                color: darkMode ? "#bbb" : "#666",
                wordBreak: "break-all",
              }}
            >
              تصویر ذخیره شده: {minioImageUrl}
            </p>
          )}
        </div>
      )}

      {loading && (
        <div
          style={{
            marginTop: "20px",
            width: "100%",
            maxWidth: "700px",
          }}
        >
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={skeletonStyle}></div>
          ))}
        </div>
      )}

      {tagGroups.length > 0 && (
        <div
          style={{
            marginTop: "30px",
            width: "100%",
            maxWidth: "700px",
          }}
        >
          {tagGroups.map((group, i) => (
            <div
              key={i}
              style={{
                ...categoryStyle,
                opacity: animateTags ? 1 : 0,
                transform: animateTags ? "translateY(0)" : "translateY(20px)",
                transition: `all 0.5s ease ${i * 0.1}s`,
              }}
            >
              <div style={categoryTitleStyle}>
                <span style={{ fontSize: "20px" }}>🏷️</span>
                <span>{group.نام || group.name}</span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                {(group.مقادیر || group.values || []).map((value, j) => (
                  <span
                    key={j}
                    style={tagStyle}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundPosition = "100% 0";
                      e.target.style.transform = "scale(1.1)";
                      e.target.style.boxShadow = "0 4px 12px rgba(0,0,0,0.25)";
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundPosition = "0 0";
                      e.target.style.transform = "scale(1)";
                      e.target.style.boxShadow = "0 2px 4px rgba(0,0,0,0.15)";
                    }}
                  >
                    {value}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        @keyframes loading {
          0% {
            background-position: 200% 0;
          }
          100% {
            background-position: -200% 0;
          }
        }
      `}</style>
    </div>
  );
}