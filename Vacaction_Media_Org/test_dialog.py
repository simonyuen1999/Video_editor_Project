#!/usr/bin/env python3
"""
Simple test to verify country_zh is working in the dialog
"""

import tkinter as tk
from tkinter import ttk

def test_dialog():
    """Test the dialog display with sample data"""
    
    # Sample data that mimics what the app should have
    sample_data = {
        'city_en': 'Tokyo',
        'city_zh': '东京',
        'country_en': 'Japan',
        'country_zh': '日本'
    }
    
    root = tk.Tk()
    root.title("Test Dialog")
    root.geometry("500x300")
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Configure grid weights for responsive layout
    main_frame.columnconfigure(1, weight=1)
    
    # Form fields
    ttk.Label(main_frame, text="City (English):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
    city_en_var = tk.StringVar(value=sample_data['city_en'])
    ttk.Entry(main_frame, textvariable=city_en_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), columnspan=2)
    
    ttk.Label(main_frame, text="City (Chinese):").grid(row=1, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
    city_zh_var = tk.StringVar(value=sample_data['city_zh'])
    ttk.Entry(main_frame, textvariable=city_zh_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
    
    ttk.Label(main_frame, text="Country (English):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
    country_en_var = tk.StringVar(value=sample_data['country_en'])
    ttk.Entry(main_frame, textvariable=country_en_var, state="readonly").grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5), columnspan=2)
    
    ttk.Label(main_frame, text="Country (Chinese):").grid(row=3, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
    country_zh_var = tk.StringVar(value=sample_data['country_zh'])
    country_zh_entry = ttk.Entry(main_frame, textvariable=country_zh_var, state="readonly")
    country_zh_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5), columnspan=2)
    
    # Add some debugging info
    ttk.Label(main_frame, text=f"Data: {sample_data}", foreground="blue").grid(row=4, column=0, columnspan=3, pady=(10, 0))
    
    def check_values():
        print("Current form values:")
        print(f"  city_en: {city_en_var.get()}")
        print(f"  city_zh: {city_zh_var.get()}")
        print(f"  country_en: {country_en_var.get()}")
        print(f"  country_zh: {country_zh_var.get()}")
    
    ttk.Button(main_frame, text="Check Values", command=check_values).grid(row=5, column=0, columnspan=3, pady=(10, 0))
    
    root.mainloop()

if __name__ == "__main__":
    test_dialog()