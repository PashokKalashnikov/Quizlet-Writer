# TODO:
#   1. Log into account (Done (?))
#       1.1. Ask for a name & description
#   2. Load words from a text file (Done)
#   3. Find matching definitions (Done)
#   4. Upload words to the table (Done)
#   5. Upload words to the website (In progress)
#   6. Make a transition stages between the first 3 steps, so 2nd can't run until 1 is done and so on.

# FIXME: Redesign the interactions between UserData / UserDataForm / WebDriver objects (and Table & WebDriver in future)
#   They should interact with each other in QuizLetApp class.

import os
import tkinter as tk
from string import ascii_lowercase as alphabet
from string import digits
from tkinter import filedialog, messagebox
from tkinter import ttk

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def center_window_in_parent(window, parent):
    window.update()
    parent_x, parent_y = parent.winfo_x(), parent.winfo_y()
    parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
    w, h = window.winfo_width(), window.winfo_height()
    x = (parent_width - w) // 2 + parent_x
    y = (parent_height - h) // 2 + parent_y

    window.geometry(f"{w}x{h}+{x}+{y}")  # widthxheight+x+y


class elements_have_error(object):
    """
    An expectation that either of the label elements have an error

    Returns the element and False if neither has an error
    """

    def __init__(self, locator):
        """Locator (tuple) - used to find the elements. Example: (By.XPATH, "//form[@class=LoginForm]")"""
        self.locator = locator

    def __call__(self, driver):
        elements = driver.find_elements(*self.locator)
        for el in elements:
            if el.get_attribute("aria-invalid") == 'true':
                return el
        return False


class element_has_new_text(object):
    """
    An expectation that the AutoSuggested element either has a new text or an empty string

    Returns the element, if either condition is True and False otherwise.
    """

    def __init__(self, parent, locator, old_defs):
        """
        Inputs:
        parent (WebElement): a parent element to AugoSuggested el.
        locator (Tuple[By.x, str]): a locator tuple
        old_defs (List): a list with old definitions
        """
        self.parent = parent
        self.locator = locator
        self.old_defs = old_defs

    def __call__(self, driver):
        """
        Returns the element, if the element's text is either empty or has at least one new definition. False
        otherwise.

        Raises NoSuchElementException, if the AugoSuggest element is not found
        """
        element = self.parent.find_element(*self.locator)
        new_defs = [t for t in element.text.split('\n')]
        for d in new_defs:
            if d not in self.old_defs:
                return element
        return len(new_defs) == 0


