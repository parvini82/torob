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
    fontSize: "1rem",
    margin: "5px 4px",
    minWidth: "65px",
    textAlign: "center",
    flex: "0 0 auto",
  };

  const skeletonStyle = {
    width: "70px",
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
          top: "18px",
          left: "18px",
          padding: "8px 16px",
          borderRadius: "20px",
          border: "none",
          cursor: "pointer",
          background: darkMode ? "#fff" : "#333",
          color: darkMode ? "#333" : "#fff",
          transition: "all 0.3s ease",
          fontWeight: "600"
        }}
      >
        {darkMode ? "Light Mode" : "Dark Mode"}
      </button>

      <img
        src="https://rahnemacollege.com/blog/wp-content/uploads/2023/02/rc-logo.png"
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

      <h1 style={{
        marginBottom: "18px",
        fontSize: "2.2rem",
        fontWeight: 700,
        color: darkMode ? "#f7f7f7" : "#333",
        textAlign: "center",
        lineHeight: "1.15"
      }}>
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
          0% { background-position: 0% 50%; }
          100% { background-position: 100% 50%; }
        }
        @keyframes loading {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @media only screen and (max-width: 600px) {
          h1 {
            font-size: 1.25rem !important;
          }
          img[alt="Logo"] {
            max-width: 120px !important;
            width:90vw !important;
            right: 10px !important;
            top: 15px !important;
          }
        }
        @media only screen and (max-width: 420px) {
          div, form {
            padding: 0px !important;
          }
        }
      `}</style>

      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: "430px",
          margin: "0 auto",
          boxSizing: "border-box"
        }}
      >
        <p style={{
          color: darkMode ? "#f7f7f7" : "#333",
          fontSize: "1rem"
        }}>
          :آدرس تصویر (URL)
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

        <p style={{
          color: darkMode ? "#f7f7f7" : "#333",
          fontSize: "1rem"
        }}>
          :یا فایل تصویر از سیستم خود انتخاب کنید
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
          }}
        >
          <div style={progressBarStyle}></div>
        </div>
      )}

      {error && (
        <p style={{
          color: "crimson",
          marginTop: "10px",
          fontWeight: "bold",
          textAlign: "center",
        }}>
          {error}
        </p>
      )}

      {uploadedImage && (
        <img
          src={uploadedImage}
          alt="Uploaded"
          style={{
            marginTop: "18px",
            maxWidth: "430px",
            width: "100vw",
            borderRadius: "8px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            display: "block"
          }}
        />
      )}

      {loading && !file && (
        <div
          style={{
            marginTop: "16px",
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
            justifyContent: "center",
            width: "100%",
            maxWidth: "430px",
            minHeight: "32px"
          }}
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={skeletonStyle}></div>
          ))}
        </div>
      )}

      {tags.length > 0 && (
        <div
          style={{
            marginTop: "18px",
            display: "flex",
            flexWrap: "wrap",
            gap: "10px",
            justifyContent: "center",
            width: "100%",
            maxWidth: "430px",
          }}
        >
          {tags.map((tag, i) => (
            <span
              key={i}
              style={{
                ...tagStyle,
                opacity: animateTags ? 1 : 0,
                transform: animateTags
                  ? "translateY(0)"
                  : "translateY(24px)",
                transition: `all 0.5s ease ${i * 0.07}s`,
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundPosition = "100% 0";
                e.target.style.transform =
                  "scale(1.13) translateY(0)";
                e.target.style.boxShadow =
                  "0 6px 16px rgba(0,0,0,0.23)";
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundPosition = "0 0";
                e.target.style.transform =
                  "scale(1) translateY(0)";
                e.target.style.boxShadow =
                  "0 2px 6px rgba(0,0,0,0.15)";
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
