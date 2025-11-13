'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Loader2, FileText, X, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Report {
  id: number;
  idea: string;
  report_md: string;
  created_at: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Report | null>(null);

  // ✅ Fetch all reports from Neon DB
  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/get-reports');
        setReports(res.data);
      } catch (err) {
        console.error('❌ Error loading reports:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

   useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelected(null);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  // ✅ Markdown Rendering Styles
  const markdownComponents = {
    h1: ({ node, ...props }: any) => (
      <h1
        className="text-4xl font-extrabold mt-10 mb-6 text-purple-300 border-b border-purple-800/30 pb-2"
        {...props}
      />
    ),
    h2: ({ node, ...props }: any) => (
      <h2
        className="text-3xl font-bold mt-8 mb-4 text-purple-400 border-b border-purple-800/20 pb-1"
        {...props}
      />
    ),
    h3: ({ node, ...props }: any) => (
      <h3
        className="text-2xl font-semibold mt-6 mb-3 text-pink-300"
        {...props}
      />
    ),
    p: ({ node, ...props }: any) => (
      <p className="text-gray-300 text-base mb-4 leading-relaxed" {...props} />
    ),
    ul: ({ node, ordered, ...props }: any) => (
      <ul
        className="list-disc ml-6 space-y-2 marker:text-purple-400"
        {...props}
      />
    ),
    ol: ({ node, ...props }: any) => (
      <ol
        className="list-decimal ml-6 space-y-2 marker:text-pink-400"
        {...props}
      />
    ),
    li: ({ node, ...props }: any) => (
      <li className="text-gray-300 leading-relaxed" {...props} />
    ),
    a: ({ node, ...props }: any) => (
      <a
        className="text-blue-400 underline hover:text-blue-300 transition-colors"
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      />
    ),
    blockquote: ({ node, ...props }: any) => (
      <blockquote
        className="border-l-4 border-purple-600 pl-4 italic text-gray-400 my-4"
        {...props}
      />
    ),
    code: ({ node, inline, ...props }: any) =>
      inline ? (
        <code
          className="bg-gray-800 text-purple-300 px-1.5 py-0.5 rounded text-sm font-mono"
          {...props}
        />
      ) : (
        <pre
          className="bg-gray-900 text-purple-200 p-3 rounded-lg overflow-x-auto my-4 font-mono text-sm"
          {...props}
        />
      ),
  };

  // ✅ Loading State
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen text-gray-400 text-lg font-medium">
        <Loader2 className="animate-spin w-6 h-6 mr-2 text-purple-400" />
        Loading Reports...
      </div>
    );
  }

  return (
    <div className="p-6 sm:px-10 sm:py-8 text-white space-y-8">
      <Card className="bg-black/30 backdrop-blur-lg border border-white/10 rounded-2xl shadow-2xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-purple-400" />
              <CardTitle className="text-3xl font-extrabold bg-linear-to-r from-purple-400 to-pink-300 bg-clip-text text-transparent">
                Saved Reports
              </CardTitle>
            </div>
            <span className="text-gray-400 text-sm">
              Total: {reports.length}
            </span>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {reports.length === 0 ? (
            <p className="text-gray-400 text-center">No reports found.</p>
          ) : (
            reports.map((r) => (
              <div
                key={r.id}
                className="flex justify-between items-center bg-black/20 border border-white/10 p-4 rounded-lg hover:bg-purple-900/10 transition-all"
              >
                <div>
                  <h3 className="text-lg font-semibold text-purple-300">
                    {r.idea}
                  </h3>
                  <p className="text-sm text-gray-400 flex items-center gap-1 mt-1">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    {new Date(r.created_at).toLocaleString()}
                  </p>
                </div>
                <Button
                  onClick={() => setSelected(r)}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold"
                >
                  View Report
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Modal Popup for Full Report */}
      {selected && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-center items-center p-6">
          <div className="relative bg-gray-900 border border-white/10 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-6">
            {/* Close Button */}
            <button
              onClick={() => setSelected(null)}
              className="absolute top-3 right-3 text-gray-400 hover:text-white transition"
            >
              <X className="w-6 h-6" />
            </button>

            {/* Header */}
            <div className="mb-4">
              <h2 className="text-3xl font-bold text-purple-300 mb-1">
                {selected.idea}
              </h2>
              <p className="text-sm text-gray-400">
                Generated on: {new Date(selected.created_at).toLocaleString()}
              </p>
            </div>

            {/* Markdown Content */}
            <div className="prose prose-invert max-w-none leading-relaxed text-gray-300">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {selected.report_md || '*No content available.*'}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}