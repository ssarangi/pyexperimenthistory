import pandas as pd
import os
import logging
import matplotlib.image as mpimg
import typing
import numpy as np
from enum import Enum
import inspect

class Markdown:
    class Header(Enum):
        H1 = 1,
        H2 = 2,
        H3 = 3,
        H4 = 4,
        H5 = 5,
        H6 = 6,

        @staticmethod
        def render(self, header, txt):
            v = int(header)
            return "#" * header + " " + txt

    class HorizontalRule:
        def render(self):
            return "----"

    class Emphasis(Enum):
        EMPHASIS = 1,
        STRONG_EMPHASIS = 2,
        COMBINED_EMPHASIS = 3,
        STRIKETHROUGH = 4,

        @staticmethod
        def render(txt, emphasis):
            if emphasis == Markdown.Emphasis.EMPHASIS:
                return "*" + txt + "*"
            elif emphasis == Markdown.Emphasis.STRONG_EMPHASIS:
                return "**" + txt + "**"
            elif emphasis == Markdown.Emphasis.COMBINED_EMPHASIS:
                return "**" + txt
            elif emphasis == Markdown.Emphasis.STRIKETHROUGH:
                return "~~" + txt + "~~"
            else:
                raise Exception("Invalid Emphasis specified")

    class List:
        """
        Currently supports only 2 levels of indentation.. i.e. one main item and one sub item
        """
        class ListType(Enum):
            ORDERED_MAIN_ITEM = 1,
            UNORDERED_MAIN_ITEM = 2,
            UNORDERED_SUB_ITEM = 3,
            ORDERED_SUB_ITEM = 4

        def __init__(self):
            self._items = []
            self._ordered_idx = 1
            self._ordered_sub_idx = 1

        def add_ordered_item(self, item):
            self._items.append((Markdown.List.ListType.ORDERED_MAIN_ITEM, str(item)))

        def add_item(self, item):
            self._items.append((Markdown.List.ListType.UNORDERED_MAIN_ITEM, str(item)))

        def add_unordered_sub_item(self, item):
            self._items.append((Markdown.List.ListType.UNORDERED_SUB_ITEM, str(item)))

        def add_ordered_sub_item(self, item):
            self._items.append((Markdown.List.ListType.ORDERED_SUB_ITEM, str(item)))

        def render(self):
            lines = []
            for item in self._items:
                if item[0] == Markdown.List.ListType.ORDERED_MAIN_ITEM:
                    line = str(self._ordered_idx) + "." + item[1]
                elif item[0] == Markdown.List.ListType.UNORDERED_MAIN_ITEM:
                    line = "* " + item[1]
                elif item[0] == Markdown.List.ListType.ORDERED_SUB_ITEM:
                    line = " " * 4 + str(self._ordered_sub_idx) + " " + item[1]
                elif item[0] == Markdown.List.ListType.UNORDERED_SUB_ITEM:
                    line = " " * 4 + "*" + item[1]
                else:
                    raise Exception("Invalid markdown List type specified")

                lines.append(line)

            markdown = "\n".join(lines)
            return markdown

    class Image:
        def __init__(self, ref_name, path, hover_txt):
            self._ref_name = ref_name
            self._path = path
            self._hover_txt = hover_txt

        def render_ref(self):
            return '[%s]: %s "%s"' % (self._ref_name, self._path, self._hover_txt)

        def render(self):
            return '![alt text][' + self._ref_name + "]"

    class Link:
        """
        Currently only inline style links are supported
        """
        def __init__(self, link, txt):
            self._link = link
            self._txt = txt

        def render(self):
            return "[" + self._txt + "](" + self._link + ")"

    class Code:
        """
        Only supports python for now. Refer to functions directly
        """
        def __init__(self, func):
            self._func = func

        def render(self):
            markdown = '```python\n'
            markdown = markdown + inspect.getsourcelines(self._func)
            markdown = markdown + "\n```"

            return markdown

    class Text:
        def __init__(self):
            self._txt = ""

        def add_text(self, txt):
            self.txt = self.txt + txt
            return self

        def render(self):
            return self._txt

        @staticmethod
        def center_text(txt, length):
            if len(txt) > length:
                raise Exception("Length for centering cannot be greater than the length of text")

            total_spaces = length - len(txt)
            left_spaces = total_spaces // 2
            right_spaces = total_spaces - left_spaces
            new_txt = " " * left_spaces + txt + " " * right_spaces
            return new_txt

    class Table:
        def __init__(self, *cols_desc: typing.List[str]):
            if len(cols_desc) == 0:
                raise Exception("Column Description needs to be an List")
            self._cols_desc = cols_desc
            self._num_cols = len(cols_desc)
            self._rows = []

        def add_row(self, *values):
            if len(values) > self._num_cols:
                raise Exception("More column values setup for than columns")

            self._rows.append(values)

        def add_title_and_description(self, title, description):
            self._title = title
            self._description = description

        def render(self):
            table = np.array(self._rows)
            max_length_per_column = [len(max(table[:, 0], key=len)) for i in range(self._num_cols)]

            # Render the Header first
            lines = []
            header = "| "
            for idx, coldesc in enumerate(self._cols_desc):
                header = header + " "
                max_length = max_length_per_column[idx]
                header = header + Markdown.Text.center_text(coldesc, max_length)
                header = header + " |"

            lines.append(header)

            # Draw the underscore
            underscores = np.array(list(header))
            non_separators = np.where(underscores != '|')
            underscores[non_separators] = '-'
            underscores = "".join(underscores)
            lines.append(underscores)

            # Now start adding the values
            for row in self._rows:
                line = "| "
                for i, value in enumerate(row):
                    line = line + " "
                    txt = Markdown.Text.center_text(value, max_length_per_column[i])
                    line = line + txt
                    line = line + " |"
                lines.append(line)

            markdown = "\n".join(lines)
            return markdown

    def __init__(self):
        self._images = []
        self._markdown_elements = []

    def add_image(self, image):
        self._images.append(image)
        self._markdown_elements.append(image)

    def add_table(self, table):
        self._markdown_elements.append(table)

    def add_link(self, link):
        self._markdown_elements.append(link)

    def add_list(self, list):
        self._markdown_elements.append(list)

    def add_txt(self, txt):
        self._markdown_elements.append(txt)

