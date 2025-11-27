"use client";

import { useState } from "react";
import StatsCards from "./StatsCards";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [refreshFlag, setRefreshFlag] = useState(0); // -> state to trigger stats reload
  
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
    setRefreshFlag(prev => prev + 1);   // 👈 triggers stats reload


  } catch (error) {
    alert("Network error: " + error);
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 p-6">
        

      
      <div className="bg-white p-8 rounded-xl shadow-xl w-full max-w-xl">
      {/* 🔥 Show Stats on top */}
      <StatsCards refreshFlag={refreshFlag} />
        <h1 className="text-3xl font-bold mb-6 text-center text-gray-900">Upload Dataset</h1>
         {/* PLANE SIMPLE INPUT */}
        {/* <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="w-full border border-gray-300 p-3 rounded mb-4 text-gray-900"
        /> */}
        {/* DRAG AND DROP AND OTHER STUFF */}
        <div
            className="
                w-full mb-4 p-6 border-2 border-dashed rounded-xl
                border-gray-300 bg-gray-50 text-gray-600
                hover:border-purple-500 hover:bg-purple-50
                transition cursor-pointer
                flex items-center justify-center
            "
            onClick={() => document.getElementById("fileInput")?.click()}
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
        />
        </div>
 
        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>

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

                <button
                    onClick={() => window.location.href = "/datasets"}
                    className="mt-4 w-full py-3 bg-black text-white rounded-lg hover:bg-gray-900"
                >
                    View This Dataset →
                </button>
            </div>
)}


        {/* {result && (
          <div className="mt-6 p-4 border rounded bg-gray-50">
            <h2 className="text-xl font-semibold mb-4">Upload Summary</h2>

            <p><strong>Dataset ID:</strong> {result.dataset_id}</p>
            <p><strong>File:</strong> {result.file_name}</p>
            <p><strong>Person:</strong> {result.metadata.person_name}</p>
            <p><strong>Flight:</strong> {result.metadata.flight_code}</p>
            <p><strong>Box:</strong> {result.metadata.box_name}</p>
            <p><strong>Color:</strong> {result.metadata.box_color}</p>
            <p><strong>Rows Inserted:</strong> {result.rows_inserted}</p>

            <button 
              className="mt-4 w-full py-2 bg-black text-white rounded-lg"
              onClick={() => window.location.href = "/datasets"}
            >
              View This Dataset →
            </button>
          </div>
        )}
      </div>
    </div>
  );
} */}      

        </div>              
    </div>
  );
}
