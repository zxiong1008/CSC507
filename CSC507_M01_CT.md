# CSC507 M01 — Commands Used

This file records the shell commands used to inspect the Ubuntu virtual machine's processor, memory, I/O devices, and storage for the computer-components assignment. Run these commands from a shell **inside the Ubuntu VM**.

## Processor

```sh
lscpu
```

Displays CPU architecture, model, virtual CPU/core/thread counts, and processor features.

## Main memory

```sh
free -h
```

Displays total, used, free, and available RAM, plus swap, in human-readable units.

Optional detailed memory summary:

```sh
head -n 12 /proc/meminfo
```

## I/O modules and controllers

```sh
lspci -nnk
```

Lists virtual PCI/PCIe devices and their kernel drivers, such as network and storage controllers.

```sh
lsusb
lsusb -t
```

Lists attached USB devices and the USB device tree. This VM had no USB devices attached when checked.

```sh
ip -br link
```

Shows concise network interface names and link state.

## Storage devices

```sh
lsblk -o NAME,MODEL,SIZE,TYPE,FSTYPE,MOUNTPOINTS
```

Lists disks, partitions, sizes, filesystems, and mount points.

```sh
df -hT
```

Shows mounted filesystem types, capacity, usage, and available space.

## Connect to the Ubuntu VM from Windows

Start this command in a PowerShell terminal and leave it running; it forwards local port 2224 to Ubuntu's SSH port:

```powershell
& "$env:LOCALAPPDATA\Programs\virtctl\virtctl.exe" port-forward vm/ubuntu-mini 2224:22 -n unix-lab
```

In a second PowerShell terminal, connect using the SSH key:

```powershell
ssh -i "$HOME\.ssh\k8s-debian-mini" -p 2224 student@127.0.0.1
```

After connecting, run the Linux inventory commands above. The VM account is `student`; password login is disabled. Keep the private SSH key private.

## Notes

- These results describe the VM's **virtual hardware**, not the Windows host's physical components.
- The Ubuntu VM is configured for 1 virtual CPU, 512 MiB requested memory, and a 20 GiB persistent virtual root disk. The usable RAM and filesystem capacity shown inside Ubuntu can be lower because of virtualization, partitions, and filesystem overhead.
- For the paper's screenshots, show each command with its output in a readable terminal capture. Do not include private keys or other credentials.
