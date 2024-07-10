import os
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont, messagebox
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Global variables
dictionary_path = r"C:\Users\style\Desktop\10 july py\TEST 1 F W.txt"
no_meaning_path = r"C:\Users\style\Desktop\10 july py\TEST 2 N F.txt"

# Function to build dictionary from TXT file
def build_dictionary(file_path):
    word_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if '=' in line:
                english_word, bangla_meanings = line.split('=', 1)
                bangla_meanings = bangla_meanings.strip()
                meanings_list = [meaning.strip() for meaning in bangla_meanings.split(',')]
                word_dict[english_word.strip().lower()] = meanings_list
    return word_dict

# Function to build a set of words with no meanings
def build_no_meaning_set(file_path):
    no_meaning_set = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                no_meaning_set.add(line.strip().lower())
    return no_meaning_set

# Function to get meaning of a word from dictionary only
def get_local_meaning(word, word_dict, no_meaning_set):
    meanings = word_dict.get(word.lower(), [])
    if meanings:
        return ', '.join(meanings)
    elif word.lower() in no_meaning_set:
        return f"{word} = found Loc Without Bang Mean"
    return ""

# Function to get meaning of a word from dictionary or online
def get_meaning(word, word_dict, no_meaning_set):
    meanings = get_local_meaning(word, word_dict, no_meaning_set)
    if meanings:
        return meanings
    return search_online(word)

# Function to search meaning online
def search_online(word):
    original_word = word
    if word.endswith('s'):
        word = word[:-1]  # Remove the 's' at the end
    
    url = f"https://www.english-bangla.com/dictionary/{word}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        return f"not found online for '{original_word}'"
    else:
        soup = BeautifulSoup(response.content, 'html.parser')
        span_tags = soup.find_all('span', class_='format1')
        
        if not span_tags:
            alt_meaning_tag = soup.find('span', class_='meaning')
            if alt_meaning_tag:
                alt_meaning_text = alt_meaning_tag.text.strip()
                return alt_meaning_text.split(' ', 1)[-1].strip()
            else:
                return search_alternate_online(original_word)
        else:
            meanings = [span.text.strip().split(' ', 1)[-1].strip() for span in span_tags]
            return ', '.join(meanings)

# Function to search meaning online on an alternate site
def search_alternate_online(word):
    url = f"https://www.shabdkosh.com/search-dictionary?lc=bn&sl=en&tl=bn&e={word}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"not found online for '{word}'"

    soup = BeautifulSoup(response.content, 'html.parser')
    meaning_tags = soup.find_all('li', class_='d-flex justify-content-between flex-wrap ps-3 mn-item')

    if not meaning_tags:
        return f"not found '{word}'"

    meanings = [tag.find('a', class_='e in l ms-2').text.strip() for tag in meaning_tags]
    return ', '.join(meanings)

# Function to handle button click event for local dictionary search
def search_local_meaning():
    input_text = input_entry.get("1.0", tk.END).strip()
    words_after, cleaned_text, num_words_before, num_words_after, removed_count = process_input_text(input_text)
    
    print(f"Cleaned text: {cleaned_text}")
    print(f"Number of words before: {num_words_before}")
    print(f"Number of words after: {num_words_after}")
    print(f"Number of removed characters: {removed_count}")

    results_text.delete("1.0", tk.END)  # Clear previous results
    not_found_text.delete("1.0", tk.END)  # Clear previous not found words
    
    results = [(word, get_local_meaning(word, word_dict, no_meaning_set)) for word in words_after]
    not_found_words = [word for word, meaning in results if not meaning]
    
    for word, meaning in results:
        if meaning:
            results_text.insert(tk.END, f"{word}: {meaning}\n")
            results_text.tag_configure(word, font=('Helvetica', 30, 'bold'), foreground='blue')  # Change font size and color
            results_text.tag_add(word, f"{results_text.index(tk.END)} - {len(meaning) + 2} chars linestart", f"{results_text.index(tk.END)} linestart + {len(word)} chars")

    not_found_text.insert(tk.END, " ".join(not_found_words))

