""" Parses .tga.option and .msh.option files.  Only used with the former as of now. """

import os


class MungeOptions:

    def __init__(self, path_to_option_file):
        self.options = {}

        if os.path.exists(path_to_option_file):
            with open(path_to_option_file, 'r') as option_file:
                option_text = option_file.read()

            option_parts = option_text.split()

            current_parameter = ""

            for part in option_parts:
                if part.startswith("-"):
                    current_parameter = part[1:]
                    self.options[current_parameter] = ""
                elif current_parameter:
                    current_value = self.options[current_parameter]
                    # Keep adding to value in case there are vector options
                    self.options[current_parameter] += part if not current_value else (" " + part)

    def is_option_present(self, param):
        return param in self.options

    def get_bool(self, param, default=False):
        return True if param in self.options else default

    def get_float(self, param, default=0.0):
        if param in self.options:
            try:
                result = float(self.options[param]) 
            except:
                result = default
            finally:
                return result
        else:
            return default

    def get_string(self, param, default=""):
        return self.options.get(param, default)
