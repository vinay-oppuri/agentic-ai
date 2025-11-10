"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { Loader2 } from "lucide-react";

interface ResearchReport {
  id: string;
  idea: string;
  marketAnalysis: string;
  competitorAnalysis: string;
  keyInsights: string;
  generatedAt: string;
  userId: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);

  useEffect(() => {
    async function fetchReports() {
      try {
        const res = await axios.get("/api/reports");
        setReports(res.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchReports();
  }, []);

  if (loading)
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="animate-spin w-8 h-8 text-gray-500" />
      </div>
    );

  if (reports.length === 0)
    return (
      <div className="text-center mt-20 text-gray-600 dark:text-gray-400 text-lg">
        No research reports found yet.
      </div>
    );

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-16 text-center bg-linear-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
        Your Research Reports
      </h1>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report, idx) => (
          <motion.div
            key={report.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="group p-6 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-md hover:shadow-xl cursor-pointer transition"
            onClick={() => setSelectedReport(report)}
          >
            <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100 group-hover:text-indigo-500 transition">
              {report.idea}
            </h2>
            <p className="text-sm text-gray-500 mb-3">
              Generated on {new Date(report.generatedAt).toLocaleDateString()}
            </p>
            <p className="text-gray-700 dark:text-gray-300 line-clamp-3">
              {report.keyInsights.length > 100
                ? report.keyInsights.slice(0, 100) + "..."
                : report.keyInsights}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Popup Dialog */}
      <AnimatePresence>
        {selectedReport && (
          <Dialog open={!!selectedReport} onOpenChange={() => setSelectedReport(null)}>
            <DialogContent className="min-w-4xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-center text-indigo-600">
                  {selectedReport.idea}
                </DialogTitle>
                <DialogDescription className="text-center text-muted-foreground text-sm">
                  Generated on{" "}
                  {new Date(selectedReport.generatedAt).toLocaleString()}
                </DialogDescription>
              </DialogHeader>

              <Accordion type="single" collapsible defaultValue="market" className="flex flex-col w-full mt-4 gap-3">
                <AccordionItem
                  value="market"
                  className="border border-gray-200 dark:border-gray-700 rounded-xl px-4"
                >
                  <AccordionTrigger className="text-lg font-medium">
                    Market Analysis
                  </AccordionTrigger>
                  <AccordionContent className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                    {selectedReport.marketAnalysis}
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem
                  value="competitor"
                  className="border border-gray-200 dark:border-gray-700 rounded-xl px-4"
                >
                  <AccordionTrigger className="text-lg font-medium">
                    Competitor Analysis
                  </AccordionTrigger>
                  <AccordionContent className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                    {selectedReport.competitorAnalysis}
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem
                  value="insights"
                  className="border border-gray-200 dark:border-gray-700 rounded-xl px-4"
                >
                  <AccordionTrigger className="text-lg font-medium">
                    Key Insights
                  </AccordionTrigger>
                  <AccordionContent className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                    {selectedReport.keyInsights}
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>
    </div>
  );
}