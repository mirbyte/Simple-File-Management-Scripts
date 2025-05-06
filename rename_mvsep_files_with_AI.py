import google.generativeai as genai
import os
import pathlib
import re
import traceback


# vibe coded with gemini

# --- Configuration ---
API_KEY = "YOUR_API_KEY"  # <<< Replace with your Gemini API Key >>>
MUSIC_DIR = str(pathlib.Path.cwd())
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a']
DRY_RUN = False # or True

# --- Configure Gemini API ---
try:
    if not API_KEY or API_KEY == "YOUR_API_KEY":
        print("ERROR: API_KEY is not set. Please edit the script and replace 'YOUR_API_KEY'.")
        exit()
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"Error configuring Gemini API or initializing model: {e}")
    exit()

def sanitize_filename(name):
    if name is None: return ""
    name = str(name)
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', ' ', name).strip()
    max_len = 200
    if len(name) > max_len:
        name_part = name[:max_len]
        last_space = name_part.rfind(' ')
        name = name_part[:last_space] if last_space != -1 else name_part
    return name

def preprocess_mvsep_filename(filename_str):
    p = pathlib.Path(filename_str)
    original_extension = p.suffix
    name_no_ext_initial = p.stem

    is_likely_mvsep_raw_format = bool(
        re.match(r"^\d{14}-[0-9a-fA-F]{10,16}-", name_no_ext_initial) or
        "[mvsep.com]" in filename_str.lower()
    )

    processed_name = name_no_ext_initial
    found_stem_type = None

    if is_likely_mvsep_raw_format:
        if processed_name.lower().endswith("[mvsep.com]"):
            temp_name = processed_name[:-len("[mvsep.com]")]
            processed_name = temp_name.rstrip("_")

        stem_patterns = {
            "Vocals": r"_(vocals|vocal)(?:_|$)", "Other": r"_(other)(?:_|$)", "Drums": r"_(drums|drum)(?:_|$)",
            "Bass": r"_(bass)(?:_|$)", "Instrumental": r"_(instrumental|instr|inst)(?:_|$)",
            "Karaoke": r"_(karaoke|karoke)(?:_|$)", "Piano": r"_(piano)(?:_|$)", "Guitar": r"_(guitar)(?:_|$)"
        }
        temp_name_for_stem_search = processed_name
        for s_key, s_pattern in stem_patterns.items():
            matches = list(re.finditer(s_pattern, temp_name_for_stem_search, re.IGNORECASE))
            if matches:
                match = matches[-1]; found_stem_type = s_key
                start_idx = match.start(); end_idx = match.end()
                if start_idx > 0 and temp_name_for_stem_search[start_idx-1] == '_': start_idx -=1
                processed_name = temp_name_for_stem_search[:start_idx] + temp_name_for_stem_search[end_idx:]
                break
        
        prefix_match_obj = re.match(r"^\d{14}-[0-9a-fA-F]{10,16}-", processed_name)
        if prefix_match_obj:
            processed_name = processed_name[prefix_match_obj.end():]

        model_artefacts_patterns = [
            r"_melroformer_mt_\d+", r"_htdemucs_ft", r"_mdx23c", r"_uvr-mdx-net-inst_hq_\d+",
            r"_demucs(_\d+)?", r"_reverb_full", r"_noise_rem", r"_(-?)remaster(ed)?", r"_hq\d*"
        ]
        for pattern in model_artefacts_patterns:
            processed_name = re.sub(pattern, "_", processed_name, flags=re.IGNORECASE)

        processed_name = re.sub(r"_+", "_", processed_name).strip('_')
        processed_name = processed_name.replace("_", "-")
        core_info = re.sub(r"-+", "-", processed_name).strip('-')
    else: 
        core_info = name_no_ext_initial
        stem_match_original = re.match(r"^(.*?)\s*\((Vocals|Instrumental|Drums|Bass|Other|Full Mix|Karaoke|Piano|Guitar)\)$", core_info, re.IGNORECASE)
        if stem_match_original:
            core_info = stem_match_original.group(1).strip()
            found_stem_type = stem_match_original.group(2).capitalize()

    if core_info.endswith('.'):
        core_info = core_info[:-1]
        
    return core_info, found_stem_type, original_extension, is_likely_mvsep_raw_format

