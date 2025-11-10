'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import axios from 'axios';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { toast } from 'sonner';

interface Report {
  idea: string;
  marketAnalysis: string | object;
  competitorAnalysis: string | object;
  keyInsights: string | object;
  generatedAt: string;
}

export default function DashboardView() {
  const [idea, setIdea] = useState('');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('latestReport');
      if (raw) setReport(JSON.parse(raw));
    } catch (e) {
      console.warn('Failed to load report:', e);
      toast.error('Failed to load a previous report from your local storage.');
    }
  }, []);

  const handleSubmit = async () => {
    if (!idea.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post('/api/research', { idea });
      const data = res.data;
      localStorage.setItem('latestReport', JSON.stringify(data));
      setReport(data);
      toast.success('Report generated successfully!');
    } catch (err) {
      console.error('Error generating insights:', err);
      toast.error('Failed to generate insights. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 p-4 sm:px-6 sm:py-0 md:gap-8 grid grid-cols-1 md:grid-cols-10 text-white">
      <div className="md:col-span-4">
        <Card className="w-full bg-black/20 backdrop-blur-lg border border-white/10 rounded-lg shadow-lg">
          <CardHeader>
            <CardTitle className="text-3xl font-bold">Startup Insight Report</CardTitle>
            <CardDescription className="text-gray-400">
              Enter your startup idea to generate a detailed report with market
              analysis and competitor insights.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center">
              <Input
                placeholder="Enter your startup idea (e.g., AI-based pet care)"
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                className="w-full max-w-lg mb-4 bg-transparent border-white/30 placeholder:text-gray-500"
              />
              <Button
                onClick={handleSubmit}
                disabled={loading || !idea.trim()}
                className="mb-6 bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-full transition-all duration-300 shadow-lg hover:shadow-purple-500/50 transform hover:scale-105"
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="md:col-span-6">
        {report && (
          <Card className="w-full bg-black/20 backdrop-blur-lg border border-white/10 rounded-lg shadow-lg">
            <CardHeader>
              <CardTitle className="text-3xl font-bold">Report for: {report.idea}</CardTitle>
              <CardDescription className="text-gray-400">
                Generated at: {' '}
                {report.generatedAt
                  ? new Date(report.generatedAt).toLocaleString()
                  : 'Unknown'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion
                type="single"
                collapsible
                defaultValue="market-analysis"
                className="text-white"
              >
                <AccordionItem value="market-analysis">
                  <AccordionTrigger className="text-xl font-bold hover:text-purple-300 transition-colors duration-300">
                    Market Analysis
                  </AccordionTrigger>
                  <AccordionContent>
                    <pre className="whitespace-pre-wrap bg-transparent p-3 rounded-md text-sm text-gray-300">
                      {typeof report.marketAnalysis === 'string'
                        ? report.marketAnalysis
                        : JSON.stringify(report.marketAnalysis, null, 2)}
                    </pre>
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="competitor-analysis">
                  <AccordionTrigger className="text-xl font-bold hover:text-purple-300 transition-colors duration-300">
                    Competitor Analysis
                  </AccordionTrigger>
                  <AccordionContent>
                    <pre className="whitespace-pre-wrap bg-transparent p-3 rounded-md text-sm text-gray-300">
                      {typeof report.competitorAnalysis === 'string'
                        ? report.competitorAnalysis
                        : JSON.stringify(report.competitorAnalysis, null, 2)}
                    </pre>
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="key-insights">
                  <AccordionTrigger className="text-xl font-bold hover:text-purple-300 transition-colors duration-300">
                    Key Insights
                  </AccordionTrigger>
                  <AccordionContent>
                    <pre className="whitespace-pre-wrap bg-transparent p-3 rounded-md text-sm text-gray-300">
                      {typeof report.keyInsights === 'string'
                        ? report.keyInsights
                        : JSON.stringify(report.keyInsights, null, 2)}
                    </pre>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
