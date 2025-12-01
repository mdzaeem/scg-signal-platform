"use client";

import { useEffect, useState } from "react";

type Dataset = {
  dataset_id: string;
  file_name: string;
  person_name?: string;
  flight_code?: string;
  box_name?: string;
};

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
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

        <p className="text-gray-600 mb-4">
          This page lists all uploaded datasets.
        </p>

        {loading ? (
          <div className="text-gray-600">Loading datasets...</div>
        ) : (
          <div className="space-y-4">

            {datasets.map((ds: Dataset) => (
              <div
                key={ds.dataset_id}
                onClick={() => (window.location.href = `/datasets/${ds.dataset_id}`)}
                className="p-4 border rounded-lg shadow cursor-pointer hover:bg-gray-100 transition"
              >

                <p className="font-semibold text-lg text-gray-900">
                    {ds.file_name}
                </p>

                {/* <p className="text-sm text-gray-600 mt-1">
                  <strong>Person:</strong> {ds.person_name} &nbsp;—&nbsp;
                  <strong>Flight:</strong> {ds.flight_code} &nbsp;—&nbsp;
                  <strong>Box:</strong> {ds.box_name}
                </p> */}

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
