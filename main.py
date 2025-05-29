import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from PIL import Image, ImageTk
import os
import threading # For non-blocking operations

# Import custom modules
import bg_rem
import ocr_processor

class NoteAppGUI:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Note Processor & OCR")
        self.root.geometry("1200x800")

        self.original_image_pil = None
        self.processed_image_pil = None
        self.current_image_path = None
        self.image_files_in_folder = []
        self.current_folder_path = None

        # --- UI Elements ---
        # Top Control Frame
        top_controls_frame = ttk.Frame(root_window, padding="10")
        top_controls_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_load_image = ttk.Button(top_controls_frame, text="Load Image", command=self.load_single_image)
        self.btn_load_image.pack(side=tk.LEFT, padx=5)

        self.btn_load_folder = ttk.Button(top_controls_frame, text="Load Folder", command=self.load_folder)
        self.btn_load_folder.pack(side=tk.LEFT, padx=5)

        self.btn_process_current = ttk.Button(top_controls_frame, text="Process Current", command=self.process_current_image_action, state=tk.DISABLED)
        self.btn_process_current.pack(side=tk.LEFT, padx=5)

        self.btn_save_processed = ttk.Button(top_controls_frame, text="Save Processed", command=self.save_processed_image_action, state=tk.DISABLED)
        self.btn_save_processed.pack(side=tk.LEFT, padx=5)

        # OCR Controls
        ocr_frame = ttk.LabelFrame(top_controls_frame, text="OCR", padding="5")
        ocr_frame.pack(side=tk.LEFT, padx=10)

        self.ocr_languages = ocr_processor.get_available_languages() # This will now get EasyOCR langs
        # Ensure the default value is one of the available EasyOCR languages
        default_lang = 'en' if 'en' in self.ocr_languages else (self.ocr_languages[0] if self.ocr_languages else '')
        self.ocr_lang_var = tk.StringVar(value=default_lang) 
        self.combo_ocr_lang = ttk.Combobox(ocr_frame, textvariable=self.ocr_lang_var, values=self.ocr_languages, width=5, state="readonly")
        self.combo_ocr_lang.pack(side=tk.LEFT, padx=2)
        if not self.ocr_languages: self.combo_ocr_lang.config(state=tk.DISABLED)


        self.btn_extract_text = ttk.Button(ocr_frame, text="Extract Text", command=self.extract_text_action, state=tk.DISABLED)
        self.btn_extract_text.pack(side=tk.LEFT, padx=5)
        
        self.btn_process_folder = ttk.Button(top_controls_frame, text="Batch Process Folder", command=self.batch_process_folder_action, state=tk.DISABLED)
        self.btn_process_folder.pack(side=tk.LEFT, padx=15)


        # Main content area (Images and OCR Text)
        main_content_frame = ttk.Frame(root_window, padding="5")
        main_content_frame.pack(fill=tk.BOTH, expand=True)

        # PanedWindow for resizable sections
        paned_window = ttk.PanedWindow(main_content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Image Display Frame (Left Pane)
        image_display_frame = ttk.Frame(paned_window, width=700) # Give it an initial width
        paned_window.add(image_display_frame, weight=2) # More weight to images

        self.lbl_original_image = ttk.Label(image_display_frame, text="Original Image", compound="top", relief="groove", anchor="center")
        self.lbl_original_image.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.lbl_processed_image = ttk.Label(image_display_frame, text="Processed Image", compound="top", relief="groove", anchor="center")
        self.lbl_processed_image.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # OCR Text Area (Right Pane)
        ocr_text_frame = ttk.LabelFrame(paned_window, text="Extracted Text (OCR)", padding="5", width=400) # Initial width
        paned_window.add(ocr_text_frame, weight=1) # Less weight to text area

        self.txt_ocr_output = scrolledtext.ScrolledText(ocr_text_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.txt_ocr_output.pack(fill=tk.BOTH, expand=True)

        # Bottom Status Bar and Progress
        bottom_frame = ttk.Frame(root_window, padding="5")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="Ready. Load an image or folder.")
        status_bar = ttk.Label(bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_bar = ttk.Progressbar(bottom_frame, orient=tk.HORIZONTAL, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

    def _update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def _display_pil_image(self, pil_image, label_widget, label_text="Image"):
        if label_widget is None: return

        if pil_image:
            container_w = label_widget.winfo_width() if label_widget.winfo_width() > 1 else 400 # Estimate if not drawn
            container_h = label_widget.winfo_height() if label_widget.winfo_height() > 1 else 500

            img_copy = pil_image.copy()
            img_copy.thumbnail((container_w - 10, container_h - 30), Image.LANCZOS) # -padding/border
            
            photo = ImageTk.PhotoImage(img_copy)
            label_widget.config(image=photo, text=label_text)
            label_widget.image = photo # Keep a reference!
        else:
            label_widget.config(image='', text=label_text) # Clear image
            label_widget.image = None

    def _clear_displays(self):
        self.original_image_pil = None
        self.processed_image_pil = None
        self.current_image_path = None
        
        self._display_pil_image(None, self.lbl_original_image, "Original Image")
        self._display_pil_image(None, self.lbl_processed_image, "Processed Image")
        
        self.txt_ocr_output.config(state=tk.NORMAL)
        self.txt_ocr_output.delete('1.0', tk.END)
        self.txt_ocr_output.config(state=tk.DISABLED)

        self.btn_process_current.config(state=tk.DISABLED)
        self.btn_save_processed.config(state=tk.DISABLED)
        self.btn_extract_text.config(state=tk.DISABLED)


    def load_single_image(self):
        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*"))
        )
        if not file_path:
            return

        self._clear_displays()
        self.image_files_in_folder = [] # Clear folder list
        self.current_folder_path = None
        self.btn_process_folder.config(state=tk.DISABLED)

        try:
            self._update_status(f"Loading {os.path.basename(file_path)}...")
            self.original_image_pil = Image.open(file_path)
            self.current_image_path = file_path
            
            # Wait for labels to have actual size before displaying
            self.root.update_idletasks() 
            self._display_pil_image(self.original_image_pil, self.lbl_original_image, f"Original: {os.path.basename(file_path)}")
            
            self.btn_process_current.config(state=tk.NORMAL)
            self.btn_extract_text.config(state=tk.NORMAL) # Can OCR original
            self._update_status(f"Loaded: {os.path.basename(file_path)}. Ready to process or OCR.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self._update_status("Error loading image.")
            self._clear_displays()

    def load_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder with Images")
        if not folder_path:
            return

        self._clear_displays()
        self.current_folder_path = folder_path
        self.image_files_in_folder = []
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        
        for fname in os.listdir(folder_path):
            if fname.lower().endswith(valid_extensions):
                self.image_files_in_folder.append(os.path.join(folder_path, fname))
        
        if not self.image_files_in_folder:
            messagebox.showinfo("No Images", "No supported image files found in the selected folder.")
            self._update_status("No images found in folder.")
            self.btn_process_folder.config(state=tk.DISABLED)
            return

        # Load and display the first image from the folder as a preview
        self.current_image_path = self.image_files_in_folder[0]
        try:
            self.original_image_pil = Image.open(self.current_image_path)
            self.root.update_idletasks()
            self._display_pil_image(self.original_image_pil, self.lbl_original_image, f"Folder Preview: {os.path.basename(self.current_image_path)}")
            self.btn_process_current.config(state=tk.NORMAL) # Allow processing this preview
            self.btn_extract_text.config(state=tk.NORMAL)
        except Exception as e:
            self._update_status(f"Error loading preview from folder: {e}")
            # Don't clear folder path or list

        self.btn_process_folder.config(state=tk.NORMAL)
        self._update_status(f"{len(self.image_files_in_folder)} images loaded from folder. Ready for batch processing.")


    def process_current_image_action(self):
        if not self.original_image_pil:
            messagebox.showwarning("No Image", "Please load an image first.")
            return

        self._update_status("Processing current image...")
        try:
            cv_original = bg_rem.pil_to_cv(self.original_image_pil)
            cv_processed = bg_rem.remove_background(cv_original) # Uses default params
            self.processed_image_pil = bg_rem.cv_to_pil(cv_processed)
            
            self.root.update_idletasks()
            self._display_pil_image(self.processed_image_pil, self.lbl_processed_image, "Processed")
            
            self.btn_save_processed.config(state=tk.NORMAL)
            self.btn_extract_text.config(state=tk.NORMAL) # Now OCR can use processed
            self._update_status("Current image processed.")
        except Exception as e:
            messagebox.showerror("Processing Error", f"Error during processing: {e}")
            self._update_status("Error processing current image.")
            self.processed_image_pil = None
            self._display_pil_image(None, self.lbl_processed_image, "Processed Image")
            self.btn_save_processed.config(state=tk.DISABLED)

    def save_processed_image_action(self):
        if not self.processed_image_pil:
            messagebox.showwarning("No Processed Image", "Process an image first.")
            return

        original_name, _ = os.path.splitext(os.path.basename(self.current_image_path or "image"))
        suggested_filename = f"{original_name}_cleaned.png"

        file_path = filedialog.asksaveasfilename(
            initialfile=suggested_filename,
            defaultextension=".png",
            filetypes=(("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*"))
        )
        if not file_path:
            return

        try:
            self._update_status(f"Saving to {os.path.basename(file_path)}...")
            save_image = self.processed_image_pil
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in [".jpg", ".jpeg"] and save_image.mode != 'RGB':
                save_image = save_image.convert('RGB')
                save_image.save(file_path, quality=90)
            else:
                save_image.save(file_path)
            
            self._update_status(f"Saved: {os.path.basename(file_path)}")
            messagebox.showinfo("Saved", f"Image saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save: {e}")
            self._update_status("Error saving image.")

    def extract_text_action(self):
        image_to_ocr = None
        source_name = ""

        if self.processed_image_pil:
            image_to_ocr = self.processed_image_pil
            source_name = "processed image"
        elif self.original_image_pil:
            image_to_ocr = self.original_image_pil
            source_name = "original image"
        
        if not image_to_ocr:
            messagebox.showwarning("No Image", "Load an image to extract text.")
            return

        lang = self.ocr_lang_var.get()
        if not lang:
            messagebox.showwarning("OCR Language", "Please select an OCR language.")
            if self.ocr_languages: self.combo_ocr_lang.focus()
            return

        self._update_status(f"Extracting text ({lang}) from {source_name}...")
        self.txt_ocr_output.config(state=tk.NORMAL)
        self.txt_ocr_output.delete('1.0', tk.END)

        # Run OCR in a thread to avoid freezing GUI
        threading.Thread(target=self._run_ocr, args=(image_to_ocr, lang), daemon=True).start()

    def _run_ocr(self, image_to_ocr, lang):
        try:
            extracted_text = ocr_processor.extract_text_from_image(image_to_ocr, lang=lang)
            
            # Update GUI from the main thread
            self.root.after(0, self.txt_ocr_output.insert, tk.END, extracted_text)
            if "OCR Error:" in extracted_text:
                 self.root.after(0, self._update_status, f"OCR completed with issues from {self.current_image_path or 'current image'}.")
            else:
                 self.root.after(0, self._update_status, f"Text extracted from {self.current_image_path or 'current image'}.")
        except Exception as e:
            error_msg = f"Unexpected OCR thread error: {e}"
            self.root.after(0, self.txt_ocr_output.insert, tk.END, error_msg)
            self.root.after(0, self._update_status, "OCR failed.")
        finally:
            self.root.after(0, self.txt_ocr_output.config, {"state": tk.DISABLED})


    def batch_process_folder_action(self):
        if not self.image_files_in_folder or not self.current_folder_path:
            messagebox.showwarning("No Folder", "Load a folder with images first.")
            return

        output_folder = filedialog.askdirectory(title="Select Output Folder for Batch Processed Images")
        if not output_folder:
            return
        
        if output_folder == self.current_folder_path:
            if not messagebox.askyesno("Confirm Overwrite", "Output folder is the same as input. Processed files might overwrite originals if names collide (e.g. if original is already `_cleaned.png`). Continue?"):
                return

        os.makedirs(output_folder, exist_ok=True)
        
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(self.image_files_in_folder)
        self._update_status("Starting batch processing...")

        # Run batch processing in a thread
        threading.Thread(target=self._run_batch_process, args=(list(self.image_files_in_folder), output_folder), daemon=True).start()


    def _run_batch_process(self, image_paths, output_dir):
        processed_count = 0
        error_count = 0
        total_files = len(image_paths)

        for i, img_path in enumerate(image_paths):
            try:
                self.root.after(0, self._update_status, f"Batch: Processing {i+1}/{total_files} - {os.path.basename(img_path)}")
                
                pil_img = Image.open(img_path)
                cv_original = bg_rem.pil_to_cv(pil_img)
                cv_processed = bg_rem.remove_background(cv_original)
                pil_processed = bg_rem.cv_to_pil(cv_processed)

                base, ext = os.path.splitext(os.path.basename(img_path))
                output_filename = f"{base}_cleaned.png" # Always save as PNG for cleaned
                output_path = os.path.join(output_dir, output_filename)
                
                pil_processed.save(output_path)
                processed_count += 1

            except Exception as e:
                error_count += 1
                print(f"Error processing {img_path}: {e}") # Log to console
                self.root.after(0, self._update_status, f"Error processing {os.path.basename(img_path)}. See console.")
            
            # Update progress bar from main thread
            self.root.after(0, self.progress_bar.config, {'value': i + 1})
            self.root.after(0, self.progress_bar.update_idletasks)


        final_status = f"Batch complete: {processed_count} processed, {error_count} errors."
        self.root.after(0, self._update_status, final_status)
        self.root.after(0, messagebox.showinfo, "Batch Processing Finished", final_status)
        self.root.after(0, self.progress_bar.config, {'value': 0})


if __name__ == "__main__":
    main_window = tk.Tk()
    app = NoteAppGUI(main_window)
    main_window.mainloop()