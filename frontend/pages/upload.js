import { useState } from "react";

export default function UploadPage() {
  const [imageUrl, setImageUrl] = useState("");
  const [file, setFile] = useState(null);
  const [tagGroups, setTagGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [darkMode, setDarkMode] = useState(true);
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
        res = await fetch("http://localhost:8000/upload-and-tag", {
          method: "POST",
          body: formData,
        });

        clearInterval(interval);
      }
      // Case 2: User provided an image URL
      else if (imageUrl) {
        setUploadedImage(imageUrl);

        // Use the original generate-tags endpoint
        res = await fetch("http://localhost:8000/generate-tags", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_url: imageUrl }),
        });
      }
      // Case 3: No input provided
      else {
        throw new Error("Please select an image URL or upload a file.");
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${res.status}`);
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
      setError(err.message || "Error connecting to server.");
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const categoryStyle = {
    marginBottom: "20px",
    padding: "18px",
    borderRadius: "14px",
    background: darkMode
      ? "rgba(255, 255, 255, 0.08)"
      : "rgba(255, 255, 255, 0.85)",
    backdropFilter: "blur(12px)",
    boxShadow: darkMode
      ? "0 6px 20px rgba(0,0,0,0.3)"
      : "0 6px 20px rgba(0,0,0,0.12)",
    maxWidth: "100%",
    width: "100%",
    transition: "all 0.3s ease",
  };

  const categoryTitleStyle = {
    fontSize: "1.15rem",
    fontWeight: "700",
    marginBottom: "14px",
    color: darkMode ? "#fff" : "#2c3e50",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    letterSpacing: "0.3px",
  };

  const tagStyle = {
    display: "inline-block",
    padding: "10px 18px",
    margin: "6px",
    borderRadius: "22px",
    color: "#fff",
    fontWeight: "600",
    fontSize: "0.95rem",
    background: "linear-gradient(45deg, #6a11cb, #2575fc)",
    backgroundSize: "200% 200%",
    transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 3px 8px rgba(0,0,0,0.18)",
    cursor: "pointer",
    minWidth: "70px",
    textAlign: "center",
    border: "none",
  };

  const skeletonCategoryStyle = {
    width: "100%",
    height: "90px",
    borderRadius: "14px",
    background:
      "linear-gradient(90deg, #e0e0e0 25%, #f5f5f5 50%, #e0e0e0 75%)",
    backgroundSize: "200% 100%",
    animation: "loading 1.5s infinite",
    margin: "12px 0",
  };

  const progressBarStyle = {
    width: `${progress}%`,
    height: "6px",
    borderRadius: "3px",
    background: "linear-gradient(90deg, #6a11cb, #2575fc)",
    transition: "width 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
        padding: "20px",
        background: darkMode
          ? "linear-gradient(135deg, #2c3e50 0%, #34495e 100%)"
          : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        position: "relative",
        transition: "background 0.6s ease",
      }}
    >
      <button
        onClick={() => setDarkMode(!darkMode)}
        style={{
          position: "absolute",
          top: "20px",
          left: "20px",
          padding: "10px 20px",
          borderRadius: "25px",
          border: "none",
          cursor: "pointer",
          background: darkMode ? "#fff" : "#2c3e50",
          color: darkMode ? "#2c3e50" : "#fff",
          transition: "all 0.3s ease",
          fontWeight: "700",
          fontSize: "0.9rem",
          zIndex: 10,
          boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = "scale(1.05)";
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = "scale(1)";
        }}
      >
        {darkMode ? "☀️ Light" : "🌙 Dark"}
      </button>

      <img
        src="https://rahnemacollege.com/blog/wp-content/uploads/2023/02/rc-logo.png"
        alt="Logo"
        style={{
          position: "absolute",
          top: "20px",
          right: "20px",
          maxWidth: "min(300px, 25vw)",
          minWidth: "100px",
          height: "auto",
          opacity: 0.92,
          transition: "all 0.3s ease",
        }}
      />

      <h1
        style={{
          marginBottom: "25px",
          marginTop: "60px",
          fontSize: "clamp(1.5rem, 5vw, 2.5rem)",
          fontWeight: 800,
          color: "#fff",
          textAlign: "center",
          lineHeight: "1.2",
          textShadow: "0 2px 10px rgba(0,0,0,0.2)",
          letterSpacing: "0.5px",
        }}
      >
        Welcome to <span className="gashtal">Gashtal</span> Image Tagging
      </h1>

      <style jsx>{`
        .gashtal {
          background: linear-gradient(90deg, #ffd89b, #19547b, #ffd89b);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          background-size: 200% 100%;
          animation: gradientMove 4s infinite linear;
          font-weight: 900;
        }
        @keyframes gradientMove {
          0% {
            background-position: 0% 50%;
          }
          100% {
            background-position: 200% 50%;
          }
        }
        @keyframes loading {
          0% {
            background-position: 200% 0;
          }
          100% {
            background-position: -200% 0;
          }
        }
        @media only screen and (max-width: 768px) {
          h1 {
            margin-top: 80px !important;
          }
        }
        @media only screen and (max-width: 600px) {
          img[alt="Logo"] {
            max-width: 100px !important;
            top: 18px !important;
            right: 15px !important;
          }
          button {
            font-size: 0.8rem !important;
            padding: 8px 14px !important;
          }
        }
        @media only screen and (max-width: 420px) {
          h1 {
            margin-top: 70px !important;
          }
        }
      `}</style>

      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: "480px",
          margin: "0 auto",
          boxSizing: "border-box",
          background: darkMode
            ? "rgba(255, 255, 255, 0.05)"
            : "rgba(255, 255, 255, 0.25)",
          padding: "25px",
          borderRadius: "16px",
          backdropFilter: "blur(10px)",
          boxShadow: "0 8px 32px rgba(0,0,0,0.15)",
        }}
      >
        <p
          style={{
            color: "#fff",
            fontSize: "1.05rem",
            marginBottom: "8px",
            fontWeight: "600",
            textShadow: "0 1px 3px rgba(0,0,0,0.2)",
          }}
        >
          Image URL:
        </p>
        <input
          type="text"
          placeholder="Paste your image URL here..."
          value={imageUrl}
          onChange={(e) => {
            setImageUrl(e.target.value);
            setFile(null);
          }}
          style={{
            width: "100%",
            padding: "12px 15px",
            fontSize: "1rem",
            marginBottom: "15px",
            borderRadius: "10px",
            border: "2px solid rgba(255,255,255,0.3)",
            boxSizing: "border-box",
            background: "rgba(255,255,255,0.9)",
            transition: "all 0.3s ease",
            outline: "none",
          }}
          onFocus={(e) => {
            e.target.style.borderColor = "#6a11cb";
            e.target.style.boxShadow = "0 0 0 3px rgba(106,17,203,0.1)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "rgba(255,255,255,0.3)";
            e.target.style.boxShadow = "none";
          }}
        />

        <p
          style={{
            color: "#fff",
            fontSize: "1.05rem",
            marginBottom: "8px",
            fontWeight: "600",
            textShadow: "0 1px 3px rgba(0,0,0,0.2)",
          }}
        >
          Or upload an image file:
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
            marginBottom: "15px",
            padding: "10px",
            color: "#fff",
            background: "rgba(255,255,255,0.15)",
            borderRadius: "10px",
            border: "2px dashed rgba(255,255,255,0.4)",
            cursor: "pointer",
            fontSize: "0.95rem",
          }}
        />

        <button
          type="submit"
          style={{
            width: "100%",
            padding: "14px",
            fontSize: "1.15rem",
            borderRadius: "12px",
            marginTop: "10px",
            fontWeight: "700",
            color: "#fff",
            background: loading
              ? "linear-gradient(90deg, #95a5a6, #7f8c8d)"
              : "linear-gradient(90deg, #f093fb 0%, #f5576c 100%)",
            border: "none",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
            transition: "all 0.3s ease",
            boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
            letterSpacing: "0.5px",
          }}
          disabled={loading}
          onMouseEnter={(e) => {
            if (!loading) {
              e.target.style.transform = "translateY(-2px)";
              e.target.style.boxShadow = "0 6px 20px rgba(0,0,0,0.3)";
            }
          }}
          onMouseLeave={(e) => {
            if (!loading) {
              e.target.style.transform = "translateY(0)";
              e.target.style.boxShadow = "0 4px 15px rgba(0,0,0,0.2)";
            }
          }}
        >
          {loading ? "⏳ Processing..." : "🚀 Generate Tags"}
        </button>
      </form>

      {progress > 0 && loading && (
        <div
          style={{
            width: "100%",
            maxWidth: "480px",
            marginTop: "15px",
            background: "rgba(255,255,255,0.25)",
            borderRadius: "6px",
            overflow: "hidden",
            padding: "2px",
          }}
        >
          <div style={progressBarStyle}></div>
        </div>
      )}

      {error && (
        <p
          style={{
            color: "#fff",
            marginTop: "15px",
            fontWeight: "700",
            textAlign: "center",
            padding: "15px 20px",
            background: "rgba(231, 76, 60, 0.9)",
            borderRadius: "12px",
            maxWidth: "480px",
            boxShadow: "0 4px 15px rgba(231, 76, 60, 0.4)",
            fontSize: "1rem",
          }}
        >
          ⚠️ {error}
        </p>
      )}

      {uploadedImage && (
        <div
          style={{
            marginTop: "25px",
            textAlign: "center",
            maxWidth: "min(750px, 90vw)",
            width: "100%",
          }}
        >
          <img
            src={uploadedImage}
            alt="Uploaded"
            style={{
              maxWidth: "100%",
              maxHeight: "450px",
              borderRadius: "12px",
              boxShadow: "0 8px 30px rgba(0,0,0,0.3)",
              objectFit: "contain",
              display: "block",
              margin: "0 auto",
              border: "3px solid rgba(255,255,255,0.3)",
            }}
          />
          {minioImageUrl && (
            <p
              style={{
                marginTop: "12px",
                fontSize: "0.85rem",
                color: darkMode ? "#bbb" : "#ecf0f1",
                wordBreak: "break-all",
                padding: "0 15px",
                fontWeight: "500",
              }}
            >
              📁 Saved image: {minioImageUrl}
            </p>
          )}
        </div>
      )}

      {loading && (
        <div
          style={{
            marginTop: "25px",
            width: "100%",
            maxWidth: "min(750px, 90vw)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
          }}
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} style={skeletonCategoryStyle}></div>
          ))}
        </div>
      )}

      {tagGroups.length > 0 && (
        <div
          style={{
            marginTop: "30px",
            width: "100%",
            maxWidth: "min(750px, 90vw)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "15px",
          }}
        >
          {tagGroups.map((group, i) => (
            <div
              key={i}
              style={{
                ...categoryStyle,
                opacity: animateTags ? 1 : 0,
                transform: animateTags
                  ? "translateY(0)"
                  : "translateY(30px)",
                transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${
                  i * 0.12
                }s`,
              }}
            >
              <div style={categoryTitleStyle}>
                <span style={{ fontSize: "24px" }}>🏷️</span>
                <span>{group.نام || group.name}</span>
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px",
                  justifyContent: "flex-start",
                }}
              >
                {(group.مقادیر || group.values || []).map((value, j) => (
                  <span
                    key={j}
                    style={{
                      ...tagStyle,
                      opacity: animateTags ? 1 : 0,
                      transform: animateTags
                        ? "translateY(0)"
                        : "translateY(20px)",
                      transition: `all 0.5s cubic-bezier(0.4, 0, 0.2, 1) ${
                        i * 0.12 + j * 0.05
                      }s`,
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundPosition = "100% 0";
                      e.target.style.transform =
                        "scale(1.12) translateY(-2px)";
                      e.target.style.boxShadow =
                        "0 8px 20px rgba(0,0,0,0.3)";
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundPosition = "0 0";
                      e.target.style.transform = "scale(1) translateY(0)";
                      e.target.style.boxShadow =
                        "0 3px 8px rgba(0,0,0,0.18)";
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
    </div>
  );
}