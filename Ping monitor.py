import time
import configparser
import smtplib
import os
import platform
from email.mime.text import MIMEText
import subprocess

def load_config(filename="config.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

def send_email(gmail_from, gmail_to, gmail_pass, subject, body, retry_interval=300):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_from
    msg["To"] = gmail_to
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")  # Current time in "YYYY-MM-DD HH:MM:SS" format

    attempt = 0
    while attempt < 5:  # Max 5 attempts
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(gmail_from, gmail_pass)
            server.sendmail(gmail_from, gmail_to, msg.as_string())
            server.quit()
            print(f"{current_time} -> Email sent successfully.")
            return True
        except Exception as e:
            print(f"{current_time} -> Error sending email: {e}")
            attempt += 1
            if attempt < 5:
                print(f"{current_time} -> Retrying in {retry_interval / 60} minutes...")
                time.sleep(retry_interval)  # Retry after 5 minutes
            else:
                print(f"{current_time} -> Max retries reached. Email not sent.")
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

def main():
    config = load_config()

    gmail_from = config["GMAIL"]["from"]
    gmail_to = config["GMAIL"]["to"]
    gmail_pass = config["GMAIL"]["api_passw"]
    check_interval = int(config["SETTINGS"]["interval"])

    ip_addresses = [config["DEVICES"][key] for key in config["DEVICES"]]

    fail_counts = {ip: 0 for ip in ip_addresses}
    previously_available = {ip: True for ip in ip_addresses}
    notified_ips = set()  # To keep track of notified IPs

    try:
        print("Press CTRL+C to exit the program.")
        while True:
            for ip in ip_addresses:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")  # Current time in "YYYY-MM-DD HH:MM:SS" format

                print(f"{current_time} -> Checking status of IP: {ip}")

                # Perform ping check for each IP address individually
                is_online = ping_device(ip)

                if is_online:
                    fail_counts[ip] = 0  # Reset the failure count if device is online
                    previously_available[ip] = True  # Mark device as available
                    print(f"{current_time} -> Device {ip} is online.")
                else:
                    fail_counts[ip] += 1  # Increment failure count for this IP
                    print(f"{current_time} -> Device {ip} is offline!")

                    if fail_counts[ip] >= 2 and previously_available[ip] and ip not in notified_ips:
                        subject = f"WARNING: Device {ip} is offline!"
                        body = f"Device with IP address {ip} did not respond to PING twice in a row."
                        email_sent = send_email(gmail_from, gmail_to, gmail_pass, subject, body)
                        if email_sent:
                            notified_ips.add(ip)  # Add the IP to the notified list
                            fail_counts[ip] = 0  # Reset fail count after sending email
                            previously_available[ip] = False  # Mark as unavailable
                            print(f"{current_time} -> Email sent for {ip}.")

            time.sleep(check_interval * 60)  # Convert minutes to seconds

    except KeyboardInterrupt:
        print("\nCTRL+C detected. Exiting program...")
        time.sleep(1)

if __name__ == "__main__":
    main()
