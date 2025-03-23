import time
import configparser
import smtplib
import os
import platform
import subprocess
import tkinter as tk
from tkinter import scrolledtext
from email.mime.text import MIMEText

def load_config(filename="config.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

def send_email(gmail_from, gmail_to, gmail_pass, subject, body, retry_interval=300):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_from
    msg["To"] = gmail_to
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    attempt = 0
    while attempt < 5:
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(gmail_from, gmail_pass)
            server.sendmail(gmail_from, gmail_to, msg.as_string())
            server.quit()
            log_event(f"Email sent for {subject} at {current_time}")
            return True
        except Exception as e:
            log_event(f"Error sending email for {subject}: {e}")
            attempt += 1
            if attempt < 5:
                time.sleep(retry_interval)
    return False

def ping_device(ip_address):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", ip_address]

    try:
        # Using subprocess to get real-time ping result
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Convert output to string
        output = result.stdout.decode()

        # Check if the output contains "Destination host unreachable"
        if "Destination host unreachable" in output:
            print(f"Ping to {ip_address} failed: Destination host unreachable.")
            return False  # Device is unreachable

        if result.returncode == 0:
            print(f"Ping to {ip_address} successful.")
            return True  # Device is reachable
        else:
            print(f"Ping to {ip_address} failed.")
            return False  # Device is unreachable

    except Exception as e:
        print(f"Error occurred while pinging {ip_address}: {e}")
        return False

    # Adding a pause of 1 second between each ping
    time.sleep(1)


def log_event(message):
    with open("log.txt", "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def update_status():
    for ip in ip_addresses:
        is_online = ping_device(ip)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if is_online:
            status_labels[ip].config(text=f"{ip} - Online", fg="green")
            fail_counts[ip] = 0
            previously_available[ip] = True
            log_event(f"{ip} is Online at {current_time}")
        else:
            status_labels[ip].config(text=f"{ip} - Offline", fg="red")
            fail_counts[ip] += 1
            log_event(f"{ip} is Offline at {current_time}")
            if fail_counts[ip] >= 2 and previously_available[ip] and ip not in notified_ips:
                subject = f"WARNING: Device {ip} is offline!"
                body = f"Device with IP address {ip} did not respond to PING twice in a row."
                if send_email(gmail_from, gmail_to, gmail_pass, subject, body):
                    notified_ips.add(ip)
                    fail_counts[ip] = 0
                    previously_available[ip] = False
    root.after(check_interval * 60000, update_status)

def exit_program():
    root.destroy()
    os._exit(0)

config = load_config()
gmail_from = config["GMAIL"]["from"]
gmail_to = config["GMAIL"]["to"]
gmail_pass = config["GMAIL"]["api_passw"]
check_interval = int(config["SETTINGS"]["interval"])
ip_addresses = [config["DEVICES"][key] for key in config["DEVICES"]]
fail_counts = {ip: 0 for ip in ip_addresses}
previously_available = {ip: True for ip in ip_addresses}
notified_ips = set()

root = tk.Tk()
root.title("Ping Monitor by 9A4AM")
root.configure(bg="#1e1e1e")
root.geometry("500x400")

title_label = tk.Label(root, text="Device Status", font=("Arial", 14), fg="gold", bg="#1e1e1e")
title_label.pack()

status_frame = tk.Frame(root, bg="#1e1e1e")
status_frame.pack(pady=10)
status_labels = {}
for ip in ip_addresses:
    lbl = tk.Label(status_frame, text=f"{ip} - Checking...", font=("Arial", 12), fg="white", bg="#1e1e1e")
    lbl.pack(anchor="w")
    status_labels[ip] = lbl

log_text = scrolledtext.ScrolledText(root, width=60, height=10, bg="#252526", fg="white", font=("Arial", 10))
log_text.pack(pady=10)

def update_log_display():
    with open("log.txt", "r") as log_file:
        lines = log_file.readlines()
        log_text.delete(1.0, tk.END)
        log_text.insert(tk.END, "".join(lines[::-1]))  # Obrnut redoslijed linija
    root.after(5000, update_log_display)

exit_button = tk.Button(root, text="EXIT", font=("Arial", 14), fg="black", bg="red", command=exit_program)
exit_button.pack(pady=10)

update_status()
update_log_display()
root.mainloop()