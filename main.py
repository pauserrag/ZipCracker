from concurrent.futures import ThreadPoolExecutor
import threading
import pyzipper
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import time


def crack_zip(zip_path, password, stop_event, progress_callback=None):
    try:
        if progress_callback:
            progress_callback(0, f"Trying password: {password}")
        with pyzipper.AESZipFile(zip_path) as zf:
            zf.extractall(pwd=password.encode('utf-8'))
        return password
    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error with password {password}: {e}")
    return None


def read_wordlist(wordlist_path):
    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            yield line.strip()


def parallel_crack(zip_path, wordlist_path, num_threads, stop_event, progress_callback=None):
    total_passwords = sum(1 for _ in read_wordlist(wordlist_path))
    current_passwords = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        passwords = read_wordlist(wordlist_path)
        for password in passwords:
            if stop_event.is_set():
                break
            future = executor.submit(crack_zip, zip_path, password, stop_event, progress_callback)
            result = future.result()
            current_passwords += 1
            progress = (current_passwords / total_passwords) * 100
            if progress_callback:
                progress_callback(progress, "")
            if result:
                stop_event.set()
                break

    end_time = time.time()
    elapsed_time = end_time - start_time
    return elapsed_time


class ZipCrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zip Cracker")
        self.geometry("600x500")
        self.configure(bg="#f0f0f0")

        self.zip_label = tk.Label(self, text="ZIP File Path:", bg="#f0f0f0", font=("Arial", 12))
        self.zip_label.pack(pady=10)
        self.zip_entry = tk.Entry(self, width=50)
        self.zip_entry.pack(pady=5)
        self.zip_browse = tk.Button(self, text="Browse", command=self.browse_zip, bg="#4CAF50", fg="white",
                                    font=("Arial", 10))
        self.zip_browse.pack(pady=5)

        self.wordlist_label = tk.Label(self, text="Wordlist File Path:", bg="#f0f0f0", font=("Arial", 12))
        self.wordlist_label.pack(pady=10)
        self.wordlist_entry = tk.Entry(self, width=50)
        self.wordlist_entry.pack(pady=5)
        self.wordlist_browse = tk.Button(self, text="Browse", command=self.browse_wordlist, bg="#4CAF50", fg="white",
                                         font=("Arial", 10))
        self.wordlist_browse.pack(pady=5)

        self.threads_label = tk.Label(self, text="Number of Threads:", bg="#f0f0f0", font=("Arial", 12))
        self.threads_label.pack(pady=10)
        self.threads_entry = tk.Entry(self, width=5)
        self.threads_entry.pack(pady=5)

        total_threads = os.cpu_count() or "unknown"
        max_threads_text = f"Max: {total_threads}" if total_threads != "unknown" else "Max: Not Available"
        suggestion_text = f"Suggested: {total_threads - 2}" if total_threads != "unknown" else "Number of threads not available"
        self.threads_suggestion_label = tk.Label(self, text=suggestion_text, bg="#f0f0f0", font=("Arial", 10))
        self.threads_suggestion_label.pack(pady=5)
        self.max_threads_label = tk.Label(self, text=max_threads_text, bg="#f0f0f0", font=("Arial", 10))
        self.max_threads_label.pack(pady=5)

        self.progress_label = tk.Label(self, text="Progress:", bg="#f0f0f0", font=("Arial", 12))
        self.progress_label.pack(pady=10)
        self.progressbar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progressbar.pack(pady=5)

        self.progress_text = tk.Text(self, height=8, width=60)
        self.progress_text.pack(pady=10)

        self.button_frame = tk.Frame(self, bg="#f0f0f0")
        self.button_frame.pack(pady=20)

        self.crack_button = tk.Button(self.button_frame, text="Crack ZIP", command=self.start_crack_zip, bg="#4CAF50",
                                      fg="white", font=("Arial", 12))
        self.crack_button.pack(side="left", padx=10)

        self.stop_button = tk.Button(self.button_frame, text="Stop Cracking", command=self.stop_crack_zip, bg="#f44336",
                                     fg="white", font=("Arial", 12))
        self.stop_button.pack(side="left", padx=10)

        self.thread = None
        self.stop_event = threading.Event()

    def browse_zip(self):
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        self.zip_entry.delete(0, tk.END)
        self.zip_entry.insert(0, path)

    def browse_wordlist(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        self.wordlist_entry.delete(0, tk.END)
        self.wordlist_entry.insert(0, path)

    def append_progress(self, progress, text):
        self.progress_text.insert(tk.END, text + "\n")
        self.progress_text.see(tk.END)
        self.progressbar["value"] = progress

    def crack_zip(self):
        zip_path = self.zip_entry.get()
        wordlist_path = self.wordlist_entry.get()
        try:
            num_threads = int(self.threads_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of threads must be an integer.")
            return

        if not (zip_path and wordlist_path and num_threads > 0):
            messagebox.showerror("Invalid Input", "Please provide all inputs correctly.")
            return

        for progress, result in parallel_crack(zip_path, wordlist_path, num_threads, self.stop_event, self.append_progress):
            if result:
                messagebox.showinfo("Success", f"Password found: {result}")
                break
        else:
            messagebox.showwarning("Failure", "Password not found.")

    def start_crack_zip(self):
        # Reset stop event
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.crack_zip)
        self.thread.start()

    def stop_crack_zip(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=0)
            messagebox.showinfo("Information", "Cracking process stopped.")
        else:
            messagebox.showinfo("Information", "No cracking process running.")


app = ZipCrackerApp()
app.mainloop()
