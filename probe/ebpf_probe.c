//go:build ignore

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

// Define the exact data structure we want to send to the Go Probe
struct event_t {
    __u32 pid;
    char filename[128];
};

// Create a high-speed "Ring Buffer" to stream data from Kernel to User-space
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24); // 16MB buffer
} events SEC(".maps");

// The layout of the sys_enter_execve tracepoint in memory
struct execve_args {
    __u64 pad;
    __u32 __syscall_nr;
    __u32 pad2;
    const char *filename;
};

// Attach to the execve tracepoint (When a process starts)
SEC("tracepoint/syscalls/sys_enter_execve")
int bpf_prog(struct execve_args *ctx) {
    struct event_t *event;

    // Reserve memory in the ring buffer
    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
    if (!event) {
        return 0; // Buffer full, drop event
    }

    // Get the Process ID
    event->pid = bpf_get_current_pid_tgid() >> 32;
    
    // Safely copy the command/filename from user memory into our kernel event
    bpf_probe_read_user_str(&event->filename, sizeof(event->filename), ctx->filename);

    // Send the event up to the Go program instantly
    bpf_ringbuf_submit(event, 0);
    return 0;
}

// Required for the Linux Kernel to load the program
char __license[] SEC("license") = "Dual MIT/GPL";