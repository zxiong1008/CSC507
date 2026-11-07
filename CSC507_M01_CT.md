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

## Start and connect to the Ubuntu VM from Windows

To start Minikube, wait for the VM, open SSH forwarding in a separate PowerShell window, and connect to an interactive Ubuntu shell in the current window, run this from the project folder in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-linux.ps1
```

Type `exit` to leave the shell; the script then closes the port forward. To run the Linux inventory commands without opening a shell, add `-Inventory` to the command. If doing this manually, use the commands in steps 3 and 4 in separate PowerShell windows.

1. Open PowerShell and start the Kubernetes cluster (Minikube must be installed):

	```powershell
	minikube start
	```

2. Confirm that the Ubuntu VM is running and ready:

	```powershell
	kubectl -n unix-lab get vm,vmi
	```

	The VM is configured to start automatically. Wait for `ubuntu-lab` to show `Running` and `True` before continuing.

3. In a separate PowerShell terminal, start the SSH port forward and leave it running:

```powershell
& "$env:LOCALAPPDATA\Programs\virtctl\virtctl.exe" port-forward vm/ubuntu-lab 2224:22 -n unix-lab
```

4. In another PowerShell terminal, connect using the SSH key:

```powershell
ssh -i "$HOME\.ssh\k8s-debian-mini" -p 2224 student@127.0.0.1
```

After connecting, run the Linux inventory commands above. The VM account is `student`; password login is disabled. Keep the private SSH key private.

## Notes

- These results describe the VM's **virtual hardware**, not the Windows host's physical components.
- The `ubuntu-lab` VM is configured for 1 virtual CPU and 1 GiB requested memory, with an approximately 10 GiB persistent virtual root disk. The usable RAM and root filesystem shown inside Ubuntu are lower because of virtualization, partitions, and filesystem overhead.
- For the paper's screenshots, show each command with its output in a readable terminal capture. Do not include private keys or other credentials.
