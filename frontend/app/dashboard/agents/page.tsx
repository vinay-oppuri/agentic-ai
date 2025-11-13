'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { ArrowDown, Bot, Network, FileText, Layers, BookText, Brain, MessageSquare } from 'lucide-react';

const pipelineStages = [
  {
    id: 1,
    title: '1. Intent Parser',
    icon: <Brain className="w-8 h-8 text-purple-400" />,
    description:
      'Understands your startup idea and extracts its core intent — what the project is about, key goals, and problem statement. Uses Gemini API (KEY_1).',
  },
  {
    id: 2,
    title: '2. Dynamic Task Planner',
    icon: <Layers className="w-8 h-8 text-purple-400" />,
    description:
      'Breaks the intent into a set of executable research tasks. It decides which agents (TrendScraper, CompetitorScout, etc.) need to work. Uses Gemini API (KEY_2).',
  },
  {
    id: 3,
    title: '3. Multi-Agent Orchestrator',
    icon: <Network className="w-8 h-8 text-purple-400" />,
    description:
      'Assigns tasks to intelligent agents like TrendScraper or CompetitorScout. Each agent gathers and summarizes information independently. Uses Gemini API (KEY_3).',
  },
  {
    id: 4,
    title: '4. RAG Indexer',
    icon: <BookText className="w-8 h-8 text-purple-400" />,
    description:
      'Builds a vector database from all collected documents and summaries using embeddings. Enables contextual knowledge retrieval for future stages. Uses Gemini Embedding API (KEY_4).',
  },
  {
    id: 5,
    title: '5. Strategy Engine',
    icon: <Bot className="w-8 h-8 text-purple-400" />,
    description:
      'Synthesizes findings from the agents and RAG to generate strategic insights and business recommendations. Uses Gemini API (KEY_5).',
  },
  {
    id: 6,
    title: '6. Report Builder',
    icon: <FileText className="w-8 h-8 text-purple-400" />,
    description:
      'Creates structured reports — JSON for your dashboard and Markdown for detailed insights. Saves results to /data/memory_store/.',
  },
  {
    id: 7,
    title: '7. Strategic Knowledge Indexer',
    icon: <BookText className="w-8 h-8 text-purple-400" />,
    description:
      'Indexes key strategy reports and agent outputs for reuse in future queries, improving intelligence over time.',
  },
  {
    id: 8,
    title: '8. Chatbot Interface',
    icon: <MessageSquare className="w-8 h-8 text-purple-400" />,
    description:
      'A context-aware chatbot that can answer user questions based on indexed knowledge — powered by RAG retrieval.',
  },
];

export default function AgentsPipelinePage() {
  return (
    <div className="p-6 sm:px-10 sm:py-8 text-white space-y-10">
      <h1 className="text-4xl font-extrabold bg-linear-to-r from-purple-400 to-pink-300 bg-clip-text text-transparent text-center mb-8">
        Agentic Research Pipeline Overview
      </h1>

      <div className="flex flex-col items-center space-y-6">
        {pipelineStages.map((stage, index) => (
          <div key={stage.id} className="w-full md:w-4/5">
            <Card className="bg-black/30 backdrop-blur-lg border border-white/10 rounded-2xl shadow-lg hover:border-purple-500/40 transition">
              <CardHeader className="flex items-center gap-4">
                {stage.icon}
                <div>
                  <CardTitle className="text-2xl font-semibold">{stage.title}</CardTitle>
                  <CardDescription className="text-gray-400 text-base mt-1">
                    {stage.description}
                  </CardDescription>
                </div>
              </CardHeader>
            </Card>

            {index < pipelineStages.length - 1 && (
              <div className="flex justify-center mt-4 mb-4">
                <ArrowDown className="w-6 h-6 text-purple-400 animate-bounce" />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="text-center text-gray-400 mt-10 text-sm">
        <p>This visualization represents how your AI-driven multi-agent research system executes a startup analysis pipeline.</p>
        <p className="mt-1">Each step uses a separate Gemini API key to distribute load and prevent quota exhaustion.</p>
      </div>
    </div>
  );
}
