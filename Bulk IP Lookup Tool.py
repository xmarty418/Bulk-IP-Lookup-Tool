import requests
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar, Checkbutton, Style
from PIL import Image, ImageTk
import threading
import concurrent.futures


def get_isp(ip, fields):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields={fields}')
        data = response.json()
        result = {field: data.get(field, 'Not found') for field in fields.split(',')}
        return ip, result
    except Exception as e:
        return ip, {field: f'Error: {e}' for field in fields.split(',')}


def select_file():
    file_path = filedialog.askopenfilename(title="Select IPs File", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, 'r') as file:
            ips = file.read().splitlines()
        threading.Thread(target=process_ips, args=(ips,)).start()


def process_ips(ips):
    selected_fields = [var.get() for var in field_vars if var.get()]
    fields = ','.join(selected_fields)

    results_text.delete(1.0, tk.END)
    results = []
    total_ips = len(ips)
    progress_var.set(0)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ip = {executor.submit(get_isp, ip, fields): ip for ip in ips}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_ip), start=1):
            ip, result = future.result()
            results.append((ip, result))
            update_results_text(ip, result)
            update_progress_bar(i, total_ips)

    save_results(results, selected_fields)


def process_single_ip():
    ip = ip_entry.get().strip()
    if ip:
        selected_fields = [var.get() for var in field_vars if var.get()]
        fields = ','.join(selected_fields)

        results_text.delete(1.0, tk.END)
        ip, result = get_isp(ip, fields)
        update_results_text(ip, result)
        save_results([(ip, result)], selected_fields)


def update_results_text(ip, result):
    result_str = ', '.join([f'{key}={value}' for key, value in result.items()])
    results_text.insert(tk.END, f'{ip}: {result_str}\n')


def update_progress_bar(current, total):
    progress_var.set(int((current / total) * 100))
    root.update_idletasks()


def save_results(results, fields):
    save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
                                             title="Save Results")
    if save_path:
        with open(save_path, 'w', newline='') as csvfile:
            fieldnames = ['IP Address'] + fields
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for ip, result in results:
                row = {'IP Address': ip}
                row.update(result)
                writer.writerow(row)
        messagebox.showinfo("Success", "Results saved successfully!")


def create_gui():
    global root, results_text, progress_var, field_vars, ip_entry

    root = tk.Tk()
    root.title("IP Lookup by ANAND")

    # Set the icon using PIL
    try:
        icon_image = Image.open("icon.png")  # Update with the correct path to your icon file
        icon_photo = ImageTk.PhotoImage(icon_image)
        root.iconphoto(False, icon_photo)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load icon: {e}")

    style = Style()
    style.configure('TCheckbutton', background='black', foreground='green')
    # style.configure('TProgressbar', troughcolor='black', background='green', thickness=1)
    # style.configure('Vertical.TScrollbar', troughcolor='black', arrowcolor='green', background='black')

    frame = tk.Frame(root, bg='black')
    frame.pack(padx=10, pady=10)

    field_options = [
        'status', 'message', 'country', 'countryCode', 'region', 'regionName', 'city', 'district',
        'zip', 'lat', 'lon', 'timezone', 'isp', 'org', 'mobile'
    ]

    field_vars = [tk.StringVar(value=field) for field in field_options]

    # Create a frame for checkboxes with a grid layout
    checkbox_frame = tk.Frame(frame, bg='black')
    checkbox_frame.pack(pady=5)

    tk.Label(checkbox_frame, text="Select Fields:", bg='yellow', fg='black').grid(row=0, column=0, columnspan=3,
                                                                                 sticky=tk.W)

    for i, var in enumerate(field_vars):
        cb = Checkbutton(checkbox_frame, text=var.get(), variable=var, onvalue=var.get(), offvalue='',
                         style='TCheckbutton')
        cb.grid(row=(i // 7) + 1, column=i % 7, sticky=tk.W)

    select_button = tk.Button(frame, text="Select IPs File", command=select_file, bg='black', fg='green')
    select_button.pack(pady=5)

    tk.Label(frame, text="Enter IP Address:", bg='black', fg='green').pack(pady=5)
    ip_entry = tk.Entry(frame, width=30, bg='black', fg='green', insertbackground='green')
    ip_entry.pack(pady=5)
    ip_button = tk.Button(frame, text="Lookup IP", command=process_single_ip, bg='black', fg='green')
    ip_button.pack(pady=5)

    results_text = scrolledtext.ScrolledText(frame, width=80, height=15, bg='black', fg='green',
                                             insertbackground='green')
    results_text.pack(pady=5)

    progress_var = tk.IntVar()
    progress_bar = Progressbar(frame, variable=progress_var, maximum=100)
    progress_bar.pack(pady=5, fill=tk.X, ipadx=5)

    # Update the scrollbar style
    results_text.configure(yscrollcommand=lambda f, l: on_scroll(f, l, results_text))

    root.configure(bg='black')
    root.mainloop()


def on_scroll(first, last, widget):
    widget.yview_moveto(first)
    scrollbar = widget.vbar
    scrollbar.set(first, last)


if __name__ == '__main__':
    create_gui()
