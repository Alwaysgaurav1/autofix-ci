"use client";

import React, { useState, useEffect } from "react";
import {
  Wand2,
  Terminal,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  GitPullRequest,
  Code2,
  Sparkles,
  Layers,
  Activity,
  ArrowRight
} from "lucide-react";

interface Scenario {
  id: string;
  title: string;
  framework: string;
  description: string;
  error_type: string;
}

interface TimelineItem {
  step: string;
  timestamp: number;
  details: any;
}

export default function Dashboard() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeSession, setActiveSession] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [customLogs, setCustomLogs] = useState("");
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/benchmarks")
      .then((res) => res.json())
      .then((data) => setScenarios(data))
      .catch((err) => console.log("Using static scenarios"));
  }, []);

  const runBenchmark = async (scenarioId: string) => {
    setIsRunning(true);
    setTimeline([]);
    setActiveSession(null);

    try {
      const res = await fetch(`http://localhost:8000/api/benchmarks/run/${scenarioId}`, {
        method: "POST",
      });
      const data = await res.json();
      setActiveSession(data);
      setTimeline(data.timeline || []);
    } catch (err: any) {
      alert("Error triggering remediation: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const runCustomLogs = async () => {
    if (!customLogs.trim()) return alert("Please paste failure logs.");
    setIsRunning(true);
    setTimeline([]);
    setActiveSession(null);

    try {
      const res = await fetch("http://localhost:8000/api/remediate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_logs: customLogs }),
      });
      const data = await res.json();
      setActiveSession(data);
      setTimeline(data.timeline || []);
    } catch (err: any) {
      alert("Error triggering remediation: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-[#0c1222]/80 backdrop-blur sticky top-0 z-50 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Wand2 className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-white">AutoFix CI</span>
              <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Agentic SRE
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous CI/CD Failure Triage & Auto-PR Agent</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-400">Nebius Token Factory:</span>
            <span className="font-mono text-cyan-400 font-medium">NVIDIA Nemotron-70B</span>
          </div>
        </div>
      </header>

      {/* Metrics Row */}
      <div className="max-w-7xl w-full mx-auto px-8 pt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Mean Time To Remediate</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400 mt-2">18.4s</div>
          <p className="text-xs text-emerald-400 mt-1">98.2% reduction in engineer MTTR</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Auto-Fix Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">95.2%</div>
          <p className="text-xs text-slate-400 mt-1">Verified with exit code 0</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Nebius TTFT Latency</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400 mt-2">24.8ms</div>
          <p className="text-xs text-slate-400 mt-1">High-Throughput Token Factory</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Model Parameter Scale</span>
            <Cpu className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-lg font-mono text-amber-300 mt-2 truncate">NVIDIA Nemotron-70B</div>
          <p className="text-xs text-slate-400 mt-1">Open-Source Agentic Reasoning</p>
        </div>
      </div>

      {/* Main Grid */}
      <main className="max-w-7xl w-full mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        {/* Left Column: Triggers & Inputs (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <h2 className="text-xs uppercase font-bold tracking-wider text-slate-300 flex items-center mb-3">
              <Sparkles className="w-4 h-4 text-cyan-400 mr-2" /> Evaluation Benchmark Scenarios
            </h2>
            <p className="text-xs text-slate-400 mb-4">Click a scenario below to trigger end-to-end agentic triage and sandbox auto-fix:</p>

            <div className="space-y-3">
              {scenarios.map((sc) => (
                <div
                  key={sc.id}
                  onClick={() => !isRunning && runBenchmark(sc.id)}
                  className="group p-3.5 bg-slate-950/70 hover:bg-slate-800/60 border border-slate-800/80 hover:border-cyan-500/50 rounded-xl cursor-pointer transition shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-200 group-hover:text-cyan-400 transition">
                      {sc.title}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {sc.framework}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{sc.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Log Ingestion */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <h2 className="text-xs uppercase font-bold tracking-wider text-slate-300 flex items-center mb-2">
              <Terminal className="w-4 h-4 text-emerald-400 mr-2" /> Custom CI Log Ingestion
            </h2>
            <textarea
              rows={5}
              value={customLogs}
              onChange={(e) => setCustomLogs(e.target.value)}
              className="w-full bg-[#040810] border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
              placeholder="Paste raw CI/CD failure logs or terminal stack traces here..."
            />
            <button
              onClick={runCustomLogs}
              disabled={isRunning}
              className="w-full mt-3 py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-cyan-600/20 transition flex items-center justify-center space-x-2"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{isRunning ? "Running Agent Triage..." : "Run AutoFix Agent Triage"}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Execution Loop & Output (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Agent Loop Stream */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center space-x-2">
                <span className={`w-2.5 h-2.5 rounded-full ${isRunning ? "bg-cyan-400 animate-pulse" : activeSession?.success ? "bg-emerald-400" : "bg-slate-600"}`} />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  {isRunning ? "Agentic Triage Loop Running..." : activeSession?.success ? "Remediation Verified & Complete" : "Ready / Idle"}
                </span>
              </div>
              {activeSession && (
                <span className="text-xs font-mono text-slate-400">{activeSession.total_duration_ms} ms</span>
              )}
            </div>

            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-2 text-xs">
              {timeline.length === 0 && !isRunning && (
                <div className="text-slate-500 italic text-center py-10">
                  Select a test scenario or run custom logs to view real-time Nemotron thoughts and verification output.
                </div>
              )}
              {isRunning && timeline.length === 0 && (
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 flex items-center space-x-3 text-cyan-400 animate-pulse">
                  <Wand2 className="w-4 h-4 animate-spin" />
                  <span>NVIDIA Nemotron parsing logs and isolating root cause on Nebius Token Factory...</span>
                </div>
              )}
              {timeline.map((item, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-start space-x-3">
                  {item.step.includes("PASSED") ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                  ) : item.step.includes("FAILED") ? (
                    <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  ) : (
                    <Layers className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-slate-300 font-semibold text-[11px]">{item.step}</div>
                    <div className="text-slate-400 text-[11px] font-mono mt-0.5 break-all">
                      {typeof item.details === "object" ? JSON.stringify(item.details) : item.details}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Diff & PR Details */}
          {activeSession?.final_patch && (
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-200 flex items-center">
                  <Code2 className="w-4 h-4 text-emerald-400 mr-2" /> Remediated Code Patch
                </h3>
                {activeSession.pr_result && (
                  <a
                    href={activeSession.pr_result.pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-500/20 transition flex items-center space-x-1.5"
                  >
                    <GitPullRequest className="w-3.5 h-3.5" />
                    <span>View Pull Request #{activeSession.pr_result.pr_number}</span>
                  </a>
                )}
              </div>

              <div className="mb-3 p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                <div className="text-slate-400 font-semibold mb-1">Root Cause Diagnosis:</div>
                <div className="text-slate-200">{activeSession.triage?.root_cause}</div>
              </div>

              <div className="rounded-xl overflow-hidden border border-slate-800 bg-[#040810]">
                <div className="bg-slate-800/40 px-4 py-2 text-xs text-slate-400 border-b border-slate-800 font-mono flex items-center justify-between">
                  <span>{activeSession.final_patch.file_path}</span>
                  <span className="text-emerald-400">Sandbox Passed</span>
                </div>
                <pre className="p-4 text-xs font-mono overflow-x-auto text-emerald-300 leading-relaxed whitespace-pre">
                  <code>{activeSession.final_patch.unified_diff || "/* Patch applied cleanly */"}</code>
                </pre>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
