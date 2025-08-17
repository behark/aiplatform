from __future__ import annotations
import typing
from .chat_prompt import ChatPrompt
from .text_prompt import TextPrompt

class Prompt_Chat(ChatPrompt):
    type: typing.Literal['chat'] = 'chat'

    class Config:
        frozen = True
        smart_union = True
        allow_population_by_field_name = True
        populate_by_name = True

class Prompt_Text(TextPrompt):
    type: typing.Literal['text'] = 'text'

    class Config:
        frozen = True
        smart_union = True
        allow_population_by_field_name = True
        populate_by_name = True
Prompt = typing.Union[Prompt_Chat, Prompt_Text]
from typing import Any, Generic, List, Optional, TextIO, TypeVar, Union, overload
from . import get_console
from .console import Console
from .text import Text, TextType
PromptType = TypeVar('PromptType')
DefaultType = TypeVar('DefaultType')

class PromptError(Exception):
    """Exception base class for prompt related errors."""

class InvalidResponse(PromptError):
    """Exception to indicate a response was invalid. Raise this within process_response() to indicate an error
    and provide an error message.

    Args:
        message (Union[str, Text]): Error message.
    """

    def __init__(self, message: TextType) -> None:
        self.message = message

    def __rich__(self) -> TextType:
        return self.message

class PromptBase(Generic[PromptType]):
    """Ask the user for input until a valid response is received. This is the base class, see one of
    the concrete classes for examples.

    Args:
        prompt (TextType, optional): Prompt text. Defaults to "".
        console (Console, optional): A Console instance or None to use global console. Defaults to None.
        password (bool, optional): Enable password input. Defaults to False.
        choices (List[str], optional): A list of valid choices. Defaults to None.
        case_sensitive (bool, optional): Matching of choices should be case-sensitive. Defaults to True.
        show_default (bool, optional): Show default in prompt. Defaults to True.
        show_choices (bool, optional): Show choices in prompt. Defaults to True.
    """
    response_type: type = str
    validate_error_message = '[prompt.invalid]Please enter a valid value'
    illegal_choice_message = '[prompt.invalid.choice]Please select one of the available options'
    prompt_suffix = ': '
    choices: Optional[List[str]] = None

    def __init__(self, prompt: TextType='', *, console: Optional[Console]=None, password: bool=False, choices: Optional[List[str]]=None, case_sensitive: bool=True, show_default: bool=True, show_choices: bool=True) -> None:
        self.console = console or get_console()
        self.prompt = Text.from_markup(prompt, style='prompt') if isinstance(prompt, str) else prompt
        self.password = password
        if choices is not None:
            self.choices = choices
        self.case_sensitive = case_sensitive
        self.show_default = show_default
        self.show_choices = show_choices

    @classmethod
    @overload
    def ask(cls, prompt: TextType='', *, console: Optional[Console]=None, password: bool=False, choices: Optional[List[str]]=None, case_sensitive: bool=True, show_default: bool=True, show_choices: bool=True, default: DefaultType, stream: Optional[TextIO]=None) -> Union[DefaultType, PromptType]:
        ...

    @classmethod
    @overload
    def ask(cls, prompt: TextType='', *, console: Optional[Console]=None, password: bool=False, choices: Optional[List[str]]=None, case_sensitive: bool=True, show_default: bool=True, show_choices: bool=True, stream: Optional[TextIO]=None) -> PromptType:
        ...

    @classmethod
    def ask(cls, prompt: TextType='', *, console: Optional[Console]=None, password: bool=False, choices: Optional[List[str]]=None, case_sensitive: bool=True, show_default: bool=True, show_choices: bool=True, default: Any=..., stream: Optional[TextIO]=None) -> Any:
        """Shortcut to construct and run a prompt loop and return the result.

        Example:
            >>> filename = Prompt.ask("Enter a filename")

        Args:
            prompt (TextType, optional): Prompt text. Defaults to "".
            console (Console, optional): A Console instance or None to use global console. Defaults to None.
            password (bool, optional): Enable password input. Defaults to False.
            choices (List[str], optional): A list of valid choices. Defaults to None.
            case_sensitive (bool, optional): Matching of choices should be case-sensitive. Defaults to True.
            show_default (bool, optional): Show default in prompt. Defaults to True.
            show_choices (bool, optional): Show choices in prompt. Defaults to True.
            stream (TextIO, optional): Optional text file open for reading to get input. Defaults to None.
        """
        _prompt = cls(prompt, console=console, password=password, choices=choices, case_sensitive=case_sensitive, show_default=show_default, show_choices=show_choices)
        return _prompt(default=default, stream=stream)

    def render_default(self, default: DefaultType) -> Text:
        """Turn the supplied default in to a Text instance.

        Args:
            default (DefaultType): Default value.

        Returns:
            Text: Text containing rendering of default value.
        """
        return Text(f'({default})', 'prompt.default')

    def make_prompt(self, default: DefaultType) -> Text:
        """Make prompt text.

        Args:
            default (DefaultType): Default value.

        Returns:
            Text: Text to display in prompt.
        """
        prompt = self.prompt.copy()
        prompt.end = ''
        if self.show_choices and self.choices:
            _choices = '/'.join(self.choices)
            choices = f'[{_choices}]'
            prompt.append(' ')
            prompt.append(choices, 'prompt.choices')
        if default != ... and self.show_default and isinstance(default, (str, self.response_type)):
            prompt.append(' ')
            _default = self.render_default(default)
            prompt.append(_default)
        prompt.append(self.prompt_suffix)
        return prompt

    @classmethod
    def get_input(cls, console: Console, prompt: TextType, password: bool, stream: Optional[TextIO]=None) -> str:
        """Get input from user.

        Args:
            console (Console): Console instance.
            prompt (TextType): Prompt text.
            password (bool): Enable password entry.

        Returns:
            str: String from user.
        """
        return console.input(prompt, password=password, stream=stream)

    def check_choice(self, value: str) -> bool:
        """Check value is in the list of valid choices.

        Args:
            value (str): Value entered by user.

        Returns:
            bool: True if choice was valid, otherwise False.
        """
        assert self.choices is not None
        if self.case_sensitive:
            return value.strip() in self.choices
        return value.strip().lower() in [choice.lower() for choice in self.choices]

    def process_response(self, value: str) -> PromptType:
        """Process response from user, convert to prompt type.

        Args:
            value (str): String typed by user.

        Raises:
            InvalidResponse: If ``value`` is invalid.

        Returns:
            PromptType: The value to be returned from ask method.
        """
        value = value.strip()
        try:
            return_value: PromptType = self.response_type(value)
        except ValueError:
            raise InvalidResponse(self.validate_error_message)
        if self.choices is not None:
            if not self.check_choice(value):
                raise InvalidResponse(self.illegal_choice_message)
            if not self.case_sensitive:
                return_value = self.response_type(self.choices[[choice.lower() for choice in self.choices].index(value.lower())])
        return return_value

    def on_validate_error(self, value: str, error: InvalidResponse) -> None:
        """Called to handle validation error.

        Args:
            value (str): String entered by user.
            error (InvalidResponse): Exception instance the initiated the error.
        """
        self.console.print(error)

    def pre_prompt(self) -> None:
        """Hook to display something before the prompt."""

    @overload
    def __call__(self, *, stream: Optional[TextIO]=None) -> PromptType:
        ...

    @overload
    def __call__(self, *, default: DefaultType, stream: Optional[TextIO]=None) -> Union[PromptType, DefaultType]:
        ...

    def __call__(self, *, default: Any=..., stream: Optional[TextIO]=None) -> Any:
        """Run the prompt loop.

        Args:
            default (Any, optional): Optional default value.

        Returns:
            PromptType: Processed value.
        """
        while True:
            self.pre_prompt()
            prompt = self.make_prompt(default)
            value = self.get_input(self.console, prompt, self.password, stream=stream)
            if value == '' and default != ...:
                return default
            try:
                return_value = self.process_response(value)
            except InvalidResponse as error:
                self.on_validate_error(value, error)
                continue
            else:
                return return_value

class Prompt(PromptBase[str]):
    """A prompt that returns a str.

    Example:
        >>> name = Prompt.ask("Enter your name")


    """
    response_type = str

class IntPrompt(PromptBase[int]):
    """A prompt that returns an integer.

    Example:
        >>> burrito_count = IntPrompt.ask("How many burritos do you want to order")

    """
    response_type = int
    validate_error_message = '[prompt.invalid]Please enter a valid integer number'

class FloatPrompt(PromptBase[float]):
    """A prompt that returns a float.

    Example:
        >>> temperature = FloatPrompt.ask("Enter desired temperature")

    """
    response_type = float
    validate_error_message = '[prompt.invalid]Please enter a number'

class Confirm(PromptBase[bool]):
    """A yes / no confirmation prompt.

    Example:
        >>> if Confirm.ask("Continue"):
                run_job()

    """
    response_type = bool
    validate_error_message = '[prompt.invalid]Please enter Y or N'
    choices: List[str] = ['y', 'n']

    def render_default(self, default: DefaultType) -> Text:
        """Render the default as (y) or (n) rather than True/False."""
        yes, no = self.choices
        return Text(f'({yes})' if default else f'({no})', style='prompt.default')

    def process_response(self, value: str) -> bool:
        """Convert choices to a bool."""
        value = value.strip().lower()
        if value not in self.choices:
            raise InvalidResponse(self.validate_error_message)
        return value == self.choices[0]
if __name__ == '__main__':
    from pip._vendor.rich import print
    if Confirm.ask('Run [i]prompt[/i] tests?', default=True):
        while True:
            result = IntPrompt.ask(':rocket: Enter a number between [b]1[/b] and [b]10[/b]', default=5)
            if result >= 1 and result <= 10:
                break
            print(':pile_of_poo: [prompt.invalid]Number must be between 1 and 10')
        print(f'number={result}')
        while True:
            password = Prompt.ask('Please enter a password [cyan](must be at least 5 characters)', password=True)
            if len(password) >= 5:
                break
            print('[prompt.invalid]password too short')
        print(f'password={password!r}')
        fruit = Prompt.ask('Enter a fruit', choices=['apple', 'orange', 'pear'])
        print(f'fruit={fruit!r}')
        doggie = Prompt.ask("What's the best Dog? (Case INSENSITIVE)", choices=['Border Terrier', 'Collie', 'Labradoodle'], case_sensitive=False)
        print(f'doggie={doggie!r}')
    else:
        print('[b]OK :loudly_crying_face:')
