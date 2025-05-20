import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import mutagen
from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen.id3 import ID3, APIC, Encoding
from mutagen.flac import FLAC, Picture
import io # To handle image data in memory


MAX_IMAGE_DIMENSION = 2500 # 2500 max res supported by windows 


def resize_image(image_path):
    """
    Resizes an image if its dimensions exceed MAX_IMAGE_DIMENSION.
    Maintains aspect ratio.
    Returns image data as bytes and its mime type.
    """
    try:
        img = Image.open(image_path)
        width, height = img.size

        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            if width > height:
                new_width = MAX_IMAGE_DIMENSION
                new_height = int(height * (MAX_IMAGE_DIMENSION / width))
            else:
                new_height = MAX_IMAGE_DIMENSION
                new_width = int(width * (MAX_IMAGE_DIMENSION / height))
            
            img = img.resize((new_width, new_height), Image.LANCZOS) # High quality downscale

        img_format = img.format.lower() if img.format else 'jpeg'
        if img_format not in ['jpeg', 'png']:
            img_format = 'jpeg' 

        mime_type = f'image/{img_format}'
        img_byte_arr = io.BytesIO()

        if img_format == 'png':
            img.save(img_byte_arr, format='PNG')
        else: 
            if img.mode == 'RGBA' or img.mode == 'P':
                img = img.convert('RGB')
            img.save(img_byte_arr, format='JPEG', quality=95) 
            mime_type = 'image/jpeg'

        image_data = img_byte_arr.getvalue()
        return image_data, mime_type, (img.width, img.height)
    except Exception as e:
        messagebox.showerror("Image Error", f"Could not process image: {e}")
        return None, None, None

# --- GUI Functions ---
def select_audio_file():
    filepath = filedialog.askopenfilename(
        title="Select Audio File",
        filetypes=(("FLAC files", "*.flac"), ("MP3 files", "*.mp3"), ("All files", "*.*"))
    )
    if filepath:
        audio_file_entry.delete(0, tk.END)
        audio_file_entry.insert(0, filepath)

def select_image_file():
    filepath = filedialog.askopenfilename(
        title="Select Album Art Image",
        filetypes=(("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
    )
    if filepath:
        image_file_entry.delete(0, tk.END)
        image_file_entry.insert(0, filepath)
        try:
            preview_width = 300
            preview_height = 300
            img_preview = Image.open(filepath)
            
            # Calculate aspect ratio preserving dimensions
            img_width, img_height = img_preview.size
            ratio = min(preview_width/img_width, preview_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            img_preview = img_preview.resize((new_width, new_height), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img_preview)
            image_preview_label.config(image=tk_img, width=new_width, height=new_height)
            image_preview_label.image = tk_img 
        except Exception as e:
            image_preview_label.config(image=None, text="Preview N/A")
            print(f"Preview error: {e}")


def apply_album_art():
    audio_path = audio_file_entry.get()
    image_path = image_file_entry.get()

    if not audio_path or not image_path:
        messagebox.showwarning("Input Missing", "Please select both an audio file and an image file.")
        return

    image_data, mime_type, dimensions = resize_image(image_path)
    if not image_data:
        return

    try:
        file_ext = audio_path.lower().split('.')[-1]

        if file_ext == "mp3":
            try:
                audio = MP3(audio_path, ID3=ID3)
            except HeaderNotFoundError:
                messagebox.showwarning("MP3 Warning", "Valid ID3 tag not found. Adding new ID3 tag.")
                audio = MP3(audio_path) 
                if audio.tags is None: # Ensure tags object exists
                    audio.add_tags()
            
            if audio.tags is None: # Double check and add if necessary after trying to load
                 audio.add_tags()

            keys_to_delete = [key for key in audio.tags.keys() if key.startswith('APIC:')]
            for key in keys_to_delete:
                del audio.tags[key]

            audio.tags.add(
                APIC(
                    encoding=Encoding.UTF8, 
                    mime=mime_type,
                    type=3, 
                    desc=u'Cover', 
                    data=image_data
                )
            )

        elif file_ext == "flac":
            audio = FLAC(audio_path)
            audio.clear_pictures() # CORRECTED LINE
            # For comments: The clear_pictures() method removes all existing embedded pictures.

            picture = Picture()
            picture.data = image_data
            picture.type = 3 
            picture.mime = mime_type
            picture.desc = u'Cover' 
            if dimensions:
                picture.width = dimensions[0]
                picture.height = dimensions[1]
            
            audio.add_picture(picture)

        else:
            messagebox.showerror("Unsupported File", f"Unsupported audio file type: .{file_ext}")
            return

        audio.save()
        messagebox.showinfo("Success", f"Album art applied successfully to {audio_path.split('/')[-1]}!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        # For debugging, you might want to print the full traceback
        import traceback
        print(traceback.format_exc())


# --- Setup Tkinter GUI ---
root = tk.Tk()
root.title("Album Art Applier (mirbyte)")

main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(expand=True, fill=tk.BOTH)

tk.Label(main_frame, text="Audio File (MP3 or FLAC):").grid(row=0, column=0, sticky=tk.W, pady=2)
audio_file_entry = tk.Entry(main_frame, width=50)
audio_file_entry.grid(row=0, column=1, padx=5, pady=2)
tk.Button(main_frame, text="Browse...", command=select_audio_file).grid(row=0, column=2, padx=5, pady=2)

tk.Label(main_frame, text="Album Art Image (JPG or PNG):").grid(row=1, column=0, sticky=tk.W, pady=2)
image_file_entry = tk.Entry(main_frame, width=50)
image_file_entry.grid(row=1, column=1, padx=5, pady=2)
tk.Button(main_frame, text="Browse...", command=select_image_file).grid(row=1, column=2, padx=5, pady=2)

image_preview_label = tk.Label(main_frame, text="Image Preview", relief="sunken", width=15, height=7) 
image_preview_label.grid(row=2, column=1, pady=10, sticky="nsew")

apply_button = tk.Button(main_frame, text="Apply Album Art", command=apply_album_art, bg="lightblue")
apply_button.grid(row=3, column=0, columnspan=3, pady=10, ipady=5) 

root.mainloop()