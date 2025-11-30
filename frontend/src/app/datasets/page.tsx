"use client";

import { useEffect, useState } from "react";


export default function DatasetsPage() {

    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
    fetch("http://127.0.0.1:8000/api/datasets")
      .then((res) => res.json())
      .then((data) => {
        setDatasets(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 p-8 flex justify-center">
      <div className="bg-white w-full max-w-4xl rounded-xl shadow-xl p-8">

        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Datasets
        </h1>

        <p className="text-gray-600">
          This page will display all uploaded datasets.  
          (Phase 3 will fetch actual data from the backend.)
        </p>

        {loading && (
            <div className="text-gray-600">Loading datasets...</div>
        )}


        {!loading && datasets.length === 0 && (
            <div className="bg-gray-100 p-4 rounded-lg text-gray-600">
                No datasets found. Upload a dataset first.
            </div>
            )}

        {!loading && datasets.length > 0 && (
            <div className="space-y-4">
                {datasets.map((ds) => (
                <div
                    key={ds.dataset_id}
                    onClick={() => window.location.href = `/datasets/${ds.dataset_id}`}
                    className="p-4 border rounded-lg shadow cursor-pointer hover:bg-gray-100 transition"
                >
                    <p className="font-bold text-lg">{ds.file_name}</p>

                    <p className="text-sm text-gray-600">
                    Person: {ds.person_name} — Flight: {ds.flight_code} — Box: {ds.box_name}
                    </p>
                </div>
                ))}
            </div>
            )}




        <button
          className="mt-6 bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800"
          onClick={() => window.location.href = "/upload"}
        >
          ← Back to Upload
        </button>

      </div>
    </div>
  );
}