class WebDriver:
    """Interacts with the Quizlet"""
    SUCCESSFUL_LOGIN_PAGE = 'https://quizlet.com/latest'
    NEW_QUIZ_PAGE = 'https://quizlet.com/create-set'
    WEBSITE_PAGE = 'https://quizlet.com/'

    def __init__(self):
        # Log in button isn't clickable in headless mode.
        chrome_options = ChromeOptions()
        chrome_options.set_capability('unhandledPromptBehavior', 'accept')
        driver_path = os.path.join(os.path.curdir, "chromedriver.exe")
        self.__driver = webdriver.Chrome(driver_path, options=chrome_options)
        self.__window_handle = self.__driver.current_window_handle

    def _restore_window(self):
        """Properly deiconifies the webdriver"""
        self.__driver.switch_to.window(self.__window_handle)
        self.__driver.set_window_rect(0, 0)

    def log_in(self, username, password) -> bool:
        """Tries to log in with the given userdata and returns True if successful. False otherwise."""
        try:
            self._navigate_to_log_in_form()
            username_entry, password_entry, log_in_btn = self._get_log_in_elements()
            username_entry.send_keys(username)
            password_entry.send_keys(password)
            log_in_btn.click()
            return self._is_successful()
        except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
            pass

    def upload_quiz(self, quiz_name: str, quiz_description: str, words_and_definitions):
        """Uploads a quiz with a given name/description and terms to the website"""
        # Navigate to a new set
        self._navigate_to_new_set()

        # Get quiz_name/descr text entries, insert given arguments
        quiz_name_e, quiz_descr_e = self._get_quiz_entries()
        quiz_name_e.send_keys(quiz_name)
        quiz_descr_e.send_keys(quiz_description)

        # Get all entries, clear them
        term_entries = self._get_term_entries(len(words_and_definitions))

        # Insert words into entries
        for i in range(len(words_and_definitions)):
            w_e, d_e = term_entries[i]
            word, definition = words_and_definitions[i]
            w_e.send_keys(word)
            d_e.send_keys(definition)

        """
        1. If there is not enough entries, create rows and append them to the term entries 
        """
        print('Uploaded', quiz_name, quiz_description, *words_and_definitions)

    def _navigate_to_log_in_form(self):
        """Navigates the webdriver to the log in form"""
        self.__driver.get(WebDriver.WEBSITE_PAGE)
        self._restore_window()
        wait = WebDriverWait(self.__driver, 10)
        log_in_el = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='SiteNavLoginSection']/button[@aria-label='Log in']")),
            "Log in button is not clickable"
        )
        log_in_el.click()

    def _navigate_to_new_set(self):
        """Navigates the webdriver to the new set page"""
        self.__driver.get(WebDriver.NEW_QUIZ_PAGE)
        self._restore_window()
        try:
            self.__driver.implicitly_wait(2)
            self.__driver.find_element_by_xpath("//div[@class='UINotification UINotification--default']"
                                                "//button[@class='UILink']").click()
            try:
                self.__driver.implicitly_wait(2)
                self.__driver.find_element_by_xpath("//button[@class='UILink UILink--revert']").click()
            except NoSuchElementException:
                pass
        except NoSuchElementException:
            pass

    def _get_log_in_elements(self):
        """
        Returns the elements of the log-in form in a tuple with the following indices

        0 - username_entry
        1 - password_entry
        2 - log_in_btn
        """

        login_form = self.__driver.find_element_by_xpath(r"//form[@class='LoginPromptModal-form']")
        username_entry = login_form.find_element_by_xpath(r"//input[@id='username']")
        password_entry = login_form.find_element_by_xpath(r"//input[@id='password']")

        wait = WebDriverWait(self.__driver, 10)
        log_in_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, r"//form[@class='LoginPromptModal-form']//button[@aria-label='Log in']")
        ))
        return username_entry, password_entry, log_in_btn

    def _is_successful(self):
        """Returns True, if login was successful. False otherwise"""
        wait = WebDriverWait(self.__driver, 3)

        try:
            wait.until(elements_have_error(
                (By.XPATH, r"//form[@class='LoginPromptModal-form']"
                           r"//label[@class='AssemblyInput AssemblyInput--filled']"))
            )
            return False
        except TimeoutException as e:
            return self.__driver.current_url == WebDriver.SUCCESSFUL_LOGIN_PAGE

    def _clear_text_entry(self, text_entry):
        """Clears the text in an text entry element"""
        while text_entry.text != '':
            try:
                text_entry.click()
                text_entry.send_keys(Keys.CONTROL + "a")
                text_entry.send_keys(Keys.DELETE)
                self.__driver.implicitly_wait(1)
            except ElementClickInterceptedException:
                pass

    def _get_quiz_entries(self):
        """Returns a tuple with name and description entries after clearing them"""
        elements_holder = self.__driver.find_element_by_xpath(r"//div[@class='CreateSetHeader-headingContent']")
        name_e = elements_holder.find_element_by_xpath(
            r"//textarea[@placeholder='Enter a title, like “Biology - Chapter 22: Evolution”']")
        descr_e = elements_holder.find_element_by_xpath(r"//textarea[@placeholder='Add a description...']")
        name_e.clear()
        descr_e.clear()
        return name_e, descr_e

    def _get_term_entries(self, n):
        """Returns a list of n tuples with term and definition entry"""
        term_rows = self.__driver.find_elements_by_xpath(r"//div[@class='TermRows-termRowWrap']")
        wait = WebDriverWait(self.__driver, 5, 0.5)

        # Creating additional entries, if needed
        while len(term_rows) < n:
            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, r"//button[@aria-label='+ Add card']"))).click()
                term_rows = self.__driver.find_elements_by_xpath(r"//div[@class='TermRows-termRowWrap']")
            except ElementClickInterceptedException:
                pass

        # Adding tuples with entries to the list
        term_entries = [t for t in zip(
            term_rows[0].find_elements_by_xpath(r"//div[@aria-labelledby='editor-term-side']"),
            term_rows[0].find_elements_by_xpath(r"//div[@aria-labelledby='editor-definition-side']")
        )]

        return term_entries

    def _get_definition_elements(self):
        """
        Returns first row elements in a tuple

        0 - term_row_wrap
        1 - password_entry
        2 - log_in_btn
        """
        term_row_wrap = self.__driver.find_element_by_xpath(
            "//div[@class='TermRows']/div/div[@data-term-luid='term-0']")
        word_entry = term_row_wrap.find_element_by_xpath("//div[@aria-labelledby='editor-term-side']")
        definition_entry = term_row_wrap.find_element_by_xpath("//div[@aria-labelledby='editor-definition-side']")
        return term_row_wrap, word_entry, definition_entry

    def _del_duplicates(self, words):
        """Deletes duplicate strings from words list"""
        assert len(words) > 0, "List should have at least one item"
        unique_words = set([words[0]])
        i = 1
        while i < len(words):
            if words[i] in unique_words:
                del (words[i])
            else:
                unique_words.add(words[i])
                i += 1

    def get_definitions(self, words):
        """
        Returns a list with definitions for each unique word in words list. Appends None if there is no definition.

        Input: words (iterable): an iterable with words

        Output: a list with definitions.
        """
        # Works, but the user must not interact with the browser (headless mode wouldn't allow this)
        try:
            definitions = []
            auto_defs = []
            words = list(words)

            # Create a new quiz, find entries
            self._navigate_to_new_set()
            term_row, word_entry, definition_entry = self._get_definition_elements()
            word_entry.clear()
            definition_entry.clear()
            wait = WebDriverWait(self.__driver, 4)

            # Delete all duplicates from words, but saves the order
            self._del_duplicates(words)

            # For each word, find an auto-suggested definition.
            for word in words:
                try:
                    word_entry.send_keys(word)
                    definition_entry.click()
                    auto_suggest_el = wait.until(
                        element_has_new_text(
                            term_row, (By.XPATH, "//div[@class='AutosuggestContext-suggestions']"), auto_defs
                        )
                    )
                    # Choose the longest proposed definition and append it to the definitions list
                    auto_defs = sorted([t for t in auto_suggest_el.text.split('\n')], key=len)
                    definitions.append(auto_defs[-1] if len(auto_defs) > 0 else None)
                    self._clear_text_entry(word_entry)
                except (NoSuchElementException, TimeoutException):
                    definitions.append(None)
                    self._clear_text_entry(word_entry)
            return definitions
        except (ElementNotInteractableException, StaleElementReferenceException):
            return self.get_definitions(words)
        except NoSuchElementException:
            messagebox.showerror("Error!", "Web elements could not be found. Retry to upload the words")

    def quit(self):
        self.__driver.quit()


