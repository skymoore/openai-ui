import sys, os, re, json, openai

from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QWidget,
    QLineEdit,
    QGridLayout,
)

from PyQt5.QtGui import QIntValidator, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import Qt


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)

        # Define the formats for syntax highlighting
        self.format = QTextCharFormat()
        self.format.setForeground(QColor("#66d9ef"))
        self.format_parentheses = QTextCharFormat()
        self.format_parentheses.setForeground(QColor("#ffff00"))
        self.format_curly_braces = QTextCharFormat()
        self.format_curly_braces.setForeground(QColor("#ff0000"))
        self.format_square_brackets = QTextCharFormat()
        self.format_square_brackets.setForeground(QColor("#ffa500"))

        # Define the regular expressions for highlighting
        self.keywords = re.compile(
            "\\b(?:and|as|assert|break|class|continue|def|del|elif|else|except|False|finally|for|from|global|if|import|in|is|lambda|None|nonlocal|not|or|pass|raise|return|True|try|while|with|yield)\\b"
        )
        self.builtins = re.compile(
            "\\b(?:abs|all|any|bin|bool|bytearray|bytes|callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|eval|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|property|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip)\\b"
        )
        self.operators = re.compile("[-+*/%=<>!&|^~]")
        # Define the regular expression for highlighting brackets
        self.brackets = re.compile(r"\(|\)|\{|\}|\[|\]")

    def highlightBlock(self, text):
        # Apply the keyword highlighting
        matches = self.keywords.finditer(text)
        for match in matches:
            self.setFormat(match.start(), match.end() - match.start(), self.format)

        # Apply the built-in function highlighting
        matches = self.builtins.finditer(text)
        for match in matches:
            self.setFormat(match.start(), match.end() - match.start(), self.format)

        # Apply the operator highlighting
        matches = self.operators.finditer(text)
        for match in matches:
            self.setFormat(match.start(), match.end() - match.start(), self.format)

        # Apply the bracket highlighting
        matches = self.brackets.finditer(text)
        for match in matches:
            if match.group() == "(":
                self.setFormat(
                    match.start(), match.end() - match.start(), self.format_parentheses
                )
            elif match.group() == ")":
                self.setFormat(
                    match.start(), match.end() - match.start(), self.format_parentheses
                )
            elif match.group() == "{":
                self.setFormat(
                    match.start(), match.end() - match.start(), self.format_curly_braces
                )
            elif match.group() == "}":
                self.setFormat(
                    match.start(), match.end() - match.start(), self.format_curly_braces
                )
            elif match.group() == "[":
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    self.format_square_brackets,
                )
            elif match.group() == "]":
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    self.format_square_brackets,
                )


