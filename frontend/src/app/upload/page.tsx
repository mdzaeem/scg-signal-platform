"use client";

import { useState } from "react";
import StatsCards from "./StatsCards";
import { useRouter } from "next/navigation";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [refreshFlag, setRefreshFlag] = useState(0);
  const router = useRouter();
  const [datasetsCount, setDatasetsCount] = useState(0);

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://127.0.0.1:8000/api/upload-csv", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        alert("Upload failed: " + err.detail);
        return;
      }

      const json = await res.json();
      setResult(json);
      setRefreshFlag((prev) => prev + 1);

    } catch (error) {
      alert("Network error: " + error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 p-6">
      <div className="bg-white p-8 rounded-xl shadow-xl w-full max-w-xl">

        {/* Stats */}
        <StatsCards
          refreshFlag={refreshFlag}
          onStatsLoaded={(count) => setDatasetsCount(count)}
        />

        {/* View Datasets Button */}
        <button
            onClick={() => {
                if (!loading) {   // Prevent navigation during upload
                if (result) {
                    router.push(`/datasets/${result.dataset_id}`);
                } else if (datasetsCount > 0) {
                    router.push(`/datasets`);
                }
                }
            }}
            disabled={(datasetsCount === 0 && !result) || loading}  // Disable while uploading
            className={`w-full py-3 rounded-lg text-white mb-6 transition ${
                (datasetsCount > 0 || result) && !loading
                ? "bg-black hover:bg-gray-900 cursor-pointer"
                : "bg-gray-400 cursor-not-allowed"
            }`}
            >
            {loading ? "Uploading…" : "View Datasets →"}
        </button>


        {/* Upload Title */}
        <h1 className="text-3xl font-bold mb-6 text-center text-gray-900">
          Upload Dataset
        </h1>

        {/* File Picker */}
        <div
            onClick={() => !loading && document.getElementById("fileInput")?.click()} 
            className={`
                w-full mb-4 p-6 border-2 border-dashed rounded-xl text-gray-600
                transition flex items-center justify-center
                ${
                loading
                    ? "bg-gray-200 border-gray-300 cursor-not-allowed opacity-50"
                    : "border-gray-300 bg-gray-50 hover:border-purple-500 hover:bg-purple-50 cursor-pointer"
                }
            `}
            >
            {file ? (
                <span className="font-medium text-gray-700">{file.name}</span>
            ) : (
                <span>Click to select a file or drag & drop</span>
            )}

            <input
                id="fileInput"
                type="file"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                disabled={loading}
        />
        </div>


        {/* Upload Button */}
        <button
            onClick={!loading ? handleUpload : undefined}
            disabled={loading}
            className={`w-full text-white py-3 rounded-lg transition ${
                loading
                ? "bg-purple-300 cursor-not-allowed"          // disabled look
                : "bg-purple-600 hover:bg-purple-700 cursor-pointer"
            }`}
            >
            {loading ? "Uploading..." : "Upload"}
        </button>



        {/* Upload Summary */}
        {result && (
          <div className="mt-6 p-6 border border-gray-300 rounded-xl bg-white shadow-lg">
            <h2 className="text-2xl font-semibold mb-4 text-gray-800">
              Upload Summary
            </h2>

            <div className="space-y-2 text-gray-700">
              <p><strong>Dataset ID:</strong> {result.dataset_id}</p>
              <p><strong>File Name:</strong> {result.file_name}</p>
              <p><strong>Person:</strong> {result.metadata.person_name}</p>
              <p><strong>Flight:</strong> {result.metadata.flight_code}</p>
              <p><strong>Box:</strong> {result.metadata.box_name}</p>
              <p><strong>Color:</strong> {result.metadata.box_color}</p>
              <p><strong>Rows Inserted:</strong> {result.rows_inserted}</p>
              <p><strong>Duration:</strong> {result.duration_seconds}s</p>
            </div>

            {/* <button
              onClick={() => window.location.href = "/datasets"}
              className="mt-4 w-full py-3 bg-black text-white rounded-lg hover:bg-gray-900"
            >
              View This Dataset →
            </button> */}

            <button
                onClick={() => router.push("/datasets")}
                disabled={loading} // 🔥 Disable only during upload
                className={`mt-4 px-4 py-2 rounded-lg text-white 
                    ${loading 
                    ? "bg-gray-400 cursor-not-allowed" 
                    : "bg-blue-500 hover:bg-blue-600"}
                `}
                >
                {loading ? "Uploading…" : "View Datasets"}
            </button>

          </div>
        )}

      </div>
    </div>
  );
}
