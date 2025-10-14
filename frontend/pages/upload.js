import { useState } from "react";

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [tags, setTags] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setTags(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      const response = await fetch("http://localhost:8000/predict/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setTags(data.tags);
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
        {/* پیش‌نمایش تصویر و آپلود - سمت چپ */}
        <div className="flex flex-col items-center w-full lg:w-1/3">
          {/* پیش‌نمایش تصویر */}
          {selectedFile && (
            <img
              src={URL.createObjectURL(selectedFile)}
              alt="Preview"
              className="mb-4 w-48 h-48 object-contain rounded border border-gray-300 shadow-md"
            />
          )}

          {/* Input و دکمه */}
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="w-full mb-3 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <button
            onClick={handleUpload}
            disabled={loading || !selectedFile}
            className={`w-full py-2 px-4 rounded text-white font-semibold ${
              loading || !selectedFile
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {/* جدول نمایش تگ‌ها - سمت راست */}
        <div className="flex-1 w-full lg:w-2/3 overflow-x-auto">
          {tags && (
            <>
              {tags.error ? (
                <p className="text-red-600 font-semibold">{tags.error}</p>
              ) : (
                <table className="min-w-full border-collapse border border-gray-400">
                  <thead className="bg-blue-100">
                    <tr>
                      <th className="px-4 py-2 border border-gray-400">Language</th>
                      <th className="px-4 py-2 border border-gray-400">Brand</th>
                      <th className="px-4 py-2 border border-gray-400">Team</th>
                      <th className="px-4 py-2 border border-gray-400">Sponsor</th>
                      <th className="px-4 py-2 border border-gray-400">Color</th>
                      <th className="px-4 py-2 border border-gray-400">Type</th>
                      <th className="px-4 py-2 border border-gray-400">Details</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white">
                    <tr className="bg-green-50 hover:bg-green-100">
                      <td className="px-4 py-2 border border-gray-400">English</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.english.brand}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.english.team}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.english.sponsor}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.english.color}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.english.type}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.english.details}</td>
                    </tr>
                    <tr className="bg-yellow-50 hover:bg-yellow-100">
                      <td className="px-4 py-2 border border-gray-400">Persian</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.persian.برند}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.persian.تیم}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.persian.اسپانسر}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.persian.رنگ}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.persian.نوع}</td>
                      <td className="px-4 py-2 border border-gray-400">{tags.persian.جزئیات}</td>
                    </tr>
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
