import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import time

class SteganographyApp:
    def __init__(self, master):
        self.master = master
        master.title("Steganography App")
        master.geometry("800x400")

        # Left side - Image selection
        self.image_frame = tk.Frame(master, width=400, height=300, bg="white")
        self.image_frame.grid(row=0, column=0, padx=10, pady=10)
        self.image_frame.grid_propagate(False)

        self.image_label = tk.Label(self.image_frame, bg="white")
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        self.choose_button = tk.Button(master, text="Choose Image", command=self.choose_image)
        self.choose_button.grid(row=1, column=0, pady=10)

        # Right side - Text input
        self.text_input = tk.Text(master, width=40, height=18)
        self.text_input.grid(row=0, column=1, padx=10, pady=10)

        # Action button
        self.action_button = tk.Button(master, text="Action", command=self.perform_action)
        self.action_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.image_path = None

        # Execution Time
        self.time_label = tk.Label(master, text="Execution Time:")
        self.time_label.grid(row=1, column=1, sticky="e", padx=(0, 5))

        self.time_entry = tk.Entry(master, width=10, state="readonly")
        self.time_entry.grid(row=1, column=2, sticky="w", padx=(0, 10))


    def choose_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.image_path = file_path
            image = Image.open(file_path)
            image.thumbnail((380, 280))
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
            # Clear the text input
            self.text_input.delete("1.0", tk.END)
            
            # Clear the execution time
            self.time_entry.config(state="normal")
            self.time_entry.delete(0, tk.END)
            self.time_entry.config(state="readonly")


    def perform_action(self):
        if not self.image_path:
            messagebox.showerror("Error", "Please choose an image first")
            return

        self.time_entry.config(state="normal")
        self.time_entry.delete(0, tk.END)
        self.time_entry.config(state="readonly")

        start_time = time.time()

        if not self.text_input.get("1.0", tk.END).strip():
            # No text entered, try to decode the image
            try:
                decoded_text = self.decode_text_from_image()
                if decoded_text:
                    self.text_input.delete("1.0", tk.END)
                    self.text_input.insert(tk.END, decoded_text)
                else:
                    messagebox.showerror("Error", "The image does not contain embedded text")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to decode image: {str(e)}")
        else:
            # Text entered, perform encoding
            text = self.text_input.get("1.0", tk.END).strip()
            self.embed_text_in_image(text)

        end_time = time.time()
        execution_time = end_time - start_time
        
        self.time_entry.config(state="normal")
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, f"{execution_time:.4f} s")
        self.time_entry.config(state="readonly")

    def decode_text_from_image(self):
        img = Image.open(self.image_path)
        img_array = np.array(img)
        
        # Extract the least significant bits
        bits = np.unpackbits(img_array.reshape(-1)[:, np.newaxis], axis=1)[:, -1]
        
        # Convert bits to characters
        chars = bits.reshape(-1, 8)[:(bits.size // 8)]
        chars = np.packbits(chars)
        
        # Find the null terminator
        null_pos = np.where(chars == 0)[0]
        if null_pos.size > 0:
            chars = chars[:null_pos[0]]
        
        # Convert to string
        decoded_text = chars.tostring().decode('ascii', errors='ignore')
        
        return decoded_text if decoded_text.isprintable() else None


    def embed_text_in_image(self, text):
        img = Image.open(self.image_path)
        img_array = np.array(img)
        
        binary_text = ''.join(format(ord(char), '08b') for char in text) + '00000000'  # Add null terminator
        
        if len(binary_text) > img_array.size:
            messagebox.showerror("Error", "Text is too long for this image")
            return
        
        # Reshape the image array to 1D for faster processing
        flat_img = img_array.reshape(-1)
        
        # Create a boolean mask for the bits to modify
        mask = np.zeros(flat_img.size, dtype=bool)
        mask[:len(binary_text)] = True
        
        # Convert to int16 to handle negative values during bitwise operations
        flat_img_int16 = flat_img.astype(np.int16)
        
        # Modify the least significant bits
        flat_img_int16[mask] = (flat_img_int16[mask] & ~1) | np.array(list(binary_text), dtype=int)
        
        # Convert back to uint8
        flat_img = flat_img_int16.astype(np.uint8)
        
        # Reshape back to the original image shape
        img_array = flat_img.reshape(img_array.shape)
        
        output_image = Image.fromarray(img_array)
        output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if output_path:
            output_image.save(output_path)
            messagebox.showinfo("Success", f"Image with embedded text saved as {output_path}")

root = tk.Tk()
app = SteganographyApp(root)
root.mainloop()
