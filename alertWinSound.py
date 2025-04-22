import tkinter as tk
from tkinter import scrolledtext
import time
import threading
import requests
import winsound
import meshtastic
import meshtastic.serial_interface
from pubsub import pub

LOG_FILE = "uaptc_log.txt"
NWS_ZONE = "ARC119"
NWS_URL = f"https://api.weather.gov/alerts/active/zone/{NWS_ZONE}"
CHECK_INTERVAL = 900  # 15 minutes

class UAPTCRepeater:
    def __init__(self, root):
        self.root = root
        self.root.title("UAPTC Repeater (PTC1)")
        self.root.geometry("880x560")
        self.root.configure(bg="#f0f4f8")
        self.meshInterface = meshtastic.serial_interface.SerialInterface(devPath="COM11")
        pub.subscribe(self.onReceive, "meshtastic.receive")

        self.createHeader()
        self.createControls()
        self.createDisplay()
        self.createStatus()

        threading.Thread(target=self.nwsAlertLoop, daemon=True).start()
        threading.Thread(target=self.scheduledStationIDLoop, daemon=True).start()

    def playSound(self, code):
        try:
            winsound.MessageBeep(code)
        except:
            pass

    def createHeader(self):
        header = tk.Frame(self.root, bg="#005596", height=60)
        header.pack(fill="x")
        tk.Label(header, text="UAPTC Emergency Repeater PTC1", font=("Segoe UI", 16, "bold"), bg="#005596", fg="white").pack(pady=10)

    def createControls(self):
        controlFrame = tk.Frame(self.root, bg="#e2e8f0", width=300)
        controlFrame.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(controlFrame, text="Emergency Controls", font=("Segoe UI", 12, "bold"), bg="#e2e8f0").pack(pady=5)
        tk.Button(controlFrame, text="🚨 Send Alert", font=("Segoe UI", 11), bg="#dc2626", fg="white", command=self.sendAlert).pack(fill="x", pady=5)
        tk.Button(controlFrame, text="✅ Suspend Alert", font=("Segoe UI", 11), bg="#16a34a", fg="white", command=self.suspendAlert).pack(fill="x", pady=5)

        tk.Label(controlFrame, text="Text Messaging", font=("Segoe UI", 12, "bold"), bg="#e2e8f0").pack(pady=10)
        self.textEntry = tk.Entry(controlFrame, font=("Segoe UI", 11))
        self.textEntry.pack(fill="x", padx=5)
        tk.Button(controlFrame, text="📤 Send Text", command=self.sendText, bg="#2563eb", fg="white", font=("Segoe UI", 10)).pack(pady=5)

        tk.Label(controlFrame, text="Repeater Broadcast", font=("Segoe UI", 12, "bold"), bg="#e2e8f0").pack(pady=10)
        tk.Button(controlFrame, text="📡 Station ID + Quote", command=self.sendStationID, bg="#0ea5e9", fg="white", font=("Segoe UI", 10)).pack(fill="x", pady=5)

        tk.Label(controlFrame, text="Weather Alerts", font=("Segoe UI", 12, "bold"), bg="#e2e8f0").pack(pady=10)
        tk.Button(controlFrame, text="🌩️ Check NWS Now", command=self.checkNWSOnce, bg="#64748b", fg="white", font=("Segoe UI", 10)).pack(fill="x", pady=5)

    def createDisplay(self):
        displayFrame = tk.Frame(self.root, bg="white")
        displayFrame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        tk.Label(displayFrame, text="📨 Messages Received", font=("Segoe UI", 12, "bold"), bg="white").pack(anchor="w")
        self.outputBox = scrolledtext.ScrolledText(displayFrame, font=("Consolas", 10), wrap=tk.WORD)
        self.outputBox.pack(expand=True, fill="both")

    def createStatus(self):
        self.statusBar = tk.Label(self.root, text="Status: CONNECTED | Channel: LongFast | Mode: FULL",
                                  bd=1, relief="sunken", anchor="w", bg="#cbd5e1", font=("Segoe UI", 10))
        self.statusBar.pack(side="bottom", fill="x")

    def sendAlert(self):
        self.sendMessage("🚨 EMERGENCY ALERT from UAPTC Repeater!")

    def suspendAlert(self):
        self.playSound(winsound.MB_ICONASTERISK)
        self.sendMessage("✅ ALERT SUSPENDED: All Clear.")

    def sendText(self):
        msg = self.textEntry.get()
        if msg:
            self.playSound(winsound.MB_OK)
            self.sendMessage(f"📨 {msg}")
            self.textEntry.delete(0, tk.END)

    def sendStationID(self):
        quote = '"You have power over your mind – not outside events. Realize this, and you will find strength." — Marcus Aurelius'
        msg = f"📡 PTC1 (UAPTC Repeater 1) is active.\n🧠 {quote}"
        self.sendMessage(msg)

    def sendMessage(self, msg):
        try:
            encoded = msg.encode("utf-8")
            if len(encoded) > 220:
                msg = encoded[:215].decode("utf-8", "ignore") + "…"
            self.meshInterface.sendText(msg)

            if "🚨" in msg or "ALERT" in msg.upper():
                self.playSound(winsound.MB_ICONHAND)

            self.addMessage("You", msg)
            self.logMessage("You", msg)
        except Exception as e:
            self.playSound(winsound.MB_ICONHAND)
            self.addMessage("ERROR", str(e))
            self.logMessage("ERROR", str(e))

    def onReceive(self, packet, interface):
        try:
            fromId = packet.get("fromId", "")
            fromField = packet.get("from", {})
            longName = fromField.get("longName") if isinstance(fromField, dict) else None

            if longName and fromId:
                sender = f"{longName} ({fromId})"
            elif longName:
                sender = longName
            elif fromId:
                sender = fromId
            else:
                sender = "Unknown"

            decoded = packet.get("decoded", {})
            if "text" in decoded:
                payload = decoded["text"]

                if "🚨" in payload or "ALERT" in payload.upper():
                    self.playSound(winsound.MB_ICONHAND)
                else:
                    self.playSound(winsound.MB_ICONEXCLAMATION)

                self.addMessage(sender, payload)
                self.logMessage(sender, payload)
            else:
                self.logMessage("ReceiveInfo", f"Non-text packet from {sender}")
        except Exception as e:
            self.playSound(winsound.MB_ICONHAND)
            self.addMessage("ReceiveError", str(e))
            self.logMessage("ReceiveError", str(e))

    def addMessage(self, sender, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.outputBox.insert(tk.END, f"[{timestamp}] {sender}: {msg}\n")
        self.outputBox.see(tk.END)

    def logMessage(self, sender, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {sender}: {msg}\n")

    def nwsAlertLoop(self):
        while True:
            self.checkNWSOnce()
            time.sleep(CHECK_INTERVAL)

    def checkNWSOnce(self):
        try:
            r = requests.get(NWS_URL, timeout=10)
            data = r.json()
            if "features" in data and len(data["features"]) > 0:
                for alert in data["features"]:
                    headline = alert["properties"]["headline"]
                    description = alert["properties"]["description"]
                    msg = f"🌩️ NWS ALERT: {headline}\n{description[:120]}..."
                    self.playSound(winsound.MB_ICONEXCLAMATION)
                    self.sendMessage(msg)
                    break
            else:
                self.root.after(0, lambda: self.addMessage("NWS", "🟢 No current weather alerts for Pulaski County."))
        except Exception as e:
            self.root.after(0, lambda: self.addMessage("NWS Error", str(e)))

    def scheduledStationIDLoop(self):
        while True:
            now = time.localtime()
            if now.tm_min == 0 and now.tm_hour % 4 == 0:
                self.sendStationID()
                time.sleep(60)
            else:
                time.sleep(30)

if __name__ == "__main__":
    root = tk.Tk()
    app = UAPTCRepeater(root)
    root.mainloop()
