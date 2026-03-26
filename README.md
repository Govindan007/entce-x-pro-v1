ENTCE-X PRO: Agentic Detection & Response (ADR)

ENTCE-X PRO is a next-generation, AI-native Endpoint Detection and Response (EDR) platform. It leverages Linux Kernel eBPF hooks, high-performance gRPC streaming, and Generative AI (Google Gemini) with Vector Memory (ChromaDB) to detect and mitigate sophisticated cyber attacks in real-time.

🏗️ System Architecture

The platform consists of three decoupled layers:

The Sentinel (Go + eBPF): A C program injected into the Linux Kernel that intercepts sys_enter_execve syscalls. It streams raw telemetry to the control plane via a bi-directional gRPC pipe.

The Brain (Python + LangChain + Gemini): An Agentic Control Plane that performs:

Semantic Search: Matches commands against a MITRE ATT&CK Knowledge Base using ChromaDB.

Reasoning: Uses Google Gemini to analyze the intent and history of a user.

Decision: Issues instant KILL_PROCESS or RATE_LIMIT commands back to the edge.

The SOC Dashboard (Next.js + Tailwind): A professional Security Operations Center interface providing live telemetry, AI reasoning logs, and "Human-in-the-Loop" mitigation buttons.

🛠️ Tech Stack

Systems: C (eBPF), Go (1.21+)

AI/ML: Google Gemini 2.5 Flash, LangChain, ChromaDB (Vector DB)

Communication: gRPC (Protocol Buffers)

Frontend: Next.js 14, TypeScript, Tailwind CSS

Environment: Ubuntu Linux (WSL2 supported)

🚀 Getting Started

Prerequisites

LLVM/Clang (for eBPF compilation)

Go, Python 3.10+, Node.js 20+

Google Gemini API Key

Installation & Setup

Clone and Install Dependencies:

# Install Go tools
go install [github.com/cilium/ebpf/cmd/bpf2go@latest](https://github.com/cilium/ebpf/cmd/bpf2go@latest)

# Install Python dependencies
pip install langchain-google-genai chromadb python-dotenv grpcio-tools

# Install Dashboard
cd dashboard && npm install


Environment Configuration:
Create a .env file in the root:

GEMINI_API_KEY=your_key_here


Compile the Kernel Hook:

cd probe
go generate
go build -o probe_bin


Running the Platform

Open three terminals:

Terminal 1 (Brain): python3 control-plane/main.py

Terminal 2 (Dashboard): cd dashboard && npm run dev

Terminal 3 (Probe): sudo ./probe/probe_bin

🛡️ Live Simulation

Run the included attack.sh script to witness a multi-stage APT attack simulation. Watch as the AI connects the dots between reconnaissance and execution, eventually triggering a critical alert and process termination on the dashboard.

./attack.sh


📜 License

MIT License - Developed by Govi as a Professional Agentic Cybersecurity Project.