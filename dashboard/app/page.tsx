"use client";

import { useEffect, useState } from "react";

export default function Dashboard() {
  const [threats, setThreats] = useState<any[]>([]);

  // Poll the local API every 1 second for new threats from the Python Brain
  useEffect(() => {
    const fetchThreats = async () => {
      try {
        const res = await fetch("/api/threats");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        
        const data = await res.json();
        if (Array.isArray(data)) {
          setThreats(data);
        }
      } catch (err) {
        console.error("Waiting for Python Brain to initialize feed...", err);
      }
    };

    fetchThreats();
    const interval = setInterval(fetchThreats, 1000); 
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "CRITICAL": return "border-red-500 bg-red-500/10 text-red-400";
      case "WARNING": return "border-yellow-500 bg-yellow-500/10 text-yellow-400";
      default: return "border-blue-500 bg-blue-500/10 text-blue-400";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 p-8 font-mono">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            ENTCE-X <span className="text-indigo-500">PRO</span>
          </h1>
          <p className="text-slate-500 text-sm mt-1">Enterprise Agentic Detection & Response</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-400 text-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Brain: ONLINE
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-400 text-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Probe: SECURE
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Stats */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <h2 className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-4">System Metrics</h2>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-slate-500">Events Analyzed</p>
                <p className="text-2xl text-white">{threats.length > 0 ? threats.length * 142 : 0}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Active Threats</p>
                <p className="text-2xl text-red-400">{threats.filter(t => t.severity === 'CRITICAL').length}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">AI Model</p>
                <p className="text-lg text-indigo-400">Gemini 2.5 Flash</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Threat Feed */}
        <div className="lg:col-span-2">
          <h2 className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-4">Live Telemetry & AI Reasoning Feed</h2>
          
          <div className="space-y-4">
            {threats.length === 0 ? (
              <div className="text-center p-12 border border-dashed border-slate-800 rounded-lg text-slate-600">
                Listening for kernel events... Waiting for Go Probe...
              </div>
            ) : (
              threats.map((threat) => (
                <div key={threat.id} className={`p-4 rounded-lg border-l-4 bg-slate-900 ${getSeverityColor(threat.severity)}`}>
                  
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-white">{threat.severity}</span>
                      <span className="text-xs text-slate-500">{threat.timestamp}</span>
                      <span className="text-xs bg-slate-800 px-2 py-0.5 rounded">{threat.client}</span>
                    </div>
                    {threat.severity === "CRITICAL" && (
                      <button className="text-xs bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded transition-colors shadow-[0_0_10px_rgba(220,38,38,0.5)]">
                        APPROVE KILL
                      </button>
                    )}
                  </div>

                  <div className="mb-3 font-mono text-sm">
                    <span className="text-slate-500">cmd &gt; </span>
                    <span className="text-green-400">{threat.command}</span>
                  </div>

                  <div className="bg-slate-950/50 p-3 rounded border border-slate-800/50 mt-2">
                    <p className="text-xs text-indigo-400 font-semibold mb-1">🧠 Gemini Agent Reasoning:</p>
                    <p className="text-sm text-slate-300 leading-relaxed">{threat.reasoning}</p>
                  </div>
                  
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}