class UserDataForm:
    """Creates a form, which pops up when UserData needs to be updated"""

    def __init__(self, parent, ok_fun):
        """Creates an instance of UserDataForm"""

        # Form with a parent
        self.__parent = parent
        self.__userdata_window = tk.Toplevel()
        self.__userdata_window.title("Insert your username & password")

        # Labels
        self.__username_lbl = tk.Label(self.__userdata_window, text="Username: ", justify=tk.LEFT)
        self.__password_lbl = tk.Label(self.__userdata_window, text="Password: ", justify=tk.LEFT)
        self.__remember_me_lbl = tk.Label(self.__userdata_window, text="Remember me")
        self.__show_pass_lbl = tk.Label(self.__userdata_window, text="Show password")

        # Entries
        self.__username_e = tk.Entry(self.__userdata_window, width=20)
        self.__password_e = tk.Entry(self.__userdata_window, width=20, show='*')

        # Checkbuttons with variables
        self.__remember_me_bool = tk.BooleanVar(self.__userdata_window, value=False)
        self.__remember_me_checkbtn = tk.Checkbutton(self.__userdata_window,
                                                     onvalue=True,
                                                     offvalue=False,
                                                     variable=self.__remember_me_bool)
        self.__show_pass_bool = tk.BooleanVar(self.__userdata_window, value=False)
        self.__show_pass_checkbutton = tk.Checkbutton(self.__userdata_window,
                                                      onvalue=True,
                                                      offvalue=False,
                                                      variable=self.__show_pass_bool,
                                                      command=self._show)
        # Function from QuizLetApp class
        self.__ok_fun = ok_fun

        # Buttons
        self.__ok_btn = tk.Button(self.__userdata_window, text='OK', command=self.__ok_fun)
        self.__cancel_btn = tk.Button(self.__userdata_window, text='Cancel', command=self._cancel)

        # Binding events
        self.__userdata_window.bind("<Return>", self._enter)
        self.__userdata_window.protocol('WM_DELETE_WINDOW', self.hide)

        # State
        self.__is_popped = False

        self._grid_widgets()
        self.__userdata_window.withdraw()

    def _set_default(self):
        """Sets all widgets values to default"""
        self.__username_e.delete(0, tk.END)
        self.__password_e.delete(0, tk.END)
        self.__remember_me_bool.set(False)
        self.__show_pass_bool.set(False)

    def _get_all_widgets(self):
        """
        Returns a tuple with widgets for testing

        Indices:
        0 - userdata_window
        1 - remember_me_bool
        2 - username_e
        3 - password_e
        4 - remember_me_checkbtn
        5 - show_pass_bool
        6 - ok_btn
        7 - cancel_btn
        """
        return self.__userdata_window, self.__remember_me_bool, self.__username_e, self.__password_e, \
               self.__remember_me_checkbtn, self.__show_pass_bool, self.__show_pass_checkbutton, self.__ok_btn, \
               self.__cancel_btn

    def _grid_widgets(self):
        """Grids widgets on the form"""
        self.__username_lbl.grid(row=0, column=0, sticky=tk.E)
        self.__username_e.grid(row=0, column=1)
        self.__remember_me_lbl.grid(row=0, column=2, sticky=tk.E)
        self.__remember_me_checkbtn.grid(row=0, column=3, sticky=tk.W)

        self.__password_lbl.grid(row=1, column=0, sticky=tk.E)
        self.__password_e.grid(row=1, column=1)
        self.__show_pass_lbl.grid(row=1, column=2, sticky=tk.E)
        self.__show_pass_checkbutton.grid(row=1, column=3, sticky=tk.W)

        self.__ok_btn.grid(row=2, column=1, sticky=tk.E + tk.W)
        self.__cancel_btn.grid(row=2, column=2, columnspan=2, sticky=tk.E + tk.W)

    def pop_up(self):
        """Pops up a form"""
        self._set_default()
        center_window_in_parent(self.__userdata_window, self.__parent)
        self.__userdata_window.deiconify()
        self.__userdata_window.grab_set()
        self.__username_e.focus()
        self.__is_popped = True

    def hide(self):
        """Hides the form"""
        self.__userdata_window.grab_release()
        self.__userdata_window.withdraw()
        self.__is_popped = False

    def _cancel(self):
        """Cancels any change to the userdata"""
        self.hide()

    def _enter(self, event=None):
        """Switches the focus between the entry and closes the form on the last entry"""
        if self.__userdata_window.focus_get() is self.__username_e:
            self.__password_e.focus_set()
        elif self.__userdata_window.focus_get() is self.__password_e:
            self.__ok_fun()

    def _show(self):
        """Makes the password entry visible, if it is invisible and vice versa"""
        self.__password_e.config(show='*' if not self.__show_pass_bool.get() else '')

    def is_empty(self):
        """Returns True if either username or password entries is empty. False otherwise"""
        return self.__username_e.get() == '' or self.__password_e.get() == ''

    def is_popped(self):
        """Returns the value of is_popped attribute"""
        return self.__is_popped

    def get_entries_values(self):
        """Returns the username and password stored in the entries in a tuple"""
        return self.__username_e.get(), self.__password_e.get()

    def remember_is_checked(self):
        """Returns the state of Remember Me checkbutton"""
        return self.__remember_me_bool.get()


