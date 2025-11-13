'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Loader2, Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';

interface Chat {
  id: number;
  user_id: string;
  query: string;
  response: string;
  created_at: string;
}

export default function ChatPage() {
  const [input, setInput] = useState('');
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const user_id = 'user_1'; // replace with actual auth user later

  // ✅ Load chat history on mount
  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/api/get-chats/${user_id}`);
      setChats(res.data.chats || []);
    } catch (err: any) {
      console.error('Error loading chats:', err);
      if (err.response?.status === 404) {
        toast.warning('No chat history found yet.');
      } else {
        toast.error('Failed to fetch chats from server.');
      }
    }
  };

  // ✅ Send message to backend + update local UI
  const handleSend = async () => {
    if (!input.trim()) return;
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/api/chat', {
        query: input,
        user_id,
      });

      const newChat = {
        id: Date.now(),
        user_id,
        query: input,
        response: res.data.reply,
        created_at: new Date().toISOString(),
      };

      setChats((prev) => [...prev, newChat]);
      setInput('');
      toast.success('Message sent successfully!');
    } catch (err) {
      console.error('Chat send failed:', err);
      toast.error('Chat failed — check backend.');
    } finally {
      setLoading(false);
    }
  };

  // ✅ Scroll to bottom on new chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chats]);

  // ✅ Delete all chats (optional endpoint)
  const clearChats = async () => {
    if (!confirm('Are you sure you want to clear all chat history?')) return;
    setClearing(true);
    try {
      await axios.delete(`http://localhost:8000/api/clear-chats/${user_id}`);
      setChats([]);
      toast.info('Chat history cleared.');
    } catch (err) {
      console.error('Failed to clear chats:', err);
      toast.error('Failed to delete chat history.');
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="p-6 sm:px-10 sm:py-6 text-white space-y-4">
      <Card className="bg-black/30 backdrop-blur-lg border border-white/10 shadow-xl">
        <CardHeader className="flex items-center justify-between">
          <CardTitle className="text-3xl font-bold text-purple-300">
            Agentic Research Chatbot
          </CardTitle>
          <Button
            onClick={clearChats}
            disabled={clearing}
            variant="outline"
            className="text-red-400 border-red-400 hover:bg-red-600/10"
          >
            {clearing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <div className="flex items-center gap-1">
                <Trash2 className="w-4 h-4" /> Clear All
              </div>
            )}
          </Button>
        </CardHeader>

        <CardContent className="flex flex-col h-[70vh]">
          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 scrollbar-thin scrollbar-thumb-purple-600/50 scrollbar-track-transparent">
            {chats.length === 0 ? (
              <div className="text-center text-gray-400 mt-10">
                💬 Start chatting about your startup report!
              </div>
            ) : (
              chats.map((chat) => (
                <div key={chat.id}>
                  {/* User message */}
                  <div className="text-right mb-2">
                    <div className="inline-block bg-purple-600 text-white rounded-lg px-4 py-2 max-w-[80%] wrap-break-word">
                      {chat.query}
                    </div>
                  </div>

                  {/* Bot message */}
                  <div className="text-left mb-6">
                    <div className="inline-block bg-gray-800 text-gray-200 rounded-lg px-4 py-2 max-w-[80%] wrap-break-word whitespace-pre-wrap">
                      {chat.response}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef}></div>
          </div>

          {/* Input area */}
          <div className="flex items-center gap-3">
            <Input
              placeholder="Ask about your startup report..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="bg-black/40 border-gray-700 text-white flex-1"
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <Button
              onClick={handleSend}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}