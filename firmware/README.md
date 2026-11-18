# Firmware (not included)

This folder is empty on purpose: the firmware is the vendor's code and is not redistributed here, and neither is the patched
image (it is a modified copy of the vendor's code). You build the patched image yourself from **your own** download of the original.

## Images the tools accept

| Image | SHA-256 | Size |
|---|---|---|
| original ID2304 V309 (inflated) | `237bbe74f2f718a08bf2b8bb9caf6ca026b86817b6baae6130e0a7794d72a6ac` | 124,668 bytes |
| the same, as served by the vendor (raw deflate) | `a0c12398adab58289e126113302b2758a105093643908d6902f5db49be934804` | 49,431 bytes |
| patched (built by `tools/build_pro_patch.py`) | `5934caf51604877baa53c3ddf0b81b8506d8af6a1a73c5f969c020a663f8eb03` | 124,950 bytes |

If the vendor publishes a newer version the hash will differ and the tools will refuse it. That is intended: the patch offsets were
only analysed for V309.

## Get the original firmware

These are the same two requests the vendor's own driver makes (Windows PowerShell):

```powershell
$r = Invoke-RestMethod -Method Post -Uri "https://api2.rongyuan.tech:3816/api/v2/get_fw_version" -ContentType "application/json" -Body '{"dev_id":2304}'
$r | ConvertTo-Json -Depth 5
Invoke-WebRequest -Uri ("https://api2.rongyuan.tech:3816/download/" + $r.data.file_path) -OutFile "fw_2304.bin"
```

Put `fw_2304.bin` in this folder. The tools inflate it automatically (it is a raw-deflate stream) and check the hash. If the server
returns something else (another version, a ZIP), stop: this project does not support it.

## Build the patched image

```
python tools/build_pro_patch.py pro firmware/fw_2304.bin ID2304-V309-livepatch.bin
python tools/fun60pro_flasher.py plan ID2304-V309-livepatch.bin
```

`*.bin` is in `.gitignore`; do not commit firmware.
