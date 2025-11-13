'use client';

import { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Brain,
  BarChart3,
  Compass,
  Lightbulb,
  Info,
  Loader2,
  Bot,
} from 'lucide-react';

interface Report {
  id: number;
  idea: string;
  result_json: any;
  report_md: string;
  created_at: string;
}

export default function DashboardView() {
  const [idea, setIdea] = useState('');
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);

  // ✅ Run pipeline and show the generated report
  const runPipeline = async () => {
    if (!idea.trim()) return alert('Enter your startup idea first!');
    setLoading(true);
    try {
      // Step 1: Call FastAPI pipeline
      const res = await axios.post('http://localhost:8000/api/run', { query: idea });
      const result = res.data.result;

      // Step 2: Get report markdown file
      const mdRes = await fetch('/report.md');
      const reportMd = await mdRes.text();

      // Step 3: Save results in Neon DB
      await axios.post('/api/save-report', {
        idea,
        resultJson: result,
        reportMd,
      });

      // Step 4: Fetch the latest report only
      const latest = await axios.get('/api/get-latest-report');
      setReport(latest.data);

      alert('✅ Report generated and saved successfully!');
    } catch (err) {
      console.error('Pipeline error:', err);
      alert('❌ Pipeline failed — check backend.');
    } finally {
      setLoading(false);
    }
  };

  if (loading)
    return (
      <div className="flex justify-center items-center h-screen text-gray-400 text-lg">
        <Loader2 className="animate-spin w-6 h-6 mr-2 text-purple-400" />
        Generating Startup Report...
      </div>
    );

  if (!report)
    return (
      <div className="flex-1 p-6 sm:px-10 sm:py-6 text-white space-y-6">
        <Card className="bg-black/30 backdrop-blur-lg border border-white/10 rounded-xl shadow-xl">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-purple-300">
              Generate New Report
            </CardTitle>
            <CardDescription className="text-gray-400">
              Enter your startup idea and run the full Agentic pipeline.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="Enter your startup idea..."
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              className="bg-black/40 border-gray-700 text-white flex-1"
            />
            <Button
              onClick={runPipeline}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6"
            >
              Run Pipeline
            </Button>
          </CardContent>
        </Card>
      </div>
    );

  // ✅ Render the latest generated report in full detail
  const data = report.result_json;
  const { strategy, agent_groups, raw_docs_count, markdown_path } = data;

  return (
    <div className="flex-1 p-6 sm:px-10 sm:py-6 text-white space-y-6">
      <Card className="bg-black/30 backdrop-blur-lg border border-white/10 rounded-xl shadow-xl">
        <CardHeader>
          <CardTitle className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-purple-400 to-pink-300 bg-clip-text text-transparent">
            {report.idea}
          </CardTitle>
          <CardDescription className="text-gray-400 text-sm">
            Generated on: {new Date(report.created_at).toLocaleString()}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Accordion type="multiple" className="text-white space-y-3">
            {/* EXECUTIVE SUMMARY */}
            <AccordionItem value="executive-summary">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <Info className="w-5 h-5 mr-2 text-purple-400" /> Executive Summary
              </AccordionTrigger>
              <AccordionContent>
                <p className="text-gray-300 leading-relaxed whitespace-pre-wrap pl-4 border-l-4 border-purple-600">
                  {strategy.executive_summary}
                </p>
              </AccordionContent>
            </AccordionItem>

            {/* KEY FINDINGS */}
            <AccordionItem value="key-findings">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <Lightbulb className="w-5 h-5 mr-2 text-yellow-400" /> Key Findings
              </AccordionTrigger>
              <AccordionContent>
                <ul className="space-y-2 pl-4">
                  {strategy.key_findings.map((f: string, i: number) => (
                    <li key={i} className="flex gap-2 items-start">
                      <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>

            {/* MARKET OPPORTUNITIES */}
            <AccordionItem value="market-opportunities">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <TrendingUp className="w-5 h-5 mr-2 text-blue-400" /> Market Opportunities
              </AccordionTrigger>
              <AccordionContent>
                <ul className="space-y-4">
                  {strategy.market_opportunities.map((op: any, idx: number) => (
                    <li
                      key={idx}
                      className="border-l-4 border-purple-600 pl-4 bg-black/20 rounded-lg p-3"
                    >
                      <p className="font-semibold text-lg text-gray-100 flex items-center gap-2">
                        <Compass className="w-5 h-5 text-purple-400" /> {op.opportunity}
                      </p>
                      <p className="text-sm text-gray-400 mb-2">
                        Impact: <span className="text-purple-400">{op.impact}</span>
                      </p>
                      <ul className="list-disc list-inside text-gray-400 ml-2 space-y-1">
                        {op.evidence.map((e: string, i: number) => (
                          <li key={i}>{e}</li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>

            {/* RISKS */}
            <AccordionItem value="risks">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <AlertTriangle className="w-5 h-5 mr-2 text-red-400" /> Risks & Challenges
              </AccordionTrigger>
              <AccordionContent>
                <ul className="space-y-2 pl-4">
                  {strategy.risks_and_challenges.map((r: string, i: number) => (
                    <li key={i} className="flex gap-2 items-start">
                      <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>

            {/* RECOMMENDATIONS */}
            <AccordionItem value="recommendations">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <Brain className="w-5 h-5 mr-2 text-pink-400" /> Strategic Recommendations
              </AccordionTrigger>
              <AccordionContent>
                {strategy.strategic_recommendations.map((rec: any, i: number) => (
                  <div
                    key={i}
                    className="border-l-4 border-green-600 pl-4 bg-black/20 p-3 rounded-lg mb-3"
                  >
                    <p className="font-semibold text-gray-100 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-400" /> {rec.area}
                    </p>
                    <p className="text-gray-300 text-sm mt-1">{rec.action}</p>
                    <p className="text-sm text-gray-400 mt-1">
                      Priority: <span className="text-green-400">{rec.priority}</span> | Owner:{' '}
                      <span className="text-blue-400">{rec.owner}</span>
                    </p>
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>

            {/* KPIs */}
            <AccordionItem value="kpis">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <BarChart3 className="w-5 h-5 mr-2 text-purple-400" /> Suggested KPIs
              </AccordionTrigger>
              <AccordionContent>
                <ul className="space-y-3 pl-2">
                  {strategy.suggested_kpis.map((kpi: any, idx: number) => (
                    <li
                      key={idx}
                      className="bg-black/20 p-3 rounded-lg border border-gray-800"
                    >
                      <p className="font-semibold text-purple-300 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-purple-400" /> {kpi.name}
                      </p>
                      <p className="text-sm text-gray-400">
                        🎯 Target: {kpi.target}
                      </p>
                      <p className="text-gray-300 text-sm">{kpi.rationale}</p>
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>

            {/* ROADMAP */}
            <AccordionItem value="roadmap">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <Compass className="w-5 h-5 mr-2 text-purple-400" /> Implementation Roadmap
              </AccordionTrigger>
              <AccordionContent>
                {Object.entries(strategy.roadmap).map(([phase, steps]: [string, any]) => (
                  <div key={phase} className="mb-5">
                    <h3 className="text-xl font-bold text-purple-400 mb-2 capitalize flex items-center gap-2">
                      <Compass className="w-5 h-5 text-purple-400" /> {phase.replace('_', ' ')}
                    </h3>
                    <ul className="space-y-1 ml-3">
                      {steps.map((s: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 text-green-400 mt-[3px]" />
                          <span className="text-gray-300">{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>

            {/* AGENT INSIGHTS */}
            <AccordionItem value="agent-insights">
              <AccordionTrigger className="text-2xl font-bold hover:text-purple-300">
                <Bot className="w-5 h-5 mr-2 text-cyan-400" /> Detailed Agent Insights
              </AccordionTrigger>
              <AccordionContent>
                {Object.entries(agent_groups).map(([agent, content]: [string, any], idx) => (
                  <div key={idx} className="mb-10">
                    <h3 className="text-2xl font-semibold text-blue-400 mb-3 flex items-center gap-2">
                      <Bot className="w-5 h-5 text-blue-400" /> {agent}
                    </h3>

                    {Array.isArray(content) &&
                      content.map((section: any, i: number) => (
                        <div
                          key={i}
                          className="border-l-4 border-gray-700 pl-4 mb-3"
                        >
                          {typeof section === 'string' ? (
                            <div className="prose prose-invert max-w-none bg-black/10 p-6 rounded-lg leading-relaxed text-gray-300">
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  h1: ({ node, ...props }) => (
                                    <h1 className="text-3xl font-extrabold text-purple-300 mb-3 mt-4" {...props} />
                                  ),
                                  h2: ({ node, ...props }) => (
                                    <h2 className="text-2xl font-bold text-purple-400 mb-2 mt-3" {...props} />
                                  ),
                                  p: ({ node, ...props }) => (
                                    <p className="text-gray-300 text-base mb-3" {...props} />
                                  ),
                                  li: ({ node, ...props }) => (
                                    <li className="text-gray-400 text-base leading-relaxed" {...props} />
                                  ),
                                }}
                              >
                                {section}
                              </ReactMarkdown>
                            </div>
                          ) : null}
                        </div>
                      ))}
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* Footer */}
          <div className="text-gray-500 text-sm mt-10 border-t border-white/10 pt-3">
            Raw Docs Indexed: {raw_docs_count} | Markdown Path: {markdown_path}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}