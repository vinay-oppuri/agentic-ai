'use client';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { BrainCircuit, ChevronRight, Search, Zap } from 'lucide-react';
import Link from 'next/link';
import Header from '../components/header';

const HomeView = () => {
  const features = [
    { title: "Market Analysis", desc: "Get a deep understanding of your target market, including size, trends, and customer demographics.", icon: BrainCircuit },
    { title: "Competitor Research", desc: "Identify and analyze your key competitors, their strengths, weaknesses, and market positioning.", icon: Search },
    { title: "Actionable Insights", desc: "Receive clear, data-driven recommendations to inform your product, marketing, and business strategy.", icon: Zap },
  ]

  return (
    <>
      <Header />
      <div className="flex flex-col items-center justify-center min-h-screen">
        <main className="flex-1 justify-center">
          <section className="w-full py-12 md:py-24">
            <div className="container px-4 md:px-6">
              <div className="grid gap-6 md:grid-cols-2 md:items-center">
                <div className="flex flex-col justify-center space-y-4">
                  <div className="space-y-6 py-4">
                    <h1 className="flex flex-col py-2 gap-4 text-4xl md:text-5xl lg:text-[3.5rem] font-bold tracking-tighter bg-clip-text text-transparent bg-linear-to-r from-purple-400 to-pink-600">
                      <span>Unlock Startup Success</span>
                      <span>with AI-Powered</span>
                      <span>Insights</span>
                    </h1>
                    <p className="max-w-[600px] text-muted-foreground md:text-xl">
                      Our intelligent agents provide comprehensive market analysis, competitor research, and actionable insights to give your startup a competitive edge.
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 min-[400px]:flex-row">
                    <Link href="/dashboard">
                      <Button size="lg" className="w-full min-[400px]:w-auto bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-full transition-all duration-300 shadow-lg hover:shadow-purple-500/50">
                        Get Started <ChevronRight size="20" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </section>
          <section id='#features' className="w-full py-10">
            <div className="container px-4 md:px-6">
              <div className="flex flex-col items-center justify-center space-y-4 text-center mb-10">
                <div className="space-y-6">
                  <div className="p-10 text-muted-foreground text-3xl font-bold mb-5">
                    - Key Features -
                  </div>
                  <h2 className="text-2xl font-bold tracking-tighter sm:text-4xl bg-clip-text text-transparent bg-linear-to-r from-purple-400 to-pink-600">
                    Powerful Tools for Startup Growth
                  </h2>
                  <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                    Our platform offers a suite of AI-driven tools to help you
                    validate your ideas, understand your market, and outsmart the
                    competition.
                  </p>
                </div>
              </div>
              <section id="features" className="max-w-6xl w-full mx-auto md:py-8 px-4 sm:px-6 lg:px-8">
                <div className="mx-auto grid max-w-5xl items-center gap-6 lg:grid-cols-3 lg:gap-12">
                  {features.map((feat) => (
                    <Card key={feat.title} className="bg-muted/60 backdrop-blur-lg rounded-lg shadow-lg border-none transition-all duration-300 hover:scale-103 hover:shadow-xl hover:shadow-purple-500/30">
                      <CardContent className="h-60 flex flex-col items-center justify-center text-md gap-4">
                        <feat.icon className="h-10 w-10 text-purple-400" />
                        <h3 className="text-xl font-bold">{feat.title}</h3>
                        <p className="text-center text-muted-foreground">
                          {feat.desc}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </section>
            </div>
          </section>
        </main>
      </div>
    </>
  );
};

export default HomeView;