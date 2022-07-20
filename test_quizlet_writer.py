import time
from unittest import TestCase

from quizlet_writer import *


class TestWordOptionsFrame(TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.frame = WordOptions(self.root)
        self.frame.grid_frame(row=0, column=0)

    def test_is_ordered_and_capitalized(self):
        alph_box, cap_box = self.frame.get_alph_ord_checkbox(), self.frame.get_capitalized_checkbox()
        assert not (self.frame.is_ordered() or self.frame.is_capitalized()), "The default value for both checkboxes is " \
                                                                             "False"
        alph_box.invoke()
        assert self.frame.is_ordered(), "The alph box was activated"

        cap_box.invoke()
        assert self.frame.is_capitalized(), "The cap box was activated"

        alph_box.invoke()
        cap_box.invoke()

        assert not (self.frame.is_ordered() or self.frame.is_capitalized()), "The value has to be False again"

    def test_get_separator_and_valid_entry(self):
        sep_e = self.frame.get_separator_entry()
        assert sep_e.get() == ',', "',' is a default value"
        sep_e.delete(0)
        sep_e.insert(0, '_')
        assert sep_e.get() == '_', "'_' was inserted"
        sep_e.delete(0)
        assert sep_e.get() == '', "'' should be a separator"
        sep_e.insert(0, 'k')
        assert sep_e.get() == '', "'k' is not a valid input"
        sep_e.insert(0, 'OH CANADA, OUR HOME AND NATIVE LAND')
        assert sep_e.get() == '', "Canadian anthem is not a valid separator"

        invalid_inputs = ('123', 'l', 'A', 'A_', '_F', '=-', 'UwU', ":)", "8===3")
        for inp in invalid_inputs:
            sep_e.delete(0, tk.END)
            sep_e.insert(0, inp)
            assert sep_e.get() == '', f"{inp} is not a valid input"


class TestWebDriver(TestCase):
    def setUp(self) -> None:
        self.web_driver = WebDriver()

    def test_log_in(self):
        incorrect_userdata = (('1', '3'),
                              ('Pashok_Kalashnikov', '12345'),
                              ('12345', 'Pashok_Kalashnikov'))

        for data in incorrect_userdata:
            assert not self.web_driver.log_in(*data), f"{data[0]} and {data[1]} aren't valid"

        assert self.web_driver.log_in("Pashok_Kalashnikov", 'vipua2000228'), "This should be valid"

    def test_del_duplicates(self):
        # Case 1: No duplicates
        words1 = ['Pashok', 'Pashtet', 'Lol']
        self.web_driver._del_duplicates(words1)
        assert words1 == ['Pashok', 'Pashtet', 'Lol']

        # Case 2: Duplicate at index 1
        words2 = ['Pashok', 'Pashok']
        self.web_driver._del_duplicates(words2)
        assert words2 == ['Pashok']

        # Case 3: Duplicate at the last index
        words3 = ['Pashok', 'Pashtet', 'Pashok']
        self.web_driver._del_duplicates(words3)
        assert words3 == ['Pashok', 'Pashtet']

        # Case 4: Duplicate in the middle
        words4 = ["Pashok", 'Kukech', 'Kukech']
        self.web_driver._del_duplicates(words4)
        assert words4 == ['Pashok', 'Kukech']

        # Case 5: Two pairs of duplicates
        words5 = ['1', '1', '2', '3', '2']
        self.web_driver._del_duplicates(words5)
        assert words5 == ['1', '2', '3']

        # Case 6: Three duplicates
        words6 = ['A', 'B', 'B', 'B', 'C', 'A']
        self.web_driver._del_duplicates(words6)
        assert words6 == ['A', 'B', 'C']

    def test_get_definitions(self):
        self.web_driver.log_in("Pashok_Kalashnikov", "vipua2000228")

        # Test 1: Words that have definitions
        words1 = ('Tree', 'Feedback', 'Water', 'Jacket', 'Canada', 'Diploma', 'Siren')
        definitions1 = self.web_driver.get_definitions(words1)
        assert all(definitions1), "Every word should have a definition"
        for i in range(len(definitions1) - 1):
            for j in range(i + 1, len(definitions1)):
                assert definitions1[i] != definitions1[j], "All defs have to be identical"
        print(definitions1)

        # Test 2.1: 77 random words.
        words2_1 = ('addition', 'additional', 'address', 'adequate', 'adjust', 'adjustment', 'administration',
                    'administrator', 'admire', 'admission', 'admit', 'adolescent', 'adopt', 'adult', 'advance',
                    'advanced', 'advantage', 'adventure', 'advertising', 'advice', 'advise', 'adviser', 'advocate',
                    'affair', 'affect', 'afford', 'afraid', 'African', 'African-American', 'after', 'afternoon',
                    'again',
                    'against', 'age', 'agency', 'agenda', 'agent', 'aggressive', 'ago', 'agree', 'agreement',
                    'agricultural', 'ah', 'ahead', 'aid', 'aide', 'AIDS', 'aim', 'air', 'aircraft', 'airline',
                    'airport',
                    'album', 'alcohol', 'alive', 'all', 'alliance', 'allow', 'ally', 'almost', 'alone', 'along',
                    'already', 'also', 'alter', 'alternative', 'although', 'always', 'AM', 'amazing', 'American',
                    'among', 'amount', 'analysis', 'analyst', 'analyze', 'ancient')
        t0 = time.perf_counter()
        definitions2_1 = self.web_driver.get_definitions(words2_1)
        t1 = time.perf_counter()
        print(f"{len(words2_1)} words were found in {t1 - t0:.2f} seconds\n"
              f"The words are:\n")
        for w, d in zip(words2_1, definitions2_1):
            print(f"{w} - {d}")

        # Test 2.2: 100 random words, with duplicates
        words2_2 = ('bishop', 'redamage', 'laddery', 'scabbedness', 'supersubstantial', 'recalcitration', 'consent',
                    'nonsacramental', 'nonatheistic', 'nonteacher', 'manky', 'premenaced', 'repasting', 'radiophoto',
                    'classier', 'dowse', 'forme', 'menispermaceous', 'misoccupying', 'rod', 'dia', 'gnathonically',
                    'counterjumper', 'unbrought', 'mesdames', 'hangable', 'preconversational', 'crucian', 'skelly',
                    'snowk', 'teahouse', 'nipper', 'unweldable', 'singultus', 'nonchemist', 'seraglios',
                    'nontraceability', 'stormlessness', 'gouge', 'auspicating', 'steeplebush', 'apostolate',
                    'antiradiating', 'firsthand', 'inflammableness', 'hiccuping', 'honeycreeper', 'pilgrimatic',
                    'stupefying', 'hilliard', 'unhappy', 'nonperiodic', 'preimpart', 'intenerating', 'pastoralist',
                    'untaunted', 'insphere', 'fernbrake', 'lilies', 'noncooperator', 'remeasurement', 'notchy',
                    'infinitively', 'unconfiscatory', 'prussianise', 'thumbscrew', 'scruffiest', 'conspectus',
                    'synoekete', 'infibulate', 'kingsburg', 'gondwana', 'reobligating', 'arizonan', 'retaste',
                    'paperer',
                    'subjacent', 'unlacerated', 'academicals', 'colonus', 'jacinth', 'par', 'bartholdi',
                    'renormalization', 'pyrrhuloxia', 'manslayer', 'supertragedy', 'semiparalytic', 'misruled',
                    'sappiness', 'microenvironmental', 'unfoul', 'ontogenesis', 'ganoblast', 'driving', 'unbreakable',
                    'empalement', 'nonexertive', 'pharmacopoeia', 'accreditati')
        t0 = time.perf_counter()
        definitions2_2 = self.web_driver.get_definitions(words2_2)
        t1 = time.perf_counter()
        print(f"{len(words2_2)} words were found in {t1 - t0:.2f} seconds\n"
              f"The words are:\n")
        for w, d in zip(words2_2, definitions2_2):
            print(f"{w} - {d}")

        # Test 3: At least two duplicate words, both consecutive and not
        words3 = ["hell", "hello", 'hell', 'hell', 'wow', 'wow']
        t0 = time.perf_counter()
        definitions3 = self.web_driver.get_definitions(words3)
        t1 = time.perf_counter()
        self.web_driver._del_duplicates(words3)
        print(f"{len(words3)} words were found in {t1 - t0:.2f} seconds\n"
              f"The words are:\n")
        for w, d in zip(words3, definitions3):
            print(f"{w} - {d}")

        # Test 4: Made-up words
        words4 = ["Kuklina", "Kukech", "Koldynchik", "Lanarata", "SlavaUkraini"]
        t0 = time.perf_counter()
        definitions4 = self.web_driver.get_definitions(words4)
        t1 = time.perf_counter()
        self.web_driver._del_duplicates(words4)
        print(f"{len(words4)} words were found in {t1 - t0:.2f} seconds\n"
              f"The words are:\n")
        for w, d in zip(words4, definitions4):
            print(f"{w} - {d}")

    def tearDown(self) -> None:
        self.web_driver.quit()


class TestUserData(TestCase):
    def test_update_userdata(self):
        user_data = UserData()
        user_data.update_userdata()

        # Case 1: File is formatted correctly
        with open("user_data.txt", 'r') as file:
            username, password = [l.strip() for l in file]
            assert user_data.get_userdata() == (username, password), "UserData has been updated"

        # Case 2: File is not formatted correctly
        with open("user_data.txt", 'w+') as file:
            print("I", "want", "pizza", sep='\n', file=file)

        with self.assertRaises(ValueError, msg='File is not formatted correctly'):
            user_data.update_userdata()

        user_data.set_userdata(username, password)
        user_data.save_file()


class TestQuizLetWriterApp(TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.app = QuizLetWriterApp(self.root)
        self.driver = vars(self.app)["_QuizLetWriterApp__web_driver"]

    def test__log_in(self):
        user_data = vars(self.app)["_QuizLetWriterApp__user_data"]
        pop_up_form = vars(self.app)["_QuizLetWriterApp__user_data_form"]
        ok_btn = vars(pop_up_form)["_UserDataForm__ok_btn"]
        cancel_btn = vars(pop_up_form)["_UserDataForm__cancel_btn"]
        name_entry = vars(pop_up_form)["_UserDataForm__username_e"]
        pop_up_form_window = vars(pop_up_form)["_UserDataForm__userdata_window"]

        # Case 1: File is empty
        user_data.clear_file()
        self.app._log_in()
        assert pop_up_form.is_popped(), "Form should pop up when the file is empty"
        cancel_btn.invoke()

        # Case 2: File is formatted correctly
        test_name, test_pass = 'pashok', '12345'
        with open("user_data.txt", 'w') as file:
            print(test_name, test_pass, sep='\n', file=file)
        self.app._log_in()
        assert user_data.get_userdata() == (test_name, test_pass), "UserData should've been updated"

        # Case 3.1: File is not formatted correctly
        with open("user_data.txt", 'w') as file:
            print('Magnum', 'Opus', 'Vae Victis', sep='\n', file=file)
        self.app._log_in()
        self.root.update()
        assert pop_up_form.is_popped(), "Form should pop up after the error"
        cancel_btn.invoke()
        with open("user_data.txt", "r") as file:
            assert file.read() == '', "File should be cleared after the error message and pressed cancel button"

    def test__load_words(self):
        self.driver.log_in("Pashok_Kalashnikov", "vipua2000228")
        def1 = ['separate compartment in which water levels rise and fall in order to raise or lower boats on a canal',
                'to burn with a hot iron or a chemical to destroy abnormal tissue and/or to stop infection and/or '
                'bleeding',
                'To prevent changes in; to hold steady']
        def2 = []
        def3 = []
        table = vars(self.app)["_QuizLetWriterApp__table"]

        # Case 1: The table is empty
        self.app._load_words()
        print(def1, [d[1] for d in table._get_words_and_definitions()], sep='\n')

        # Case 2: The table is not empty; the user cancels modifications

        # Case 3: The table is not empty; the user accepts modifications
        self.fail()

    def tearDown(self) -> None:
        self.driver.quit()