CLICKUP_TASK_CREATE_PROMPT = '\n    This tool is a wrapper around clickup\'s create_task API, useful when you need to create a CLICKUP task. \n    The input to this tool is a dictionary specifying the fields of the CLICKUP task, and will be passed into clickup\'s CLICKUP `create_task` function.\n    Only add fields described by the user.\n    Use the following mapping in order to map the user\'s priority to the clickup priority: {{\n            Urgent = 1,\n            High = 2,\n            Normal = 3,\n            Low = 4,\n        }}. If the user passes in "urgent" replace the priority value as 1.\n \n    Here are a few task descriptions and corresponding input examples:\n    Task: create a task called "Daily report"\n    Example Input: {{"name": "Daily report"}}\n    Task: Make an open task called "ClickUp toolkit refactor" with description "Refactor the clickup toolkit to use dataclasses for parsing", with status "open"\n    Example Input: {{"name": "ClickUp toolkit refactor", "description": "Refactor the clickup toolkit to use dataclasses for parsing", "status": "Open"}}\n    Task: create a task with priority 3 called "New Task Name" with description "New Task Description", with status "open"\n    Example Input: {{"name": "New Task Name", "description": "New Task Description", "status": "Open", "priority": 3}}\n    Task: Add a task called "Bob\'s task" and assign it to Bob (user id: 81928627)\n    Example Input: {{"name": "Bob\'s task", "description": "Task for Bob", "assignees": [81928627]}}\n    '
CLICKUP_LIST_CREATE_PROMPT = '\n    This tool is a wrapper around clickup\'s create_list API, useful when you need to create a CLICKUP list.\n    The input to this tool is a dictionary specifying the fields of a clickup list, and will be passed to clickup\'s create_list function.\n    Only add fields described by the user.\n    Use the following mapping in order to map the user\'s priority to the clickup priority: {{\n        Urgent = 1,\n        High = 2,\n        Normal = 3,\n        Low = 4,\n    }}. If the user passes in "urgent" replace the priority value as 1.\n\n    Here are a few list descriptions and corresponding input examples:\n    Description: make a list with name "General List"\n    Example Input: {{"name": "General List"}} \n    Description: add a new list ("TODOs") with low priority\n    Example Input: {{"name": "General List", "priority": 4}}\n    Description: create a list with name "List name", content "List content", priority 2, and status "red"\n    Example Input: {{"name": "List name", "content": "List content", "priority": 2, "status": "red"}} \n'
CLICKUP_FOLDER_CREATE_PROMPT = '\n    This tool is a wrapper around clickup\'s create_folder API, useful when you need to create a CLICKUP folder.\n    The input to this tool is a dictionary specifying the fields of a clickup folder, and will be passed to clickup\'s create_folder function.\n    For example, to create a folder with name "Folder name" you would pass in the following dictionary:\n    {{\n        "name": "Folder name",\n    }} \n'
CLICKUP_GET_TASK_PROMPT = '\n    This tool is a wrapper around clickup\'s API,\n    Do NOT use to get a task specific attribute. Use get task attribute instead. \n    useful when you need to get a specific task for the user. Given the task id you want to create a request similar to the following dictionary:\n    payload = {{"task_id": "86a0t44tq"}}\n    '
CLICKUP_GET_TASK_ATTRIBUTE_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to get a specific attribute from a task. Given the task id and desired attribute create a request similar to the following dictionary:\n    payload = {{"task_id": "<task_id_to_update>", "attribute_name": "<attribute_name_to_update>"}}\n\n    Here are some example queries their corresponding payloads:\n    Get the name of task 23jn23kjn -> {{"task_id": "23jn23kjn", "attribute_name": "name"}}\n    What is the priority of task 86a0t44tq? -> {{"task_id": "86a0t44tq", "attribute_name": "priority"}}\n    Output the description of task sdc9ds9jc -> {{"task_id": "sdc9ds9jc", "attribute_name": "description"}}\n    Who is assigned to task bgjfnbfg0 -> {{"task_id": "bgjfnbfg0", "attribute_name": "assignee"}}\n    Which is the status of task kjnsdcjc? -> {{"task_id": "kjnsdcjc", "attribute_name": "description"}}\n    How long is the time estimate of task sjncsd999? -> {{"task_id": "sjncsd999", "attribute_name": "time_estimate"}}\n    Is task jnsd98sd archived?-> {{"task_id": "jnsd98sd", "attribute_name": "archive"}}\n    '
CLICKUP_GET_ALL_TEAMS_PROMPT = "\n    This tool is a wrapper around clickup's API, useful when you need to get all teams that the user is a part of.\n    To get a list of all the teams there is no necessary request parameters. \n    "
CLICKUP_GET_LIST_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to get a specific list for the user. Given the list id you want to create a request similar to the following dictionary:\n    payload = {{"list_id": "901300608424"}}\n    '
CLICKUP_GET_FOLDERS_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to get a specific folder for the user. Given the user\'s workspace id you want to create a request similar to the following dictionary:\n    payload = {{"folder_id": "90130119692"}}\n    '
CLICKUP_GET_SPACES_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to get all the spaces available to a user. Given the user\'s workspace id you want to create a request similar to the following dictionary:\n    payload = {{"team_id": "90130119692"}}\n    '
CLICKUP_GET_SPACES_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to get all the spaces available to a user. Given the user\'s workspace id you want to create a request similar to the following dictionary:\n    payload = {{"team_id": "90130119692"}}\n    '
CLICKUP_UPDATE_TASK_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to update a specific attribute of a task. Given the task id, desired attribute to change and the new value you want to create a request similar to the following dictionary:\n    payload = {{"task_id": "<task_id_to_update>", "attribute_name": "<attribute_name_to_update>", "value": "<value_to_update_to>"}}\n\n    Here are some example queries their corresponding payloads:\n    Change the name of task 23jn23kjn to new task name -> {{"task_id": "23jn23kjn", "attribute_name": "name", "value": "new task name"}}\n    Update the priority of task 86a0t44tq to 1 -> {{"task_id": "86a0t44tq", "attribute_name": "priority", "value": 1}}\n    Re-write the description of task sdc9ds9jc to \'a new task description\' -> {{"task_id": "sdc9ds9jc", "attribute_name": "description", "value": "a new task description"}}\n    Forward the status of task kjnsdcjc to done -> {{"task_id": "kjnsdcjc", "attribute_name": "description", "status": "done"}}\n    Increase the time estimate of task sjncsd999 to 3h -> {{"task_id": "sjncsd999", "attribute_name": "time_estimate", "value": 8000}}\n    Archive task jnsd98sd -> {{"task_id": "jnsd98sd", "attribute_name": "archive", "value": true}}\n    *IMPORTANT*: Pay attention to the exact syntax above and the correct use of quotes. \n    For changing priority and time estimates, we expect integers (int).\n    For name, description and status we expect strings (str).\n    For archive, we expect a boolean (bool).\n    '
CLICKUP_UPDATE_TASK_ASSIGNEE_PROMPT = '\n    This tool is a wrapper around clickup\'s API, \n    useful when you need to update the assignees of a task. Given the task id, the operation add or remove (rem), and the list of user ids. You want to create a request similar to the following dictionary:\n    payload = {{"task_id": "<task_id_to_update>", "operation": "<operation, (add or rem)>", "users": [<user_id_1>, <user_id_2>]}}\n\n    Here are some example queries their corresponding payloads:\n    Add 81928627 and 3987234 as assignees to task 21hw21jn -> {{"task_id": "21hw21jn", "operation": "add", "users": [81928627, 3987234]}}\n    Remove 67823487 as assignee from task jin34ji4 -> {{"task_id": "jin34ji4", "operation": "rem", "users": [67823487]}}\n    *IMPORTANT*: Users id should always be ints. \n    '
GET_ISSUES_PROMPT = "\nThis tool will fetch a list of the repository's issues. It will return the title, and issue number of 5 issues. It takes no input.\n"
GET_ISSUE_PROMPT = '\nThis tool will fetch the title, body, and comment thread of a specific issue. **VERY IMPORTANT**: You must specify the issue number as an integer.\n'
COMMENT_ON_ISSUE_PROMPT = "\nThis tool is useful when you need to comment on a GitLab issue. Simply pass in the issue number and the comment you would like to make. Please use this sparingly as we don't want to clutter the comment threads. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify the issue number as an integer\n- Then you must place two newlines\n- Then you must specify your comment\n"
CREATE_PULL_REQUEST_PROMPT = '\nThis tool is useful when you need to create a new pull request in a GitLab repository. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify the title of the pull request\n- Then you must place two newlines\n- Then you must write the body or description of the pull request\n\nTo reference an issue in the body, put its issue number directly after a #.\nFor example, if you would like to create a pull request called "README updates" with contents "added contributors\' names, closes issue #3", you would pass in the following string:\n\nREADME updates\n\nadded contributors\' names, closes issue #3\n'
CREATE_FILE_PROMPT = '\nThis tool is a wrapper for the GitLab API, useful when you need to create a file in a GitLab repository. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify which file to create by passing a full file path (**IMPORTANT**: the path must not start with a slash)\n- Then you must specify the contents of the file\n\nFor example, if you would like to create a file called /test/test.txt with contents "test contents", you would pass in the following string:\n\ntest/test.txt\n\ntest contents\n'
READ_FILE_PROMPT = '\nThis tool is a wrapper for the GitLab API, useful when you need to read the contents of a file in a GitLab repository. Simply pass in the full file path of the file you would like to read. **IMPORTANT**: the path must not start with a slash\n'
UPDATE_FILE_PROMPT = '\nThis tool is a wrapper for the GitLab API, useful when you need to update the contents of a file in a GitLab repository. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify which file to modify by passing a full file path (**IMPORTANT**: the path must not start with a slash)\n- Then you must specify the old contents which you would like to replace wrapped in OLD <<<< and >>>> OLD\n- Then you must specify the new contents which you would like to replace the old contents with wrapped in NEW <<<< and >>>> NEW\n\nFor example, if you would like to replace the contents of the file /test/test.txt from "old contents" to "new contents", you would pass in the following string:\n\ntest/test.txt\n\nThis is text that will not be changed\nOLD <<<<\nold contents\n>>>> OLD\nNEW <<<<\nnew contents\n>>>> NEW\n'
DELETE_FILE_PROMPT = '\nThis tool is a wrapper for the GitLab API, useful when you need to delete a file in a GitLab repository. Simply pass in the full file path of the file you would like to delete. **IMPORTANT**: the path must not start with a slash\n'
GET_REPO_FILES_IN_MAIN = '\nThis tool will provide an overview of all existing files in the main branch of the GitLab repository repository. It will list the file names. No input parameters are required.\n'
GET_REPO_FILES_IN_BOT_BRANCH = '\nThis tool will provide an overview of all files in your current working branch where you should implement changes. No input parameters are required.\n'
GET_REPO_FILES_FROM_DIRECTORY = '\nThis tool will provide an overview of all files in your current working branch from a specific directory. **VERY IMPORTANT**: You must specify the path of the directory as a string input parameter.\n'
LIST_REPO_BRANCES = '\nThis tool is a wrapper for the GitLab API, useful when you need to read the branches names in a GitLab repository. No input parameters are required.\n'
CREATE_REPO_BRANCH = '\nThis tool will create a new branch in the repository. **VERY IMPORTANT**: You must specify the name of the new branch as a string input parameter.\n'
SET_ACTIVE_BRANCH = '\nThis tool will set the active branch in the repository, similar to `git checkout <branch_name>` and `git switch -c <branch_name>`. **VERY IMPORTANT**: You must specify the name of the branch as a string input parameter.\n'
BASE_ZAPIER_TOOL_PROMPT = 'A wrapper around Zapier NLA actions. The input to this tool is a natural language instruction, for example "get the latest email from my bank" or "send a slack message to the #general channel". Each tool will have params associated with it that are specified as a list. You MUST take into account the params when creating the instruction. For example, if the params are [\'Message_Text\', \'Channel\'], your instruction should be something like \'send a slack message to the #general channel with the text hello world\'. Another example: if the params are [\'Calendar\', \'Search_Term\'], your instruction should be something like \'find the meeting in my personal calendar at 3pm\'. Do not make up params, they will be explicitly specified in the tool description. If you do not have enough information to fill in the params, just say \'not enough information provided in the instruction, missing <param>\'. If you get a none or null response, STOP EXECUTION, do not try to another tool!This tool specifically used for: {zapier_description}, and has params: {params}'
'Tools for interacting with an Apache Cassandra database.'
QUERY_PATH_PROMPT = '"\nYou are an Apache Cassandra expert query analysis bot with the following features \nand rules:\n - You will take a question from the end user about finding certain \n   data in the database.\n - You will examine the schema of the database and create a query path. \n - You will provide the user with the correct query to find the data they are looking \n   for showing the steps provided by the query path.\n - You will use best practices for querying Apache Cassandra using partition keys \n   and clustering columns.\n - Avoid using ALLOW FILTERING in the query.\n - The goal is to find a query path, so it may take querying other tables to get \n   to the final answer. \n\nThe following is an example of a query path in JSON format:\n\n {\n  "query_paths": [\n    {\n      "description": "Direct query to users table using email",\n      "steps": [\n        {\n          "table": "user_credentials",\n          "query": \n             "SELECT userid FROM user_credentials WHERE email = \'example@example.com\';"\n        },\n        {\n          "table": "users",\n          "query": "SELECT * FROM users WHERE userid = ?;"\n        }\n      ]\n    }\n  ]\n}'
JIRA_ISSUE_CREATE_PROMPT = '\n    This tool is a wrapper around atlassian-python-api\'s Jira issue_create API, useful when you need to create a Jira issue. \n    The input to this tool is a dictionary specifying the fields of the Jira issue, and will be passed into atlassian-python-api\'s Jira `issue_create` function.\n    For example, to create a low priority task called "test issue" with description "test description", you would pass in the following dictionary: \n    {{"summary": "test issue", "description": "test description", "issuetype": {{"name": "Task"}}, "priority": {{"name": "Low"}}}}\n    '
JIRA_GET_ALL_PROJECTS_PROMPT = "\n    This tool is a wrapper around atlassian-python-api's Jira project API, \n    useful when you need to fetch all the projects the user has access to, find out how many projects there are, or as an intermediary step that involve searching by projects. \n    there is no input to this tool.\n    "
JIRA_JQL_PROMPT = '\n    This tool is a wrapper around atlassian-python-api\'s Jira jql API, useful when you need to search for Jira issues.\n    The input to this tool is a JQL query string, and will be passed into atlassian-python-api\'s Jira `jql` function,\n    For example, to find all the issues in project "Test" assigned to the me, you would pass in the following string:\n    project = Test AND assignee = currentUser()\n    or to find issues with summaries that contain the word "test", you would pass in the following string:\n    summary ~ \'test\'\n    '
JIRA_CATCH_ALL_PROMPT = '\n    This tool is a wrapper around atlassian-python-api\'s Jira API.\n    There are other dedicated tools for fetching all projects, and creating and searching for issues, \n    use this tool if you need to perform any other actions allowed by the atlassian-python-api Jira API.\n    The input to this tool is a dictionary specifying a function from atlassian-python-api\'s Jira API, \n    as well as a list of arguments and dictionary of keyword arguments to pass into the function.\n    For example, to get all the users in a group, while increasing the max number of results to 100, you would\n    pass in the following dictionary: {{"function": "get_all_users_from_group", "args": ["group"], "kwargs": {{"limit":100}} }}\n    or to find out how many projects are in the Jira instance, you would pass in the following string:\n    {{"function": "projects"}}\n    For more information on the Jira API, refer to https://atlassian-python-api.readthedocs.io/jira.html\n    '
JIRA_CONFLUENCE_PAGE_CREATE_PROMPT = 'This tool is a wrapper around atlassian-python-api\'s Confluence \natlassian-python-api API, useful when you need to create a Confluence page. The input to this tool is a dictionary \nspecifying the fields of the Confluence page, and will be passed into atlassian-python-api\'s Confluence `create_page` \nfunction. For example, to create a page in the DEMO space titled "This is the title" with body "This is the body. You can use \n<strong>HTML tags</strong>!", you would pass in the following dictionary: {{"space": "DEMO", "title":"This is the \ntitle","body":"This is the body. You can use <strong>HTML tags</strong>!"}} '
QUERY_CHECKER = '\n{query}\nDouble check the {dialect} query above for common mistakes, including:\n- Using NOT IN with NULL values\n- Using UNION when UNION ALL should have been used\n- Using BETWEEN for exclusive ranges\n- Data type mismatch in predicates\n- Properly quoting identifiers\n- Using the correct number of arguments for functions\n- Casting to the correct data type\n- Using the proper columns for joins\n\nIf there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.\n\nOutput the final SQL query only.\n\nSQL Query: '
NASA_SEARCH_PROMPT = '\n    This tool is a wrapper around NASA\'s search API, useful when you need to search through NASA\'s Image and Video Library. \n    The input to this tool is a query specified by the user, and will be passed into NASA\'s `search` function.\n    \n    At least one parameter must be provided.\n\n    There are optional parameters that can be passed by the user based on their query\n    specifications. Each item in this list contains pound sign (#) separated values, the first value is the parameter name, \n    the second value is the datatype and the third value is the description: {{\n\n        - q#string#Free text search terms to compare to all indexed metadata.\n        - center#string#NASA center which published the media.\n        - description#string#Terms to search for in “Description” fields.\n        - description_508#string#Terms to search for in “508 Description” fields.\n        - keywords #string#Terms to search for in “Keywords” fields. Separate multiple values with commas.\n        - location #string#Terms to search for in “Location” fields.\n        - media_type#string#Media types to restrict the search to. Available types: [“image”,“video”, “audio”]. Separate multiple values with commas.\n        - nasa_id #string#The media asset’s NASA ID.\n        - page#integer#Page number, starting at 1, of results to get.-\n        - page_size#integer#Number of results per page. Default: 100.\n        - photographer#string#The primary photographer’s name.\n        - secondary_creator#string#A secondary photographer/videographer’s name.\n        - title #string#Terms to search for in “Title” fields.\n        - year_start#string#The start year for results. Format: YYYY.\n        - year_end #string#The end year for results. Format: YYYY.\n\n    }}\n    \n    Below are several task descriptions along with their respective input examples.\n    Task: get the 2nd page of image and video content starting from the year 2002 to 2010\n    Example Input: {{"year_start":  "2002", "year_end":  "2010", "page": 2}}\n    \n    Task: get the image and video content of saturn photographed by John Appleseed\n    Example Input: {{"q": "saturn", "photographer": "John Appleseed"}}\n    \n    Task: search for Meteor Showers with description "Search Description" with media type image\n    Example Input: {{"q": "Meteor Shower", "description": "Search Description", "media_type": "image"}}\n    \n    Task: get the image and video content from year 2008 to 2010 from Kennedy Center\n    Example Input: {{"year_start":  "2002", "year_end":  "2010", "location": "Kennedy Center}}\n    '
NASA_MANIFEST_PROMPT = "\n    This tool is a wrapper around NASA's media asset manifest API, useful when you need to retrieve a media \n    asset's manifest. The input to this tool should include a string representing a NASA ID for a media asset that the user is trying to get the media asset manifest data for. The NASA ID will be passed as a string into NASA's `get_media_metadata_manifest` function.\n\n    The following list are some examples of NASA IDs for a media asset that you can use to better extract the NASA ID from the input string to the tool.\n    - GSFC_20171102_Archive_e000579\n    - Launch-Sound_Delta-PAM-Random-Commentary\n    - iss066m260341519_Expedition_66_Education_Inflight_with_Random_Lake_School_District_220203\n    - 6973610\n    - GRC-2020-CM-0167.4\n    - Expedition_55_Inflight_Japan_VIP_Event_May_31_2018_659970\n    - NASA 60th_SEAL_SLIVER_150DPI\n"
NASA_METADATA_PROMPT = "\n    This tool is a wrapper around NASA's media asset metadata location API, useful when you need to retrieve the media asset's metadata. The input to this tool should include a string representing a NASA ID for a media asset that the user is trying to get the media asset metadata location for. The NASA ID will be passed as a string into NASA's `get_media_metadata_manifest` function.\n\n    The following list are some examples of NASA IDs for a media asset that you can use to better extract the NASA ID from the input string to the tool.\n    - GSFC_20171102_Archive_e000579\n    - Launch-Sound_Delta-PAM-Random-Commentary\n    - iss066m260341519_Expedition_66_Education_Inflight_with_Random_Lake_School_District_220203\n    - 6973610\n    - GRC-2020-CM-0167.4\n    - Expedition_55_Inflight_Japan_VIP_Event_May_31_2018_659970\n    - NASA 60th_SEAL_SLIVER_150DPI\n"
NASA_CAPTIONS_PROMPT = "\n    This tool is a wrapper around NASA's video assests caption location API, useful when you need \n    to retrieve the location of the captions of a specific video. The input to this tool should include a string representing a NASA ID for a video media asset that the user is trying to get the get the location of the captions for. The NASA ID will be passed as a string into NASA's `get_media_metadata_manifest` function.\n\n    The following list are some examples of NASA IDs for a video asset that you can use to better extract the NASA ID from the input string to the tool.\n    - 2017-08-09 - Video File RS-25 Engine Test\n    - 20180415-TESS_Social_Briefing\n    - 201_TakingWildOutOfWildfire\n    - 2022-H1_V_EuropaClipper-4\n    - 2022_0429_Recientemente\n"
STEAM_GET_GAMES_DETAILS = '\n    This tool is a wrapper around python-steam-api\'s steam.apps.search_games API and \n    steam.apps.get_app_details API, useful when you need to search for a game.\n    The input to this tool is a string specifying the name of the game you want to \n    search for. For example, to search for a game called "Counter-Strike: Global \n    Offensive", you would input "Counter-Strike: Global Offensive" as the game name.\n    This input will be passed into steam.apps.search_games to find the game id, link \n    and price, and then the game id will be passed into steam.apps.get_app_details to \n    get the detailed description and supported languages of the game. Finally the \n    results are combined and returned as a string.\n'
STEAM_GET_RECOMMENDED_GAMES = '\n    This tool is a wrapper around python-steam-api\'s steam.users.get_owned_games API \n    and steamspypi\'s steamspypi.download API, useful when you need to get a list of \n    recommended games. The input to this tool is a string specifying the steam id of \n    the user you want to get recommended games for. For example, to get recommended \n    games for a user with steam id 76561197960435530, you would input \n    "76561197960435530" as the steam id.  This steamid is then utilized to form a \n    data_request sent to steamspypi\'s steamspypi.download to retrieve genres of user\'s \n    owned games. Then, calculates the frequency of each genre, identifying the most \n    popular one, and stored it in a dictionary. Subsequently, use steamspypi.download\n    to returns all games in this genre and return 5 most-played games that is not owned\n    by the user.\n\n'
GET_ISSUES_PROMPT = "\nThis tool will fetch a list of the repository's issues. It will return the title, and issue number of 5 issues. It takes no input."
GET_ISSUE_PROMPT = '\nThis tool will fetch the title, body, and comment thread of a specific issue. **VERY IMPORTANT**: You must specify the issue number as an integer.'
COMMENT_ON_ISSUE_PROMPT = "\nThis tool is useful when you need to comment on a GitHub issue. Simply pass in the issue number and the comment you would like to make. Please use this sparingly as we don't want to clutter the comment threads. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify the issue number as an integer\n- Then you must place two newlines\n- Then you must specify your comment"
CREATE_PULL_REQUEST_PROMPT = '\nThis tool is useful when you need to create a new pull request in a GitHub repository. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify the title of the pull request\n- Then you must place two newlines\n- Then you must write the body or description of the pull request\n\nWhen appropriate, always reference relevant issues in the body by using the syntax `closes #<issue_number` like `closes #3, closes #6`.\nFor example, if you would like to create a pull request called "README updates" with contents "added contributors\' names, closes #3", you would pass in the following string:\n\nREADME updates\n\nadded contributors\' names, closes #3'
CREATE_FILE_PROMPT = '\nThis tool is a wrapper for the GitHub API, useful when you need to create a file in a GitHub repository. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify which file to create by passing a full file path (**IMPORTANT**: the path must not start with a slash)\n- Then you must specify the contents of the file\n\nFor example, if you would like to create a file called /test/test.txt with contents "test contents", you would pass in the following string:\n\ntest/test.txt\n\ntest contents'
READ_FILE_PROMPT = '\nThis tool is a wrapper for the GitHub API, useful when you need to read the contents of a file. Simply pass in the full file path of the file you would like to read. **IMPORTANT**: the path must not start with a slash'
UPDATE_FILE_PROMPT = '\nThis tool is a wrapper for the GitHub API, useful when you need to update the contents of a file in a GitHub repository. **VERY IMPORTANT**: Your input to this tool MUST strictly follow these rules:\n\n- First you must specify which file to modify by passing a full file path (**IMPORTANT**: the path must not start with a slash)\n- Then you must specify the old contents which you would like to replace wrapped in OLD <<<< and >>>> OLD\n- Then you must specify the new contents which you would like to replace the old contents with wrapped in NEW <<<< and >>>> NEW\n\nFor example, if you would like to replace the contents of the file /test/test.txt from "old contents" to "new contents", you would pass in the following string:\n\ntest/test.txt\n\nThis is text that will not be changed\nOLD <<<<\nold contents\n>>>> OLD\nNEW <<<<\nnew contents\n>>>> NEW'
DELETE_FILE_PROMPT = '\nThis tool is a wrapper for the GitHub API, useful when you need to delete a file in a GitHub repository. Simply pass in the full file path of the file you would like to delete. **IMPORTANT**: the path must not start with a slash'
GET_PR_PROMPT = '\nThis tool will fetch the title, body, comment thread and commit history of a specific Pull Request (by PR number). **VERY IMPORTANT**: You must specify the PR number as an integer.'
LIST_PRS_PROMPT = "\nThis tool will fetch a list of the repository's Pull Requests (PRs). It will return the title, and PR number of 5 PRs. It takes no input."
LIST_PULL_REQUEST_FILES = '\nThis tool will fetch the full text of all files in a pull request (PR) given the PR number as an input. This is useful for understanding the code changes in a PR or contributing to it. **VERY IMPORTANT**: You must specify the PR number as an integer input parameter.'
OVERVIEW_EXISTING_FILES_IN_MAIN = '\nThis tool will provide an overview of all existing files in the main branch of the repository. It will list the file names, their respective paths, and a brief summary of their contents. This can be useful for understanding the structure and content of the repository, especially when navigating through large codebases. No input parameters are required.'
OVERVIEW_EXISTING_FILES_BOT_BRANCH = '\nThis tool will provide an overview of all files in your current working branch where you should implement changes. This is great for getting a high level overview of the structure of your code. No input parameters are required.'
SEARCH_ISSUES_AND_PRS_PROMPT = '\nThis tool will search for issues and pull requests in the repository. **VERY IMPORTANT**: You must specify the search query as a string input parameter.'
SEARCH_CODE_PROMPT = '\nThis tool will search for code in the repository. **VERY IMPORTANT**: You must specify the search query as a string input parameter.'
CREATE_REVIEW_REQUEST_PROMPT = '\nThis tool will create a review request on the open pull request that matches the current active branch. **VERY IMPORTANT**: You must specify the username of the person who is being requested as a string input parameter.'
LIST_BRANCHES_IN_REPO_PROMPT = '\nThis tool will fetch a list of all branches in the repository. It will return the name of each branch. No input parameters are required.'
SET_ACTIVE_BRANCH_PROMPT = '\nThis tool will set the active branch in the repository, similar to `git checkout <branch_name>` and `git switch -c <branch_name>`. **VERY IMPORTANT**: You must specify the name of the branch as a string input parameter.'
CREATE_BRANCH_PROMPT = '\nThis tool will create a new branch in the repository. **VERY IMPORTANT**: You must specify the name of the new branch as a string input parameter.'
GET_FILES_FROM_DIRECTORY_PROMPT = '\nThis tool will fetch a list of all files in a specified directory. **VERY IMPORTANT**: You must specify the path of the directory as a string input parameter.'
GET_LATEST_RELEASE_PROMPT = '\nThis tool will fetch the latest release of the repository. No input parameters are required.'
GET_RELEASES_PROMPT = '\nThis tool will fetch the latest 5 releases of the repository. No input parameters are required.'
GET_RELEASE_PROMPT = '\nThis tool will fetch a specific release of the repository. **VERY IMPORTANT**: You must specify the tag name of the release as a string input parameter.'
QUESTION_TO_QUERY_BASE = '\nAnswer the question below with a DAX query that can be sent to Power BI. DAX queries have a simple syntax comprised of just one required keyword, EVALUATE, and several optional keywords: ORDER BY, START AT, DEFINE, MEASURE, VAR, TABLE, and COLUMN. Each keyword defines a statement used for the duration of the query. Any time < or > are used in the text below it means that those values need to be replaced by table, columns or other things. If the question is not something you can answer with a DAX query, reply with "I cannot answer this" and the question will be escalated to a human.\n\nSome DAX functions return a table instead of a scalar, and must be wrapped in a function that evaluates the table and returns a scalar; unless the table is a single column, single row table, then it is treated as a scalar value. Most DAX functions require one or more arguments, which can include tables, columns, expressions, and values. However, some functions, such as PI, do not require any arguments, but always require parentheses to indicate the null argument. For example, you must always type PI(), not PI. You can also nest functions within other functions. \n\nSome commonly used functions are:\nEVALUATE <table> - At the most basic level, a DAX query is an EVALUATE statement containing a table expression. At least one EVALUATE statement is required, however, a query can contain any number of EVALUATE statements.\nEVALUATE <table> ORDER BY <expression> ASC or DESC - The optional ORDER BY keyword defines one or more expressions used to sort query results. Any expression that can be evaluated for each row of the result is valid.\nEVALUATE <table> ORDER BY <expression> ASC or DESC START AT <value> or <parameter> - The optional START AT keyword is used inside an ORDER BY clause. It defines the value at which the query results begin.\nDEFINE MEASURE | VAR; EVALUATE <table> - The optional DEFINE keyword introduces one or more calculated entity definitions that exist only for the duration of the query. Definitions precede the EVALUATE statement and are valid for all EVALUATE statements in the query. Definitions can be variables, measures, tables1, and columns1. Definitions can reference other definitions that appear before or after the current definition. At least one definition is required if the DEFINE keyword is included in a query.\nMEASURE <table name>[<measure name>] = <scalar expression> - Introduces a measure definition in a DEFINE statement of a DAX query.\nVAR <name> = <expression> - Stores the result of an expression as a named variable, which can then be passed as an argument to other measure expressions. Once resultant values have been calculated for a variable expression, those values do not change, even if the variable is referenced in another expression.\n\nFILTER(<table>,<filter>) - Returns a table that represents a subset of another table or expression, where <filter> is a Boolean expression that is to be evaluated for each row of the table. For example, [Amount] > 0 or [Region] = "France"\nROW(<name>, <expression>) - Returns a table with a single row containing values that result from the expressions given to each column.\nTOPN(<n>, <table>, <OrderBy_Expression>, <Order>) - Returns a table with the top n rows from the specified table, sorted by the specified expression, in the order specified by 0 for descending, 1 for ascending, the default is 0. Multiple OrderBy_Expressions and Order pairs can be given, separated by a comma.\nDISTINCT(<column>) - Returns a one-column table that contains the distinct values from the specified column. In other words, duplicate values are removed and only unique values are returned. This function cannot be used to Return values into a cell or column on a worksheet; rather, you nest the DISTINCT function within a formula, to get a list of distinct values that can be passed to another function and then counted, summed, or used for other operations.\nDISTINCT(<table>) - Returns a table by removing duplicate rows from another table or expression.\n\nAggregation functions, names with a A in it, handle booleans and empty strings in appropriate ways, while the same function without A only uses the numeric values in a column. Functions names with an X in it can include a expression as an argument, this will be evaluated for each row in the table and the result will be used in the regular function calculation, these are the functions:\nCOUNT(<column>), COUNTA(<column>), COUNTX(<table>,<expression>), COUNTAX(<table>,<expression>), COUNTROWS([<table>]), COUNTBLANK(<column>), DISTINCTCOUNT(<column>), DISTINCTCOUNTNOBLANK (<column>) - these are all variations of count functions.\nAVERAGE(<column>), AVERAGEA(<column>), AVERAGEX(<table>,<expression>) - these are all variations of average functions.\nMAX(<column>), MAXA(<column>), MAXX(<table>,<expression>) - these are all variations of max functions.\nMIN(<column>), MINA(<column>), MINX(<table>,<expression>) - these are all variations of min functions.\nPRODUCT(<column>), PRODUCTX(<table>,<expression>) - these are all variations of product functions.\nSUM(<column>), SUMX(<table>,<expression>) - these are all variations of sum functions.\n\nDate and time functions:\nDATE(year, month, day) - Returns a date value that represents the specified year, month, and day.\nDATEDIFF(date1, date2, <interval>) - Returns the difference between two date values, in the specified interval, that can be SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR.\nDATEVALUE(<date_text>) - Returns a date value that represents the specified date.\nYEAR(<date>), QUARTER(<date>), MONTH(<date>), DAY(<date>), HOUR(<date>), MINUTE(<date>), SECOND(<date>) - Returns the part of the date for the specified date.\n\nFinally, make sure to escape double quotes with a single backslash, and make sure that only table names have single quotes around them, while names of measures or the values of columns that you want to compare against are in escaped double quotes. Newlines are not necessary and can be skipped. The queries are serialized as json and so will have to fit be compliant with json syntax. Sometimes you will get a question, a DAX query and a error, in that case you need to rewrite the DAX query to get the correct answer.\n\nThe following tables exist: {tables}\n\nand the schema\'s for some are given here:\n{schemas}\n\nExamples:\n{examples}\n'
USER_INPUT = '\nQuestion: {tool_input}\nDAX: \n'
SINGLE_QUESTION_TO_QUERY = f'{QUESTION_TO_QUERY_BASE}{USER_INPUT}'
DEFAULT_FEWSHOT_EXAMPLES = '\nQuestion: How many rows are in the table <table>?\nDAX: EVALUATE ROW("Number of rows", COUNTROWS(<table>))\n----\nQuestion: How many rows are in the table <table> where <column> is not empty?\nDAX: EVALUATE ROW("Number of rows", COUNTROWS(FILTER(<table>, <table>[<column>] <> "")))\n----\nQuestion: What was the average of <column> in <table>?\nDAX: EVALUATE ROW("Average", AVERAGE(<table>[<column>]))\n----\n'
RETRY_RESPONSE = '{tool_input} DAX: {query} Error: {error}. Please supply a new DAX query.'
BAD_REQUEST_RESPONSE = 'Error on this question, the error was {error}, you can try to rephrase the question.'
SCHEMA_ERROR_RESPONSE = 'Bad request, are you sure the table name is correct?'
UNAUTHORIZED_RESPONSE = 'Unauthorized. Try changing your authentication, do not retry.'
QUERY_CHECKER = '\n{query}\nDouble check the Spark SQL query above for common mistakes, including:\n- Using NOT IN with NULL values\n- Using UNION when UNION ALL should have been used\n- Using BETWEEN for exclusive ranges\n- Data type mismatch in predicates\n- Properly quoting identifiers\n- Using the correct number of arguments for functions\n- Casting to the correct data type\n- Using the proper columns for joins\n\nIf there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.'
from langchain.chains.natbot.prompt import PROMPT
__all__ = ['PROMPT']
SQL_PREFIX = 'You are an agent designed to interact with a SQL database.\nGiven an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.\nUnless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.\nYou can order the results by a relevant column to return the most interesting examples in the database.\nNever query for all the columns from a specific table, only ask for the relevant columns given the question.\nYou have access to tools for interacting with the database.\nOnly use the below tools. Only use the information returned by the below tools to construct your final answer.\nYou MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.\n\nDO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.\n\nIf the question does not seem related to the database, just return "I don\'t know" as the answer.\n'
SQL_SUFFIX = 'Begin!\n\nQuestion: {input}\nThought: I should look at the tables in the database to see what I can query.  Then I should query the schema of the most relevant tables.\n{agent_scratchpad}'
SQL_FUNCTIONS_SUFFIX = 'I should look at the tables in the database to see what I can query.  Then I should query the schema of the most relevant tables.'
JSON_PREFIX = 'You are an agent designed to interact with JSON.\nYour goal is to return a final answer by interacting with the JSON.\nYou have access to the following tools which help you learn more about the JSON you are interacting with.\nOnly use the below tools. Only use the information returned by the below tools to construct your final answer.\nDo not make up any information that is not contained in the JSON.\nYour input to the tools should be in the form of `data["key"][0]` where `data` is the JSON blob you are interacting with, and the syntax used is Python. \nYou should only use keys that you know for a fact exist. You must validate that a key exists by seeing it previously when calling `json_spec_list_keys`. \nIf you have not seen a key in one of those responses, you cannot use it.\nYou should only add one key at a time to the path. You cannot add multiple keys at once.\nIf you encounter a "KeyError", go back to the previous key, look at the available keys, and try again.\n\nIf the question does not seem to be related to the JSON, just return "I don\'t know" as the answer.\nAlways begin your interaction with the `json_spec_list_keys` tool with input "data" to see what keys exist in the JSON.\n\nNote that sometimes the value at a given path is large. In this case, you will get an error "Value is a large dictionary, should explore its keys directly".\nIn this case, you should ALWAYS follow up by using the `json_spec_list_keys` tool to see what keys exist at that path.\nDo not simply refer the user to the JSON or a section of the JSON, as this is not a valid answer. Keep digging until you find the answer and explicitly return it.\n'
JSON_SUFFIX = 'Begin!"\n\nQuestion: {input}\nThought: I should look at the keys that exist in data to see what I have access to\n{agent_scratchpad}'
'Prompts for PowerBI agent.'
POWERBI_PREFIX = 'You are an agent designed to help users interact with a PowerBI Dataset.\n\nAgent has access to a tool that can write a query based on the question and then run those against PowerBI, Microsofts business intelligence tool. The questions from the users should be interpreted as related to the dataset that is available and not general questions about the world. If the question does not seem related to the dataset, return "This does not appear to be part of this dataset." as the answer.\n\nGiven an input question, ask to run the questions against the dataset, then look at the results and return the answer, the answer should be a complete sentence that answers the question, if multiple rows are asked find a way to write that in a easily readable format for a human, also make sure to represent numbers in readable ways, like 1M instead of 1000000. Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.\n'
POWERBI_SUFFIX = 'Begin!\n\nQuestion: {input}\nThought: I can first ask which tables I have, then how each table is defined and then ask the query tool the question I need, and finally create a nice sentence that answers the question.\n{agent_scratchpad}'
POWERBI_CHAT_PREFIX = 'Assistant is a large language model built to help users interact with a PowerBI Dataset.\n\nAssistant should try to create a correct and complete answer to the question from the user. If the user asks a question not related to the dataset it should return "This does not appear to be part of this dataset." as the answer. The user might make a mistake with the spelling of certain values, if you think that is the case, ask the user to confirm the spelling of the value and then run the query again. Unless the user specifies a specific number of examples they wish to obtain, and the results are too large, limit your query to at most {top_k} results, but make it clear when answering which field was used for the filtering. The user has access to these tables: {{tables}}.\n\nThe answer should be a complete sentence that answers the question, if multiple rows are asked find a way to write that in a easily readable format for a human, also make sure to represent numbers in readable ways, like 1M instead of 1000000. \n'
POWERBI_CHAT_SUFFIX = "TOOLS\n------\nAssistant can ask the user to use tools to look up information that may be helpful in answering the users original question. The tools the human can use are:\n\n{{tools}}\n\n{format_instructions}\n\nUSER'S INPUT\n--------------------\nHere is the user's input (remember to respond with a markdown code snippet of a json blob with a single action, and NOTHING else):\n\n{{{{input}}}}\n"
OPENAPI_PREFIX = "You are an agent designed to answer questions by making web requests to an API given the openapi spec.\n\nIf the question does not seem related to the API, return I don't know. Do not make up an answer.\nOnly use information provided by the tools to construct your response.\n\nFirst, find the base URL needed to make the request.\n\nSecond, find the relevant paths needed to answer the question. Take note that, sometimes, you might need to make more than one request to more than one path to answer the question.\n\nThird, find the required parameters needed to make the request. For GET requests, these are usually URL parameters and for POST requests, these are request body parameters.\n\nFourth, make the requests needed to answer the question. Ensure that you are sending the correct parameters to the request by checking which parameters are required. For parameters with a fixed set of values, please use the spec to look at which values are allowed.\n\nUse the exact parameter names as listed in the spec, do not make up any names or abbreviate the names of parameters.\nIf you get a not found error, ensure that you are using a path that actually exists in the spec.\n"
OPENAPI_SUFFIX = 'Begin!\n\nQuestion: {input}\nThought: I should explore the spec to find the base server url for the API in the servers node.\n{agent_scratchpad}'
DESCRIPTION = "Can be used to answer questions about the openapi spec for the API. Always use this tool before trying to make a request. \nExample inputs to this tool: \n    'What are the required query parameters for a GET request to the /bar endpoint?`\n    'What are the required parameters in the request body for a POST request to the /foo endpoint?'\nAlways give this tool a specific question."
SQL_PREFIX = 'You are an agent designed to interact with Spark SQL.\nGiven an input question, create a syntactically correct Spark SQL query to run, then look at the results of the query and return the answer.\nUnless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.\nYou can order the results by a relevant column to return the most interesting examples in the database.\nNever query for all the columns from a specific table, only ask for the relevant columns given the question.\nYou have access to tools for interacting with the database.\nOnly use the below tools. Only use the information returned by the below tools to construct your final answer.\nYou MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.\n\nDO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.\n\nIf the question does not seem related to the database, just return "I don\'t know" as the answer.\n'
SQL_SUFFIX = 'Begin!\n\nQuestion: {input}\nThought: I should look at the tables in the database to see what I can query.\n{agent_scratchpad}'
'Prompt schema definition.'
from __future__ import annotations
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union
from pydantic import BaseModel, model_validator
from typing_extensions import override
from langchain_core.prompts.string import DEFAULT_FORMATTER_MAPPING, PromptTemplateFormat, StringPromptTemplate, check_valid_template, get_template_variables, mustache_schema
if TYPE_CHECKING:
    from langchain_core.runnables.config import RunnableConfig