class ExperimentManagerOptions:
    def __init__(self):
        self.overwrite_if_experiment_exists = False

class ExperimentManager:
    def __init__(self, options : ExperimentManagerOptions):
        self._logger = logging.getLogger(__name__)
        if os.path.exists("experiments.csv") and os.path.exists("experiments"):
            self._df = pd.read_csv("experiments.csv")
        else:
            self._df = pd.DataFrame()
            if not os.path.exists("experiments"):
                try:
                    os.mkdir("experiments")
                except:
                    raise Exception("Cannot create an experiments directory. Please create one and rerun")

        self._options = options
        self._new_experiments = []
        self._new_experiments_dict = {}


    def set_logger(self, loggerobj):
        """
        Set the custom logger object from your application
        :param loggerobj: Any object which is obtained from logging.getLogger()
        :return: None
        """
        self._logger = loggerobj

    def new_experiment(self, name):
        if name is None or name.strip() == "":
            raise Exception("A New experiment needs a name")

        if 'experiment' in self._df.columns:
            if name in self._df.experiment.unique():
                if self._options.overwrite_if_experiment_exists is False:
                    raise Exception("Experiment already exists. If you want to overwrite set it in options - overwrite_if_experiment_exists")
                else:
                    self._df = self._df[self._df.experiment != name]

        experiment = Experiment(self, name, self._logger)
        self._new_experiments.append(experiment)
        self._new_experiments_dict[name] = experiment

        return experiment

    def commit_experiment(self, s: pd.Series):
        """
        Commit a particular experiment if it is not committed. Checkpoints are automatically done after every certain
        number of operations
        :param experiment: object
        :return: 
        """
        self._df = self._df.append(s)
        self._df.to_csv('experiments.csv', index=False)

    def get_experiment(self, experiment_name : str):
        """
        Get the Experiment Object for the name specified
        :param experiment_name: String for the experiment name
        :return: Experiment Object
        """
        return self._df[self._df.experiment == experiment_name]

    @staticmethod
    def get_index_field(self, df, index):
        return df[df.index == index]

    def to_markdown(self, experiment_name : str):
        """
        Creates a markdown file from the experiments data. This has limited support for now
        :param filename: str
        :return: None
        """
        experiment = self.get_experiment(experiment_name)
        f = open(experiment.root_dir + "/" + experiment_name + ".md", 'w')
        # Create a markdown object
        markdown = Markdown()

        for img in experiment.images:
            mkimg = Markdown.Image(img.title, img.filename, img.description)
            markdown.add_image(img.filename)

        table = Markdown.Table(["Parameter Name", "Input/Output", "Value", "Title", "Description"])
        for param in experiment.parameters:
            table.add_row([param.name, ])

        markdown.add_table(table)