# Function to handle button click event for online search only
def search_online_meaning():
    input_text = input_entry.get("1.0", tk.END).strip()
    words_after, cleaned_text, num_words_before, num_words_after, removed_count = process_input_text(input_text)

    print(f"Cleaned text: {cleaned_text}")
    print(f"Number of words before: {num_words_before}")
    print(f"Number of words after: {num_words_after}")
    print(f"Number of removed characters: {removed_count}")

    results_text.delete("1.0", tk.END)  # Clear previous results
    
    with tqdm(total=len(words_after), desc="Searching online") as pbar:
        for word in words_after:
            meaning = get_meaning(word, word_dict, no_meaning_set)
            results_text.insert(tk.END, f"{word}: {meaning}\n")
            results_text.tag_configure(word, font=('Helvetica', 30, 'bold'), foreground='green')  # Change font size and color
            results_text.tag_add(word, f"{results_text.index(tk.END)} - {len(meaning) + 2} chars linestart", f"{results_text.index(tk.END)} linestart + {len(word)} chars")
            pbar.update(1)  # Update progress bar
            
            if meaning and word.lower() not in word_dict:
                if "not found online" in meaning or "not found" in meaning:
                    store_no_meaning_word(word)
                else:
                    store_word(word, meaning)

# Function to store a new word in the dictionary file
def store_word(word, meaning):
    if re.search('[\u0980-\u09FF]', meaning):
        with open(dictionary_path, 'a', encoding='utf-8') as file:
            file.write(f"{word} = {meaning}\n")
        word_dict[word.lower()] = meaning.split(', ')  # Update local dictionary cache

# Function to store words with no Bangla meaning in a file
def store_no_meaning_word(word):
    word = word.lower()
    if word not in no_meaning_set:
        no_meaning_set.add(word)
        with open(no_meaning_path, 'a', encoding='utf-8') as file:
            file.write(f"{word}\n")

# Function to handle button click event for displaying stored words
def show_stored_words():
    stored_words = list(word_dict.keys())
    stored_words_text.delete("1.0", tk.END)  # Clear previous stored words

    if stored_words:
        stored_words_text.insert(tk.END, "\n".join(stored_words))
    else:
        stored_words_text.insert(tk.END, "No stored words.")

# Function to process input text
def process_input_text(input_text):
    lower_input_text = input_text.lower()
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz '
    cleaned_text = ""
    removed_count = 0

    for char in lower_input_text:
        if char in allowed_chars:
            cleaned_text += char
        else:
            cleaned_text += " "
            removed_count += 1

    cleaned_text = ' '.join(cleaned_text.split())
    words_after = list(set(cleaned_text.split()))

    words_before = lower_input_text.split()
    num_words_before = len(words_before)
    num_words_after = len(words_after)

    return words_after, cleaned_text, num_words_before, num_words_after, removed_count

# Tkinter GUI setup
root = tk.Tk()
root.title("Word Meaning Finder")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Label and text area for user input
input_label = ttk.Label(frame, text="Enter words separated by spaces:")
input_label.grid(row=0, column=0, sticky=tk.W)

input_entry = scrolledtext.ScrolledText(frame, width=80, height=10)
input_entry.grid(row=1, column=0, columnspan=2)

# Button to search for local dictionary meanings
local_search_button = ttk.Button(frame, text="Search Local", command=search_local_meaning)
local_search_button.grid(row=2, column=0, pady=10, sticky=tk.W)

# Button to search for online meanings
online_search_button = ttk.Button(frame, text="Search Online", command=search_online_meaning)
online_search_button.grid(row=2, column=1, pady=10, sticky=tk.E)

# Text area to display results
results_text = scrolledtext.ScrolledText(frame, width=80, height=20)
results_text.grid(row=3, column=0, columnspan=2)

# Text area to display not found words
not_found_label = ttk.Label(frame, text="Words not found:")
not_found_label.grid(row=4, column=0, sticky=tk.W)

not_found_text = scrolledtext.ScrolledText(frame, width=80, height=5)
not_found_text.grid(row=5, column=0, columnspan=2)

# Button to show stored words
stored_words_button = ttk.Button(frame, text="Show Stored Words", command=show_stored_words)
stored_words_button.grid(row=6, column=0, columnspan=2, pady=10)

# Text area to display stored words
stored_words_text = scrolledtext.ScrolledText(frame, width=80, height=10)
stored_words_text.grid(row=7, column=0, columnspan=2)

# Initialize dictionary and no meaning set
word_dict = build_dictionary(dictionary_path)
no_meaning_set = build_no_meaning_set(no_meaning_path)

# Run the GUI event loop
root.mainloop()