class PromptTemplate(StringPromptTemplate):
    """Prompt template for a language model.

    A prompt template consists of a string template. It accepts a set of parameters
    from the user that can be used to generate a prompt for a language model.

    The template can be formatted using either f-strings (default), jinja2,
    or mustache syntax.

    *Security warning*:
        Prefer using `template_format="f-string"` instead of
        `template_format="jinja2"`, or make sure to NEVER accept jinja2 templates
        from untrusted sources as they may lead to arbitrary Python code execution.

        As of LangChain 0.0.329, Jinja2 templates will be rendered using
        Jinja2's SandboxedEnvironment by default. This sand-boxing should
        be treated as a best-effort approach rather than a guarantee of security,
        as it is an opt-out rather than opt-in approach.

        Despite the sand-boxing, we recommend to never use jinja2 templates
        from untrusted sources.

    Example:

        .. code-block:: python

            from langchain_core.prompts import PromptTemplate

            # Instantiation using from_template (recommended)
            prompt = PromptTemplate.from_template("Say {foo}")
            prompt.format(foo="bar")

            # Instantiation using initializer
            prompt = PromptTemplate(template="Say {foo}")

    """

    @property
    @override
    def lc_attributes(self) -> dict[str, Any]:
        return {'template_format': self.template_format}

    @classmethod
    @override
    def get_lc_namespace(cls) -> list[str]:
        return ['langchain', 'prompts', 'prompt']
    template: str
    'The prompt template.'
    template_format: PromptTemplateFormat = 'f-string'
    "The format of the prompt template.\n    Options are: 'f-string', 'mustache', 'jinja2'."
    validate_template: bool = False
    'Whether or not to try validating the template.'

    @model_validator(mode='before')
    @classmethod
    def pre_init_validation(cls, values: dict) -> Any:
        """Check that template and input variables are consistent."""
        if values.get('template') is None:
            return values
        values.setdefault('template_format', 'f-string')
        values.setdefault('partial_variables', {})
        if values.get('validate_template'):
            if values['template_format'] == 'mustache':
                msg = 'Mustache templates cannot be validated.'
                raise ValueError(msg)
            if 'input_variables' not in values:
                msg = 'Input variables must be provided to validate the template.'
                raise ValueError(msg)
            all_inputs = values['input_variables'] + list(values['partial_variables'])
            check_valid_template(values['template'], values['template_format'], all_inputs)
        if values['template_format']:
            values['input_variables'] = [var for var in get_template_variables(values['template'], values['template_format']) if var not in values['partial_variables']]
        return values

    @override
    def get_input_schema(self, config: RunnableConfig | None=None) -> type[BaseModel]:
        """Get the input schema for the prompt.

        Args:
            config: The runnable configuration.

        Returns:
            The input schema for the prompt.
        """
        if self.template_format != 'mustache':
            return super().get_input_schema(config)
        return mustache_schema(self.template)

    def __add__(self, other: Any) -> PromptTemplate:
        """Override the + operator to allow for combining prompt templates."""
        if isinstance(other, PromptTemplate):
            if self.template_format != 'f-string':
                msg = 'Adding prompt templates only supported for f-strings.'
                raise ValueError(msg)
            if other.template_format != 'f-string':
                msg = 'Adding prompt templates only supported for f-strings.'
                raise ValueError(msg)
            input_variables = list(set(self.input_variables) | set(other.input_variables))
            template = self.template + other.template
            validate_template = self.validate_template and other.validate_template
            partial_variables = dict(self.partial_variables.items())
            for k, v in other.partial_variables.items():
                if k in partial_variables:
                    msg = 'Cannot have same variable partialed twice.'
                    raise ValueError(msg)
                partial_variables[k] = v
            return PromptTemplate(template=template, input_variables=input_variables, partial_variables=partial_variables, template_format='f-string', validate_template=validate_template)
        if isinstance(other, str):
            prompt = PromptTemplate.from_template(other)
            return self + prompt
        msg = f'Unsupported operand type for +: {type(other)}'
        raise NotImplementedError(msg)

    @property
    def _prompt_type(self) -> str:
        """Return the prompt type key."""
        return 'prompt'

    def format(self, **kwargs: Any) -> str:
        """Format the prompt with the inputs.

        Args:
            kwargs: Any arguments to be passed to the prompt template.

        Returns:
            A formatted string.
        """
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        return DEFAULT_FORMATTER_MAPPING[self.template_format](self.template, **kwargs)

    @classmethod
    def from_examples(cls, examples: list[str], suffix: str, input_variables: list[str], example_separator: str='\n\n', prefix: str='', **kwargs: Any) -> PromptTemplate:
        """Take examples in list format with prefix and suffix to create a prompt.

        Intended to be used as a way to dynamically create a prompt from examples.

        Args:
            examples: List of examples to use in the prompt.
            suffix: String to go after the list of examples. Should generally
                set up the user's input.
            input_variables: A list of variable names the final prompt template
                will expect.
            example_separator: The separator to use in between examples. Defaults
                to two new line characters.
            prefix: String that should go before any examples. Generally includes
                examples. Default to an empty string.

        Returns:
            The final prompt generated.
        """
        template = example_separator.join([prefix, *examples, suffix])
        return cls(input_variables=input_variables, template=template, **kwargs)

    @classmethod
    def from_file(cls, template_file: Union[str, Path], input_variables: Optional[list[str]]=None, encoding: Optional[str]=None, **kwargs: Any) -> PromptTemplate:
        """Load a prompt from a file.

        Args:
            template_file: The path to the file containing the prompt template.
            input_variables: [DEPRECATED] A list of variable names the final prompt
                template will expect. Defaults to None.
            encoding: The encoding system for opening the template file.
                If not provided, will use the OS default.

        input_variables is ignored as from_file now delegates to from_template().

        Returns:
            The prompt loaded from the file.
        """
        template = Path(template_file).read_text(encoding=encoding)
        if input_variables:
            warnings.warn("`input_variables' is deprecated and ignored.", DeprecationWarning, stacklevel=2)
        return cls.from_template(template=template, **kwargs)

    @classmethod
    def from_template(cls, template: str, *, template_format: PromptTemplateFormat='f-string', partial_variables: Optional[dict[str, Any]]=None, **kwargs: Any) -> PromptTemplate:
        """Load a prompt template from a template.

        *Security warning*:
            Prefer using `template_format="f-string"` instead of
            `template_format="jinja2"`, or make sure to NEVER accept jinja2 templates
            from untrusted sources as they may lead to arbitrary Python code execution.

            As of LangChain 0.0.329, Jinja2 templates will be rendered using
            Jinja2's SandboxedEnvironment by default. This sand-boxing should
            be treated as a best-effort approach rather than a guarantee of security,
            as it is an opt-out rather than opt-in approach.

            Despite the sand-boxing, we recommend never using jinja2 templates
            from untrusted sources.

        Args:
            template: The template to load.
            template_format: The format of the template. Use `jinja2` for jinja2,
                             `mustache` for mustache, and `f-string` for f-strings.
                             Defaults to `f-string`.
            partial_variables: A dictionary of variables that can be used to partially
                               fill in the template. For example, if the template is
                              `"{variable1} {variable2}"`, and `partial_variables` is
                              `{"variable1": "foo"}`, then the final prompt will be
                              `"foo {variable2}"`. Defaults to None.
            kwargs: Any other arguments to pass to the prompt template.

        Returns:
            The prompt template loaded from the template.
        """
        input_variables = get_template_variables(template, template_format)
        partial_variables_ = partial_variables or {}
        if partial_variables_:
            input_variables = [var for var in input_variables if var not in partial_variables_]
        return cls(input_variables=input_variables, template=template, template_format=template_format, partial_variables=partial_variables_, **kwargs)
