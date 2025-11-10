'use client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BrainCircuit, Search, Zap } from 'lucide-react';

const agents = [
  {
    name: 'Market Analysis Agent',
    description: 'Provides a deep understanding of your target market.',
    icon: <BrainCircuit className="h-8 w-8 text-primary" />,
  },
  {
    name: 'Competitor Research Agent',
    description: 'Identifies and analyzes your key competitors.',
    icon: <Search className="h-8 w-8 text-primary" />,
  },
  {
    name: 'Actionable Insights Agent',
    description: 'Delivers clear, data-driven recommendations.',
    icon: <Zap className="h-8 w-8 text-primary" />,
  },
];

const AgentsPage = () => {
  return (
    <div className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8">
      <Card>
        <CardHeader>
          <CardTitle>Meet Your Intelligent Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <Card key={agent.name}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {agent.name}
                  </CardTitle>
                  {agent.icon}
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    {agent.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AgentsPage;
