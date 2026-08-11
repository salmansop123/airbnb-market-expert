"use client";

import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";

type Property = { id: string; title: string };
type ChatResponse = {
  conversation_id: string;
  messages: { id: string; role: string; content: string }[];
};

function ChatInner() {
  const search = useSearchParams();
  const initial = search.get("property") || "";
  const [propertyId, setPropertyId] = useState(initial);
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);

  const properties = useQuery({
    queryKey: ["properties"],
    queryFn: () => api<Property[]>("/v1/properties"),
  });

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!propertyId || !message.trim()) return;
    const res = await api<ChatResponse>(`/v1/properties/${propertyId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    setConversationId(res.conversation_id);
    setMessages(res.messages);
    setMessage("");
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl">AI Chat</h1>
      <p className="mt-2 text-slate">Ask questions about pricing, comps, and improvements.</p>
      <select
        className="mt-6 w-full rounded-lg border bg-sand px-3 py-2"
        value={propertyId}
        onChange={(e) => {
          setPropertyId(e.target.value);
          setConversationId(null);
          setMessages([]);
        }}
      >
        <option value="">Select property</option>
        {(properties.data || []).map((p) => (
          <option key={p.id} value={p.id}>
            {p.title}
          </option>
        ))}
      </select>
      <div className="mt-6 min-h-[320px] space-y-3 rounded-2xl bg-sand p-6">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-xl px-4 py-3 text-sm ${
              m.role === "user" ? "ml-8 bg-mist" : "mr-8 bg-ink text-sand"
            }`}
          >
            {m.content}
          </div>
        ))}
        {!messages.length && <p className="text-sm text-slate">Start a conversation…</p>}
      </div>
      <form onSubmit={send} className="mt-4 flex gap-2">
        <input
          className="flex-1 rounded-full border px-4 py-2"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Why is my suggested price higher than comps?"
        />
        <button className="rounded-full bg-pine px-5 py-2 text-sand">Send</button>
      </form>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatInner />
    </Suspense>
  );
}
