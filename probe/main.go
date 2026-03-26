package main

// This magic comment tells Go to compile our C code into Go bytecode!
//go:generate go run github.com/cilium/ebpf/cmd/bpf2go bpf ebpf_probe.c

import (
	"bytes"
	"context"
	"encoding/binary"
	"log"
	"strings"
	"time"

	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
	"github.com/cilium/ebpf/rlimit"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "github.com/entce-x/probe/proto"
)

// This must match the struct in our C code
type bpfEvent struct {
	Pid      uint32
	Filename [128]byte
}

func main() {
	log.Println("[*] ENTCE-X Kernel Probe Initializing...")

	// 1. Remove memory limits so the kernel can load our eBPF program
	if err := rlimit.RemoveMemlock(); err != nil {
		log.Fatalf("Failed to remove memlock: %v", err)
	}

	// 2. Load the compiled eBPF objects into the Kernel
	objs := bpfObjects{}
	if err := loadBpfObjects(&objs, nil); err != nil {
		log.Fatalf("Failed to load eBPF objects (did you run go generate?): %v", err)
	}
	defer objs.Close()

	// 3. Attach our C program to the 'execve' tracepoint
	tp, err := link.Tracepoint("syscalls", "sys_enter_execve", objs.BpfProg, nil)
	if err != nil {
		log.Fatalf("Failed to attach tracepoint: %v", err)
	}
	defer tp.Close()
	log.Println("[+] eBPF Hook Injected into Kernel successfully.")

	// 4. Connect to the Python Brain
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to connect to Brain: %v", err)
	}
	defer conn.Close()
	
	client := pb.NewThreatIntelligenceClient(conn)
	stream, err := client.StreamEvents(context.Background())
	if err != nil {
		log.Fatalf("Stream error: %v", err)
	}
	log.Println("[+] Secure gRPC Stream Established. Watching live system calls...")

	// 5. Open the Ring Buffer to receive data from the Kernel
	rd, err := ringbuf.NewReader(objs.Events)
	if err != nil {
		log.Fatalf("Failed to open ring buffer: %v", err)
	}
	defer rd.Close()

	// 6. Listen forever
	for {
		record, err := rd.Read()
		if err != nil {
			log.Printf("Read error: %v", err)
			continue
		}

		// Parse the raw binary data from C into our Go struct
		var event bpfEvent
		if err := binary.Read(bytes.NewBuffer(record.RawSample), binary.LittleEndian, &event); err != nil {
			continue
		}

		// Convert C string to Go string (cut off empty null bytes)
		filename := string(bytes.TrimRight(event.Filename[:], "\x00"))

		// Ignore background noise (WSL runs a lot of background tasks)
		if strings.Contains(filename, "vscode") || strings.Contains(filename, "node") {
			continue 
		}

		log.Printf("\n[🚨 KERNEL EVENT CATCH] Process Executed: %s (PID: %d)", filename, event.Pid)

		// Send to the AI Brain!
		rpcEvent := &pb.SecurityEvent{
			ClientId:    "client-wsl-victim-01",
			Timestamp:   time.Now().Format(time.RFC3339),
			EventType:   "PROCESS_EXEC",
			CommandLine: filename,
			SourceIp:    "127.0.0.1",
			ProcessId:   int32(event.Pid),
		}
		
		if err := stream.Send(rpcEvent); err != nil {
			log.Printf("Send error: %v", err)
		}
	}
}