from typing import Any, Generic, List, Optional, TextIO, TypeVar, Union, overload
from . import get_console
from .console import Console
from .text import Text, TextType
PromptType = TypeVar('PromptType')
DefaultType = TypeVar('DefaultType')
if __name__ == '__main__':
    from rich import print
    if Confirm.ask('Run [i]prompt[/i] tests?', default=True):
        while True:
            result = IntPrompt.ask(':rocket: Enter a number between [b]1[/b] and [b]10[/b]', default=5)
            if result >= 1 and result <= 10:
                break
            print(':pile_of_poo: [prompt.invalid]Number must be between 1 and 10')
        print(f'number={result}')
        while True:
            password = Prompt.ask('Please enter a password [cyan](must be at least 5 characters)', password=True)
            if len(password) >= 5:
                break
            print('[prompt.invalid]password too short')
        print(f'password={password!r}')
        fruit = Prompt.ask('Enter a fruit', choices=['apple', 'orange', 'pear'])
        print(f'fruit={fruit!r}')
        doggie = Prompt.ask("What's the best Dog? (Case INSENSITIVE)", choices=['Border Terrier', 'Collie', 'Labradoodle'], case_sensitive=False)
        print(f'doggie={doggie!r}')
    else:
        print('[b]OK :loudly_crying_face:')
