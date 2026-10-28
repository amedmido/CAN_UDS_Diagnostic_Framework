# Automotive CAN & UDS (ISO 14229) Test Automation Framework

An automated test bench framework developed in Python to validate automotive Electronic Control Units (ECUs) over a virtual CAN bus using DBC signal decoding and UDS diagnostic protocol services.

---

## 📌 Project Architecture
1. **Network Definition (`vehicle_network.dbc`):** Defines CAN message frames, signals, bit offsets, scaling factors, and physical ranges for `EngineSpeed`, `VehicleSpeed`, and `BrakePedalStatus`.
2. **ECU Emulation (`ecu_simulator.py`):** Virtual ECU node handling cyclic telemetry transmission and acting as an ISO 14229-1 UDS diagnostic server.
3. **Automated Test Suite (`test_diagnostic_suite.py`):** Structured validation test cases implemented with `pytest` and `cantools` for automated ECU communication validation.

---

## 🧪 Validated Services & Test Scope
* **DBC Signal Decoding:** Verification of frame IDs, byte order, scaling offsets, and payload decoding.
* **UDS Service 0x10 (DiagnosticSessionControl):** Positive response validation for switching to Extended Diagnostic Session (`0x03`).
* **UDS Service 0x22 (ReadDataByIdentifier):** Positive response validation for fetching Vehicle Identification Number (VIN) under DID `0xF190`.

---

## 🚀 Execution & Results
```bash
python -m pytest test_diagnostic_suite.py -v -s