def get_formatted_name_from_gemini(core_info_input, stem_type_input, original_filename_for_context, is_likely_mvsep_raw_format_flag):
    global model

    if not core_info_input: return None
    detected_stem_str = stem_type_input if stem_type_input else "Not explicitly detected"

    diacritic_instruction = """
        - **Language Hint:** The Artist or Title is likely in **English or Finnish**.
        - **Finnish Diacritic Restoration:** If Finnish is identified or strongly suspected for any part of the Artist or Title:
            - Where an 'a' appears, consider if it should be an 'ä' (e.g., 'sa' might be 'sä').
            - Where an 'o' appears, consider if it should be an 'ö' (e.g., 'korso' might be 'körsö').
          Please apply these specific restorations only if it makes strong linguistic sense for Finnish words. Be conservative with other diacritics.
    """
    feat_formatting_instruction = """
        - **Featuring Artist Formatting:** If the Song Title includes a featuring artist (e.g., from "feat-Someone" or "ft-Someone"), ensure it is formatted as "feat. Someone" or "ft. Someone" (with a period after "feat" or "ft") within the final Song Title.
    """

    if not is_likely_mvsep_raw_format_flag:
        prompt = f"""
        The following filename stem appears to be an already organized song name: "{core_info_input}"
        A stem type explicitly parsed from the original name is: "{detected_stem_str}".

        Your tasks:
        1. Analyze if "{core_info_input}" represents "Artist - Title" or primarily "Song Title". A "Song Title" might include "feat. Someone".
           - If "{core_info_input}" seems to be primarily a song title (even with "feat." parts) and a distinct artist before a separator like ' - ' is not clear, output the artist as "Unknown Artist". Treat the entirety of "{core_info_input}" (after fixes) as the Song Title.
           - If it clearly separates an artist and a title, identify them.
        2. Ensure proper capitalization.
        {diacritic_instruction}
        {feat_formatting_instruction}
        3. If a stem was detected from the original ("{detected_stem_str}" if not "Not explicitly detected"), use it. Otherwise, append "(Full Mix)".
        4. Output as "Artist - Title (Stem)". If the artist is "Unknown Artist", still include it in this output; Python will handle removing it later if needed.
        5. If input is already perfect (or only needs minor fixes covered above like diacritics, capitalization, "feat." period, or adding "(Full Mix)"), reply with "NO_CHANGE_NEEDED_AS_IS".
        6. If generic (e.g., "Track 01"), respond "UNKNOWN_FORMAT".

        Examples:
        Input: "sa teet sen feat artisti", Detected Stem: "Not explicitly detected" -> Output: Sä Teet Sen feat. Artisti (Full Mix)
        Input: "Artisti Esiintyjä - Biisin Nimi feat Toinen Artisti", Detected Stem: "Not explicitly detected" -> Output: Artisti Esiintyjä - Biisin Nimi feat. Toinen Artisti (Full Mix)
        Input: "Chance - Aspyer", Detected Stem: "Not explicitly detected" -> Output: NO_CHANGE_NEEDED_AS_IS
        Input: "My Song (vocals)", Detected Stem: "Vocals" -> Output: Unknown Artist - My Song (Vocals)

        Filename stem to analyze: "{core_info_input}"
        Detected Stem: "{detected_stem_str}"
        Output:
        """
    else: # is_likely_mvsep_raw_format_flag is True
        prompt = f"""
        Analyze messy audio file Core Information: "{core_info_input}" (pre-processed from mvsep.com; words may be hyphenated)
        Detected Stem Type: "{detected_stem_str}"

        Your tasks:
        1. Parse "Core Information" for Artist and Song Title.
           - If it seems to be only a song title (may include "feat-Someone"), use "Unknown Artist". Treat the entire processed "Core Information" (hyphens to spaces, diacritics restored) as Song Title.
           - If "artist-name-separator-song-title" is clear, parse accordingly.
        2. Convert hyphens between words to spaces.
        3. Capitalize appropriately.
        {diacritic_instruction}
        {feat_formatting_instruction}
        4. Use "Detected Stem Type" or "Full Mix".
        Format STRICTLY as: Artist - Title (Stem). If artist is "Unknown Artist", still include it here.
        If "Core Information" is too garbled, respond "UNKNOWN_FORMAT".

        Examples:
        Input Core: "sa-teet-saman-muille-feat-mimosa" / Detected Stem: "Vocals" -> Output: Unknown Artist - Sä Teet Saman Muille feat. Mimosa (Vocals)
        Input Core: "artisti-esiintyja-laulun-nimi-feat-vierailija" / Detected Stem: "Other" -> Output: Artisti Esiintyjä - Laulun Nimi feat. Vierailija (Other)
        Input Core: "kostonliekki-liekeissa" / Detected Stem: "Other" -> Output: Kostonliekki - Liekeissä (Other)

        Core Information: "{core_info_input}"
        Detected Stem Type: "{detected_stem_str}"
        Formatted name:
        """
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text == "UNKNOWN_FORMAT" or not response_text: return None
        if response_text == "NO_CHANGE_NEEDED_AS_IS": return "NO_CHANGE_NEEDED_AS_IS"
        
        if not re.match(r".+ - .+ \([^)]+\)$", response_text):
            print(f"  WARNING: Gemini response for '{original_filename_for_context}' not in 'Artist - Title (Stem)' format: '{response_text}'. Treating as UNKNOWN_FORMAT.")
            return None
        return response_text
    except Exception as e:
        print(f"  ERROR: Exception calling Gemini API for '{original_filename_for_context}' (Core: '{core_info_input}'): {e}")
        return None