'Prompts for comparing the outputs of two models for a given question.\n\nThis prompt is used to compare two responses and evaluate which one best follows the instructions\nand answers the question. The prompt is based on the paper from\nZheng, et. al. https://arxiv.org/abs/2306.05685\n'
from langchain_core.prompts.chat import ChatPromptTemplate
SYSTEM_MESSAGE = 'Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user\'s instructions and answers \the user\'s question better. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. Be as objective as possible. After providing your explanation, output your final verdict by strictly following this format: "[[A]]" if assistant A is better, "[[B]]" if assistant B is better, and "[[C]]" for a tie.'
CRITERIA_INSTRUCTIONS = 'For this evaluation, you should primarily consider the following criteria:\n'
COMPARISON_TEMPLATE = ChatPromptTemplate.from_messages([('system', SYSTEM_MESSAGE), ('human', "{criteria}[User Question]\n{input}\n\n[The Start of Assistant A's Answer]\n{prediction}\n[The End of Assistant A's Answer]\n\n[The Start of Assistant B's Answer]\n{prediction_b}\n[The End of Assistant B's Answer]")])
COMPARISON_TEMPLATE_WITH_REFERENCE = ChatPromptTemplate.from_messages([('system', SYSTEM_MESSAGE), ('human', "{criteria}\n\nTo help you evaluate the responses, here is a reference answer to the user's question:\n{reference}[User Question]\n{input}\n\n[The Start of Assistant A's Answer]\n{prediction}\n[The End of Assistant A's Answer]\n\n[The Start of Assistant B's Answer]\n{prediction_b}\n[The End of Assistant B's Answer]")])
from langchain_core.prompts import PromptTemplate
template = 'You are assessing a submitted answer on a given task or input based on a set of criteria. Here is the data:\n[BEGIN DATA]\n***\n[Input]: {input}\n***\n[Submission]: {output}\n***\n[Criteria]: {criteria}\n***\n[END DATA]\nDoes the submission meet the Criteria? First, write out in a step by step manner your reasoning about each criterion to be sure that your conclusion is correct. Avoid simply stating the correct answers at the outset. Then print only the single character "Y" or "N" (without quotes or punctuation) on its own line corresponding to the correct answer of whether the submission meets all criteria. At the end, repeat just the letter again by itself on a new line.'
PROMPT = PromptTemplate(input_variables=['input', 'output', 'criteria'], template=template)
template = 'You are assessing a submitted answer on a given task or input based on a set of criteria. Here is the data:\n[BEGIN DATA]\n***\n[Input]: {input}\n***\n[Submission]: {output}\n***\n[Criteria]: {criteria}\n***\n[Reference]: {reference}\n***\n[END DATA]\nDoes the submission meet the Criteria? First, write out in a step by step manner your reasoning about each criterion to be sure that your conclusion is correct. Avoid simply stating the correct answers at the outset. Then print only the single character "Y" or "N" (without quotes or punctuation) on its own line corresponding to the correct answer of whether the submission meets all criteria. At the end, repeat just the letter again by itself on a new line.'
PROMPT_WITH_REFERENCES = PromptTemplate(input_variables=['input', 'output', 'criteria', 'reference'], template=template)
'Prompts for scoring the outputs of a models for a given question.\n\nThis prompt is used to score the responses and evaluate how it follows the instructions\nand answers the question. The prompt is based on the paper from\nZheng, et. al. https://arxiv.org/abs/2306.05685\n'
from langchain_core.prompts.chat import ChatPromptTemplate
SYSTEM_MESSAGE = 'You are a helpful assistant.'
CRITERIA_INSTRUCTIONS = 'For this evaluation, you should primarily consider the following criteria:\n'
DEFAULT_CRITERIA = ' Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response.'
SCORING_TEMPLATE = ChatPromptTemplate.from_messages([('system', SYSTEM_MESSAGE), ('human', '[Instruction]\nPlease act as an impartial judge and evaluate the quality of the response provided by an AI assistant to the user question displayed below. {criteria}Begin your evaluation by providing a short explanation. Be as objective as possible. After providing your explanation, you must rate the response on a scale of 1 to 10 by strictly following this format: "[[rating]]", for example: "Rating: [[5]]".\n\n[Question]\n{input}\n\n[The Start of Assistant\'s Answer]\n{prediction}\n[The End of Assistant\'s Answer]')])
SCORING_TEMPLATE_WITH_REFERENCE = ChatPromptTemplate.from_messages([('system', SYSTEM_MESSAGE), ('human', '[Instruction]\nPlease act as an impartial judge and evaluate the quality of the response provided by an AI assistant to the user question displayed below. {criteria}[Ground truth]\n{reference}\nBegin your evaluation by providing a short explanation. Be as objective as possible. After providing your explanation, you must rate the response on a scale of 1 to 10 by strictly following this format: "[[rating]]", for example: "Rating: [[5]]".\n\n[Question]\n{input}\n\n[The Start of Assistant\'s Answer]\n{prediction}\n[The End of Assistant\'s Answer]')])
from langchain_core.prompt_values import PromptValue
__all__ = ['PromptValue']
'For backwards compatibility.'
from typing import TYPE_CHECKING, Any
from langchain._api import create_importer
if TYPE_CHECKING:
    from langchain_community.tools.sql_database.prompt import QUERY_CHECKER
_importer = create_importer(__package__, deprecated_lookups={'QUERY_CHECKER': 'langchain_community.tools.sql_database.prompt'})

def __getattr__(name: str) -> Any:
    """Look up attributes dynamically."""
    return _importer(name)
