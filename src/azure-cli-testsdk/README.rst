Azure CLI Test Modules
======================

Playback polling
++++++++++++++++

Playback skips ARM service polling delays. The CLI's foreground completion-check
loop instead waits briefly (1 ms requested per iteration) using a threading event,
so background pollers can progress without a CPU-intensive busy loop. This wait
is independent of the playback patch that disables ``time.sleep``. Both delay
patches are restored during test cleanup; live execution is unchanged.
