"use client";
import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch("/result.json")
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error("Error loading JSON:", err));
  }, []);

  if (!data) return <div className="p-8 text-gray-600">Loading result.json...</div>;

  const strategy = data.strategy;
  const agentGroups = data.agent_groups || {};

  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-blue-700">📊 Agentic AI Final Report Viewer</h1>
      <p className="text-sm text-gray-500">Generated at: {data.generated_at}</p>

      {/* Executive Summary */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">📘 Executive Summary</h2>
        <p className="text-gray-700 mt-2">{strategy.executive_summary}</p>
      </section>

      {/* Key Findings */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">🔍 Key Findings</h2>
        <ul className="list-disc list-inside text-gray-700 mt-2">
          {strategy.key_findings.map((f: string, idx: number) => (
            <li key={idx}>{f}</li>
          ))}
        </ul>
      </section>

      {/* Market Opportunities */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">💡 Market Opportunities</h2>
        {strategy.market_opportunities.map((op: any, idx: number) => (
          <div key={idx} className="border-l-4 border-blue-400 pl-3 my-2">
            <p className="font-medium text-gray-800">{op.opportunity}</p>
            <p className="text-sm text-gray-500">Impact: {op.impact}</p>
            <ul className="list-disc list-inside text-gray-600 mt-1">
              {op.evidence.map((e: string, i: number) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* Risks and Challenges */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">⚠️ Risks and Challenges</h2>
        <ul className="list-disc list-inside text-gray-700 mt-2">
          {strategy.risks_and_challenges.map((r: string, idx: number) => (
            <li key={idx}>{r}</li>
          ))}
        </ul>
      </section>

      {/* Strategic Recommendations */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">🎯 Strategic Recommendations</h2>
        {strategy.strategic_recommendations.map((rec: any, idx: number) => (
          <div key={idx} className="border-l-4 border-green-500 pl-3 my-2">
            <p className="font-medium">{rec.area}</p>
            <p className="text-gray-700">{rec.action}</p>
            <p className="text-sm text-gray-500">Priority: {rec.priority} | Owner: {rec.owner}</p>
          </div>
        ))}
      </section>

      {/* Suggested KPIs */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">📈 Suggested KPIs</h2>
        <table className="w-full border mt-2 text-sm">
          <thead className="bg-blue-100">
            <tr>
              <th className="border p-2 text-left">Name</th>
              <th className="border p-2 text-left">Target</th>
              <th className="border p-2 text-left">Rationale</th>
            </tr>
          </thead>
          <tbody>
            {strategy.suggested_kpis.map((kpi: any, idx: number) => (
              <tr key={idx} className="odd:bg-white even:bg-gray-50">
                <td className="border p-2 font-medium">{kpi.name}</td>
                <td className="border p-2">{kpi.target}</td>
                <td className="border p-2">{kpi.rationale}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Roadmap */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">🗺️ Roadmap</h2>
        {Object.entries(strategy.roadmap).map(([phase, steps]: [string, any]) => (
          <div key={phase} className="mt-3">
            <h3 className="font-semibold capitalize text-blue-700">{phase.replace("_", " ")}:</h3>
            <ul className="list-disc list-inside text-gray-700">
              {steps.map((s: string, idx: number) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* Supporting References */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">🔗 Supporting References</h2>
        <ul className="list-disc list-inside text-blue-700 mt-2">
          {strategy.supporting_references.map((ref: string, idx: number) => (
            <li key={idx}>
              {ref.startsWith("http") ? (
                <a href={ref} target="_blank" rel="noreferrer" className="underline">
                  {ref}
                </a>
              ) : (
                ref
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Agent Groups */}
      <section className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold text-blue-600">🤖 Agent Groups</h2>
        {Object.entries(agentGroups).map(([agentName, content]: [string, any], idx) => (
          <div key={idx} className="mt-4">
            <h3 className="text-lg font-semibold text-gray-800">{agentName}</h3>
            {Array.isArray(content)
              ? content.map((section: any, i: number) => (
                  <div key={i} className="mt-2 border-l-4 border-gray-300 pl-3">
                    {Array.isArray(section)
                      ? section.map((item: any, j: number) => (
                          <div key={j} className="my-2">
                            {item.trend_name && (
                              <p className="font-medium text-blue-700">{item.trend_name}</p>
                            )}
                            {item.name && (
                              <p className="font-medium text-blue-700">{item.name}</p>
                            )}
                            {item.short_summary && (
                              <p className="text-gray-700">{item.short_summary}</p>
                            )}
                            {item.summary && (
                              <p className="text-gray-700">{item.summary}</p>
                            )}
                          </div>
                        ))
                      : typeof section === "string" && (
                          <pre className="text-sm bg-gray-50 p-2 rounded whitespace-pre-wrap">
                            {section}
                          </pre>
                        )}
                  </div>
                ))
              : null}
          </div>
        ))}
      </section>

      {/* Footer */}
      <footer className="text-center text-gray-500 text-sm mt-8">
        Raw docs count: {data.raw_docs_count} | Markdown path: {data.markdown_path}
      </footer>
    </div>
  );
}