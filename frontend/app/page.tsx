"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DocumentResult } from "@/lib/api";
import UploadPanel from "@/components/UploadPanel";
import RecentDocuments from "@/components/RecentDocuments";
import DocumentResultView from "@/components/DocumentResultView";

export default function HomePage() {
  const [result, setResult] = useState<DocumentResult | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const resultRef = useRef<HTMLElement>(null);

  const handleUploaded = useCallback((doc: DocumentResult) => {
    setResult(doc);
    setRefreshKey((key) => key + 1);
  }, []);

  const handleReset = useCallback(() => setResult(null), []);

  useEffect(() => {
    if (result) {
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  return (
    <div className="space-y-10">
      <section aria-labelledby="upload-heading">
        <h1 id="upload-heading" className="mb-3 text-lg font-semibold text-slate-900">
          Analyze a document
        </h1>
        <UploadPanel onUploaded={handleUploaded} onReset={handleReset} />
      </section>

      {result && (
        <section ref={resultRef} aria-labelledby="result-heading">
          <h2
            id="result-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500"
          >
            Result
          </h2>
          <DocumentResultView doc={result} />
        </section>
      )}

      <RecentDocuments refreshKey={refreshKey} />
    </div>
  );
}
