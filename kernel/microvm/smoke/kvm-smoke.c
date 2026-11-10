/*
 * Prove that the guest kernel can run a nested VM through /dev/kvm.
 *
 * The smallest real KVM user: create a VM with one vCPU and 4 KiB of memory,
 * run 16-bit code that computes 2 + 2 and writes the digit to I/O port
 * 0x3f8, then halts. Passing needs the kernel's KVM, the CPU's
 * virtualization flag from the VMM, and a working VM entry and exit.
 *
 * x86_64 only: the guest code and register layout are x86.
 * Exit status 0 and "KVM_SMOKE_PASS" on success; non-zero otherwise.
 */
#include <err.h>
#include <fcntl.h>
#include <linux/kvm.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>

#define GUEST_ADDR 0x1000
#define SERIAL_PORT 0x3f8

int main(void) {
    /* mov dx,0x3f8; add al,bl; add al,'0'; out dx,al; hlt */
    const uint8_t code[] = {0xba, 0xf8, 0x03, 0x00, 0xd8, 0x04, '0', 0xee, 0xf4};

    int kvm = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    if (kvm < 0) err(1, "open /dev/kvm");
    int api = ioctl(kvm, KVM_GET_API_VERSION, NULL);
    if (api != KVM_API_VERSION) errx(1, "KVM API version %d, expected %d", api, KVM_API_VERSION);

    int vm = ioctl(kvm, KVM_CREATE_VM, 0UL);
    if (vm < 0) err(1, "KVM_CREATE_VM");

    /* One page of guest memory at GUEST_ADDR holds the code. */
    uint8_t *mem = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (mem == MAP_FAILED) err(1, "mmap guest memory");
    memcpy(mem, code, sizeof(code));
    struct kvm_userspace_memory_region region = {
        .slot = 0,
        .guest_phys_addr = GUEST_ADDR,
        .memory_size = 0x1000,
        .userspace_addr = (uint64_t)(uintptr_t)mem,
    };
    if (ioctl(vm, KVM_SET_USER_MEMORY_REGION, &region) < 0) err(1, "KVM_SET_USER_MEMORY_REGION");

    int vcpu = ioctl(vm, KVM_CREATE_VCPU, 0UL);
    if (vcpu < 0) err(1, "KVM_CREATE_VCPU");
    int run_size = ioctl(kvm, KVM_GET_VCPU_MMAP_SIZE, NULL);
    if (run_size <= 0) err(1, "KVM_GET_VCPU_MMAP_SIZE");
    struct kvm_run *run = mmap(NULL, (size_t)run_size, PROT_READ | PROT_WRITE, MAP_SHARED, vcpu, 0);
    if (run == MAP_FAILED) err(1, "mmap kvm_run");

    /* Real mode with a flat code segment, so RIP is the physical address. */
    struct kvm_sregs sregs;
    if (ioctl(vcpu, KVM_GET_SREGS, &sregs) < 0) err(1, "KVM_GET_SREGS");
    sregs.cs.base = 0;
    sregs.cs.selector = 0;
    if (ioctl(vcpu, KVM_SET_SREGS, &sregs) < 0) err(1, "KVM_SET_SREGS");
    struct kvm_regs regs = {.rip = GUEST_ADDR, .rax = 2, .rbx = 2, .rflags = 0x2};
    if (ioctl(vcpu, KVM_SET_REGS, &regs) < 0) err(1, "KVM_SET_REGS");

    /* Run until HLT; check the one byte the guest writes on the way. */
    char result = 0;
    for (;;) {
        if (ioctl(vcpu, KVM_RUN, NULL) < 0) err(1, "KVM_RUN");
        switch (run->exit_reason) {
        case KVM_EXIT_IO:
            if (run->io.direction == KVM_EXIT_IO_OUT && run->io.port == SERIAL_PORT)
                result = *((char *)run + run->io.data_offset);
            break;
        case KVM_EXIT_HLT:
            if (result != '4') errx(1, "nested guest wrote %d, expected '4'", result);
            printf("KVM_SMOKE_PASS api=%d result=%c\n", api, result);
            return 0;
        default:
            errx(1, "unexpected KVM exit reason %u", run->exit_reason);
        }
    }
}
