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
    maxWidth: "700px",
    width: "100%",
  };

  const categoryTitleStyle = {
    fontSize: "1.1rem",
    fontWeight: "700",
    marginBottom: "12px",
    color: darkMode ? "#fff" : "#333",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  };

  const tagStyle = {
    display: "inline-block",
    padding: "8px 16px",
    margin: "5px 4px",
    borderRadius: "20px",
    color: "#fff",
    fontWeight: "500",
    fontSize: "1rem",
    background: "linear-gradient(45deg, #6a11cb, #2575fc)",
    backgroundSize: "200% 200%",
    transition: "all 0.4s ease",
    boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
    cursor: "pointer",
    minWidth: "65px",
    textAlign: "center",
  };

  const skeletonCategoryStyle = {
    width: "100%",
    maxWidth: "700px",
    height: "80px",
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
          top: "18px",
          left: "18px",
          padding: "8px 16px",
          borderRadius: "20px",
          border: "none",
          cursor: "pointer",
          background: darkMode ? "#fff" : "#333",
          color: darkMode ? "#333" : "#fff",
          transition: "all 0.3s ease",
          fontWeight: "600",
          zIndex: 10,
        }}
      >
        {darkMode ? "Light Mode" : "Dark Mode"}
      </button>

      <img
        src="https://tmooty.com/wp-content/uploads/2023/09/download-1-1.png"
        alt="Logo"
        style={{
          position: "absolute",
          top: "18px",
          right: "18px",
          maxWidth: "32vw",
          width: "350px",
          minWidth: "140px",
          height: "auto",
          opacity: 0.9,
        }}
      />

      <h1
        style={{
          marginBottom: "18px",
          fontSize: "2.2rem",
          fontWeight: 700,
          color: darkMode ? "#f7f7f7" : "#333",
          textAlign: "center",
          lineHeight: "1.15",
        }}
      >
        Welcome to <span className="gashtal">Gashtal</span> Image Tagging
      </h1>

      <style jsx>{`
        .gashtal {
          background: linear-gradient(90deg, #6a11cb, #2575fc, #6a11cb);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-size: 200% 100%;
          animation: gradientMove 3s infinite linear;
        }
        @keyframes gradientMove {
          0% {
            background-position: 0% 50%;
          }
          100% {
            background-position: 100% 50%;
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
            font-size: 1.5rem !important;
          }
        }
        @media only screen and (max-width: 600px) {
          h1 {
            font-size: 1.25rem !important;
          }
          img[alt="Logo"] {
            max-width: 120px !important;
            width: 90vw !important;
            right: 10px !important;
            top: 15px !important;
          }
        }
        @media only screen and (max-width: 420px) {
          div,
          form {
            padding: 10px !important;
          }
        }
      `}</style>

      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: "430px",
          margin: "0 auto",
          boxSizing: "border-box",
        }}
      >
        <p
          style={{
            color: darkMode ? "#f7f7f7" : "#333",
            fontSize: "1rem",
            marginBottom: "5px",
          }}
        >
          آدرس تصویر (URL):
        </p>
        <input
          type="text"
          placeholder="...آدرس تصویر خود را اینجا قرار دهید"
          value={imageUrl}
          onChange={(e) => {
            setImageUrl(e.target.value);
            setFile(null);
          }}
          style={{
            width: "100%",
            padding: "10px",
            fontSize: "15px",
            marginBottom: "10px",
            borderRadius: "8px",
            border: "1px solid #999",
            boxSizing: "border-box",
          }}
        />

        <p
          style={{
            color: darkMode ? "#f7f7f7" : "#333",
            fontSize: "1rem",
            marginBottom: "5px",
          }}
        >
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
            padding: "5px 0",
            color: darkMode ? "#f7f7f7" : "#333",
          }}
        />

        <button
          type="submit"
          style={{
            width: "100%",
            padding: "10px",
            fontSize: "1.1rem",
            borderRadius: "12px",
            marginTop: "8px",
            fontWeight: "600",
            color: "#fff",
            background: "linear-gradient(90deg, #6a11cb, #2575fc)",
            border: "none",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.75 : 1,
            transition: "opacity 0.2s",
          }}
          disabled={loading}
        >
          {loading ? "در حال پردازش..." : "نمایش تگ ها"}
        </button>
      </form>

      {progress > 0 && loading && (
        <div
          style={{
            width: "100%",
            maxWidth: "430px",
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
            fontWeight: "bold",
            textAlign: "center",
            padding: "10px",
            background: darkMode ? "rgba(255, 255, 255, 0.1)" : "rgba(255, 0, 0, 0.1)",
            borderRadius: "8px",
            maxWidth: "430px",
          }}
        >
          {error}
        </p>
      )}

      {uploadedImage && (
        <div style={{ marginTop: "18px", textAlign: "center", maxWidth: "700px", width: "100%" }}>
          <img
            src={uploadedImage}
            alt="Uploaded"
            style={{
              maxWidth: "100%",
              maxHeight: "400px",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              objectFit: "contain",
              display: "block",
              margin: "0 auto",
            }}
          />
          {minioImageUrl && (
            <p
              style={{
                marginTop: "10px",
                fontSize: "0.85rem",
                color: darkMode ? "#bbb" : "#666",
                wordBreak: "break-all",
                padding: "0 10px",
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
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "10px",
          }}
        >
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={skeletonCategoryStyle}></div>
          ))}
        </div>
      )}

      {tagGroups.length > 0 && (
        <div
          style={{
            marginTop: "30px",
            width: "100%",
            maxWidth: "700px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
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
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "10px",
                  justifyContent: "flex-start",
                }}
              >
                {(group.مقادیر || group.values || []).map((value, j) => (
                  <span
                    key={j}
                    style={{
                      ...tagStyle,
                      opacity: animateTags ? 1 : 0,
                      transform: animateTags ? "translateY(0)" : "translateY(24px)",
                      transition: `all 0.5s ease ${(i * 0.1) + (j * 0.05)}s`,
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundPosition = "100% 0";
                      e.target.style.transform = "scale(1.13) translateY(0)";
                      e.target.style.boxShadow = "0 6px 16px rgba(0,0,0,0.23)";
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundPosition = "0 0";
                      e.target.style.transform = "scale(1) translateY(0)";
                      e.target.style.boxShadow = "0 2px 6px rgba(0,0,0,0.15)";
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
