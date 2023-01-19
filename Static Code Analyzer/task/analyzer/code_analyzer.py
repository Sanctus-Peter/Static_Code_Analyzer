import glob
import sys
import os
import ast


class StaticCodeAnalyzer:
    def __init__(self):
        self.file_name = sys.argv[1]
        self.line_number = 1
        self.lines = []
        self.blankline_count = 0
        self.tree = None

    def get_files(self):
        files = []
        if self.file_name.endswith(".py"):
            files.append(self.file_name)
        for file in glob.iglob(self.file_name + os.sep + "**" + os.sep + "*.py", recursive=True):
            files.append(file)
        return sorted(files)

    def read_file(self):
        with open(self.file_name, 'r') as f:
            self.lines = f.readlines()

    def too_long_line(self, line):
        if len(line) >= 79:
            print(f"{self.file_name}: Line {self.line_number}: S001 Too long")

    def check_blankline(self, line):
        if not line.strip():
            self.blankline_count += 1
        else:
            if self.blankline_count > 2:
                print(
                    f"{self.file_name}: Line {self.line_number}: S006 More than two blank lines used before this line"
                )
            self.blankline_count = 0

    def check_semicolon(self, line):
        words = line.split("#")
        if words[0].strip().endswith(";"):
            print(f"{self.file_name}: Line {self.line_number}: S003 Unnecessary semicolon")

    def check_indentation(self, line):
        # line_no = self.line_number - 1
        # if line_no - 1 < 0:
        #     return
        # prev_line = self.lines[line_no - 1]
        # if prev_line.strip().endswith(":") or\
        #         (prev_line.startswith(" ") and (len(prev_line) - len(prev_line.lstrip())) % 4 == 0):
        if line.startswith(" ") and (len(line) - len(line.lstrip())) % 4:
            print(f"{self.file_name}: Line {self.line_number}: S002 Indentation is not a multiple of 4")

    def inline_comment_spaces(self, line):
        words = line.split("#")
        if len(words) > 1 and len(words[0]) and not words[0].endswith("  "):
            print(
                f"{self.file_name}: Line {self.line_number}: S004 At least two spaces required before inline comments"
            )

    def found_todo(self, line):
        if "#" not in line:
            return
        words = line.split("#")
        for word in words:
            if word.strip().lower().startswith("todo"):
                print(f"{self.file_name}: Line {self.line_number}: S005 TODO found")
                break

    def check_name_spaces(self, line):
        class_def = ""
        if line.lstrip().startswith("class "):
            class_def = line.split("class")
        elif line.lstrip().startswith("def "):
            class_def = line.split("def")
        if len(class_def) > 1 and class_def[1].startswith("  "):
            print(f"{self.file_name}: Line {self.line_number}: S007 Too many spaces after 'class'")

    def check_class_name(self, line):
        if line.lstrip().startswith("class "):
            class_name = line.split("class")[1].strip()
            if "_" in class_name or class_name[0].islower():
                print(f"{self.file_name}: Line {self.line_number}: S008 Class name 'user' should use CamelCase")

    def check_func_name(self, line):
        if line.lstrip().startswith("def "):
            func_name = line.split("def ")[1].strip()
            if func_name[0].isupper():
                print(
                    f"{self.file_name}: Line {self.line_number}: S009 Function name '{func_name}' should use snake_case"
                )

    def check_args_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.lineno == self.line_number:
                for arg in node.args.args:
                    if not arg.arg.islower():
                        print(
                            f"{self.file_name}: Line {node.lineno}: S010 Argument name '{arg.arg}' should be snake_case"
                        )

    def check_var_names(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                for assignment in ast.walk(node):
                    if isinstance(assignment, ast.Assign) and assignment.lineno == self.line_number:
                        for target in assignment.targets:
                            if isinstance(target, ast.Name):
                                if not target.id.islower():
                                    print(
                                        f"{self.file_name}: Line {assignment.lineno}: S011 Variable '{target.id}' in function should be snake_case"
                                    )

    def check_mutable_default_args(self):
        mutable_types = [ast.List, ast.Dict, ast.Set]
        mutable_default_args = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.lineno == self.line_number:
                for arg in node.args.defaults:
                    if type(arg) in mutable_types:
                        if node.name not in mutable_default_args:
                            mutable_default_args.append(node.name)
                            print(
                                f"{self.file_name}: Line {node.lineno}: S012 Default argument value is mutable"
                            )

    def generate_tree(self):
        source = "".join(self.lines)
        try:
            self.tree = ast.parse(source)
        except Exception:
            pass

    def process_files(self):
        for line in self.lines:
            self.too_long_line(line)
            self.check_indentation(line)
            self.check_semicolon(line)
            self.inline_comment_spaces(line)
            self.found_todo(line)
            self.check_blankline(line)
            self.check_name_spaces(line)
            self.check_class_name(line)
            self.check_func_name(line)
            self.check_args_names()
            self.check_var_names()
            self.check_mutable_default_args()
            self.line_number += 1

    def analyze(self):
        files = self.get_files()
        for file in files:
            if file.endswith("tests.py"):
                continue
            self.file_name = file
            self.read_file()
            self.generate_tree()
            self.process_files()
            self.line_number = 1


if __name__ == '__main__':
    analyzer = StaticCodeAnalyzer()
    analyzer.analyze()
