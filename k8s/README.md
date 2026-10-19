# Ubuntu VM on Kubernetes (KubeVirt)

This directory stores configuration and assignment notes for a small Ubuntu 24.04 VM running on KubeVirt: 1 vCPU, 512 MiB RAM, and a 20 GiB persistent root disk. The VM is named `ubuntu-mini` in namespace `unix-lab`.

## Prerequisites

- A Kubernetes cluster with KubeVirt and CDI installed and healthy.
- A worker node with hardware virtualization/KVM available (or KubeVirt software emulation explicitly enabled).
- A default StorageClass that can provision a 20 GiB volume.
- `kubectl`, plus `virtctl` for the VM console.

KubeVirt and CDI must already be installed in the cluster. This setup uses Minikube's KubeVirt addon plus upstream CDI. Other clusters must allow KubeVirt and provide KVM or software emulation.

## Configure access

The Ubuntu cloud-init configuration is in `ubuntu-cloud-init.yaml` and uses the public half of a dedicated SSH key generated at `~/.ssh/k8s-debian-mini.pub` on the setup computer. The guest account is `student`; password login is disabled. Keep the matching private key (`~/.ssh/k8s-debian-mini`) private. Never place a private key or password in the configuration.

This Windows/WSL2 Minikube setup has no `/dev/kvm`, so KubeVirt was configured with software emulation. It is slower than hardware-assisted virtualization and is for lightweight coursework/testing, not production.

The cloud-init document is held in a Kubernetes Secret because that is the source type KubeVirt uses here. A Secret manifest in source control is not automatically encrypted: use only the public key in this example, and configure cluster encryption/RBAC appropriately if storing sensitive values.

## Add the Ubuntu VM

The Ubuntu 24.04 VM requests 1 vCPU and 512 MiB RAM. Its original 8 GiB disk was cloned into a 20 GiB persistent root disk because this Minikube StorageClass does not support in-place expansion. The VM uses `ubuntu-mini-root-20g`; the original `ubuntu-mini-root` DataVolume/PVC is retained as a rollback copy for now.

The resize was performed by stopping the VM, applying `ubuntu-disk-20g.yaml` to clone the original PVC, updating `ubuntu-vm.yaml` to attach the clone, and starting the VM again. Do not reapply `ubuntu-disk-20g.yaml` unless the original source DataVolume still exists and you intentionally want to recreate the clone. The Debian VM's local manifests were removed; its already-created Kubernetes resources are unaffected.

```sh
kubectl -n unix-lab get datavolume,pvc,vm,vmi
kubectl -n unix-lab describe pvc ubuntu-mini-root-20g
```

Wait for `ubuntu-mini-root-20g` to finish importing and for the `ubuntu-mini` VMI to show `Running` and `Ready` before opening its console. The guest login is `student`; SSH-key access uses the `~/.ssh/k8s-debian-mini` private key. Ubuntu's cloud-init network config requests DHCP on `enp1s0`.

## Inspect and access

```sh
kubectl -n unix-lab get datavolume,pvc,vm,vmi
kubectl -n unix-lab describe pvc ubuntu-mini-root-20g
virtctl console ubuntu-mini -n unix-lab
```

Use `Ctrl+]` to exit the console. The VM starts automatically (`runStrategy: Always`). Its original root disk is retained as a rollback copy; delete it only when you are certain it is no longer needed.