__all__ = ['QUERY_CHECKER']
from langchain_core.prompts.prompt import PromptTemplate
_PROMPT_TEMPLATE = '\nYou are an agents controlling a browser. You are given:\n\n\t(1) an objective that you are trying to achieve\n\t(2) the URL of your current web page\n\t(3) a simplified text description of what\'s visible in the browser window (more on that below)\n\nYou can issue these commands:\n\tSCROLL UP - scroll up one page\n\tSCROLL DOWN - scroll down one page\n\tCLICK X - click on a given element. You can only click on links, buttons, and inputs!\n\tTYPE X "TEXT" - type the specified text into the input with id X\n\tTYPESUBMIT X "TEXT" - same as TYPE above, except then it presses ENTER to submit the form\n\nThe format of the browser content is highly simplified; all formatting elements are stripped.\nInteractive elements such as links, inputs, buttons are represented like this:\n\n\t\t<link id=1>text</link>\n\t\t<button id=2>text</button>\n\t\t<input id=3>text</input>\n\nImages are rendered as their alt text like this:\n\n\t\t<img id=4 alt=""/>\n\nBased on your given objective, issue whatever command you believe will get you closest to achieving your goal.\nYou always start on Google; you should submit a search query to Google that will take you to the best page for\nachieving your objective. And then interact with that page to achieve your objective.\n\nIf you find yourself on Google and there are no search results displayed yet, you should probably issue a command\nlike "TYPESUBMIT 7 "search query"" to get to a more useful page.\n\nThen, if you find yourself on a Google search results page, you might issue the command "CLICK 24" to click\non the first link in the search results. (If your previous command was a TYPESUBMIT your next command should\nprobably be a CLICK.)\n\nDon\'t try to interact with elements that you can\'t see.\n\nHere are some examples:\n\nEXAMPLE 1:\n==================================================\nCURRENT BROWSER CONTENT:\n------------------\n<link id=1>About</link>\n<link id=2>Store</link>\n<link id=3>Gmail</link>\n<link id=4>Images</link>\n<link id=5>(Google apps)</link>\n<link id=6>Sign in</link>\n<img id=7 alt="(Google)"/>\n<input id=8 alt="Search"></input>\n<button id=9>(Search by voice)</button>\n<button id=10>(Google Search)</button>\n<button id=11>(I\'m Feeling Lucky)</button>\n<link id=12>Advertising</link>\n<link id=13>Business</link>\n<link id=14>How Search works</link>\n<link id=15>Carbon neutral since 2007</link>\n<link id=16>Privacy</link>\n<link id=17>Terms</link>\n<text id=18>Settings</text>\n------------------\nOBJECTIVE: Find a 2 bedroom house for sale in Anchorage AK for under $750k\nCURRENT URL: https://www.google.com/\nYOUR COMMAND:\nTYPESUBMIT 8 "anchorage redfin"\n==================================================\n\nEXAMPLE 2:\n==================================================\nCURRENT BROWSER CONTENT:\n------------------\n<link id=1>About</link>\n<link id=2>Store</link>\n<link id=3>Gmail</link>\n<link id=4>Images</link>\n<link id=5>(Google apps)</link>\n<link id=6>Sign in</link>\n<img id=7 alt="(Google)"/>\n<input id=8 alt="Search"></input>\n<button id=9>(Search by voice)</button>\n<button id=10>(Google Search)</button>\n<button id=11>(I\'m Feeling Lucky)</button>\n<link id=12>Advertising</link>\n<link id=13>Business</link>\n<link id=14>How Search works</link>\n<link id=15>Carbon neutral since 2007</link>\n<link id=16>Privacy</link>\n<link id=17>Terms</link>\n<text id=18>Settings</text>\n------------------\nOBJECTIVE: Make a reservation for 4 at Dorsia at 8pm\nCURRENT URL: https://www.google.com/\nYOUR COMMAND:\nTYPESUBMIT 8 "dorsia nyc opentable"\n==================================================\n\nEXAMPLE 3:\n==================================================\nCURRENT BROWSER CONTENT:\n------------------\n<button id=1>For Businesses</button>\n<button id=2>Mobile</button>\n<button id=3>Help</button>\n<button id=4 alt="Language Picker">EN</button>\n<link id=5>OpenTable logo</link>\n<button id=6 alt ="search">Search</button>\n<text id=7>Find your table for any occasion</text>\n<button id=8>(Date selector)</button>\n<text id=9>Sep 28, 2022</text>\n<text id=10>7:00 PM</text>\n<text id=11>2 people</text>\n<input id=12 alt="Location, Restaurant, or Cuisine"></input>\n<button id=13>Let’s go</button>\n<text id=14>It looks like you\'re in Peninsula. Not correct?</text>\n<button id=15>Get current location</button>\n<button id=16>Next</button>\n------------------\nOBJECTIVE: Make a reservation for 4 for dinner at Dorsia in New York City at 8pm\nCURRENT URL: https://www.opentable.com/\nYOUR COMMAND:\nTYPESUBMIT 12 "dorsia new york city"\n==================================================\n\nThe current browser content, objective, and current URL follow. Reply with your next command to the browser.\n\nCURRENT BROWSER CONTENT:\n------------------\n{browser_content}\n------------------\n\nOBJECTIVE: {objective}\nCURRENT URL: {url}\nPREVIOUS COMMAND: {previous_command}\nYOUR COMMAND:\n'
PROMPT = PromptTemplate(input_variables=['browser_content', 'url', 'previous_command', 'objective'], template=_PROMPT_TEMPLATE)
from langchain_core.output_parsers.list import CommaSeparatedListOutputParser
from langchain_core.prompts.prompt import PromptTemplate
PROMPT_SUFFIX = 'Only use the following tables:\n{table_info}\n\nQuestion: {input}'
_DEFAULT_TEMPLATE = 'Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer. Unless the user specifies in his question a specific number of examples he wishes to obtain, always limit your query to at most {top_k} results. You can order the results by a relevant column to return the most interesting examples in the database.\n\nNever query for all the columns from a specific table, only ask for a few relevant columns given the question.\n\nPay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'dialect', 'top_k'], template=_DEFAULT_TEMPLATE + PROMPT_SUFFIX)
_DECIDER_TEMPLATE = 'Given the below input question and list of potential tables, output a comma separated list of the table names that may be necessary to answer this question.\n\nQuestion: {query}\n\nTable Names: {table_names}\n\nRelevant Table Names:'
DECIDER_PROMPT = PromptTemplate(input_variables=['query', 'table_names'], template=_DECIDER_TEMPLATE, output_parser=CommaSeparatedListOutputParser())
_cratedb_prompt = 'You are a CrateDB expert. Given an input question, first create a syntactically correct CrateDB query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per CrateDB. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use CURRENT_DATE function to get the current date, if the question involves "today". \n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
CRATEDB_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_cratedb_prompt + PROMPT_SUFFIX)
_duckdb_prompt = 'You are a DuckDB expert. Given an input question, first create a syntactically correct DuckDB query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per DuckDB. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use today() function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
DUCKDB_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_duckdb_prompt + PROMPT_SUFFIX)
_googlesql_prompt = 'You are a GoogleSQL expert. Given an input question, first create a syntactically correct GoogleSQL query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per GoogleSQL. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use CURRENT_DATE() function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
GOOGLESQL_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_googlesql_prompt + PROMPT_SUFFIX)
_mssql_prompt = 'You are an MS SQL expert. Given an input question, first create a syntactically correct MS SQL query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the TOP clause as per MS SQL. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in square brackets ([]) to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use CAST(GETDATE() as date) function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
MSSQL_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_mssql_prompt + PROMPT_SUFFIX)
_mysql_prompt = 'You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use CURDATE() function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
MYSQL_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_mysql_prompt + PROMPT_SUFFIX)
_mariadb_prompt = 'You are a MariaDB expert. Given an input question, first create a syntactically correct MariaDB query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MariaDB. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use CURDATE() function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
MARIADB_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_mariadb_prompt + PROMPT_SUFFIX)
_oracle_prompt = 'You are an Oracle SQL expert. Given an input question, first create a syntactically correct Oracle SQL query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the FETCH FIRST n ROWS ONLY clause as per Oracle SQL. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use TRUNC(SYSDATE) function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
ORACLE_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_oracle_prompt + PROMPT_SUFFIX)
_postgres_prompt = 'You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use CURRENT_DATE function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
POSTGRES_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_postgres_prompt + PROMPT_SUFFIX)
_sqlite_prompt = 'You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per SQLite. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use date(\'now\') function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: Question here\nSQLQuery: SQL Query to run\nSQLResult: Result of the SQLQuery\nAnswer: Final answer here\n\n'
SQLITE_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_sqlite_prompt + PROMPT_SUFFIX)
_clickhouse_prompt = 'You are a ClickHouse expert. Given an input question, first create a syntactically correct Clic query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per ClickHouse. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use today() function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: "Question here"\nSQLQuery: "SQL Query to run"\nSQLResult: "Result of the SQLQuery"\nAnswer: "Final answer here"\n\n'
CLICKHOUSE_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_clickhouse_prompt + PROMPT_SUFFIX)
_prestodb_prompt = 'You are a PrestoDB expert. Given an input question, first create a syntactically correct PrestoDB query to run, then look at the results of the query and return the answer to the input question.\nUnless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PrestoDB. You can order the results to return the most informative data in the database.\nNever query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.\nPay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.\nPay attention to use current_date function to get the current date, if the question involves "today".\n\nUse the following format:\n\nQuestion: "Question here"\nSQLQuery: "SQL Query to run"\nSQLResult: "Result of the SQLQuery"\nAnswer: "Final answer here"\n\n'
PRESTODB_PROMPT = PromptTemplate(input_variables=['input', 'table_info', 'top_k'], template=_prestodb_prompt + PROMPT_SUFFIX)
SQL_PROMPTS = {'crate': CRATEDB_PROMPT, 'duckdb': DUCKDB_PROMPT, 'googlesql': GOOGLESQL_PROMPT, 'mssql': MSSQL_PROMPT, 'mysql': MYSQL_PROMPT, 'mariadb': MARIADB_PROMPT, 'oracle': ORACLE_PROMPT, 'postgresql': POSTGRES_PROMPT, 'sqlite': SQLITE_PROMPT, 'clickhouse': CLICKHOUSE_PROMPT, 'prestodb': PRESTODB_PROMPT}
from langchain.chains.prompt_selector import ConditionalPromptSelector, is_chat_model
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
templ1 = 'You are a smart assistant designed to help high school teachers come up with reading comprehension questions.\nGiven a piece of text, you must come up with a question and answer pair that can be used to test a student\'s reading comprehension abilities.\nWhen coming up with this question/answer pair, you must respond in the following format:\n```\n{{\n    "question": "$YOUR_QUESTION_HERE",\n    "answer": "$THE_ANSWER_HERE"\n}}\n```\n\nEverything between the ``` must be valid json.\n'
templ2 = 'Please come up with a question/answer pair, in the specified JSON format, for the following text:\n----------------\n{text}'
CHAT_PROMPT = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(templ1), HumanMessagePromptTemplate.from_template(templ2)])
templ = 'You are a smart assistant designed to help high school teachers come up with reading comprehension questions.\nGiven a piece of text, you must come up with a question and answer pair that can be used to test a student\'s reading comprehension abilities.\nWhen coming up with this question/answer pair, you must respond in the following format:\n```\n{{\n    "question": "$YOUR_QUESTION_HERE",\n    "answer": "$THE_ANSWER_HERE"\n}}\n```\n\nEverything between the ``` must be valid json.\n\nPlease come up with a question/answer pair, in the specified JSON format, for the following text:\n----------------\n{text}'
PROMPT = PromptTemplate.from_template(templ)
PROMPT_SELECTOR = ConditionalPromptSelector(default_prompt=PROMPT, conditionals=[(is_chat_model, CHAT_PROMPT)])
from langchain_core.prompts.prompt import PromptTemplate
_CREATE_DRAFT_ANSWER_TEMPLATE = '{question}\n\n'
CREATE_DRAFT_ANSWER_PROMPT = PromptTemplate(input_variables=['question'], template=_CREATE_DRAFT_ANSWER_TEMPLATE)
_LIST_ASSERTIONS_TEMPLATE = 'Here is a statement:\n{statement}\nMake a bullet point list of the assumptions you made when producing the above statement.\n\n'
LIST_ASSERTIONS_PROMPT = PromptTemplate(input_variables=['statement'], template=_LIST_ASSERTIONS_TEMPLATE)
_CHECK_ASSERTIONS_TEMPLATE = 'Here is a bullet point list of assertions:\n{assertions}\nFor each assertion, determine whether it is true or false. If it is false, explain why.\n\n'
CHECK_ASSERTIONS_PROMPT = PromptTemplate(input_variables=['assertions'], template=_CHECK_ASSERTIONS_TEMPLATE)
_REVISED_ANSWER_TEMPLATE = "{checked_assertions}\n\nQuestion: In light of the above assertions and checks, how would you answer the question '{question}'?\n\nAnswer:"
REVISED_ANSWER_PROMPT = PromptTemplate(input_variables=['checked_assertions', 'question'], template=_REVISED_ANSWER_TEMPLATE)
from langchain_core.prompts import PromptTemplate
prompt_template = "Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\n{context}\n\nQuestion: {question}\nHelpful Answer:"
PROMPT = PromptTemplate(template=prompt_template, input_variables=['context', 'question'])
from langchain_core.prompts.prompt import PromptTemplate
_PROMPT_TEMPLATE = 'Translate a math problem into a expression that can be executed using Python\'s numexpr library. Use the output of running this code to answer the question.\n\nQuestion: ${{Question with math problem.}}\n```text\n${{single line mathematical expression that solves the problem}}\n```\n...numexpr.evaluate(text)...\n```output\n${{Output of running the code}}\n```\nAnswer: ${{Answer}}\n\nBegin.\n\nQuestion: What is 37593 * 67?\n```text\n37593 * 67\n```\n...numexpr.evaluate("37593 * 67")...\n```output\n2518731\n```\nAnswer: 2518731\n\nQuestion: 37593^(1/5)\n```text\n37593**(1/5)\n```\n...numexpr.evaluate("37593**(1/5)")...\n```output\n8.222831614237718\n```\nAnswer: 8.222831614237718\n\nQuestion: {question}\n'
PROMPT = PromptTemplate(input_variables=['question'], template=_PROMPT_TEMPLATE)
from langchain_core.prompts.prompt import PromptTemplate
API_URL_PROMPT_TEMPLATE = 'You are given the below API Documentation:\n{api_docs}\nUsing this documentation, generate the full API url to call for answering the user question.\nYou should build the API url in order to get a response that is as short as possible, while still getting the necessary information to answer the question. Pay attention to deliberately exclude any unnecessary pieces of data in the API call.\n\nQuestion:{question}\nAPI url:'
API_URL_PROMPT = PromptTemplate(input_variables=['api_docs', 'question'], template=API_URL_PROMPT_TEMPLATE)
API_RESPONSE_PROMPT_TEMPLATE = API_URL_PROMPT_TEMPLATE + ' {api_url}\n\nHere is the response from the API:\n\n{api_response}\n\nSummarize this response to answer the original question.\n\nSummary:'
API_RESPONSE_PROMPT = PromptTemplate(input_variables=['api_docs', 'question', 'api_url', 'api_response'], template=API_RESPONSE_PROMPT_TEMPLATE)
from langchain_core.prompts import PromptTemplate
SONG_DATA_SOURCE = '```json\n{{\n    "content": "Lyrics of a song",\n    "attributes": {{\n        "artist": {{\n            "type": "string",\n            "description": "Name of the song artist"\n        }},\n        "length": {{\n            "type": "integer",\n            "description": "Length of the song in seconds"\n        }},\n        "genre": {{\n            "type": "string",\n            "description": "The song genre, one of "pop", "rock" or "rap""\n        }}\n    }}\n}}\n```'
FULL_ANSWER = '```json\n{{\n    "query": "teenager love",\n    "filter": "and(or(eq(\\"artist\\", \\"Taylor Swift\\"), eq(\\"artist\\", \\"Katy Perry\\")), lt(\\"length\\", 180), eq(\\"genre\\", \\"pop\\"))"\n}}\n```'
NO_FILTER_ANSWER = '```json\n{{\n    "query": "",\n    "filter": "NO_FILTER"\n}}\n```'
WITH_LIMIT_ANSWER = '```json\n{{\n    "query": "love",\n    "filter": "NO_FILTER",\n    "limit": 2\n}}\n```'
DEFAULT_EXAMPLES = [{'i': 1, 'data_source': SONG_DATA_SOURCE, 'user_query': 'What are songs by Taylor Swift or Katy Perry about teenage romance under 3 minutes long in the dance pop genre', 'structured_request': FULL_ANSWER}, {'i': 2, 'data_source': SONG_DATA_SOURCE, 'user_query': 'What are songs that were not published on Spotify', 'structured_request': NO_FILTER_ANSWER}]
EXAMPLES_WITH_LIMIT = [{'i': 1, 'data_source': SONG_DATA_SOURCE, 'user_query': 'What are songs by Taylor Swift or Katy Perry about teenage romance under 3 minutes long in the dance pop genre', 'structured_request': FULL_ANSWER}, {'i': 2, 'data_source': SONG_DATA_SOURCE, 'user_query': 'What are songs that were not published on Spotify', 'structured_request': NO_FILTER_ANSWER}, {'i': 3, 'data_source': SONG_DATA_SOURCE, 'user_query': 'What are three songs about love', 'structured_request': WITH_LIMIT_ANSWER}]
EXAMPLE_PROMPT_TEMPLATE = '<< Example {i}. >>\nData Source:\n{data_source}\n\nUser Query:\n{user_query}\n\nStructured Request:\n{structured_request}\n'
EXAMPLE_PROMPT = PromptTemplate.from_template(EXAMPLE_PROMPT_TEMPLATE)
USER_SPECIFIED_EXAMPLE_PROMPT = PromptTemplate.from_template('<< Example {i}. >>\nUser Query:\n{user_query}\n\nStructured Request:\n```json\n{structured_request}\n```\n')
DEFAULT_SCHEMA = '<< Structured Request Schema >>\nWhen responding use a markdown code snippet with a JSON object formatted in the following schema:\n\n```json\n{{{{\n    "query": string \\ text string to compare to document contents\n    "filter": string \\ logical condition statement for filtering documents\n}}}}\n```\n\nThe query string should contain only text that is expected to match the contents of documents. Any conditions in the filter should not be mentioned in the query as well.\n\nA logical condition statement is composed of one or more comparison and logical operation statements.\n\nA comparison statement takes the form: `comp(attr, val)`:\n- `comp` ({allowed_comparators}): comparator\n- `attr` (string):  name of attribute to apply the comparison to\n- `val` (string): is the comparison value\n\nA logical operation statement takes the form `op(statement1, statement2, ...)`:\n- `op` ({allowed_operators}): logical operator\n- `statement1`, `statement2`, ... (comparison statements or logical operation statements): one or more statements to apply the operation to\n\nMake sure that you only use the comparators and logical operators listed above and no others.\nMake sure that filters only refer to attributes that exist in the data source.\nMake sure that filters only use the attributed names with its function names if there are functions applied on them.\nMake sure that filters only use format `YYYY-MM-DD` when handling date data typed values.\nMake sure that filters take into account the descriptions of attributes and only make comparisons that are feasible given the type of data being stored.\nMake sure that filters are only used as needed. If there are no filters that should be applied return "NO_FILTER" for the filter value.'
DEFAULT_SCHEMA_PROMPT = PromptTemplate.from_template(DEFAULT_SCHEMA)
SCHEMA_WITH_LIMIT = '<< Structured Request Schema >>\nWhen responding use a markdown code snippet with a JSON object formatted in the following schema:\n\n```json\n{{{{\n    "query": string \\ text string to compare to document contents\n    "filter": string \\ logical condition statement for filtering documents\n    "limit": int \\ the number of documents to retrieve\n}}}}\n```\n\nThe query string should contain only text that is expected to match the contents of documents. Any conditions in the filter should not be mentioned in the query as well.\n\nA logical condition statement is composed of one or more comparison and logical operation statements.\n\nA comparison statement takes the form: `comp(attr, val)`:\n- `comp` ({allowed_comparators}): comparator\n- `attr` (string):  name of attribute to apply the comparison to\n- `val` (string): is the comparison value\n\nA logical operation statement takes the form `op(statement1, statement2, ...)`:\n- `op` ({allowed_operators}): logical operator\n- `statement1`, `statement2`, ... (comparison statements or logical operation statements): one or more statements to apply the operation to\n\nMake sure that you only use the comparators and logical operators listed above and no others.\nMake sure that filters only refer to attributes that exist in the data source.\nMake sure that filters only use the attributed names with its function names if there are functions applied on them.\nMake sure that filters only use format `YYYY-MM-DD` when handling date data typed values.\nMake sure that filters take into account the descriptions of attributes and only make comparisons that are feasible given the type of data being stored.\nMake sure that filters are only used as needed. If there are no filters that should be applied return "NO_FILTER" for the filter value.\nMake sure the `limit` is always an int value. It is an optional parameter so leave it blank if it does not make sense.\n'
SCHEMA_WITH_LIMIT_PROMPT = PromptTemplate.from_template(SCHEMA_WITH_LIMIT)
DEFAULT_PREFIX = "Your goal is to structure the user's query to match the request schema provided below.\n\n{schema}"
PREFIX_WITH_DATA_SOURCE = DEFAULT_PREFIX + '\n\n<< Data Source >>\n```json\n{{{{\n    "content": "{content}",\n    "attributes": {attributes}\n}}}}\n```\n'
DEFAULT_SUFFIX = '<< Example {i}. >>\nData Source:\n```json\n{{{{\n    "content": "{content}",\n    "attributes": {attributes}\n}}}}\n```\n\nUser Query:\n{{query}}\n\nStructured Request:\n'
SUFFIX_WITHOUT_DATA_SOURCE = '<< Example {i}. >>\nUser Query:\n{{query}}\n\nStructured Request:\n'
from langchain.memory.prompt import ENTITY_EXTRACTION_PROMPT, ENTITY_MEMORY_CONVERSATION_TEMPLATE, ENTITY_SUMMARIZATION_PROMPT, KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT, SUMMARY_PROMPT
from langchain_core.prompts.prompt import PromptTemplate
DEFAULT_TEMPLATE = 'The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.\n\nCurrent conversation:\n{history}\nHuman: {input}\nAI:'
PROMPT = PromptTemplate(input_variables=['history', 'input'], template=DEFAULT_TEMPLATE)
__all__ = ['SUMMARY_PROMPT', 'ENTITY_MEMORY_CONVERSATION_TEMPLATE', 'ENTITY_SUMMARIZATION_PROMPT', 'ENTITY_EXTRACTION_PROMPT', 'KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT', 'PROMPT']
from langchain_core.prompts.prompt import PromptTemplate
_DEFAULT_ENTITY_MEMORY_CONVERSATION_TEMPLATE = 'You are an assistant to a human, powered by a large language model trained by OpenAI.\n\nYou are designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, you are able to generate human-like text based on the input you receive, allowing you to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.\n\nYou are constantly learning and improving, and your capabilities are constantly evolving. You are able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. You have access to some personalized information provided by the human in the Context section below. Additionally, you are able to generate your own text based on the input you receive, allowing you to engage in discussions and provide explanations and descriptions on a wide range of topics.\n\nOverall, you are a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether the human needs help with a specific question or just wants to have a conversation about a particular topic, you are here to assist.\n\nContext:\n{entities}\n\nCurrent conversation:\n{history}\nLast line:\nHuman: {input}\nYou:'
ENTITY_MEMORY_CONVERSATION_TEMPLATE = PromptTemplate(input_variables=['entities', 'history', 'input'], template=_DEFAULT_ENTITY_MEMORY_CONVERSATION_TEMPLATE)
_DEFAULT_SUMMARIZER_TEMPLATE = 'Progressively summarize the lines of conversation provided, adding onto the previous summary returning a new summary.\n\nEXAMPLE\nCurrent summary:\nThe human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good.\n\nNew lines of conversation:\nHuman: Why do you think artificial intelligence is a force for good?\nAI: Because artificial intelligence will help humans reach their full potential.\n\nNew summary:\nThe human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.\nEND OF EXAMPLE\n\nCurrent summary:\n{summary}\n\nNew lines of conversation:\n{new_lines}\n\nNew summary:'
SUMMARY_PROMPT = PromptTemplate(input_variables=['summary', 'new_lines'], template=_DEFAULT_SUMMARIZER_TEMPLATE)
_DEFAULT_ENTITY_EXTRACTION_TEMPLATE = 'You are an AI assistant reading the transcript of a conversation between an AI and a human. Extract all of the proper nouns from the last line of conversation. As a guideline, a proper noun is generally capitalized. You should definitely extract all names and places.\n\nThe conversation history is provided just in case of a coreference (e.g. "What do you know about him" where "him" is defined in a previous line) -- ignore items mentioned there that are not in the last line.\n\nReturn the output as a single comma-separated list, or NONE if there is nothing of note to return (e.g. the user is just issuing a greeting or having a simple conversation).\n\nEXAMPLE\nConversation history:\nPerson #1: how\'s it going today?\nAI: "It\'s going great! How about you?"\nPerson #1: good! busy working on Langchain. lots to do.\nAI: "That sounds like a lot of work! What kind of things are you doing to make Langchain better?"\nLast line:\nPerson #1: i\'m trying to improve Langchain\'s interfaces, the UX, its integrations with various products the user might want ... a lot of stuff.\nOutput: Langchain\nEND OF EXAMPLE\n\nEXAMPLE\nConversation history:\nPerson #1: how\'s it going today?\nAI: "It\'s going great! How about you?"\nPerson #1: good! busy working on Langchain. lots to do.\nAI: "That sounds like a lot of work! What kind of things are you doing to make Langchain better?"\nLast line:\nPerson #1: i\'m trying to improve Langchain\'s interfaces, the UX, its integrations with various products the user might want ... a lot of stuff. I\'m working with Person #2.\nOutput: Langchain, Person #2\nEND OF EXAMPLE\n\nConversation history (for reference only):\n{history}\nLast line of conversation (for extraction):\nHuman: {input}\n\nOutput:'
ENTITY_EXTRACTION_PROMPT = PromptTemplate(input_variables=['history', 'input'], template=_DEFAULT_ENTITY_EXTRACTION_TEMPLATE)
_DEFAULT_ENTITY_SUMMARIZATION_TEMPLATE = 'You are an AI assistant helping a human keep track of facts about relevant people, places, and concepts in their life. Update the summary of the provided entity in the "Entity" section based on the last line of your conversation with the human. If you are writing the summary for the first time, return a single sentence.\nThe update should only include facts that are relayed in the last line of conversation about the provided entity, and should only contain facts about the provided entity.\n\nIf there is no new information about the provided entity or the information is not worth noting (not an important or relevant fact to remember long-term), return the existing summary unchanged.\n\nFull conversation history (for context):\n{history}\n\nEntity to summarize:\n{entity}\n\nExisting summary of {entity}:\n{summary}\n\nLast line of conversation:\nHuman: {input}\nUpdated summary:'
ENTITY_SUMMARIZATION_PROMPT = PromptTemplate(input_variables=['entity', 'summary', 'history', 'input'], template=_DEFAULT_ENTITY_SUMMARIZATION_TEMPLATE)
KG_TRIPLE_DELIMITER = '<|>'
_DEFAULT_KNOWLEDGE_TRIPLE_EXTRACTION_TEMPLATE = f"You are a networked intelligence helping a human track knowledge triples about all relevant people, things, concepts, etc. and integrating them with your knowledge stored within your weights as well as that stored in a knowledge graph. Extract all of the knowledge triples from the last line of conversation. A knowledge triple is a clause that contains a subject, a predicate, and an object. The subject is the entity being described, the predicate is the property of the subject that is being described, and the object is the value of the property.\n\nEXAMPLE\nConversation history:\nPerson #1: Did you hear aliens landed in Area 51?\nAI: No, I didn't hear that. What do you know about Area 51?\nPerson #1: It's a secret military base in Nevada.\nAI: What do you know about Nevada?\nLast line of conversation:\nPerson #1: It's a state in the US. It's also the number 1 producer of gold in the US.\n\nOutput: (Nevada, is a, state){KG_TRIPLE_DELIMITER}(Nevada, is in, US){KG_TRIPLE_DELIMITER}(Nevada, is the number 1 producer of, gold)\nEND OF EXAMPLE\n\nEXAMPLE\nConversation history:\nPerson #1: Hello.\nAI: Hi! How are you?\nPerson #1: I'm good. How are you?\nAI: I'm good too.\nLast line of conversation:\nPerson #1: I'm going to the store.\n\nOutput: NONE\nEND OF EXAMPLE\n\nEXAMPLE\nConversation history:\nPerson #1: What do you know about Descartes?\nAI: Descartes was a French philosopher, mathematician, and scientist who lived in the 17th century.\nPerson #1: The Descartes I'm referring to is a standup comedian and interior designer from Montreal.\nAI: Oh yes, He is a comedian and an interior designer. He has been in the industry for 30 years. His favorite food is baked bean pie.\nLast line of conversation:\nPerson #1: Oh huh. I know Descartes likes to drive antique scooters and play the mandolin.\nOutput: (Descartes, likes to drive, antique scooters){KG_TRIPLE_DELIMITER}(Descartes, plays, mandolin)\nEND OF EXAMPLE\n\nConversation history (for reference only):\n{{history}}\nLast line of conversation (for extraction):\nHuman: {{input}}\n\nOutput:"
KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT = PromptTemplate(input_variables=['history', 'input'], template=_DEFAULT_KNOWLEDGE_TRIPLE_EXTRACTION_TEMPLATE)
from langchain_core.prompts.prompt import PromptTemplate
Prompt = PromptTemplate
__all__ = ['PromptTemplate', 'Prompt']
agent_instructions = "You are a helpful assistant. Help the user answer any questions.\n\nYou have access to the following tools:\n\n{tools}\n\nIn order to use a tool, you can use <tool></tool> and <tool_input></tool_input> tags. You will then get back a response in the form <observation></observation>\nFor example, if you have a tool called 'search' that could run a google search, in order to search for the weather in SF you would respond:\n\n<tool>search</tool><tool_input>weather in SF</tool_input>\n<observation>64 degrees</observation>\n\nWhen you are done, respond with a final answer between <final_answer></final_answer>. For example:\n\n<final_answer>The weather in SF is 64 degrees</final_answer>\n\nBegin!\n\nQuestion: {question}"
from langchain_core.prompts.prompt import PromptTemplate
_DEFAULT_TEMPLATE = 'Question: Who lived longer, Muhammad Ali or Alan Turing?\nAre follow up questions needed here: Yes.\nFollow up: How old was Muhammad Ali when he died?\nIntermediate answer: Muhammad Ali was 74 years old when he died.\nFollow up: How old was Alan Turing when he died?\nIntermediate answer: Alan Turing was 41 years old when he died.\nSo the final answer is: Muhammad Ali\n\nQuestion: When was the founder of craigslist born?\nAre follow up questions needed here: Yes.\nFollow up: Who was the founder of craigslist?\nIntermediate answer: Craigslist was founded by Craig Newmark.\nFollow up: When was Craig Newmark born?\nIntermediate answer: Craig Newmark was born on December 6, 1952.\nSo the final answer is: December 6, 1952\n\nQuestion: Who was the maternal grandfather of George Washington?\nAre follow up questions needed here: Yes.\nFollow up: Who was the mother of George Washington?\nIntermediate answer: The mother of George Washington was Mary Ball Washington.\nFollow up: Who was the father of Mary Ball Washington?\nIntermediate answer: The father of Mary Ball Washington was Joseph Ball.\nSo the final answer is: Joseph Ball\n\nQuestion: Are both the directors of Jaws and Casino Royale from the same country?\nAre follow up questions needed here: Yes.\nFollow up: Who is the director of Jaws?\nIntermediate answer: The director of Jaws is Steven Spielberg.\nFollow up: Where is Steven Spielberg from?\nIntermediate answer: The United States.\nFollow up: Who is the director of Casino Royale?\nIntermediate answer: The director of Casino Royale is Martin Campbell.\nFollow up: Where is Martin Campbell from?\nIntermediate answer: New Zealand.\nSo the final answer is: No\n\nQuestion: {input}\nAre followup questions needed here:{agent_scratchpad}'
PROMPT = PromptTemplate(input_variables=['input', 'agent_scratchpad'], template=_DEFAULT_TEMPLATE)
PREFIX = 'Respond to the human as helpfully and accurately as possible. You have access to the following tools:'
FORMAT_INSTRUCTIONS = 'Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\nValid "action" values: "Final Answer" or {tool_names}\n\nProvide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}}}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{{{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}}}\n```'
SUFFIX = 'Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation:.\nThought:'
PREFIX = 'Assistant is a large language model trained by OpenAI.\n\nAssistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.\n\nAssistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.\n\nOverall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.\n\nTOOLS:\n------\n\nAssistant has access to the following tools:'
FORMAT_INSTRUCTIONS = 'To use a tool, please use the following format:\n\n```\nThought: Do I need to use a tool? Yes\nAction: the action to take, should be one of [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n```\n\nWhen you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:\n\n```\nThought: Do I need to use a tool? No\n{ai_prefix}: [your response here]\n```'
SUFFIX = 'Begin!\n\nPrevious conversation history:\n{chat_history}\n\nNew input: {input}\n{agent_scratchpad}'
TEMPLATE_TOOL_RESPONSE = "TOOL RESPONSE: \n---------------------\n{observation}\n\nUSER'S INPUT\n--------------------\n\nOkay, so what is the response to my last comment? If using information obtained from the tools you must mention it explicitly without mentioning the tool names - I have forgotten all TOOL RESPONSES! Remember to respond with a markdown code snippet of a json blob with a single action, and NOTHING else - even if you just want to respond to the user. Do NOT respond with anything except a JSON snippet no matter what!"
SYSTEM_MESSAGE_PREFIX = 'Answer the following questions as best you can. You have access to the following tools:'
FORMAT_INSTRUCTIONS = 'The way you use the tools is by specifying a json blob.\nSpecifically, this json should have a `action` key (with the name of the tool to use) and a `action_input` key (with the input to the tool going here).\n\nThe only values that should be in the "action" field are: {tool_names}\n\nThe $JSON_BLOB should only contain a SINGLE action, do NOT return a list of multiple actions. Here is an example of a valid $JSON_BLOB:\n\n```\n{{{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}}}\n```\n\nALWAYS use the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction:\n```\n$JSON_BLOB\n```\nObservation: the result of the action\n... (this Thought/Action/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question'
SYSTEM_MESSAGE_SUFFIX = 'Begin! Reminder to always use the exact characters `Final Answer` when responding.'
HUMAN_MESSAGE = '{input}\n\n{agent_scratchpad}'
PREFIX = 'Answer the following questions as best you can. You have access to the following tools:'
FORMAT_INSTRUCTIONS = 'Use the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question'
SUFFIX = 'Begin!\n\nQuestion: {input}\nThought:{agent_scratchpad}'
from typing import TYPE_CHECKING, Any
from langchain._api import create_importer
if TYPE_CHECKING:
    from langchain_community.agent_toolkits.sql.prompt import SQL_FUNCTIONS_SUFFIX, SQL_PREFIX, SQL_SUFFIX
