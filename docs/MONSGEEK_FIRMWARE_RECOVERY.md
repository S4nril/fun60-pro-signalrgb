# MonsGeek Keyboard - Firmware Recovery Guide

## 1. Overview

This guide describes how to manually flash the firmware of a MonsGeek keyboard, restore its settings, and perform keyboard calibration.

**Warning:** Make sure you are using the correct firmware for your specific keyboard model. Installing incompatible firmware may permanently damage the keyboard (brick the device) and void its warranty.

---

## 2. Requirements and Precautions

Before starting the firmware recovery process, follow these precautions:

- Disconnect other USB devices that could be mistaken for the keyboard.
- Connect the keyboard directly to the computer's USB port.
- Do not use USB hubs during the firmware update.
- Do not disconnect the keyboard while the firmware is being flashed.
- Do not open the MonsGeek driver or operate the keyboard during the update.
- Make sure the firmware is specifically intended for your keyboard model.

**Identifying the correct device:**

If multiple devices appear in the firmware upgrade tool, unplug and reconnect the keyboard. Identify the entry that disappears and reappears.

---

## 3. Required Files

Download the firmware package from the following link:

**Firmware Download:**  
https://mega.nz/file/Rq1gRLYZ#ynFtB8uXk4msA1AULmWtS7SoCiytowQLuLqkVXe4xlE

Download all files included in the package and extract them into the same folder.

The package should contain one of the following firmware upgrade executables:

- `royuan_tool.exe`
- `ry_upgrade.exe`

---

## 4. Manual Firmware Flashing

Follow these steps carefully:

1. Extract all downloaded files into the same folder.
2. Disconnect unnecessary USB devices.
3. Connect the keyboard directly to the computer.
4. Locate `royuan_tool.exe` or `ry_upgrade.exe`.
5. Right-click the executable and select **Run as administrator**.
6. Wait for the firmware upgrade tool to open.
7. Identify the correct keyboard in the device list.
8. Click the **Upgrade** button to begin flashing.
9. Wait for the process to finish.

**Important:** Do not disconnect the keyboard, close the upgrade tool, or interrupt the process while the firmware is being installed.

### If the Update Fails

If the firmware update fails:

1. Reboot the computer.
2. Disconnect and reconnect the keyboard.
3. Open the firmware upgrade tool again as administrator.
4. Repeat the update procedure.

---

## 5. Driver Installation and Settings Recovery

After flashing the firmware, the keyboard settings will be reset.

The MonsGeek driver may also fail to correctly read the keyboard's current settings after installing firmware through the non-driver method.

To restore proper communication between the keyboard and its driver, use one of the following options:

- **Retrieve Current Setting:** Retrieves the keyboard's current configuration.
- **Reset:** Resets the configuration through the driver.

### Download the Latest Driver

Official MonsGeek Driver Page:  
https://www.monsgeek.com/download/

Alternatively, use the online driver:

https://app.monsgeek.com/

**Note:** The online driver supports Google Chrome only.

---

## 6. Keyboard Calibration

Calibration is essential after firmware recovery to ensure that all keys register correctly.

### Calibration Procedure

1. Open the latest MonsGeek driver.
2. Navigate to the **Configuration** page.
3. Locate and click the **Calibration** button.
4. Read the calibration instructions.
5. Click **Start Calibration**.

### Performing the Calibration

During calibration:

- Press every key all the way down.
- Apply approximately the same amount of force to each key.
- Hold each key at its lowest point for approximately 4–5 seconds.
- Make sure every key is both pressed and released during the process.

After completing the calibration, click:

**Calibration is completed**

### Calibration Troubleshooting

If any keys fail to function correctly after calibration:

1. Repeat the calibration procedure.
2. Make sure every key reaches its lowest point.
3. Maintain consistent pressure.
4. Ensure that every key is pressed and released.

Incomplete key presses during calibration may result in incorrect key behavior.

---

## 7. Final Verification Checklist

After completing the recovery process, verify the following:

- [ ] Firmware update completed successfully.
- [ ] Keyboard is detected by the MonsGeek driver.
- [ ] Current settings have been retrieved or reset.
- [ ] Keyboard calibration completed successfully.
- [ ] All keys register correctly.
- [ ] No unexpected key behavior is present.
- [ ] Keyboard functions normally after reconnecting.

---

## 8. Important Notes

- Always verify firmware compatibility before flashing.
- Never interrupt the firmware installation.
- Always connect the keyboard directly to the computer.
- Perform calibration after firmware recovery.
- Recheck keyboard functionality before restoring custom configurations.

**Disclaimer:** This procedure is based on the firmware recovery instructions provided by MonsGeek. Firmware compatibility and successful recovery depend on the exact keyboard model and firmware version.