class UserData:
    """Stores user data and loads it from a file, if present"""

    def __init__(self):
        self.__username = ''
        self.__password = ''

    def set_userdata(self, new_name, new_pass):
        """Sets new username and password"""
        self.__username = new_name
        self.__password = new_pass

    def get_userdata(self):
        """Returns username and password in a tuple"""
        return self.__username, self.__password

    def save_file(self):
        """Rewrites the userdata into a file"""
        with open("user_data.txt", "w") as file:
            print(f"{self.__username}\n"
                  f"{self.__password}", file=file)

    def clear_file(self):
        """Clears the file"""
        with open("user_data.txt", "w"):
            pass

    def update_userdata(self):
        """Sets username and password from the file. Raises ValueError exception, if the file is not
        formatted correctly"""
        with open("user_data.txt", "r") as file:
            file_lines = [l.strip() for l in file]
            if len(file_lines) == 2:
                self.__username, self.__password = file_lines
            else:
                raise ValueError("File is not formatted correctly")


class Table:
    """A table, on which words and definitions will be printed"""

    def __init__(self, parent):
        """
        Creates a frame with a treeview and buttons, which can be placed on a parent widget

        Inputs:
            parent (tk.Tk): a root widget, on which this instance can be placed
            headings (tuple): a tuple with strings, which contains the column names
            word_dictionary (list): a list of tuples with words and definitions, created in the application class
        """

        # Main frame
        self.__main_frame = tk.LabelFrame(parent)

        # Treeview instance
        self.__tree = ttk.Treeview(self.__main_frame)
        self.__tree.config(columns=('Word', 'Definition'))

        # Format columns
        self.__tree.column("#0", width=0, stretch=tk.NO)
        self.__tree.column("Word", width=80, minwidth=40, anchor=tk.W)
        self.__tree.column("Definition", width=200, minwidth=40, anchor=tk.W)

        # Format headings
        self.__tree.heading("#0", text='')
        self.__tree.heading("Word", text='Word', anchor=tk.CENTER, command=lambda: self.sort(0))
        self.__tree.heading('Definition', text='Definition', anchor=tk.CENTER, command=lambda: self.sort(1))

        # Buttons
        self.__del_button = tk.Button(self.__main_frame, text='Delete (Del)', command=self.delete_row)
        self.__modify_button = tk.Button(self.__main_frame, text='Modify (M)', command=self.modify_row)

        # Binding events to keys
        self.__tree.bind("<Double-Button-1>", lambda e: self.__modify_button.invoke())
        self.__tree.bind("<Key-m>", lambda e: self.__modify_button.invoke())
        self.__tree.bind("<Key-Delete>", lambda e: self.__del_button.invoke())

        self.pack_widgets()

    def pack_widgets(self):
        self.__tree.pack(side=tk.TOP)
        self.__del_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.__modify_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)

    def grid_table(self, **kwargs):
        self.__main_frame.grid(**kwargs)

    def clear(self):
        """Deletes all items from the table"""
        for c in self.__tree.get_children():
            self.__tree.delete(c)

    def append(self, word, definition):
        """Appends a word with its definition to the table"""
        if definition is None:
            definition = 'Not found'
        self.__tree.insert(parent='', index='end', values=(word, definition))

    def extend(self, words, definitions):
        """Appends all words and definitions to the table"""
        for w, d in zip(words, definitions):
            self.append(w, d)

    def delete_row(self, event=None):
        """Deletes a focused row from the table"""
        item_iid = self.__tree.focus()
        self.__tree.delete(item_iid)

    def modify_row(self, event=None):
        """Modifies the data on the selected row"""

        def ok():
            """Changes the data on the selected row"""
            item_iid = self.__tree.focus()
            new_word, new_def = new_word_e.get(), new_def_e.get()
            self.__tree.item(item_iid, values=(new_word, new_def))
            modify_window.destroy()

        def cancel():
            """Closes the form and does not change anything"""
            modify_window.destroy()

        def enter(event):
            """Switches the focus between the entries"""
            if event.widget is new_word_e:
                new_def_e.focus()
            elif event.widget is new_def_e:
                ok()

        if self.__tree.focus() != '':
            modify_window = tk.Toplevel()
            modify_window.title("Modify word & definition")

            new_word_lbl = tk.Label(modify_window, text='New word: ', justify=tk.LEFT)
            new_def_lbl = tk.Label(modify_window, text='New definition: ', justify=tk.LEFT)
            new_word_e = tk.Entry(modify_window, width=20)
            old_word = self.__tree.item(self.__tree.focus()).get('values')[0]
            new_word_e.insert(0, old_word)
            new_def_e = tk.Entry(modify_window, width=20)
            ok_button = tk.Button(modify_window, text='OK', command=ok)
            cancel_button = tk.Button(modify_window, text='Cancel', command=cancel)
            modify_window.bind("<Return>", enter)

            new_word_lbl.grid(row=0, column=0, sticky=tk.E)
            new_word_e.grid(row=0, column=1, columnspan=2)
            new_def_lbl.grid(row=1, column=0, sticky=tk.E)
            new_def_e.grid(row=1, column=1, columnspan=2)
            ok_button.grid(row=2, column=1, sticky=tk.E + tk.W)
            cancel_button.grid(row=2, column=2, sticky=tk.E + tk.W)
            parent = self.__main_frame._nametowidget(self.__main_frame.winfo_parent())

            center_window_in_parent(modify_window, parent)
            modify_window.grab_set()
            new_def_e.focus()

    def sort(self, col):
        """
        Sorts the table in alphabetical order with corresponding column, which is used as a key function

        Inputs:
            col (int): column numbers. Starts from 0
        """
        word_def_list = [self.__tree.item(iid).get('values') for iid in self.__tree.get_children()]
        word_def_list.sort(key=lambda x: x[col])
        self.clear()
        for row_data in word_def_list:
            self.append(*row_data)

    def configure_column(self, cid, **kwargs):
        """
        Configures the appearance of the logical column specified by cid

        Inputs:
            cid (str): a string identifier for a column (a heading which is set in the init method)
        """
        assert cid in self.__tree.cget('columns'), f"{cid} is not column identifier. Choose one from" \
                                                   f" {'-' + ' -'.join(self.__tree.cget('columns'))}"
        self.__tree.column(cid, **kwargs)

    def get_words_and_definitions(self):
        """Returns a list with tuples containing a word and a definition"""
        words_and_definitions = []
        for iid in self.__tree.get_children():
            w, d = self.__tree.item(iid)['values']
            words_and_definitions.append((w, d))
        return words_and_definitions

    def __len__(self):
        """Returns the number of words in the table"""
        return len(self.__tree.get_children())


