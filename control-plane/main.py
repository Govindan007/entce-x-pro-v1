import grpc
from concurrent import futures
import time
import os
import json
from dotenv import load_dotenv

import chromadb
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

import telemetry_pb2
import telemetry_pb2_grpc

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_FILE = os.path.join(BASE_DIR, "threat_feed.json")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

class EnterpriseBrain(telemetry_pb2_grpc.ThreatIntelligenceServicer):
    def __init__(self):
        print("[SYSTEM] ENTCE-X AI Control Plane Initialized.")
        
        # 1. Initialize Vector Database
        print("[SYSTEM] Booting Vector Database (ChromaDB)...")
        self.chroma_client = chromadb.PersistentClient(path=DB_DIR)
        
        # Collection A: Short-term User Memory
        self.memory = self.chroma_client.get_or_create_collection(name="threat_history")
        
        # Collection B: The Threat Intelligence Knowledge Base (NEW)
        self.kb = self.chroma_client.get_or_create_collection(name="mitre_attack_kb")
        self._seed_knowledge_base()
        
        # 2. Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
        
        # 3. The RAG-Enhanced Prompt
        self.prompt = PromptTemplate.from_template("""
        You are an elite Cybersecurity AI Agent protecting a Linux server.
        Analyze the command using the user's history and our Threat Intelligence DB.
        
        --- THREAT INTELLIGENCE MATCH (Vector Database) ---
        {threat_intel}
        ---------------------------------------------------
        
        --- RECENT HISTORY FROM THIS IP ---
        {history}
        -----------------------------------
        
        Current Command Executed: {command}
        
        Based on the history and threat intelligence, is this benign, reconnaissance, or a critical attack?
        Respond ONLY with a valid JSON object in this exact format:
        {{"action": "OBSERVE" | "RATE_LIMIT" | "KILL_PROCESS", "reasoning": "A brief 1-sentence explanation"}}
        """)
        
        print(f"[SYSTEM] Brain Online. Writing UI feed to: {FEED_FILE}")
        with open(FEED_FILE, "w") as f:
            json.dump([], f)

    def _seed_knowledge_base(self):
        """Pre-loads the Vector DB with known threat actor semantics"""
        if self.kb.count() == 0:
            print("[SYSTEM] Seeding MITRE ATT&CK Playbooks into Vector DB...")
            self.kb.add(
                documents=[
                    "Reconnaissance: nmap, masscan, or ping sweeps to discover network topology and open ports.",
                    "Execution: reverse shells using nc -e, bash -i, or python pty modules to gain remote access.",
                    "Credential Access: dumping /etc/shadow, accessing id_rsa keys, or looking for AWS credentials.",
                    "Defense Evasion: clearing bash history, stopping auditd, or disabling firewalls via iptables."
                ],
                metadatas=[
                    {"tactic": "Reconnaissance"}, 
                    {"tactic": "Execution"}, 
                    {"tactic": "Credential Access"}, 
                    {"tactic": "Defense Evasion"}
                ],
                ids=["mitre_1", "mitre_2", "mitre_3", "mitre_4"]
            )
            print("[SYSTEM] Knowledge Base Seeded.")

    def StreamEvents(self, request_iterator, context):
        for event in request_iterator:
            print(f"\n[🚨 TELEMETRY] Node: {event.client_id} | CMD: {event.command_line}")
            
            try:
                # --- 1. VECTOR SEARCH (THREAT INTEL) ---
                # We ask ChromaDB: "Does this command semantically look like any known attacks?"
                kb_results = self.kb.query(
                    query_texts=[event.command_line],
                    n_results=1
                )
                
                threat_intel_str = "No specific APT signatures matched."
                # Check the semantic distance (lower is a closer match)
                distance = kb_results['distances'][0][0]
                if distance < 1.5:  # Adjust threshold based on embedding model sensitivity
                    tactic = kb_results['metadatas'][0][0]['tactic']
                    threat_intel_str = f"WARNING: Command shares semantic similarity (Distance: {distance:.2f}) with MITRE Tactic: {tactic}"
                    print(f"[🔎 VECTOR SEARCH] {threat_intel_str}")

                # --- 2. MEMORY RETRIEVAL (HISTORY) ---
                recent_docs = self.memory.get(
                    where={"client_id": event.client_id},
                    limit=5
                )
                history_str = "No prior history."
                if recent_docs and recent_docs['documents']:
                    history_str = "\n".join(recent_docs['documents'])

                # --- 3. AI REASONING (GEMINI) ---
                chain = self.prompt | self.llm
                response = chain.invoke({
                    "threat_intel": threat_intel_str,
                    "history": history_str,
                    "command": event.command_line
                })
                
                clean_text = response.content.replace('```json', '').replace('```', '').strip()
                ai_decision = json.loads(clean_text)
                
                action_str = ai_decision.get("action", "OBSERVE")
                reasoning = ai_decision.get("reasoning", "AI Error.")
                print(f"[🧠 AI REASONING] {reasoning}")
                
                # --- 4. UPDATE MEMORY ---
                self.memory.add(
                    documents=[event.command_line],
                    metadatas=[{"client_id": event.client_id}],
                    ids=[str(time.time())]
                )
                
                # --- 5. UI FEED UPDATE ---
                if action_str == "KILL_PROCESS":
                    final_action = telemetry_pb2.MitigationAction.KILL_PROCESS
                    severity = "CRITICAL"
                elif action_str == "RATE_LIMIT":
                    final_action = telemetry_pb2.MitigationAction.RATE_LIMIT
                    severity = "WARNING"
                else:
                    final_action = telemetry_pb2.MitigationAction.OBSERVE
                    severity = "INFO"
                    
                alert_data = {
                    "id": str(time.time()),
                    "timestamp": time.strftime('%H:%M:%S'),
                    "client": event.client_id,
                    "command": event.command_line,
                    "reasoning": reasoning,
                    "action": action_str,
                    "severity": severity
                }
                
                try:
                    with open(FEED_FILE, "r") as f: feed = json.load(f)
                except: feed = []
                feed.insert(0, alert_data)
                with open(FEED_FILE, "w") as f: json.dump(feed, f, indent=2)

                yield telemetry_pb2.MitigationAction(
                    type=final_action,
                    target=str(event.process_id),
                    reasoning=reasoning,
                    duration_sec=300
                )
                
            except Exception as e:
                print(f"[!] Processing Error: {e}")
                yield telemetry_pb2.MitigationAction(
                    type=telemetry_pb2.MitigationAction.OBSERVE,
                    target=str(event.process_id),
                    reasoning="Fallback action due to error.",
                    duration_sec=0
                )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    telemetry_pb2_grpc.add_ThreatIntelligenceServicer_to_server(EnterpriseBrain(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try: server.wait_for_termination()
    except KeyboardInterrupt: server.stop(0)

if __name__ == '__main__':
    serve()