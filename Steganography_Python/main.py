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
        
        binary_text = ""
        for i in range(img_array.shape[0]):
            for j in range(img_array.shape[1]):
                for k in range(img_array.shape[2]):
                    binary_text += str(img_array[i, j, k] & 1)
                    if len(binary_text) % 8 == 0:
                        if binary_text[-8:] == '00000000':
                            # Found null terminator, end of message
                            decoded_text = ''.join(chr(int(binary_text[i:i+8], 2)) for i in range(0, len(binary_text)-8, 8))
                            if decoded_text.isprintable():  # Check if the decoded text is valid
                                return decoded_text
                            else:
                                return None  # Invalid text, likely no embedded message
        
        return None  # No hidden text found


    def embed_text_in_image(self, text):
        # Simple LSB steganography
        img = Image.open(self.image_path)
        img_array = np.array(img)
        
        binary_text = ''.join(format(ord(char), '08b') for char in text)
        binary_text += '00000000'  # Add null terminator
        
        if len(binary_text) > img_array.size:
            messagebox.showerror("Error", "Text is too long for this image")
            return
        
        index = 0
        for i in range(img_array.shape[0]):
            for j in range(img_array.shape[1]):
                for k in range(img_array.shape[2]):
                    if index < len(binary_text):
                        img_array[i, j, k] = (img_array[i, j, k] & 254) | int(binary_text[index])
                        index += 1
                    else:
                        break
                if index >= len(binary_text):
                    break
            if index >= len(binary_text):
                break
        
        output_image = Image.fromarray(img_array)
        output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if output_path:
            output_image.save(output_path)
            messagebox.showinfo("Success", f"Image with embedded text saved as {output_path}")

root = tk.Tk()
app = SteganographyApp(root)
root.mainloop()