def rename_files_in_current_directory():
    print(f"--- MVSEP File Renamer ---")
    print(f"Scanning current directory: {MUSIC_DIR}")
    if DRY_RUN: print("DRY RUN IS ACTIVE: No files will actually be renamed.")
    else: print("WARNING: DRY RUN IS FALSE. Files will be renamed.")
    print("-" * 30)

    counts = {"processed": 0, "renamed": 0, "skipped_generic": 0, "skipped_no_gemini": 0, "skipped_no_change":0}
    all_files_in_dir = []
    try: all_files_in_dir = os.listdir(MUSIC_DIR)
    except Exception as e: print(f"ERROR: Could not list directory '{MUSIC_DIR}': {e}"); return
    print(f"Found {len(all_files_in_dir)} items in the directory.")

    for current_filename_str in all_files_in_dir:
        core_info, stem_type, original_ext, is_raw = ("Err", "Err", "", False)
        current_file_path = pathlib.Path(MUSIC_DIR) / current_filename_str

        if not (current_file_path.is_file() and current_file_path.suffix.lower() in AUDIO_EXTENSIONS):
            continue
        
        counts["processed"] += 1
        print(f"\nProcessing ({counts['processed']}): {current_filename_str}")
        try:
            core_info, stem_type, original_ext, is_raw = preprocess_mvsep_filename(current_filename_str)
            print(f"  Pre-processed: Core='{core_info}', Stem='{stem_type if stem_type else 'N/A'}', Ext='{original_ext}', IsRawMVSEP='{is_raw}'")

            if not core_info or core_info.lower() in ["input", "audio", "track", "untitled", "temp", "unknown"]:
                print(f"  Skipped (pre-process): Core info '{core_info}' is too generic.")
                counts["skipped_generic"] +=1; continue

            new_name_suggestion = get_formatted_name_from_gemini(core_info, stem_type, current_filename_str, is_raw)

            if new_name_suggestion == "NO_CHANGE_NEEDED_AS_IS":
                print(f"  Skipped (no change needed): Gemini indicates '{current_filename_str}' is well-formatted.")
                counts["skipped_no_change"] +=1; continue
            
            if new_name_suggestion:
                clean_new_name_base = sanitize_filename(new_name_suggestion)

                # --- Post-process Gemini's suggestion ---
                # 1. Remove "Unknown Artist - " prefix if present
                if clean_new_name_base.lower().startswith("unknown artist - "):
                    clean_new_name_base = clean_new_name_base[len("Unknown Artist - "):].strip()
                
                # 2. Ensure "feat." or "ft." has a period
                #    \b for word boundary, (?!\.) to ensure no dot already exists if Gemini added one.
                clean_new_name_base = re.sub(r'\b(feat)(?!\.)\b', r'feat.', clean_new_name_base, flags=re.IGNORECASE)
                clean_new_name_base = re.sub(r'\b(ft)(?!\.)\b', r'ft.', clean_new_name_base, flags=re.IGNORECASE)
                # Correct potential double dots (e.g., if original had "feat." and regex added another)
                clean_new_name_base = clean_new_name_base.replace('feat..', 'feat.').replace('ft..', 'ft.')
                # --- End Post-process ---

                if not clean_new_name_base: # Check after stripping "Unknown Artist"
                    print(f"  Skipped (empty suggestion): Name became empty after processing for '{current_filename_str}'.")
                    counts["skipped_no_gemini"] +=1; continue
                
                new_filename_str = clean_new_name_base + original_ext
                new_file_path = pathlib.Path(MUSIC_DIR) / new_filename_str

                # --- Refined Skip Logic for already good/no change files ---
                if not is_raw: 
                    original_stem_lower = current_file_path.stem.lower()
                    if new_filename_str.lower() == current_filename_str.lower():
                        print(f"  Skipped (already good): File '{current_filename_str}' confirmed by Gemini (case or identical).")
                        counts["skipped_no_change"] +=1; continue
                    elif not '(' in current_file_path.stem and \
                         clean_new_name_base.lower() == f"{current_file_path.stem.lower()} (full mix)":
                        print(f"  Skipped (already good): Original '{current_filename_str}' became '{new_filename_str}' by adding (Full Mix).")
                        counts["skipped_no_change"] +=1; continue
                
                if new_filename_str == current_filename_str: 
                    print(f"  Skipped (no change): Suggested name '{new_filename_str}' is identical to current.")
                    counts["skipped_no_change"] +=1; continue
                # --- End Refined Skip Logic ---
                
                print(f"  Gemini Suggestion (final): '{new_filename_str}'") # Changed label for clarity

                if not DRY_RUN:
                    try:
                        if new_file_path.exists() and current_file_path.resolve() != new_file_path.resolve():
                            print(f"  WARNING: Target file '{new_filename_str}' already exists. Skipping rename.")
                        else:
                            current_file_path.rename(new_file_path)
                            print(f"  SUCCESS: Renamed to '{new_filename_str}'")
                            counts["renamed"] += 1
                    except Exception as e_rename: print(f"  ERROR: Could not rename file: {e_rename}")
                else: 
                    if new_file_path is None: 
                        print(f"  DRY RUN ERROR: new_file_path is None for '{current_filename_str}'.")
                        continue
                    if new_file_path.exists() and current_file_path.resolve() != new_file_path.resolve():
                         print(f"  DRY RUN: Would attempt rename, but target '{new_filename_str}' already exists.")
                    else: print(f"  DRY RUN: Would rename '{current_filename_str}' to '{new_filename_str}'")
            else:
                print(f"  Skipped (no suggestion): No valid suggestion from Gemini for '{current_filename_str}'.")
                counts["skipped_no_gemini"] +=1
        except Exception as e_main_loop:
            print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"!!! UNEXPECTED ERROR processing file: {current_filename_str} !!!")
            print(f"Error Type: {type(e_main_loop).__name__}, Details: {e_main_loop}")
            print(f"State: Core='{core_info}', Stem='{stem_type if stem_type else 'N/A'}', IsRaw='{is_raw}'")
            traceback.print_exc(); print("--- Traceback End ---")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\nAttempting to continue...")
    
    print("-" * 30 + "\n--- Summary ---")
    print(f"Total items scanned: {len(all_files_in_dir)}")
    print(f"Audio files processed: {counts['processed']}")
    print(f"Skipped (generic pre-processed name): {counts['skipped_generic']}")
    print(f"Skipped (no Gemini suggestion/unknown format): {counts['skipped_no_gemini']}")
    print(f"Skipped (already well-formatted/no change needed): {counts['skipped_no_change']}")
    if DRY_RUN: print(f"Files that would be renamed: {counts['renamed']} (DRY RUN WAS ACTIVE)")
    else: print(f"Files successfully renamed: {counts['renamed']}")
    print("--- Script Finished ---")

if __name__ == "__main__":
    rename_files_in_current_directory()