class OpenAICompletionUI(QWidget):
    def __init__(self):
        super().__init__()
        self.models = {
            "code-davinci-002": 8000,
            "code-cushman-001": 2048,
            "text-davinci-003": 4000,
            "text-curie-001": 2048,
            "text-babbage-001": 2048,
            "text-ada-001": 2048,
        }

        self.initUI()

    def initUI(self):
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setToolTip(
            "Enter your api key, get one at https://beta.openai.com/account/api-keys"
        )
        self.api_key_input.setText(self.read_api_key())
        self.api_key_input.textChanged[str].connect(self.on_api_key_changed)

        # Create a label for the dropdown menu
        model_label = QLabel("Model:")

        # Create the dropdown menu with the available models
        self.model_dropdown = QComboBox()
        for model in self.models:
            self.model_dropdown.addItem(model)
        self.model_dropdown.setToolTip("Select the model to use for completion")
        self.model_dropdown.currentTextChanged[str].connect(self.on_model_changed)

        # Create a label for the text input
        completion_label = QLabel("Prompt:")

        # Create a text input for the completion text
        self.completion_input = QTextEdit()
        self.completion_input.setToolTip(
            "Enter the text to use as the starting point for completion"
        )

        # Create a label for the max tokens slider
        self.max_tokens_label = QLabel("Max tokens:")

        # Create a slider for the max tokens
        self.max_tokens_slider = QSlider(Qt.Horizontal)
        self.max_tokens_slider.setMinimum(1)
        self.max_tokens_slider.setMaximum(self.models["code-davinci-002"])
        self.max_tokens_slider.setToolTip(
            "Adjust the maximum number of tokens to generate"
        )
        self.max_tokens_slider.valueChanged.connect(self.on_max_tokens_changed)
        self.max_tokens_slider.setValue(int(self.models["code-davinci-002"] / 2))

        # Create a label for the temperature input
        temperature_label = QLabel("Temperature:")

        # Create a number input for the temperature
        self.temperature_input = QLineEdit()
        self.temperature_input.setValidator(QIntValidator())
        self.temperature_input.setPlaceholderText("0")
        self.temperature_input.setToolTip(
            "Enter the temperature to use for generation (0 for default temperature)"
        )

        # Create a label for the n value input
        n_label = QLabel("n value:")

        # Create a number input for the n value
        self.n_input = QLineEdit()
        self.n_input.setValidator(QIntValidator())
        self.n_input.setPlaceholderText("1")
        self.n_input.setToolTip(
            "Enter the n value to use for generation (1 for default n value, higher values will generate more diverse completions)"
        )

        # Create a submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.setToolTip("Click to generate completion")
        self.submit_button.clicked.connect(self.on_submit)

        # Create a text box to display the generated response
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setToolTip("The generated completion will display here")
        self.response_box_highlighter = PythonSyntaxHighlighter(self.response_box)

        # Create a grid layout to organize the widgets
        grid = QGridLayout()
        grid.setSpacing(10)

        # Add the widgets to the grid layout
        grid.addWidget(api_key_label, 0, 0)
        grid.addWidget(self.api_key_input, 0, 1)
        grid.addWidget(model_label, 1, 0)
        grid.addWidget(self.model_dropdown, 1, 1)
        grid.addWidget(completion_label, 2, 0)
        grid.addWidget(self.completion_input, 2, 1)
        grid.addWidget(self.max_tokens_label, 3, 0)
        grid.addWidget(self.max_tokens_slider, 3, 1)
        grid.addWidget(temperature_label, 4, 0)
        grid.addWidget(self.temperature_input, 4, 1)
        grid.addWidget(n_label, 5, 0)
        grid.addWidget(self.n_input, 5, 1)
        grid.addWidget(self.submit_button, 6, 1)
        grid.addWidget(self.response_box, 7, 0, 1, 2)

        # Set the layout of the main window
        self.setLayout(grid)

        # Set the window title and size
        self.setWindowTitle("OpenAI Completion Generator")
        self.resize(800, 600)

    @staticmethod
    def persist_api_key(api_key):
        home_dir = os.path.expanduser("~")
        openai_dir = os.path.join(home_dir, ".openai")
        if not os.path.exists(openai_dir):
            os.makedirs(openai_dir)
        api_key_file = os.path.join(openai_dir, "api_key.json")
        with open(api_key_file, "w") as f:
            json.dump({"api_key": api_key}, f)

    @staticmethod
    def read_api_key():
        home_dir = os.path.expanduser("~")
        openai_dir = os.path.join(home_dir, ".openai")
        api_key_file = os.path.join(openai_dir, "api_key.json")

        if not os.path.exists(openai_dir):
            return ""

        if not os.path.exists(api_key_file):
            return ""

        with open(api_key_file, "r") as f:
            return json.load(f)["api_key"]

    def on_api_key_changed(self, value):
        self.persist_api_key(value)

    # @pyqtSlot
    def on_max_tokens_changed(self, value):
        # Set the text of the max tokens label to the current value of the slider
        self.max_tokens_label.setText(f"Max tokens: {value}")

    def on_model_changed(self, model):
        if self.max_tokens_slider.maximum() == self.models[model]:
            return
        self.max_tokens_slider.setMaximum(self.models[model])
        self.max_tokens_slider.setValue(int(self.models[model] / 2))

    # @pyqtSlot
    def on_submit(self):
        # Get the api key
        openai.api_key = self.api_key_input.text()

        # Get the selected model from the dropdown menu
        model = self.model_dropdown.currentText()

        # Get the completion text from the input
        completion_text = self.completion_input.toPlainText()

        # Get the max tokens value from the slider
        max_tokens = self.max_tokens_slider.value()

        # Get the temperature value from the input
        try:
            temperature = int(self.temperature_input.text())
        except Exception:
            temperature = 0

        # Get the n value from the input
        try:
            n = int(self.n_input.text())
        except Exception:
            n = 1

        # Set the OpenAI API key
        # openai.api_key = '<your-api-key>'

        try:
            # Call the OpenAI API to generate the completion
            response = openai.Completion.create(
                engine=model,
                prompt=completion_text,
                max_tokens=max_tokens,
                temperature=temperature,
                n=n,
                stop=None,
            )

            # Get the generated text from the response
            generated_text = response["choices"][0]["text"]

            # Display the generated text in the response box
            self.response_box.setText(generated_text)

        except Exception as e:
            self.response_box.setText(str(e))


def ui():
    app = QApplication(sys.argv)
    ex = OpenAICompletionUI()
    ex.show()
    sys.exit(app.exec_())