class WordOptions:
    def __init__(self, parent):
        """
        Creates a frame with additional widgets, which can be placed on a parent widget

        Inputs:
            parent (tk.Tk): a root widget, on which this instance can be placed
        """

        # Main frame
        self.__word_options_frame = tk.LabelFrame(parent, text='Word options')

        # Labels
        self.__word_options_labels = tuple(tk.Label(self.__word_options_frame, text=t) for t in ('Separator:',
                                                                                                 'Alphabetical order:',
                                                                                                 'Capitalize:'))
        # Entry with a validation command
        self.__separator_entry = tk.Entry(self.__word_options_frame, width=3, justify=tk.CENTER)
        self.__separator_entry.insert(0, ',')
        validation = (parent.register(self.is_valid_entry), '%P')  # Tcl wrapper
        self.__separator_entry.config(validate='key', validatecommand=validation)

        # Checkbox and their variables
        self.__is_ordered = tk.BooleanVar(self.__word_options_frame, value=False)
        self.__is_capitalized = tk.BooleanVar(self.__word_options_frame, value=False)
        self.__alph_ord_checkbox = tk.Checkbutton(self.__word_options_frame, onvalue=True, offvalue=False,
                                                  variable=self.__is_ordered)
        self.__capitalized_checkbox = tk.Checkbutton(self.__word_options_frame, onvalue=True, offvalue=False,
                                                     variable=self.__is_capitalized)

        # Places all widgets on the frame
        self.grid_widgets()

    def grid_widgets(self):
        """Places widgets on the main frame"""
        temp = (self.__separator_entry, self.__alph_ord_checkbox, self.__capitalized_checkbox)
        for i in range(len(temp)):
            self.__word_options_labels[i].grid(row=i, column=0, sticky=tk.W)
            temp[i].grid(row=i, column=1, sticky=tk.W)

    def grid_frame(self, **kwargs):
        """Places the main frame on parent widget"""
        self.__word_options_frame.grid(**kwargs)

    def is_ordered(self):
        """Returns True if the corresponding checkbutton is activated. False otherwise"""
        return self.__is_ordered.get()

    def is_capitalized(self):
        """Returns True if the corresponding checkbutton is activated. False otherwise"""
        return self.__is_capitalized.get()

    def get_separator(self):
        """Returns the text from separator entry"""
        return self.__separator_entry.get()

    def get_separator_entry(self):
        """Returns the separator entry widget"""
        return self.__separator_entry

    def get_alph_ord_checkbox(self):
        """Returns the alph_ord_checkbox widget"""
        return self.__alph_ord_checkbox

    def get_capitalized_checkbox(self):
        """Returns the capitalized_checkbox widget"""
        return self.__capitalized_checkbox

    def is_valid_entry(self, text):
        """
        Validates text in the entry area if two conditions are satisfied:
            1. Text is not a digit or a character from English alphabet
            2. Length of the text is at most 1
        """
        if text.lower() not in set(alphabet + digits) and len(text) <= 1:
            if len(text) == 1:
                self.__word_options_frame.focus()
            return True
        else:
            return False


