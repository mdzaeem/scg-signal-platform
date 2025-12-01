"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";


export default function DatasetPage() {
  const params = useParams();
  const id = params.id;   //  Works in Client Components
  const [metaLoading, setMetaLoading] = useState(true);

  const [meta, setMeta] = useState<any>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  //Pagination state
  const [page, setPage] = useState(1);
  const limit = 200;
  const [totalRows, setTotalRows] = useState(0);

  // Fetch metadata + rows
  // useEffect(() => {
  //   if (!id) return;

  //   async function load() {
  //     try {
  //       // 1️⃣ Fetch dataset metadata
  //       const metaRes = await fetch(`http://127.0.0.1:8000/api/datasets/${id}`);
  //       const metaJson = await metaRes.json();
  //       setMeta(metaJson);

  //       // Fetch paginated rows
  //       const offset = (page - 1) * limit;
  //       const rowsRes = await fetch(`http://127.0.0.1:8000/api/dataset-rows/${id}?offset=${offset}&limit=${limit}`);
        
  //       const rowsJson = await rowsRes.json();

  //       setRows(rowsJson.rows || []);
  //       setTotalRows(rowsJson.total_rows || 0);

  //     } catch (err) {
  //       console.error("Dataset load error:", err);
  //     } finally {
  //       setLoading(false);
  //     }
  //   }

  //   load();
  // }, [id,page]);

  useEffect(() => {
  if (!id) return;

  async function loadMeta() {
    try {
      const metaRes = await fetch(`http://127.0.0.1:8000/api/datasets/${id}`);
      const metaJson = await metaRes.json();
      setMeta(metaJson);
    } catch (err) {
      console.error("Metadata load error:", err);
    } finally {
      setMetaLoading(false);   // ← IMPORTANT!
    }
  }

  loadMeta();
}, [id]);  // ONLY ID

useEffect(() => {
  if (!id) return;

  async function loadRows() {
    try {
      setLoading(true);
      const offset = (page - 1) * limit;

      const res = await fetch(
        `http://127.0.0.1:8000/api/dataset-rows/${id}?offset=${offset}&limit=${limit}`
      );

      const json = await res.json();
      setRows(json.rows || []);
      setTotalRows(json.total_rows || 0);

    } catch (err) {
      console.error("Rows load error:", err);
    } finally {
      setLoading(false);  // stop loading rows
    }
  }

  loadRows();
}, [id, page]); // ID + PAGE


  if (!meta) {
    return <div className="text-white text-center mt-20">Loading dataset...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 p-10 text-white">

      {/* Back Button */}
      <button
        onClick={() => window.history.back()}
        className="mb-6 px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600"
      >
        ← Back
      </button>

      {/* Metadata Card */}
      <div className="bg-white text-black p-6 rounded-xl shadow-xl mb-10 max-w-3xl">
        <h1 className="text-3xl font-bold mb-4">Dataset #{id}</h1>

        <p><strong>File Name:</strong> {meta.file_name}</p>
        <p><strong>Person:</strong> {meta.person_name}</p>
        <p><strong>Role:</strong> {meta.role}</p>
        <p><strong>Flight:</strong> {meta.flight_code}</p>
        <p><strong>Box:</strong> {meta.box_name}</p>
        <p><strong>Color:</strong> {meta.box_color}</p>
        <p><strong>File Date:</strong> {meta.file_date}</p>
      </div>

      {/* Rows Table */}
      <h2 className="text-2xl font-bold mb-4">Rows</h2>

      <div className="bg-white text-black p-6 rounded-xl shadow-lg 
                overflow-x-auto overflow-y-auto 
                max-h-[600px]">
        
        <table className="min-w-full text-left">
          <thead>
              <tr>
                <th className="p-2 border-b">Time</th>
                <th className="p-2 border-b">Header</th>
                <th className="p-2 border-b">ax_alpha</th>
                <th className="p-2 border-b">ax_beta</th>
                <th className="p-2 border-b">ax_gamma</th>
                <th className="p-2 border-b">ay_alpha</th>
                <th className="p-2 border-b">ay_beta</th>
                <th className="p-2 border-b">ay_gamma</th>
                <th className="p-2 border-b">az_alpha</th>
                <th className="p-2 border-b">az_beta</th>
                <th className="p-2 border-b">az_gamma</th>
                <th className="p-2 border-b">gx_alpha</th>
                <th className="p-2 border-b">gx_beta</th>
                <th className="p-2 border-b">gx_gamma</th>
                <th className="p-2 border-b">gy_alpha</th>
                <th className="p-2 border-b">gy_beta</th>
                <th className="p-2 border-b">gy_gamma</th>
                <th className="p-2 border-b">gz_alpha</th>
                <th className="p-2 border-b">gz_beta</th>
                <th className="p-2 border-b">gz_gamma</th>
                <th className="p-2 border-b">ECG</th>
                <th className="p-2 border-b">Frame</th>
              </tr>
            </thead>


          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className="border-b">
                <td className="p-2">{row.time}</td>
                <td className="p-2">{row.header}</td>

                <td className="p-2">{row.ax_alpha}</td>
                <td className="p-2">{row.ax_beta}</td>
                <td className="p-2">{row.ax_gamma}</td>

                <td className="p-2">{row.ay_alpha}</td>
                <td className="p-2">{row.ay_beta}</td>
                <td className="p-2">{row.ay_gamma}</td>

                <td className="p-2">{row.az_alpha}</td>
                <td className="p-2">{row.az_beta}</td>
                <td className="p-2">{row.az_gamma}</td>

                <td className="p-2">{row.gx_alpha}</td>
                <td className="p-2">{row.gx_beta}</td>
                <td className="p-2">{row.gx_gamma}</td>

                <td className="p-2">{row.gy_alpha}</td>
                <td className="p-2">{row.gy_beta}</td>
                <td className="p-2">{row.gy_gamma}</td>

                <td className="p-2">{row.gz_alpha}</td>
                <td className="p-2">{row.gz_beta}</td>
                <td className="p-2">{row.gz_gamma}</td>

                <td className="p-2">{row.ecg}</td>
                <td className="p-2">{row.frame_separator}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* PAGINATION BAR */}
      <div className="flex items-center justify-center gap-6 mt-6">

        {/* Previous button */}
        <button
          disabled={page === 1}
          onClick={() => {
            setPage(page - 1);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
          className={`px-4 py-2 rounded-lg ${
            page === 1
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-black text-white hover:bg-gray-800"
          }`}
        >
          ← Previous
        </button>

        {/* Page number */}
        <span className="text-white">
          Page {page} of {Math.ceil(totalRows / limit)}
        </span>

        {/* Next button */}
        <button
          disabled={page >= Math.ceil(totalRows / limit)}
          onClick={() => {
            setPage(page + 1);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
          className={`px-4 py-2 rounded-lg ${
            page >= Math.ceil(totalRows / limit)
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-black text-white hover:bg-gray-800"
          }`}
        >
          Next →
        </button>

      </div>
    </div>
  );
}
