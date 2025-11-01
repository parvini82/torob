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
  const [mode, setMode] = useState("fast");
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith("image/")) {
      setFile(droppedFile);
      setImageUrl("");
      setUploadedImage(URL.createObjectURL(droppedFile));
    }
  };

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

      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        setUploadedImage(URL.createObjectURL(file));

        let prog = 0;
        const interval = setInterval(() => {
          prog += 5;
          if (prog >= 95) clearInterval(interval);
          setProgress(prog);
        }, 100);

        const uploadUrl = `http://localhost:8000/upload-and-tag?mode=${mode}`;
        res = await fetch(uploadUrl, {
          method: "POST",
          body: formData,
        });

        clearInterval(interval);
      } else if (imageUrl) {
        setUploadedImage(imageUrl);

        res = await fetch("http://localhost:8000/generate-tags", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_url: imageUrl, mode: mode }),
        });
      } else {
        throw new Error("Please select an image URL or upload a file.");
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${res.status}`);
      }

      const data = await res.json();

      if (file && data.image_url) {
        setMinioImageUrl(data.image_url);
      }

      let groups = [];

      if (data.tags && data.tags.entities) {
        groups = data.tags.entities;
      } else if (data.entities) {
        groups = data.entities;
      } else if (data.tags && data.tags["ویژگی‌ها"]) {
        groups = data.tags["ویژگی‌ها"];
      } else if (data["ویژگی‌ها"]) {
        groups = data["ویژگی‌ها"];
      }

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
      : "rgba(245, 245, 245, 0.95)",
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
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
        padding: "20px",
        background: darkMode
          ? "linear-gradient(135deg, #2c3e50 0%, #34495e 100%)"
          : "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
        position: "relative",
        transition: "background 0.6s ease",
        overflow: "hidden",
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

      <div
        style={{
          flexShrink: 0,
          width: "100%",
        }}
      >
        <h1
          style={{
            marginBottom: "15px",
            marginTop: "20px",
            fontSize: "clamp(1.3rem, 4vw, 2rem)",
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

        <div
          style={{
            width: "100%",
            maxWidth: "600px",
            margin: "0 auto 15px",
            padding: "0 20px",
          }}
        >
          <p
            style={{
              color: "#fff",
              fontSize: "1.1rem",
              marginBottom: "10px",
              fontWeight: "600",
              textAlign: "center",
              textShadow: "0 1px 3px rgba(0,0,0,0.2)",
            }}
          >
            Please select your model first
          </p>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            style={{
              width: "100%",
              padding: "14px 18px",
              fontSize: "1.05rem",
              borderRadius: "12px",
              border: "3px solid rgba(255,255,255,0.4)",
              boxSizing: "border-box",
              background: darkMode ? "rgba(255,255,255,0.95)" : "#e0e0e0",
              color: darkMode ? "#2c3e50" : "#2c3e50",
              transition: "all 0.3s ease",
              outline: "none",
              cursor: "pointer",
              fontWeight: "600",
              boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "#6a11cb";
              e.target.style.boxShadow = "0 0 0 4px rgba(106,17,203,0.15)";
              e.target.style.transform = "scale(1.02)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "rgba(255,255,255,0.4)";
              e.target.style.boxShadow = "0 4px 15px rgba(0,0,0,0.2)";
              e.target.style.transform = "scale(1)";
            }}
          >
            <option value="fast">⚡ Fast (Fastest processing)</option>
            <option value="reasoning">🧠 Reasoning (Better accuracy)</option>
            <option value="advanced_reasoning">🚀 Advanced Reasoning (Best quality with SerpAPI)</option>
          </select>
        </div>
      </div>

      <div
        style={{
          flex: "1",
          display: "flex",
          flexDirection: "row",
          overflow: "hidden",
          width: "100%",
          maxWidth: "1600px",
          margin: "0 auto",
          padding: "0 20px",
          gap: "20px",
        }}
      >
        <div
          style={{
            flex: "0 0 auto",
            minWidth: "400px",
            maxWidth: "500px",
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
          }}
        >
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              width: "100%",
              height: "550px",
              border: isDragging
                ? "3px dashed #6a11cb"
                : "3px dashed rgba(0,0,0,0.2)",
              borderRadius: "12px",
              background: isDragging
                ? "rgba(106,17,203,0.1)"
                : darkMode
                  ? "rgba(255,255,255,0.05)"
                  : "#f0f0f0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.3s ease",
              position: "relative",
            }}
          >
            {uploadedImage ? (
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <img
                  src={uploadedImage}
                  alt="Uploaded"
                  style={{
                    maxWidth: "100%",
                    maxHeight: "100%",
                    width: "auto",
                    height: "auto",
                    borderRadius: "8px",
                    boxShadow: "0 8px 30px rgba(0,0,0,0.3)",
                    objectFit: "contain",
                    display: "block",
                  }}
                />
                {minioImageUrl && (
                  <p
                    style={{
                      marginTop: "8px",
                      fontSize: "0.75rem",
                      color: darkMode ? "#bbb" : "#2c3e50",
                      wordBreak: "break-all",
                      padding: "0 15px",
                      fontWeight: "500",
                    }}
                  >
                    📁 Saved image: {minioImageUrl}
                  </p>
                )}
              </div>
            ) : loading ? (
              <div
                style={{
                  color: "#fff",
                  fontSize: "1.2rem",
                  textAlign: "center",
                }}
              >
                ⏳ Processing...
              </div>
            ) : (
              <div
                style={{
                  color: darkMode ? "#fff" : "#2c3e50",
                  fontSize: "1.1rem",
                  textAlign: "center",
                  padding: "20px",
                  opacity: 0.7,
                }}
              >
                {isDragging ? (
                  <>
                    <div style={{ fontSize: "3rem", marginBottom: "10px" }}>
                      📤
                    </div>
                    <div>Drop image here</div>
                  </>
                ) : (
                  <>
                    <div style={{ fontSize: "3rem", marginBottom: "10px" }}>
                      🖼️
                    </div>
                    <div>Drag & drop image here</div>
                    <div style={{ fontSize: "0.9rem", marginTop: "10px" }}>
                      or use upload below
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        <div
          style={{
            flex: "1",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "flex-start",
            maxHeight: "550px",
            overflowY: "auto",
            overflowX: "hidden",
            padding: "0 15px",
          }}
        >
          {tagGroups.length > 0 && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                width: "100%",
                maxWidth: "400px",
              }}
            >
              {tagGroups.map((group, i) => (
                <div
                  key={i}
                  style={{
                    ...categoryStyle,
                    width: "100%",
                    opacity: animateTags ? 1 : 0,
                    transform: animateTags
                      ? "translateY(0)"
                      : "translateY(30px)",
                    transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${i * 0.12
                      }s`,
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
                      gap: "6px",
                      justifyContent: "flex-start",
                    }}
                  >
                    {(group.مقادیر || group.values || []).map((value, j) => (
                      <span
                        key={j}
                        style={{
                          ...tagStyle,
                          padding: "8px 14px",
                          fontSize: "0.85rem",
                          opacity: animateTags ? 1 : 0,
                          transform: animateTags
                            ? "translateY(0)"
                            : "translateY(20px)",
                          transition: `all 0.5s cubic-bezier(0.4, 0, 0.2, 1) ${i * 0.12 + j * 0.05
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

        <div
          style={{
            flex: "0 0 auto",
            minWidth: "450px",
            maxWidth: "550px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-start",
            alignItems: "center",
          }}
        >
          <form
            onSubmit={handleSubmit}
            style={{
              width: "100%",
              boxSizing: "border-box",
              background: darkMode
                ? "rgba(255, 255, 255, 0.05)"
                : "#f0f0f0",
              padding: "30px",
              borderRadius: "16px",
              backdropFilter: "blur(10px)",
              boxShadow: "0 8px 32px rgba(0,0,0,0.15)",
              minHeight: "550px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <p
              style={{
                color: darkMode ? "#fff" : "#2c3e50",
                fontSize: "1.05rem",
                marginBottom: "10px",
                fontWeight: "600",
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
                border: "2px solid rgba(0,0,0,0.2)",
                boxSizing: "border-box",
                background: "#e0e0e0",
                color: "#2c3e50",
                transition: "all 0.3s ease",
                outline: "none",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "#6a11cb";
                e.target.style.boxShadow = "0 0 0 3px rgba(106,17,203,0.1)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "rgba(0,0,0,0.2)";
                e.target.style.boxShadow = "none";
              }}
            />

            <p
              style={{
                color: darkMode ? "#fff" : "#2c3e50",
                fontSize: "1.05rem",
                marginBottom: "10px",
                fontWeight: "600",
              }}
            >
              Or upload an image file:
            </p>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-upload-input").click()}
              style={{
                width: "100%",
                marginBottom: "15px",
                padding: "20px",
                color: darkMode ? "#fff" : "#2c3e50",
                background: isDragging
                  ? "rgba(106,17,203,0.2)"
                  : "#e0e0e0",
                borderRadius: "10px",
                border: isDragging
                  ? "2px dashed #6a11cb"
                  : "2px dashed rgba(0,0,0,0.3)",
                cursor: "pointer",
                fontSize: "0.95rem",
                textAlign: "center",
                transition: "all 0.3s ease",
                position: "relative",
              }}
            >
              {isDragging ? (
                <div>📤 Drop image here</div>
              ) : (
                <>
                  <div style={{ marginBottom: "8px" }}>📁</div>
                  <div>Click to upload or drag & drop</div>
                </>
              )}
              <input
                id="file-upload-input"
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const selectedFile = e.target.files[0];
                  if (selectedFile) {
                    setFile(selectedFile);
                    setImageUrl("");
                    setUploadedImage(URL.createObjectURL(selectedFile));
                  }
                }}
                style={{
                  position: "absolute",
                  opacity: 0,
                  width: "100%",
                  height: "100%",
                  cursor: "pointer",
                  top: 0,
                  left: 0,
                }}
              />
            </div>

            <button
              type="submit"
              style={{
                width: "100%",
                padding: "14px",
                fontSize: "1.1rem",
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
                marginTop: "12px",
                background: "rgba(0,0,0,0.1)",
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
                marginTop: "12px",
                fontWeight: "700",
                textAlign: "center",
                padding: "12px 16px",
                background: "rgba(231, 76, 60, 0.9)",
                borderRadius: "12px",
                boxShadow: "0 4px 15px rgba(231, 76, 60, 0.4)",
                fontSize: "0.9rem",
              }}
            >
              ⚠️ {error}
            </p>
          )}

          {loading && !uploadedImage && (
            <div
              style={{
                width: "100%",
                marginTop: "15px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "10px",
              }}
            >
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} style={skeletonCategoryStyle}></div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