class QuizLetWriterApp:
    def __init__(self, parent):
        """
        Creates an instance of QuizLetWriterApp

        Inputs:
            parent (tk.Tk): a root widget

        Private attributes:
            pass
        """

        # Class instances initialization
        self.__word_options = WordOptions(parent)
        self.__web_driver = WebDriver()
        self.__user_data = UserData()
        self.__user_data_form = UserDataForm(parent, self._userdata_form_ok)
        self.__table = Table(parent)

        # Text entries initialization
        self.__name_lbl = tk.Label(parent, text="Quiz name:", justify=tk.LEFT)
        self.__name_e = tk.Entry(parent)
        self.__description_lbl = tk.Label(parent, text="Desription name:", justify=tk.LEFT)
        self.__description_e = tk.Entry(parent)

        # Buttons initialization
        self.__login_button = tk.Button(parent, text='Log in', command=self._log_in)
        self.__load_button = tk.Button(parent, text='Load words', command=self._load_words)
        self.__upload_button = tk.Button(parent, text='Upload words', command=self._upload_words)

        self.grid_widgets()

    def grid_widgets(self):
        """Places all defined widgets from __init__ method on the parent widget"""
        # Placing labels & entries
        self.__name_lbl.grid(row=0, column=0)
        self.__name_e.grid(row=0, column=1, columnspan=2, sticky=tk.E + tk.W)
        self.__description_lbl.grid(row=1, column=0)
        self.__description_e.grid(row=1, column=1, columnspan=2, sticky=tk.E + tk.W)

        # Placing a table
        self.__table.grid_table(row=2, column=0, columnspan=3)

        # Placing word options frame's widgets
        # self.__word_options.grid_frame(row=0, column=1, columnspan=3, sticky=tk.N)

        # Placing buttons
        self.__login_button.grid(row=3, column=0, sticky=tk.E + tk.W)
        self.__load_button.grid(row=3, column=1, sticky=tk.E + tk.W)
        self.__upload_button.grid(row=3, column=2, sticky=tk.E + tk.W)

    def _load_words(self):
        """Loads words from a file to the table. Assumes that the user is already logged in"""

        if self._is_update():
            self.__table.clear()
            file_path = self._get_path()
            words = []
            definitions = []
            with open(file_path, 'r') as file:
                for word in file.read().split(self.__word_options.get_separator()):
                    word = word.strip()
                    words.append(word)

            definitions = self.__web_driver.get_definitions(words)
            self.__table.extend(words, definitions)

    def _upload_words(self):
        """Uploads words from a table to QuizLet website"""

        """
        if there's no quiz_name -> pop up a warning message
        else ask webdriver to upload a new quiz with a given quiz name/descr
        """
        if self.__name_e.get() != '':
            quiz_name, quiz_description = self.__name_e.get(), self.__description_e.get()
            words_and_definitions = self.__table.get_words_and_definitions()
            self.__web_driver.upload_quiz(quiz_name, quiz_description, words_and_definitions)
        else:
            messagebox.showwarning("Title is missing!", "Please insert title for your quiz (description is optional)")

    def _is_update(self):
        """Returns True, if the table is empty or the user agrees to overwrite the words"""
        if len(self.__table) == 0:
            return True
        else:
            return tk.messagebox.askyesno(title="Rewriting", message="Would you like to overwrite the words?")

    def _get_path(self):
        """Returns a path to a text file with words, and an empty string if the filedialog was closed"""
        desktop_dir = os.path.join(os.path.expanduser("~"), "desktop")
        path = tk.filedialog.askopenfilename(initialdir=desktop_dir, title='Select a Text File',
                                             filetypes=[('Text file', '*.txt')])
        return path

    def _log_in(self):
        """Logs in on QuizLet Website. If successful, lets the user to upload the words"""
        with open("user_data.txt", "r") as file:
            file_lines = [l.strip() for l in file]
            if not file_lines:
                self.__user_data_form.pop_up()
            else:
                try:
                    self.__user_data.update_userdata()
                    self.try_to_log_in()
                except ValueError:
                    self.__user_data.clear_file()
                    messagebox.showerror("Error!", "The file was not formatted correctly. Please insert new userdata.")
                    self.__user_data_form.pop_up()

    def _userdata_form_ok(self):
        """Updates the UserData instance. Then calls try_to_log_in function"""
        if not self.__user_data_form.is_empty():
            self.__user_data_form.hide()
            username, password = self.__user_data_form.get_entries_values()
            self.__user_data.set_userdata(username, password)
            self.try_to_log_in()

    def try_to_log_in(self):
        """Tries to log in to QuizLet account"""
        username, password = self.__user_data.get_userdata()
        if self.__web_driver.log_in(username, password):
            if self.__user_data_form.remember_is_checked():
                self.__user_data.save_file()
        else:
            messagebox.showerror("Error!", "Provided userdata is not valid. Please, try again...")


def main():
    root = tk.Tk()
    QuizLetWriterApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