DEPRECATED_LOOKUP = {'SQL_PREFIX': 'langchain_community.agent_toolkits.sql.prompt', 'SQL_SUFFIX': 'langchain_community.agent_toolkits.sql.prompt', 'SQL_FUNCTIONS_SUFFIX': 'langchain_community.agent_toolkits.sql.prompt'}
_import_attribute = create_importer(__package__, deprecated_lookups=DEPRECATED_LOOKUP)
__all__ = ['SQL_PREFIX', 'SQL_SUFFIX', 'SQL_FUNCTIONS_SUFFIX']
from typing import TYPE_CHECKING, Any
from langchain._api import create_importer
if TYPE_CHECKING:
    from langchain_community.agent_toolkits.json.prompt import JSON_PREFIX, JSON_SUFFIX
DEPRECATED_LOOKUP = {'JSON_PREFIX': 'langchain_community.agent_toolkits.json.prompt', 'JSON_SUFFIX': 'langchain_community.agent_toolkits.json.prompt'}
_import_attribute = create_importer(__package__, deprecated_lookups=DEPRECATED_LOOKUP)
__all__ = ['JSON_PREFIX', 'JSON_SUFFIX']
PREFIX = 'You are an agent designed to answer questions about sets of documents.\nYou have access to tools for interacting with the documents, and the inputs to the tools are questions.\nSometimes, you will be asked to provide sources for your questions, in which case you should use the appropriate tool to do so.\nIf the question does not seem relevant to any of the tools provided, just return "I don\'t know" as the answer.\n'
ROUTER_PREFIX = 'You are an agent designed to answer questions.\nYou have access to tools for interacting with different sources, and the inputs to the tools are questions.\nYour main task is to decide which of the tools is relevant for answering question at hand.\nFor complex questions, you can break the question down into sub questions and use tools to answers the sub questions.\n'
from typing import TYPE_CHECKING, Any
from langchain._api import create_importer
if TYPE_CHECKING:
    from langchain_community.agent_toolkits.powerbi.prompt import POWERBI_CHAT_PREFIX, POWERBI_CHAT_SUFFIX, POWERBI_PREFIX, POWERBI_SUFFIX
