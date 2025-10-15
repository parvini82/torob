import { useState } from "react";

export default function UploadPage() {
  const [imageUrl, setImageUrl] = useState("");
  const [tags, setTags] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!imageUrl) return;
    setLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiBase}/generate-tags`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl }),
      });
      const data = await response.json();
      setTags(data);
    } catch (error) {
      console.error("Error uploading image:", error);
      setTags({ error: "Something went wrong" });
    }

    setLoading(false);
  };

  return (
    <div
      className="min-h-screen w-full flex flex-col items-center justify-start relative"
      style={{
        backgroundImage:
          "url('https://hamravesh.com/blog/wp-content/uploads/2023/03/rahnema_1_22.jpg')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Overlay برای کمرنگ شدن تصویر */}
      <div className="absolute inset-0 bg-black opacity-30"></div>

      {/* عنوان بالا - مرکز */}
      <h1 className="relative z-10 text-3xl md:text-4xl font-bold mt-8 text-center text-white w-full flex justify-center">
        Welcome to Gashtal Image Tagger
      </h1>

      {/* کارت اصلی */}
      <div className="relative z-10 mt-8 p-6 bg-white bg-opacity-90 rounded-xl shadow-2xl w-full max-w-6xl flex flex-col lg:flex-row gap-6">
        {/* ورودی آدرس تصویر و ارسال - سمت چپ */}
        <div className="flex flex-col items-center w-full lg:w-1/3">
          <input
            type="url"
            placeholder="https://example.com/image.jpg"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            className="w-full mb-3 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <button
            onClick={handleSubmit}
            disabled={loading || !imageUrl}
            className={`w-full py-2 px-4 rounded text-white font-semibold ${
              loading || !imageUrl
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Generating..." : "Generate Tags"}
          </button>
        </div>

        {/* جدول نمایش تگ‌ها - سمت راست */}
        <div className="flex-1 w-full lg:w-2/3 overflow-x-auto">
          {tags && (
  <>
    {tags.error ? (
      <p className="text-red-600 font-semibold">{tags.error}</p>
    ) : (
      (() => {
        // your backend returns direct key-value pairs (no nested object)
        const tagEntries = Object.entries(tags);

        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            {tagEntries.map(([key, value]) => (
              <div
                key={key}
                className="bg-white bg-opacity-90 rounded-lg shadow p-4 border border-gray-200 hover:bg-gray-50 transition"
              >
                <h3 className="text-gray-700 font-semibold text-sm uppercase mb-1">
                  {key}
                </h3>
                <p className="text-gray-900 text-base">{String(value)}</p>
              </div>
            ))}
          </div>
        );
      })()
    )}
  </>
)}

        </div>
      </div>
    </div>
  );
}