class Image:
    def __init__(self, exp_name, img, input_or_output, filename, title, description=""):
        self.exp_name = exp_name
        self.img = img
        self.filename = filename
        self.title = title
        self.description = description
        self.input_or_output = input_or_output

    def commit(self):
        mpimg.imsave(self.filename, self.img)

    def to_series(self):
        s = pd.Series([self.exp_name, self.input_or_output, self.filename, self.title, self.description],
                      index=['experiment', 'input_or_output', 'filename', 'title', 'description'], name="image")
        return s

class Parameter:
    def __init__(self, exp_name, input_or_output, param_name, param_value, title, description):
        self.exp_name = exp_name
        self.title = title
        self.description = description
        self.input_or_output = input_or_output
        self.param_name = param_name
        self.param_value = param_value

    def to_series(self):
        s = pd.Series([self.exp_name, self.input_or_output, self.param_name, self.param_value, type(self.param_value), self.title, self.description],
                      index=['experiment', 'input_or_output', 'parameter_name', 'parameter_value', 'type', 'title', 'description'],
                      name='parameter')

class Text:
    def __init__(self, exp_name, title, description):
        self.exp_name = exp_name
        self.title = title
        self.description = description

    def to_series(self):
        s = pd.Series([self.exp_name, self.title, self.description],
                      index=['experiment', 'title', 'description'])

class Experiment:
    """
    This is the Experiment Object. This should not be instantiated directly but should be done from the Experiment
    Manager which will set up certain defaults for it
    """
    def __init__(self, exp_mgr : ExperimentManager, name : str, logger):
        self._logger = logger
        self._name = name
        self._dirname = "experiments/" + name
        self._exp_mgr = exp_mgr

        if not os.path.exists(self._dirname):
            os.mkdir(self._dirname)

        # See if the images folder exists
        self._img_folder = self._dirname + "/images"
        if not os.path.exists(self._img_folder):
            os.mkdir(self._img_folder)

        self._images = []
        self._parameters = []

    @property
    def name(self):
        return self._name

    @property
    def root_dir(self):
        return self._dirname

    @property
    def images(self):
        return self._images

    @property
    def parameters(self):
        return self._parameters

    def _commit(self, s):
        self._exp_mgr.commit_experiment(s)

    def add_image(self, img, input_or_output, filename, title, description=""):
        """
        Adds an image to the experiment
        :param img: The raw image data 
        :param input_or_output Whether the image is a part of the inputs or outputs
        :param filename: Filename to save the image data
        :param description: Associate a description with the image data
        :return: None
        """
        if input_or_output.lower() != "input" and input_or_output.lower() != "output":
            raise Exception("input_or_output parameter can only contain 'input' or 'output'")

        image_object = Image(self._name, img, input_or_output, self._img_folder + "/" + filename, title, description="")
        image_object.commit()
        s = image_object.to_series()
        self._commit(s)

    def add_input_parameter(self, param_name, param_value, title, description):
        """
        Adds a parameter to the experiment. This could be either an input or output
        :param param_name: Parameter Name
        :param param_value: Parameter Value. Could be a single value or could be a list or dictionary
        :param title: Title of the parameter
        :param description: Description of the parameter
        :return: None
        """
        param_object = Parameter(self._name, "input", param_name, param_value, title, description)
        s = param_object.to_series()
        self._commit(s)