DEPRECATED_LOOKUP = {'POWERBI_CHAT_PREFIX': 'langchain_community.agent_toolkits.powerbi.prompt', 'POWERBI_CHAT_SUFFIX': 'langchain_community.agent_toolkits.powerbi.prompt', 'POWERBI_PREFIX': 'langchain_community.agent_toolkits.powerbi.prompt', 'POWERBI_SUFFIX': 'langchain_community.agent_toolkits.powerbi.prompt'}
_import_attribute = create_importer(__package__, deprecated_lookups=DEPRECATED_LOOKUP)
__all__ = ['POWERBI_PREFIX', 'POWERBI_SUFFIX', 'POWERBI_CHAT_PREFIX', 'POWERBI_CHAT_SUFFIX']
from typing import TYPE_CHECKING, Any
from langchain._api import create_importer
if TYPE_CHECKING:
    from langchain_community.agent_toolkits.openapi.prompt import DESCRIPTION, OPENAPI_PREFIX, OPENAPI_SUFFIX
DEPRECATED_LOOKUP = {'DESCRIPTION': 'langchain_community.agent_toolkits.openapi.prompt', 'OPENAPI_PREFIX': 'langchain_community.agent_toolkits.openapi.prompt', 'OPENAPI_SUFFIX': 'langchain_community.agent_toolkits.openapi.prompt'}
_import_attribute = create_importer(__package__, deprecated_lookups=DEPRECATED_LOOKUP)
__all__ = ['OPENAPI_PREFIX', 'OPENAPI_SUFFIX', 'DESCRIPTION']
from typing import TYPE_CHECKING, Any
from langchain._api import create_importer
if TYPE_CHECKING:
    from langchain_community.agent_toolkits.spark_sql.prompt import SQL_PREFIX, SQL_SUFFIX
DEPRECATED_LOOKUP = {'SQL_PREFIX': 'langchain_community.agent_toolkits.spark_sql.prompt', 'SQL_SUFFIX': 'langchain_community.agent_toolkits.spark_sql.prompt'}
_import_attribute = create_importer(__package__, deprecated_lookups=DEPRECATED_LOOKUP)
__all__ = ['SQL_PREFIX', 'SQL_SUFFIX']
PREFIX = 'Assistant is a large language model trained by OpenAI.\n\nAssistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.\n\nAssistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.\n\nOverall, Assistant is a powerful system that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.'
FORMAT_INSTRUCTIONS = 'RESPONSE FORMAT INSTRUCTIONS\n----------------------------\n\nWhen responding to me, please output a response in one of two formats:\n\n**Option 1:**\nUse this if you want the human to use a tool.\nMarkdown code snippet formatted in the following schema:\n\n```json\n{{{{\n    "action": string, \\\\ The action to take. Must be one of {tool_names}\n    "action_input": string \\\\ The input to the action\n}}}}\n```\n\n**Option #2:**\nUse this if you want to respond directly to the human. Markdown code snippet formatted in the following schema:\n\n```json\n{{{{\n    "action": "Final Answer",\n    "action_input": string \\\\ You should put what you want to return to use here\n}}}}\n```'
SUFFIX = "TOOLS\n------\nAssistant can ask the user to use tools to look up information that may be helpful in answering the users original question. The tools the human can use are:\n\n{{tools}}\n\n{format_instructions}\n\nUSER'S INPUT\n--------------------\nHere is the user's input (remember to respond with a markdown code snippet of a json blob with a single action, and NOTHING else):\n\n{{{{input}}}}"
TEMPLATE_TOOL_RESPONSE = "TOOL RESPONSE: \n---------------------\n{observation}\n\nUSER'S INPUT\n--------------------\n\nOkay, so what is the response to my last comment? If using information obtained from the tools you must mention it explicitly without mentioning the tool names - I have forgotten all TOOL RESPONSES! Remember to respond with a markdown code snippet of a json blob with a single action, and NOTHING else."